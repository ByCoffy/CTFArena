import json
import logging
import docker
from datetime import datetime, timedelta
from flask import current_app
from app import db
from app.models import DockerInstance

logger = logging.getLogger(__name__)


class DockerService:
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            base_url = current_app.config.get('DOCKER_BASE_URL', 'unix://var/run/docker.sock')
            cls._client = docker.DockerClient(base_url=base_url)
        return cls._client

    @classmethod
    def ensure_network(cls):
        client = cls.get_client()
        network_name = current_app.config.get('DOCKER_NETWORK', 'ctf_challenges')
        try:
            client.networks.get(network_name)
        except docker.errors.NotFound:
            client.networks.create(
                network_name,
                driver='bridge',
                internal=True
            )
            logger.info(f"Created Docker network: {network_name}")

    @classmethod
    def start_instance(cls, user, challenge):
        """Create and start a Docker container for a user's challenge."""
        # Check for existing active instance
        existing = DockerInstance.query.filter_by(
            user_id=user.id,
            challenge_id=challenge.id,
            status='running'
        ).first()
        if existing and not existing.is_expired():
            return existing, None

        # Check max instances per user
        max_instances = current_app.config.get('DOCKER_MAX_INSTANCES_PER_USER', 3)
        active_count = DockerInstance.query.filter_by(
            user_id=user.id,
            status='running'
        ).count()
        if active_count >= max_instances:
            return None, f'Límite de {max_instances} instancias activas alcanzado. Para una instancia antes de iniciar otra.'

        client = cls.get_client()
        cls.ensure_network()

        timeout_minutes = challenge.docker_timeout or current_app.config.get('DOCKER_DEFAULT_TIMEOUT', 30)
        memory_limit = challenge.docker_memory_limit or current_app.config.get('DOCKER_DEFAULT_MEMORY', '256m')
        cpu_limit = challenge.docker_cpu_limit or current_app.config.get('DOCKER_DEFAULT_CPU', 0.5)
        network_name = current_app.config.get('DOCKER_NETWORK', 'ctf_challenges')

        container_name = f"ctf_{user.id}_{challenge.id}_{int(datetime.utcnow().timestamp())}"

        # Parse ports to expose
        port_bindings = {}
        ports_config = {}
        if challenge.docker_ports:
            try:
                ports_def = json.loads(challenge.docker_ports)
                for port_str in ports_def.keys():
                    container_port = f"{port_str}/tcp"
                    port_bindings[container_port] = None  # Let Docker assign host port
                    ports_config[port_str] = ports_def[port_str]
            except (json.JSONDecodeError, AttributeError):
                pass

        # Create instance record
        instance = DockerInstance(
            user_id=user.id,
            challenge_id=challenge.id,
            container_name=container_name,
            status='creating',
            expires_at=datetime.utcnow() + timedelta(minutes=timeout_minutes)
        )
        db.session.add(instance)
        db.session.commit()

        try:
            container = client.containers.run(
                image=challenge.docker_image,
                name=container_name,
                detach=True,
                tty=True,
                stdin_open=True,
                network=network_name,
                mem_limit=memory_limit,
                nano_cpus=int(cpu_limit * 1e9),
                pids_limit=100,
                ports=port_bindings if port_bindings else None,
                privileged=False,
                read_only=False,
                security_opt=['no-new-privileges:true'],
                environment={
                    'CTF_USER': user.username,
                    'CTF_CHALLENGE': challenge.title,
                },
                labels={
                    'ctf.user_id': str(user.id),
                    'ctf.challenge_id': str(challenge.id),
                    'ctf.instance_id': str(instance.id),
                    'ctf.managed': 'true',
                }
            )

            # Get actual port mappings
            container.reload()
            actual_ports = {}
            if container.attrs.get('NetworkSettings', {}).get('Ports'):
                for container_port, host_bindings in container.attrs['NetworkSettings']['Ports'].items():
                    if host_bindings:
                        port_num = container_port.split('/')[0]
                        host_port = host_bindings[0]['HostPort']
                        actual_ports[port_num] = {
                            'host_port': host_port,
                            'service': ports_config.get(port_num, 'unknown')
                        }

            instance.container_id = container.id
            instance.status = 'running'
            instance.port_mappings = json.dumps(actual_ports) if actual_ports else None
            db.session.commit()

            logger.info(f"Started container {container_name} for user {user.username} challenge {challenge.title}")
            return instance, None

        except docker.errors.ImageNotFound:
            instance.status = 'error'
            instance.error_message = f'Imagen Docker no encontrada: {challenge.docker_image}'
            db.session.commit()
            return None, instance.error_message

        except docker.errors.APIError as e:
            instance.status = 'error'
            instance.error_message = str(e)[:500]
            db.session.commit()
            logger.error(f"Docker API error: {e}")
            return None, f'Error al crear el contenedor: {str(e)[:200]}'

    @classmethod
    def stop_instance(cls, instance):
        """Stop and remove a Docker container."""
        client = cls.get_client()
        try:
            container = client.containers.get(instance.container_id)
            container.stop(timeout=5)
            container.remove(force=True)
        except docker.errors.NotFound:
            pass
        except docker.errors.APIError as e:
            logger.error(f"Error stopping container {instance.container_name}: {e}")

        instance.status = 'stopped'
        db.session.commit()
        logger.info(f"Stopped container {instance.container_name}")

    @classmethod
    def restart_instance(cls, instance):
        """Restart a container (stop + start new)."""
        cls.stop_instance(instance)
        from app.models import User, Challenge
        user = db.session.get(User, instance.user_id)
        challenge = db.session.get(Challenge, instance.challenge_id)
        return cls.start_instance(user, challenge)

    @classmethod
    def get_instance_status(cls, instance):
        """Get real-time status of a container."""
        if instance.status != 'running':
            return instance.status

        if instance.is_expired():
            cls.stop_instance(instance)
            return 'stopped'

        client = cls.get_client()
        try:
            container = client.containers.get(instance.container_id)
            return container.status
        except docker.errors.NotFound:
            instance.status = 'stopped'
            db.session.commit()
            return 'stopped'

    @classmethod
    def cleanup_expired(cls, app):
        """Remove expired containers. Called periodically."""
        with app.app_context():
            expired = DockerInstance.query.filter(
                DockerInstance.status == 'running',
                DockerInstance.expires_at < datetime.utcnow()
            ).all()

            for instance in expired:
                logger.info(f"Cleaning up expired container: {instance.container_name}")
                cls.stop_instance(instance)

            return len(expired)

    @classmethod
    def exec_attach(cls, instance):
        """Create an exec instance attached to the container for terminal I/O."""
        client = cls.get_client()
        api_client = client.api
        try:
            exec_id = api_client.exec_create(
                instance.container_id,
                cmd='/bin/bash',
                stdin=True,
                tty=True,
                stdout=True,
                stderr=True
            )
            socket = api_client.exec_start(
                exec_id['Id'],
                socket=True,
                tty=True
            )
            return exec_id['Id'], socket
        except docker.errors.APIError as e:
            logger.error(f"Error attaching to container {instance.container_name}: {e}")
            return None, None

    @classmethod
    def exec_resize(cls, exec_id, height, width):
        """Resize the TTY of an exec instance."""
        client = cls.get_client()
        try:
            client.api.exec_resize(exec_id, height=height, width=width)
        except docker.errors.APIError:
            pass

    @classmethod
    def get_active_instances_count(cls):
        """Get count of running instances."""
        return DockerInstance.query.filter_by(status='running').count()

    @classmethod
    def get_all_active_instances(cls):
        """Get all running instances for admin view."""
        return DockerInstance.query.filter_by(status='running').order_by(
            DockerInstance.created_at.desc()
        ).all()

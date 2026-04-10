import threading
import logging
from flask_login import current_user
from flask_socketio import emit, disconnect
from app.models import DockerInstance
from app.services.docker_service import DockerService

logger = logging.getLogger(__name__)

# Store active terminal sessions: {sid: {'exec_id': ..., 'socket': ..., 'thread': ...}}
terminal_sessions = {}


def register_events(socketio):
    """Register WebSocket events for terminal I/O."""

    @socketio.on('connect', namespace='/terminal')
    def handle_connect():
        if not current_user.is_authenticated:
            disconnect()
            return
        logger.info(f"Terminal WebSocket connected: user={current_user.username}")

    @socketio.on('disconnect', namespace='/terminal')
    def handle_disconnect():
        sid = getattr(current_user, 'id', None)
        session_key = f"{sid}_{id(current_user)}"
        # Clean up terminal sessions for this connection
        for key in list(terminal_sessions.keys()):
            if key.startswith(f"{current_user.id}_"):
                session = terminal_sessions.pop(key, None)
                if session and session.get('socket'):
                    try:
                        session['socket'].close()
                    except Exception:
                        pass
        logger.info(f"Terminal WebSocket disconnected: user={getattr(current_user, 'username', 'unknown')}")

    @socketio.on('start_terminal', namespace='/terminal')
    def handle_start_terminal(data):
        if not current_user.is_authenticated:
            emit('terminal_error', {'message': 'No autenticado.'})
            disconnect()
            return

        instance_id = data.get('instance_id')
        if not instance_id:
            emit('terminal_error', {'message': 'ID de instancia no proporcionado.'})
            return

        instance = DockerInstance.query.get(instance_id)
        if not instance:
            emit('terminal_error', {'message': 'Instancia no encontrada.'})
            return

        # Security: verify the instance belongs to the current user
        if instance.user_id != current_user.id:
            emit('terminal_error', {'message': 'Acceso denegado.'})
            return

        if instance.status != 'running':
            emit('terminal_error', {'message': 'La instancia no está activa.'})
            return

        if instance.is_expired():
            emit('terminal_error', {'message': 'La instancia ha expirado.'})
            return

        exec_id, sock = DockerService.exec_attach(instance)
        if not exec_id:
            emit('terminal_error', {'message': 'Error al conectar con el contenedor.'})
            return

        session_key = f"{current_user.id}_{instance_id}"

        # Clean up previous session if exists
        if session_key in terminal_sessions:
            old_session = terminal_sessions.pop(session_key)
            if old_session.get('socket'):
                try:
                    old_session['socket'].close()
                except Exception:
                    pass

        terminal_sessions[session_key] = {
            'exec_id': exec_id,
            'socket': sock,
            'instance_id': instance_id,
        }

        # Start reading output in a background thread
        def read_output():
            try:
                raw_socket = sock._sock if hasattr(sock, '_sock') else sock
                while True:
                    data = raw_socket.recv(4096)
                    if not data:
                        break
                    socketio.emit('terminal_output', {'data': data.decode('utf-8', errors='replace')},
                                  namespace='/terminal', to=data.get('sid') if isinstance(data, dict) else None)
            except Exception as e:
                logger.debug(f"Terminal read ended: {e}")
            finally:
                socketio.emit('terminal_output', {'data': '\r\n\x1b[31m[Sesión terminada]\x1b[0m\r\n'},
                              namespace='/terminal')

        # Use a simpler approach - read from the Docker stream
        def stream_output():
            try:
                raw_socket = sock._sock if hasattr(sock, '_sock') else sock
                while session_key in terminal_sessions:
                    try:
                        chunk = raw_socket.recv(4096)
                        if not chunk:
                            break
                        socketio.emit('terminal_output',
                                      {'data': chunk.decode('utf-8', errors='replace')},
                                      namespace='/terminal')
                    except (ConnectionError, OSError):
                        break
            except Exception as e:
                logger.debug(f"Stream ended: {e}")
            finally:
                socketio.emit('terminal_output',
                              {'data': '\r\n\x1b[33m[Conexión terminada]\x1b[0m\r\n'},
                              namespace='/terminal')

        thread = threading.Thread(target=stream_output, daemon=True)
        thread.start()
        terminal_sessions[session_key]['thread'] = thread

        emit('terminal_ready', {'message': 'Terminal conectada.'})

    @socketio.on('terminal_input', namespace='/terminal')
    def handle_terminal_input(data):
        if not current_user.is_authenticated:
            return

        instance_id = data.get('instance_id')
        session_key = f"{current_user.id}_{instance_id}"
        session = terminal_sessions.get(session_key)

        if not session:
            emit('terminal_error', {'message': 'Sesión no encontrada. Reconecta la terminal.'})
            return

        try:
            raw_socket = session['socket']._sock if hasattr(session['socket'], '_sock') else session['socket']
            raw_socket.send(data['data'].encode('utf-8'))
        except Exception as e:
            emit('terminal_error', {'message': 'Error al enviar datos al contenedor.'})
            logger.error(f"Terminal input error: {e}")

    @socketio.on('terminal_resize', namespace='/terminal')
    def handle_terminal_resize(data):
        if not current_user.is_authenticated:
            return

        instance_id = data.get('instance_id')
        session_key = f"{current_user.id}_{instance_id}"
        session = terminal_sessions.get(session_key)

        if session:
            DockerService.exec_resize(
                session['exec_id'],
                height=data.get('rows', 24),
                width=data.get('cols', 80)
            )

import json
from flask import redirect, url_for, flash, jsonify, request
from flask_login import login_required, current_user
from app.docker_challenges import bp
from app.models import Challenge, DockerInstance
from app.services.docker_service import DockerService
from app import db


@bp.route('/<int:challenge_id>/start', methods=['POST'])
@login_required
def start_instance(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)

    if not challenge.is_docker() or not challenge.is_available():
        flash('Este reto no está disponible.', 'warning')
        return redirect(url_for('challenges.challenge_detail', challenge_id=challenge_id))

    instance, error = DockerService.start_instance(current_user, challenge)
    if error:
        flash(f'Error al iniciar el reto: {error}', 'danger')
    else:
        flash('Instancia iniciada correctamente.', 'success')

    return redirect(url_for('challenges.challenge_detail', challenge_id=challenge_id))


@bp.route('/<int:challenge_id>/stop', methods=['POST'])
@login_required
def stop_instance(challenge_id):
    instance = DockerInstance.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id,
        status='running'
    ).first()

    if not instance:
        flash('No tienes una instancia activa para este reto.', 'warning')
        return redirect(url_for('challenges.challenge_detail', challenge_id=challenge_id))

    DockerService.stop_instance(instance)
    flash('Instancia detenida.', 'info')
    return redirect(url_for('challenges.challenge_detail', challenge_id=challenge_id))


@bp.route('/<int:challenge_id>/restart', methods=['POST'])
@login_required
def restart_instance(challenge_id):
    instance = DockerInstance.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id,
        status='running'
    ).first()

    if not instance:
        flash('No tienes una instancia activa para reiniciar.', 'warning')
        return redirect(url_for('challenges.challenge_detail', challenge_id=challenge_id))

    new_instance, error = DockerService.restart_instance(instance)
    if error:
        flash(f'Error al reiniciar: {error}', 'danger')
    else:
        flash('Instancia reiniciada correctamente.', 'success')

    return redirect(url_for('challenges.challenge_detail', challenge_id=challenge_id))


@bp.route('/<int:challenge_id>/status')
@login_required
def instance_status(challenge_id):
    instance = DockerInstance.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id,
        status='running'
    ).first()

    if not instance:
        return jsonify({'status': 'stopped', 'active': False})

    status = DockerService.get_instance_status(instance)
    port_mappings = json.loads(instance.port_mappings) if instance.port_mappings else {}

    return jsonify({
        'status': status,
        'active': status == 'running',
        'time_remaining': instance.time_remaining_seconds(),
        'port_mappings': port_mappings,
        'container_name': instance.container_name,
        'instance_id': instance.id
    })

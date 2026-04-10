from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.challenges import bp
from app.models import Challenge, Category, Solve, Hint, SubmissionLog, DockerInstance
from app import db
from datetime import datetime, timezone


@bp.route('/')
def challenge_list():
    categories = Category.query.all()
    selected_cat = request.args.get('category', 'all')
    selected_diff = request.args.get('difficulty', 'all')

    query = Challenge.query.filter_by(is_active=True)

    if selected_cat != 'all':
        query = query.filter_by(category_id=int(selected_cat))
    if selected_diff != 'all':
        query = query.filter_by(difficulty=selected_diff)

    challenges = query.order_by(Challenge.points.asc()).all()

    return render_template('challenges/list.html',
                         challenges=challenges,
                         categories=categories,
                         selected_cat=selected_cat,
                         selected_diff=selected_diff)


@bp.route('/<int:challenge_id>')
@login_required
def challenge_detail(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)

    if not challenge.is_active:
        flash('Este reto no está disponible.', 'warning')
        return redirect(url_for('challenges.challenge_list'))

    solved = current_user.has_solved(challenge)
    solvers = challenge.get_solvers()
    first_blood = challenge.get_first_blood()
    hints = challenge.hints.order_by(Hint.order.asc()).all()

    # Check which hints the user has unlocked
    unlocked_hint_ids = [h.id for h in current_user.unlocked_hints.all()]

    # Docker instance info
    docker_instance = None
    if challenge.is_docker():
        docker_instance = DockerInstance.query.filter_by(
            user_id=current_user.id,
            challenge_id=challenge.id,
            status='running'
        ).first()
        # Check if expired
        if docker_instance and docker_instance.is_expired():
            from app.services.docker_service import DockerService
            DockerService.stop_instance(docker_instance)
            docker_instance = None

    return render_template('challenges/detail.html',
                         challenge=challenge,
                         solved=solved,
                         solvers=solvers,
                         first_blood=first_blood,
                         hints=hints,
                         unlocked_hint_ids=unlocked_hint_ids,
                         docker_instance=docker_instance)


@bp.route('/<int:challenge_id>/submit', methods=['POST'])
@login_required
def submit_flag(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)

    if not challenge.is_available():
        flash('Este reto no está disponible en este momento.', 'warning')
        return redirect(url_for('challenges.challenge_detail', challenge_id=challenge_id))

    if current_user.has_solved(challenge):
        flash('Ya has resuelto este reto.', 'info')
        return redirect(url_for('challenges.challenge_detail', challenge_id=challenge_id))

    submitted_flag = request.form.get('flag', '').strip()

    # Log the submission
    log = SubmissionLog(
        user_id=current_user.id,
        challenge_id=challenge.id,
        submitted_flag=submitted_flag,
        is_correct=(submitted_flag == challenge.flag),
        ip_address=request.remote_addr
    )
    db.session.add(log)

    if submitted_flag == challenge.flag:
        # Check if first blood
        is_first = challenge.solve_count() == 0

        solve = Solve(
            user_id=current_user.id,
            challenge_id=challenge.id,
            is_first_blood=is_first
        )
        db.session.add(solve)
        db.session.commit()

        if is_first:
            bonus = current_app.config.get('FIRST_BLOOD_BONUS', 50)
            flash(f'🩸 ¡FIRST BLOOD! +{challenge.points} puntos +{bonus} bonus', 'success')
        else:
            flash(f'🚩 ¡Flag correcta! +{challenge.points} puntos', 'success')
    else:
        db.session.commit()
        flash('❌ Flag incorrecta. Sigue intentando.', 'danger')

    return redirect(url_for('challenges.challenge_detail', challenge_id=challenge_id))


@bp.route('/<int:challenge_id>/hint/<int:hint_id>/unlock', methods=['POST'])
@login_required
def unlock_hint(challenge_id, hint_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    hint = Hint.query.get_or_404(hint_id)

    if hint.challenge_id != challenge.id:
        flash('Pista no válida.', 'danger')
        return redirect(url_for('challenges.challenge_detail', challenge_id=challenge_id))

    if hint in current_user.unlocked_hints.all():
        flash('Ya has desbloqueado esta pista.', 'info')
        return redirect(url_for('challenges.challenge_detail', challenge_id=challenge_id))

    # Unlock the hint
    current_user.unlocked_hints.append(hint)
    db.session.commit()

    flash(f'🔓 Pista desbloqueada. Penalización: -{hint.cost} puntos.', 'warning')
    return redirect(url_for('challenges.challenge_detail', challenge_id=challenge_id))

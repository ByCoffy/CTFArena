from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager


# --- Association Tables ---

team_members = db.Table('team_members',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('team_id', db.Integer, db.ForeignKey('teams.id'), primary_key=True),
    db.Column('joined_at', db.DateTime, default=lambda: datetime.now(timezone.utc))
)

hint_unlocks = db.Table('hint_unlocks',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('hint_id', db.Integer, db.ForeignKey('hints.id'), primary_key=True),
    db.Column('unlocked_at', db.DateTime, default=lambda: datetime.now(timezone.utc))
)


# --- Models ---

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active_user = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Avatar/profile
    bio = db.Column(db.String(500), default='')
    avatar_url = db.Column(db.String(256), default='')

    # Relationships
    solves = db.relationship('Solve', backref='user', lazy='dynamic')
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)
    owned_team = db.relationship('Team', backref='owner', lazy='dynamic',
                                  foreign_keys='Team.owner_id')
    unlocked_hints = db.relationship('Hint', secondary=hint_unlocks, lazy='dynamic',
                                      backref=db.backref('unlocked_by', lazy='dynamic'))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_solved(self, challenge):
        return self.solves.filter_by(challenge_id=challenge.id).first() is not None

    def get_score(self):
        """Calculate total score including first blood bonuses and hint penalties."""
        total = 0
        for solve in self.solves.all():
            challenge = solve.challenge
            points = challenge.points
            # First blood bonus
            if solve.is_first_blood:
                from flask import current_app
                points += current_app.config.get('FIRST_BLOOD_BONUS', 50)
            total += points

        # Subtract hint penalties
        for hint in self.unlocked_hints.all():
            total -= hint.cost

        return max(total, 0)

    def get_solve_count(self):
        return self.solves.count()

    def __repr__(self):
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(id):
    return db.session.get(User, int(id))


class Team(db.Model):
    __tablename__ = 'teams'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False, index=True)
    description = db.Column(db.String(500), default='')
    invite_code = db.Column(db.String(32), unique=True, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Members
    members = db.relationship('User', backref='team_ref',
                               foreign_keys='User.team_id', lazy='dynamic')

    def get_score(self):
        """Sum of all members' scores."""
        return sum(m.get_score() for m in self.members.all())

    def get_solve_count(self):
        return sum(m.get_solve_count() for m in self.members.all())

    def member_count(self):
        return self.members.count()

    def __repr__(self):
        return f'<Team {self.name}>'


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256), default='')
    icon = db.Column(db.String(64), default='bi-puzzle')
    color = db.Column(db.String(7), default='#00ff88')

    challenges = db.relationship('Challenge', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'


class Challenge(db.Model):
    __tablename__ = 'challenges'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=False)
    flag = db.Column(db.String(256), nullable=False)
    points = db.Column(db.Integer, nullable=False, default=100)
    difficulty = db.Column(db.String(20), nullable=False, default='medium')  # easy, medium, hard, insane
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    author = db.Column(db.String(64), default='Admin')

    # Challenge type: static (default) or docker
    challenge_type = db.Column(db.String(20), nullable=False, default='static')

    # Time-limited challenge
    starts_at = db.Column(db.DateTime, nullable=True)
    ends_at = db.Column(db.DateTime, nullable=True)

    # File attachment
    attachment_filename = db.Column(db.String(256), nullable=True)

    # URL for external challenge (e.g., Docker container)
    challenge_url = db.Column(db.String(512), nullable=True)

    # Docker-specific fields
    docker_image = db.Column(db.String(256), nullable=True)
    docker_ports = db.Column(db.Text, nullable=True)  # JSON: {"22": "ssh", "80": "http"}
    docker_timeout = db.Column(db.Integer, nullable=True, default=30)  # minutes
    docker_memory_limit = db.Column(db.String(20), nullable=True, default='256m')
    docker_cpu_limit = db.Column(db.Float, nullable=True, default=0.5)

    # Relationships
    solves = db.relationship('Solve', backref='challenge', lazy='dynamic')
    hints = db.relationship('Hint', backref='challenge', lazy='dynamic',
                             order_by='Hint.order')
    docker_instances = db.relationship('DockerInstance', backref='challenge', lazy='dynamic')

    def solve_count(self):
        return self.solves.count()

    def is_available(self):
        """Check if challenge is within its time window."""
        if not self.is_active:
            return False
        now = datetime.now(timezone.utc)
        if self.starts_at and now < self.starts_at:
            return False
        if self.ends_at and now > self.ends_at:
            return False
        return True

    def is_timed(self):
        return self.starts_at is not None or self.ends_at is not None

    def time_remaining(self):
        if self.ends_at:
            now = datetime.now(timezone.utc)
            delta = self.ends_at - now
            if delta.total_seconds() > 0:
                return delta
        return None

    def get_first_blood(self):
        """Return the first solve for this challenge."""
        return self.solves.order_by(Solve.solved_at.asc()).first()

    def get_solvers(self):
        """Return all users who solved this challenge, ordered by time."""
        return self.solves.order_by(Solve.solved_at.asc()).all()

    def get_difficulty_badge(self):
        badges = {
            'easy': ('Fácil', 'success'),
            'medium': ('Media', 'warning'),
            'hard': ('Difícil', 'danger'),
            'insane': ('Insane', 'dark')
        }
        return badges.get(self.difficulty, ('Media', 'warning'))

    def is_docker(self):
        return self.challenge_type == 'docker'

    def __repr__(self):
        return f'<Challenge {self.title}>'


class Solve(db.Model):
    __tablename__ = 'solves'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id'), nullable=False)
    solved_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    is_first_blood = db.Column(db.Boolean, default=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'challenge_id', name='unique_user_challenge'),
    )

    def __repr__(self):
        return f'<Solve user={self.user_id} challenge={self.challenge_id}>'


class Hint(db.Model):
    __tablename__ = 'hints'

    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    cost = db.Column(db.Integer, nullable=False, default=25)
    order = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Hint challenge={self.challenge_id} cost={self.cost}>'


class SubmissionLog(db.Model):
    """Log all flag submissions (correct and incorrect) for security monitoring."""
    __tablename__ = 'submission_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id'), nullable=False)
    submitted_flag = db.Column(db.String(256), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    submitted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='submissions')
    challenge = db.relationship('Challenge', backref='submissions')


class DockerInstance(db.Model):
    __tablename__ = 'docker_instances'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id'), nullable=False)
    container_id = db.Column(db.String(128), nullable=True)
    container_name = db.Column(db.String(128), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='creating')  # creating, running, stopped, error
    port_mappings = db.Column(db.Text, nullable=True)  # JSON
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=False)
    error_message = db.Column(db.String(512), nullable=True)

    user = db.relationship('User', backref=db.backref('docker_instances', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'challenge_id', 'status',
                            name='unique_active_instance'),
    )

    def is_expired(self):
        return datetime.now(timezone.utc) > self.expires_at

    def time_remaining_seconds(self):
        delta = self.expires_at - datetime.now(timezone.utc)
        return max(int(delta.total_seconds()), 0)

    def __repr__(self):
        return f'<DockerInstance user={self.user_id} challenge={self.challenge_id} status={self.status}>'

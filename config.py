import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ctf-platform-secret-key-change-in-production'

    # MySQL/MariaDB
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://ctf_user:ctf_password@localhost/ctf_platform'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)

    # CTF Settings
    CTF_NAME = os.environ.get('CTF_NAME') or 'HackArena CTF'
    CTF_DESCRIPTION = os.environ.get('CTF_DESCRIPTION') or 'Plataforma de Capture The Flag'
    FIRST_BLOOD_BONUS = int(os.environ.get('FIRST_BLOOD_BONUS', 50))
    MAX_TEAM_SIZE = int(os.environ.get('MAX_TEAM_SIZE', 5))
    FLAG_FORMAT = os.environ.get('FLAG_FORMAT') or 'FLAG{}'

    # File uploads for challenge attachments
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max

    # Admin
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'admin'
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@hackarena.local'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'AdminCTF2025!'

    # Docker Challenges
    DOCKER_BASE_URL = os.environ.get('DOCKER_BASE_URL') or 'unix://var/run/docker.sock'
    DOCKER_NETWORK = os.environ.get('DOCKER_NETWORK') or 'ctf_challenges'
    DOCKER_DEFAULT_TIMEOUT = int(os.environ.get('DOCKER_DEFAULT_TIMEOUT', 30))  # minutes
    DOCKER_DEFAULT_MEMORY = os.environ.get('DOCKER_DEFAULT_MEMORY') or '256m'
    DOCKER_DEFAULT_CPU = float(os.environ.get('DOCKER_DEFAULT_CPU', 0.5))
    DOCKER_MAX_INSTANCES_PER_USER = int(os.environ.get('DOCKER_MAX_INSTANCES_PER_USER', 3))
    DOCKER_PORT_RANGE_START = int(os.environ.get('DOCKER_PORT_RANGE_START', 10000))
    DOCKER_PORT_RANGE_END = int(os.environ.get('DOCKER_PORT_RANGE_END', 20000))

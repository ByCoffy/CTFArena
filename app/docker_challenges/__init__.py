from flask import Blueprint

bp = Blueprint('docker_challenges', __name__)

from app.docker_challenges import routes, events

from flask import Blueprint

analisis_bp = Blueprint('analisis', __name__)

from app.analisis import routes  # noqa: F401, E402
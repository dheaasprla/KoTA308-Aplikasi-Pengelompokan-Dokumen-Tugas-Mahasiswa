from flask import Blueprint

riwayat_bp = Blueprint('riwayat', __name__)

from app.riwayat import routes  # noqa: F401, E402
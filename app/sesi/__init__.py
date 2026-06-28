# ============================================================
# FILE: app/sesi/__init__.py
# Inisialisasi Blueprint 'sesi'
# Mencakup UC-01 (Membuat Sesi Analisis Baru) dan
# UC-02 (Mengunggah Dokumen Tugas)
# ============================================================

from flask import Blueprint

sesi_bp = Blueprint('sesi', __name__)

# Import routes di akhir untuk menghindari circular import
from app.sesi import routes
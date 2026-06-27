# ============================================================
# FILE: config.py
# Letakkan di root folder project kalian
# Membaca .env dan mengkonfigurasi koneksi database
# ============================================================

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ── Secret Key Flask ──────────────────────────────────────
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')

    # ── Konfigurasi Database PostgreSQL ───────────────────────
    DB_HOST     = os.getenv('DB_HOST',     'localhost')
    DB_PORT     = os.getenv('DB_PORT',     '5432')
    DB_NAME     = os.getenv('DB_NAME',     'db_KoTA308')
    DB_USER     = os.getenv('DB_USER',     'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')

    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    # Matikan tracking modifikasi (hemat memori)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Tampilkan query SQL di console saat development
    SQLALCHEMY_ECHO = os.getenv('FLASK_DEBUG', 'False') == 'True'
    
    GOOGLE_CLIENT_ID     = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    
    # ── Konfigurasi Upload Dokumen (UC-02) ─────────────────────
    # Folder penyimpanan fisik file PDF, relatif terhadap root project
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')

    # Batas ukuran per file dalam MB. Bisa diubah via .env tanpa
    # mengubah kode, karena nilai ini masih bisa berubah sesuai
    # hasil diskusi dengan dosen pembimbing (lihat laporan TA bab III).
    MAX_FILE_SIZE_MB = float(os.getenv('MAX_FILE_SIZE_MB', '5'))

    # MAX_CONTENT_LENGTH adalah konfigurasi bawaan Flask: request
    # dengan body lebih besar dari nilai ini otomatis ditolak (413)
    # sebelum masuk ke route handler.
    MAX_CONTENT_LENGTH = int(MAX_FILE_SIZE_MB * 1024 * 1024)

    # Batas jumlah file per sesi (sesuai C-09 SRS)
    MAX_FILES_PER_SESSION = int(os.getenv('MAX_FILES_PER_SESSION', '32'))

    # Total kuota penyimpanan per sesi dalam MB
    MAX_TOTAL_SIZE_MB = float(os.getenv('MAX_TOTAL_SIZE_MB', '200'))

    # Nilai threshold default saat sesi dibuat, skala 0-100
    DEFAULT_THRESHOLD = float(os.getenv('DEFAULT_THRESHOLD', '70'))

class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False


# Mapping nama config
config = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'default':     DevelopmentConfig,
}
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
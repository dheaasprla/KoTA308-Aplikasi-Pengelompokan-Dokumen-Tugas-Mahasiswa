from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
from config import config
from models import db

oauth = OAuth()

def create_app(config_name='default'):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    app.config.from_object(config[config_name])
    
    db.init_app(app)
    Migrate(app, db)
    oauth.init_app(app)

    # Konfigurasi Google OAuth
    oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

    # Daftarkan blueprint auth
    from app.auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Daftarkan blueprint sesi (UC-01 & UC-02)
    from app.sesi import sesi_bp
    app.register_blueprint(sesi_bp, url_prefix='/sesi')
    
    # Daftarkan blueprint analisis (UC-03: eksekusi analisis klaster)
    from app.analisis import analisis_bp
    app.register_blueprint(analisis_bp, url_prefix='/analisis') 

    # Daftarkan blueprint riwayat
    from app.riwayat import riwayat_bp
    app.register_blueprint(riwayat_bp, url_prefix='/riwayat')

    # Context processor untuk last_id_sesi di semua template
    @app.context_processor
    def inject_last_sesi():
        from flask import session as flask_session
        from models import SesiAnalisis

        last_id_sesi = flask_session.get('last_id_sesi')

        if not last_id_sesi:
            id_dosen = flask_session.get('user_id')
            if id_dosen:
                sesi_terakhir = SesiAnalisis.query.filter_by(
                    id_dosen=id_dosen,
                    status='analyzed'
                ).order_by(SesiAnalisis.tanggal_buat.desc()).first()
                if sesi_terakhir:
                    last_id_sesi = sesi_terakhir.id_sesi
                    flask_session['last_id_sesi'] = last_id_sesi

        return {'last_id_sesi': last_id_sesi}

    # Route redirect halaman utama ke login
    @app.route('/')
    def index():
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        from flask import redirect, url_for, flash, request as req
        
        try:
            parts = req.path.strip('/').split('/')
            id_sesi = int(parts[1])
        except (IndexError, ValueError):
            id_sesi = None

        max_total = app.config.get('MAX_TOTAL_SIZE_MB', 200)
        flash(
            f'Total ukuran file yang diunggah melebihi batas maksimal '
            f'{max_total}MB. Kurangi jumlah atau ukuran file, '
            f'lalu coba lagi.',
            'error'
        )

        if id_sesi:
            return redirect(url_for('sesi.form_upload', id_sesi=id_sesi))
        return redirect(url_for('auth.login'))

    return app
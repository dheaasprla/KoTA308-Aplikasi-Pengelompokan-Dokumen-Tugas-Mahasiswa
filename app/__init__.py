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

    # Route redirect halaman utama ke login
    @app.route('/')
    def index():
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))

    return app
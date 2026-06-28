from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, DosenPengampu
from app import oauth

auth_bp = Blueprint('auth', __name__)


# ── HELPER: cek apakah user sudah login ──────────────────────────────────────
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


# ── REGISTER ─────────────────────────────────────────────────────────────────
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Jika sudah login, langsung ke profil
    if 'user_id' in session:
        return redirect(url_for('auth.profile'))

    if request.method == 'POST':
        email            = request.form.get('email', '').strip()
        password         = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        # Validasi input
        if not email or not password or not confirm_password:
            return render_template('register.html', error='Semua kolom wajib diisi.')

        if password != confirm_password:
            return render_template('register.html', error='Konfirmasi kata sandi tidak cocok.')

        if len(password) < 8:
            return render_template('register.html', error='Kata sandi minimal 8 karakter.')

        # Cek apakah email sudah terdaftar
        existing_user = DosenPengampu.query.filter_by(email=email).first()
        if existing_user:
            return render_template('register.html', error='Email sudah terdaftar. Silakan login.')

        # Ambil nama dari bagian depan email (sebelum @)
        nama = email.split('@')[0]

        # Simpan user baru ke database
        new_user = DosenPengampu(
            nama          = nama,
            email         = email,
            password_hash = generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()

        # Langsung login setelah register berhasil
        session['user_id'] = new_user.id_dosen
        session['user_nama'] = new_user.nama
        session['user_email'] = new_user.email

        return redirect(url_for('auth.profile'))

    return render_template('register.html', error=None)


# ── LOGIN ─────────────────────────────────────────────────────────────────────
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Jika sudah login, langsung ke profil
    if 'user_id' in session:
        return redirect(url_for('auth.profile'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            return render_template('login.html', error='Email dan kata sandi wajib diisi.')

        # Cari user di database
        user = DosenPengampu.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            return render_template('login.html', error='Email atau kata sandi salah.')

        # Simpan data user ke session
        session['user_id']    = user.id_dosen
        session['user_nama']  = user.nama
        session['user_email'] = user.email

        return redirect(url_for('auth.profile'))

    return render_template('login.html', error=None)


# ── LOGOUT ────────────────────────────────────────────────────────────────────
@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


# ── PROFILE ───────────────────────────────────────────────────────────────────
@auth_bp.route('/profile')
@login_required
def profile():
    user = DosenPengampu.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))
    return render_template('profile.html', user=user)


# ── GOOGLE LOGIN ──────────────────────────────────────────────────────────────
@auth_bp.route('/google/login')
def google_login():
    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri, prompt='select_account')


# ── GOOGLE CALLBACK ───────────────────────────────────────────────────────────
@auth_bp.route('/google/callback')
def google_callback():
    token     = oauth.google.authorize_access_token()
    user_info = token.get('userinfo')

    if not user_info:
        return render_template('login.html', error='Gagal mendapatkan data dari Google.')

    email = user_info.get('email')
    nama  = user_info.get('name', email.split('@')[0])

    # Cek apakah user sudah ada di database
    user = DosenPengampu.query.filter_by(email=email).first()

    if not user:
        # Buat akun baru otomatis jika belum terdaftar
        user = DosenPengampu(
            nama          = nama,
            email         = email,
            password_hash = generate_password_hash(email + '_google_oauth')
        )
        db.session.add(user)
        db.session.commit()

    # Simpan ke session
    session['user_id']    = user.id_dosen
    session['user_nama']  = user.nama
    session['user_email'] = user.email

    return redirect(url_for('auth.profile'))
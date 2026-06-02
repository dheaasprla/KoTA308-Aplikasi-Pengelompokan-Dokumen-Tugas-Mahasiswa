# unggah_dokumen.py
# Route Flask untuk halaman Unggah Dokumen

import os
from flask import Blueprint, render_template, request, jsonify
from werkzeug.utils import secure_filename

# Blueprint agar bisa dipisah dari app utama (app.py)
unggah_dokumen_bp = Blueprint('unggah_dokumen', __name__)

# Konfigurasi upload
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE_MB = 50


def allowed_file(filename):
    """Cek apakah file ber-ekstensi .pdf"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ── GET: tampilkan halaman Unggah Dokumen ──────────────────────────────────
@unggah_dokumen_bp.route('/unggah', methods=['GET'])
def unggah_dokumen():
    return render_template('unggah_dokumen.html')


# ── POST: terima file PDF yang di-upload ──────────────────────────────────
@unggah_dokumen_bp.route('/unggah/upload', methods=['POST'])
def upload_file():
    mata_kuliah = request.form.get('mata_kuliah', '').strip()
    kelas       = request.form.get('kelas', '').strip()
    files       = request.files.getlist('files')

    if not mata_kuliah or not kelas:
        return jsonify({'status': 'error', 'message': 'Nama mata kuliah dan kelas wajib diisi.'}), 400

    if not files or all(f.filename == '' for f in files):
        return jsonify({'status': 'error', 'message': 'Tidak ada file yang dipilih.'}), 400

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    uploaded = []
    for f in files:
        if f and allowed_file(f.filename):
            filename = secure_filename(f.filename)
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            f.save(save_path)
            uploaded.append(filename)

    if not uploaded:
        return jsonify({'status': 'error', 'message': 'Hanya file .pdf yang diterima.'}), 400

    return jsonify({
        'status'      : 'success',
        'mata_kuliah' : mata_kuliah,
        'kelas'       : kelas,
        'files'       : uploaded
    })
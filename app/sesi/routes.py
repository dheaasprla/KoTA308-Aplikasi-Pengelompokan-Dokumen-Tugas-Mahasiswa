import os
import uuid
import time
from datetime import datetime
from flask import (
    render_template, request, redirect, url_for,
    flash, session, current_app, jsonify
)

from app.sesi import sesi_bp
from app.auth.routes import login_required
from models import db, SesiAnalisis, DokumenTugas
from utils.pdf_validator import (
    is_allowed_extension,
    is_text_based_pdf,
    extract_text_from_pdf,
)
from utils.text_preprocessor import clean_text


@sesi_bp.route('/baru', methods=['GET'])
@login_required
def form_sesi_baru():
    return render_template('unggah_dokumen.html')


@sesi_bp.route('/baru', methods=['POST'])
@login_required
def submit_session_data():
    nama_matkul = request.form.get('mata_kuliah', '').strip()
    kelas = request.form.get('kelas', '').strip()

    errors = []
    if not nama_matkul:
        errors.append('Nama Mata Kuliah tidak boleh kosong.')
    if not kelas:
        errors.append('Kelas tidak boleh kosong.')

    if errors:
        for err in errors:
            flash(err, 'error')
        return redirect(url_for('sesi.form_sesi_baru'))

    id_dosen = session.get('user_id')
    if id_dosen is None:
        flash('Sesi login tidak ditemukan, silakan login kembali.', 'error')
        return redirect(url_for('auth.login'))

    sesi_baru = SesiAnalisis(
        id_dosen=id_dosen,
        nama_matkul=nama_matkul,
        kelas=kelas,
        threshold_awal=current_app.config['DEFAULT_THRESHOLD'],
        status='uploaded',
        total_file_terunggah=0,
        ukuran_terpakai_mb=0.0,
    )
    db.session.add(sesi_baru)
    db.session.commit()

    flash('Sesi analisis baru berhasil dibuat.', 'success')
    return redirect(url_for('sesi.form_upload', id_sesi=sesi_baru.id_sesi))


@sesi_bp.route('/<int:id_sesi>/unggah', methods=['GET'])
@login_required
def form_upload(id_sesi):
    sesi = SesiAnalisis.query.get_or_404(id_sesi)
    return render_template('unggah_dokumen.html', sesi=sesi)


@sesi_bp.route('/<int:id_sesi>/unggah', methods=['POST'])
@login_required
def confirm_batch_upload(id_sesi):
    sesi = SesiAnalisis.query.get_or_404(id_sesi)
    uploaded_files = request.files.getlist('files[]')
    uploaded_files = [f for f in uploaded_files if f and f.filename]

    if not uploaded_files:
        flash('Tidak ada berkas yang dipilih.', 'error')
        return redirect(url_for('sesi.form_upload', id_sesi=id_sesi))

    max_files = current_app.config['MAX_FILES_PER_SESSION']
    total_setelah_upload = sesi.total_file_terunggah + len(uploaded_files)

    if total_setelah_upload > max_files:
        sisa_kuota = max_files - sesi.total_file_terunggah
        flash(
            f'Jumlah berkas melebihi batas maksimal {max_files} dokumen. '
            f'Sisa kuota: {sisa_kuota} berkas.',
            'error'
        )
        return redirect(url_for('sesi.form_upload', id_sesi=id_sesi))

    max_size_mb = current_app.config['MAX_FILE_SIZE_MB']
    max_total_mb = current_app.config['MAX_TOTAL_SIZE_MB']
    upload_folder = current_app.config['UPLOAD_FOLDER']
    sesi_folder = os.path.join(upload_folder, f'sesi_{id_sesi}')
    os.makedirs(sesi_folder, exist_ok=True)

    berhasil = []
    ditolak = []
    total_size_baru = 0.0

    for file in uploaded_files:
        filename = file.filename
        if not is_allowed_extension(filename):
            ditolak.append(f'{filename} (format bukan .pdf)')
            continue
        file.stream.seek(0, os.SEEK_END)
        size_bytes = file.stream.tell()
        file.stream.seek(0)
        size_mb = size_bytes / (1024 * 1024)
        if size_mb > max_size_mb:
            ditolak.append(f'{filename} (ukuran {size_mb:.2f}MB > {max_size_mb}MB)')
            continue
        if sesi.ukuran_terpakai_mb + total_size_baru + size_mb > max_total_mb:
            ditolak.append(f'{filename} (kuota penyimpanan sesi {max_total_mb}MB penuh)')
            continue
        file.stream.seek(0)
        if not is_text_based_pdf(file.stream):
            ditolak.append(f'{filename} (terdeteksi scan/tidak ada teks)')
            continue
        file.stream.seek(0)
        try:
            raw_text = extract_text_from_pdf(file.stream)
        except Exception:
            ditolak.append(f'{filename} (gagal membaca PDF)')
            continue
        cleaned_text = clean_text(raw_text)
        file.stream.seek(0)
        ext = os.path.splitext(filename)[1]
        disk_filename = f'{uuid.uuid4().hex}{ext}'
        disk_path = os.path.join(sesi_folder, disk_filename)
        file.save(disk_path)
        dokumen = DokumenTugas(
            id_sesi=id_sesi,
            nama_file=filename,
            ukuran_file_mb=round(size_mb, 2),
            path_penyimpanan=disk_path,
            teks_ekstraksi=cleaned_text,
            is_outlier=False,
        )
        db.session.add(dokumen)
        berhasil.append(filename)
        total_size_baru += size_mb

    if berhasil:
        sesi.total_file_terunggah += len(berhasil)
        sesi.ukuran_terpakai_mb = round(sesi.ukuran_terpakai_mb + total_size_baru, 2)
    db.session.commit()

    if berhasil:
        flash(f'{len(berhasil)} berkas berhasil diunggah.', 'success')
    if ditolak:
        for pesan in ditolak:
            flash(f'Ditolak: {pesan}', 'error')

    return redirect(url_for('sesi.form_upload', id_sesi=id_sesi))


@sesi_bp.route('/<int:id_sesi>/hasil-klaster', methods=['POST'])
@login_required
def update_threshold(id_sesi):
    sesi = SesiAnalisis.query.get_or_404(id_sesi)
    try:
        threshold_value = float(request.form.get('threshold', ''))
    except (ValueError, TypeError):
        return jsonify({'status': 'error', 'pesan': 'Nilai threshold tidak valid.'}), 400

    if not (0 <= threshold_value <= 100):
        threshold_value = current_app.config['DEFAULT_THRESHOLD']

    # 1. Update nilai threshold di database sesi
    sesi.threshold_awal = threshold_value
    
    # 2. Commit perubahan threshold
    db.session.commit()
    
    return jsonify({
        'status': 'sukses',
        'pesan': f'Ambang batas kemiripan (threshold) berhasil diatur ke {threshold_value:.0f}%.'
    }), 200


@sesi_bp.route('/baru/api', methods=['POST'])
@login_required
def api_buat_sesi():
    nama_matkul = request.form.get('mata_kuliah', '').strip()
    kelas = request.form.get('kelas', '').strip()

    errors = []
    if not nama_matkul:
        errors.append('Nama Mata Kuliah tidak boleh kosong.')
    if not kelas:
        errors.append('Kelas tidak boleh kosong.')
    if errors:
        return jsonify({'status': 'error', 'messages': errors}), 400

    id_dosen = session.get('user_id')
    if id_dosen is None:
        return jsonify({'status': 'error', 'messages': ['Sesi login tidak ditemukan.']}), 401

    sesi_baru = SesiAnalisis(
        id_dosen=id_dosen,
        nama_matkul=nama_matkul,
        kelas=kelas,
        threshold_awal=current_app.config['DEFAULT_THRESHOLD'],
        status='uploaded',
        total_file_terunggah=0,
        ukuran_terpakai_mb=0.0,
    )
    db.session.add(sesi_baru)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'id_sesi': sesi_baru.id_sesi,
        'message': 'Sesi analisis baru berhasil dibuat.'
    })


@sesi_bp.route('/<int:id_sesi>/unggah/api', methods=['POST'])
@login_required
def api_upload_files(id_sesi):
    sesi = SesiAnalisis.query.get_or_404(id_sesi)
    existing_files = {d.nama_file for d in DokumenTugas.query.filter_by(id_sesi=id_sesi).all()}
    uploaded_files = request.files.getlist('files[]')
    uploaded_files = [f for f in uploaded_files if f and f.filename]
    
    if not uploaded_files:
        return jsonify({'status': 'error', 'message': 'Tidak ada berkas yang dipilih.'}), 400
    
    new_unique_count = 0
    for file in uploaded_files:
        if file.filename and file.filename not in existing_files:
            new_unique_count += 1
            
    total_prediksi = len(existing_files) + new_unique_count
    
    max_files = current_app.config['MAX_FILES_PER_SESSION']
    #total_setelah_upload = sesi.total_file_terunggah + len(uploaded_files)
    if total_prediksi > max_files:
        sisa_kuota = max_files - len(existing_files)
        return jsonify({
            'status': 'error',
            'message': f'Jumlah berkas melebihi batas {max_files}. Sisa kuota: {sisa_kuota} berkas.'
        }), 400

    max_size_mb = current_app.config['MAX_FILE_SIZE_MB']
    max_total_mb = current_app.config['MAX_TOTAL_SIZE_MB']
    upload_folder = current_app.config['UPLOAD_FOLDER']
    sesi_folder = os.path.join(upload_folder, f'sesi_{id_sesi}')
    os.makedirs(sesi_folder, exist_ok=True)

    berhasil = []
    ditolak = []
    total_size_baru = 0.0

    for file in uploaded_files:
        filename = file.filename
        if filename in existing_files:
            continue
        
        if not is_allowed_extension(filename):
            ditolak.append(f'{filename} (format bukan .pdf)')
            continue
        
        file.stream.seek(0, os.SEEK_END)
        size_bytes = file.stream.tell()
        file.stream.seek(0)
        size_mb = size_bytes / (1024 * 1024)
        
        if size_mb > max_size_mb:
            ditolak.append(f'{filename} (ukuran {size_mb:.2f}MB > {max_size_mb}MB)')
            continue
        
        if sesi.ukuran_terpakai_mb + total_size_baru + size_mb > max_total_mb:
            ditolak.append(f'{filename} (kuota sesi penuh)')
            continue
        
        file.stream.seek(0)
        if not is_text_based_pdf(file.stream):
            ditolak.append(f'{filename} (terdeteksi scan/tidak ada teks)')
            continue
        
        file.stream.seek(0)
        try:
            raw_text = extract_text_from_pdf(file.stream)
        except Exception:
            ditolak.append(f'{filename} (gagal membaca PDF)')
            continue
        
        cleaned_text = clean_text(raw_text)
        file.stream.seek(0)
        ext = os.path.splitext(filename)[1]
        disk_filename = f'{uuid.uuid4().hex}{ext}'
        disk_path = os.path.join(sesi_folder, disk_filename)
        file.save(disk_path)
        dokumen = DokumenTugas(
            id_sesi=id_sesi,
            nama_file=filename,
            ukuran_file_mb=round(size_mb, 2),
            path_penyimpanan=disk_path,
            teks_ekstraksi=cleaned_text,
            is_outlier=False,
        )
        db.session.add(dokumen)
        berhasil.append(filename)
        total_size_baru += size_mb
        existing_files.add(filename)

    if berhasil:
        sesi.total_file_terunggah = len(existing_files)
        sesi.ukuran_terpakai_mb = round(sesi.ukuran_terpakai_mb + total_size_baru, 2)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'berhasil': berhasil,
        'ditolak': ditolak,
        'total_file_terunggah': sesi.total_file_terunggah,
        'ukuran_terpakai_mb': sesi.ukuran_terpakai_mb,
        'message': f'{len(berhasil)} berkas berhasil diunggah.'
    })


@sesi_bp.route('/<int:id_sesi>/state', methods=['GET'])
@login_required
def get_session_state(id_sesi):
    """
    Mengambil state terakhir sesi analisis jika aplikasi berhenti di tengah jalan.
    """
    sesi = SesiAnalisis.query.get_or_404(id_sesi)

    dokumen_list = DokumenTugas.query.filter_by(
        id_sesi=id_sesi
    ).order_by(DokumenTugas.id_dokumen.asc()).all()

    dokumen_data = [{
        "id_dokumen": dok.id_dokumen,
        "nama_file": dok.nama_file,
        "nama_tampil": dok.nama_file.rsplit('.', 1)[0],
        "ukuran_file_mb": dok.ukuran_file_mb,
    } for dok in dokumen_list]

    from models import Klaster
    klaster_list = Klaster.query.filter_by(id_sesi=id_sesi).all()
    klaster_tersedia = [k.id_klaster for k in klaster_list]
    sudah_dianalisis = len(klaster_tersedia) > 0

    max_files = current_app.config['MAX_FILES_PER_SESSION']
    sisa_kuota = max_files - sesi.total_file_terunggah

    return jsonify({
        "status": "selesai",
        "id_sesi": sesi.id_sesi,
        "nama_matkul": sesi.nama_matkul,
        "kelas": sesi.kelas,
        "threshold_awal": sesi.threshold_awal,
        "status_sesi": sesi.status,
        "total_file_terunggah": sesi.total_file_terunggah,
        "ukuran_terpakai_mb": sesi.ukuran_terpakai_mb,
        "sisa_kuota_file": sisa_kuota,
        "tanggal_buat": sesi.tanggal_buat.isoformat(),
        "sudah_dianalisis": sudah_dianalisis,
        "dokumen": dokumen_data,
        "klaster_tersedia": klaster_tersedia
    }), 200
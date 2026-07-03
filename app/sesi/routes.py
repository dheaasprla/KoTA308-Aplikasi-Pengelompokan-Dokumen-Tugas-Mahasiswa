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
    from services.embedding_service import embed_semua_dokumen
    from services.similarity_service import hitung_similarity_matrix
    from services.clustering_service import jalankan_clustering
    from models import Klaster, DokumenKlaster, DetailKemiripan
    from itertools import combinations

    sesi = SesiAnalisis.query.get_or_404(id_sesi)
    try:
        threshold_value = float(request.form.get('threshold', ''))
    except (ValueError, TypeError):
        flash('Nilai threshold tidak valid.', 'error')
        return redirect(url_for('sesi.form_upload', id_sesi=id_sesi))

    if not (0 <= threshold_value <= 100):
        flash('Nilai threshold harus 0-100.', 'error')
        threshold_value = current_app.config['DEFAULT_THRESHOLD']

    sesi.threshold_awal = threshold_value

    from models import Klaster, DetailKemiripan
    klaster_list = Klaster.query.filter_by(id_sesi=id_sesi).all()
    for klaster in klaster_list:
        detail_list = DetailKemiripan.query.filter_by(
            id_klaster=klaster.id_klaster
        ).all()
        for detail in detail_list:
            detail.kalimat_highlight1 = None
            detail.kalimat_highlight2 = None

    db.session.commit()

    dokumen_list = DokumenTugas.query.filter_by(id_sesi=id_sesi).all()
    if len(dokumen_list) < 2:
        flash('Minimal 2 dokumen diperlukan untuk analisis.', 'error')
        return redirect(url_for('sesi.form_upload', id_sesi=id_sesi))

    klaster_lama = Klaster.query.filter_by(id_sesi=id_sesi).all()
    if klaster_lama:
        Klaster.query.filter_by(id_sesi=id_sesi).delete()
        for dok in dokumen_list:
            dok.is_outlier = False
        db.session.flush()

    waktu_mulai = time.time()

    embeddings = embed_semua_dokumen(dokumen_list)
    similarity_matrix = hitung_similarity_matrix(embeddings)
    hasil = jalankan_clustering(similarity_matrix, threshold_value)

    waktu_selesai = time.time()
    waktu_proses_detik = round(waktu_selesai - waktu_mulai, 1)

    for anggota_ids in hasil['kelompok']:
        skor_dalam_klaster = []
        for id_a, id_b in combinations(sorted(anggota_ids), 2):
            key = tuple(sorted([id_a, id_b]))
            skor = similarity_matrix.get(key, 0.0)
            skor_dalam_klaster.append(round(skor * 100, 2))

        skor_tertinggi = max(skor_dalam_klaster) if skor_dalam_klaster else 0.0
        skor_terendah = min(skor_dalam_klaster) if skor_dalam_klaster else 0.0

        klaster_baru = Klaster(
            id_sesi=id_sesi,
            skor_tertinggi=skor_tertinggi,
            skor_terendah=skor_terendah
        )
        db.session.add(klaster_baru)
        db.session.flush()

        for id_dok in anggota_ids:
            db.session.add(DokumenKlaster(
                id_klaster=klaster_baru.id_klaster,
                id_dokumen=id_dok
            ))

        for id_a, id_b in combinations(sorted(anggota_ids), 2):
            key = tuple(sorted([id_a, id_b]))
            skor = similarity_matrix.get(key, 0.0)
            db.session.add(DetailKemiripan(
                id_klaster=klaster_baru.id_klaster,
                id_dokumen1=id_a,
                id_dokumen2=id_b,
                persentase_kemiripan=round(skor * 100, 2),
                kalimat_highlight1=None,
                kalimat_highlight2=None,
            ))

    for id_dok in hasil['outlier']:
        dok = DokumenTugas.query.get(id_dok)
        if dok:
            dok.is_outlier = True

    sesi.status = 'analyzed'
    sesi.tanggal_selesai = datetime.now()
    db.session.commit()

    session[f'waktu_proses_{id_sesi}'] = waktu_proses_detik
    session['last_id_sesi'] = id_sesi

    flash(f'Analisis selesai! Threshold {threshold_value:.0f}%.', 'success')
    return redirect(url_for('analisis.halaman_hasil_klaster', id_sesi=id_sesi))


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
    uploaded_files = request.files.getlist('files[]')
    uploaded_files = [f for f in uploaded_files if f and f.filename]

    if not uploaded_files:
        return jsonify({'status': 'error', 'message': 'Tidak ada berkas yang dipilih.'}), 400

    max_files = current_app.config['MAX_FILES_PER_SESSION']
    total_setelah_upload = sesi.total_file_terunggah + len(uploaded_files)
    if total_setelah_upload > max_files:
        sisa_kuota = max_files - sesi.total_file_terunggah
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

    if berhasil:
        sesi.total_file_terunggah += len(berhasil)
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
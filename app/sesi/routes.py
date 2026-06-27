# ============================================================
# FILE: app/sesi/routes.py
# Routes untuk UC-01 (Membuat Sesi Analisis Baru) dan
# UC-02 (Mengunggah Dokumen Tugas)
#
# Cross reference SRS:
#   - CO-01: membuatSesiBaru
#   - CO-02: mengunggahBerkasTugas
#   - CO-03 (sebagian): capture nilai threshold saja
# ============================================================

import os
import uuid
from flask import (
    render_template, request, redirect, url_for,
    flash, session, current_app
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


# ============================================================
# UC-01: Membuat Sesi Analisis Baru (CO-01: membuatSesiBaru)
# ============================================================

@sesi_bp.route('/baru', methods=['GET'])
@login_required
def form_sesi_baru():
    """
    Menampilkan form pembuatan sesi analisis baru.
    Cross ref: SSD UC-01, langkah 1-2
    (requestNewAnalysisSession -> present session input form).
    """
    return render_template('sesi_baru.html')


@sesi_bp.route('/baru', methods=['POST'])
@login_required
def submit_session_data():
    """
    Menangani submit form sesi baru.
    Cross ref: SSD UC-01, langkah 3-4 (submitSessionData).

    Validasi:
        - Nama Mata Kuliah tidak boleh kosong (Extension 3a SRS)
        - Kelas tidak boleh kosong (Extension 3a SRS)

    Jika valid:
        - Buat record SesiAnalisis baru dengan threshold_awal
          default sesuai config.DEFAULT_THRESHOLD (skala 0-100)
        - Redirect ke halaman upload dokumen (UC-02)

    Jika tidak valid:
        - Tampilkan flash message error
        - Kembali ke form sesi baru (Extension 3a)
    """
    nama_matkul = request.form.get('mata_kuliah', '').strip()
    kelas = request.form.get('kelas', '').strip()

    # ── Validasi field tidak boleh kosong (Extension 3a) ──
    errors = []
    if not nama_matkul:
        errors.append('Nama Mata Kuliah tidak boleh kosong.')
    if not kelas:
        errors.append('Kelas tidak boleh kosong.')

    if errors:
        for err in errors:
            flash(err, 'error')
        return redirect(url_for('sesi.form_sesi_baru'))

    # Key session sesuai app/auth/routes.py adalah 'user_id'
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


# ============================================================
# UC-02: Mengunggah Dokumen Tugas (CO-02: mengunggahBerkasTugas)
# ============================================================

@sesi_bp.route('/<int:id_sesi>/unggah', methods=['GET'])
@login_required
def form_upload(id_sesi):
    """
    Menampilkan halaman upload dokumen untuk sesi tertentu.

    Variabel 'sesi' dikirim utuh ke template, termasuk
    sesi.threshold_awal (skala 0-100) yang langsung dipakai
    oleh konfigurasi_threshold.html tanpa konversi apapun.
    """
    sesi = SesiAnalisis.query.get_or_404(id_sesi)
    return render_template('upload_dokumen.html', sesi=sesi)


@sesi_bp.route('/<int:id_sesi>/unggah', methods=['POST'])
@login_required
def confirm_batch_upload(id_sesi):
    """
    Menangani upload massal dokumen PDF.
    Cross ref: SSD UC-02, CO-02 confirmBatchUpload().

    Alur validasi per file (urut dari yang termurah komputasinya):
        1. Validasi jumlah file total (<= MAX_FILES_PER_SESSION)
        2. Untuk setiap file:
           a. Validasi ekstensi (.pdf)
           b. Validasi ukuran (<= MAX_FILE_SIZE_MB, dari .env)
           c. Validasi kuota total sesi (<= MAX_TOTAL_SIZE_MB)
           d. Validasi teks-based vs scan (PyMuPDF)
        3. Ekstrak teks mentah (PyMuPDF)
        4. Preprocessing: clean_text() - case folding
        5. Simpan file fisik ke UPLOAD_FOLDER
        6. Insert metadata + teks_ekstraksi ke dokumen_tugas
        7. Update total_file_terunggah & ukuran_terpakai_mb di sesi

    Extension 4a (SRS): jumlah file > 32 -> tolak SEMUA file
    Extension 4b (SRS): file bukan PDF / hasil scan -> tolak file
                        tersebut saja, file lain tetap diproses
    """
    sesi = SesiAnalisis.query.get_or_404(id_sesi)

    uploaded_files = request.files.getlist('files[]')
    uploaded_files = [f for f in uploaded_files if f and f.filename]

    if not uploaded_files:
        flash('Tidak ada berkas yang dipilih.', 'error')
        return redirect(url_for('sesi.form_upload', id_sesi=id_sesi))

    # ── Validasi 1: Jumlah file tidak boleh melebihi kuota sesi ──
    max_files = current_app.config['MAX_FILES_PER_SESSION']
    total_setelah_upload = sesi.total_file_terunggah + len(uploaded_files)

    if total_setelah_upload > max_files:
        sisa_kuota = max_files - sesi.total_file_terunggah
        flash(
            f'Jumlah berkas melebihi batas maksimal {max_files} dokumen '
            f'per sesi. Sisa kuota Anda saat ini: {sisa_kuota} berkas.',
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

        # ── Validasi 2a: Ekstensi harus .pdf ──
        if not is_allowed_extension(filename):
            ditolak.append(f'{filename} (format bukan .pdf)')
            continue

        # ── Validasi 2b: Ukuran file <= MAX_FILE_SIZE_MB ──
        file.stream.seek(0, os.SEEK_END)
        size_bytes = file.stream.tell()
        file.stream.seek(0)
        size_mb = size_bytes / (1024 * 1024)

        if size_mb > max_size_mb:
            ditolak.append(
                f'{filename} (ukuran {size_mb:.2f}MB > {max_size_mb}MB)'
            )
            continue

        # ── Validasi 2c: Kuota total penyimpanan sesi ──
        if sesi.ukuran_terpakai_mb + total_size_baru + size_mb > max_total_mb:
            ditolak.append(
                f'{filename} (kuota penyimpanan sesi {max_total_mb}MB penuh)'
            )
            continue

        # ── Validasi 2d: Deteksi PDF berbasis teks vs scan ──
        file.stream.seek(0)
        if not is_text_based_pdf(file.stream):
            ditolak.append(
                f'{filename} (terdeteksi sebagai hasil scan/tidak '
                f'memiliki teks yang dapat dibaca)'
            )
            continue
        file.stream.seek(0)

        # ── Ekstraksi teks mentah ──
        try:
            raw_text = extract_text_from_pdf(file.stream)
        except Exception:
            ditolak.append(f'{filename} (gagal membaca isi PDF / file rusak)')
            continue

        # ── Preprocessing: case folding ──
        cleaned_text = clean_text(raw_text)

        # ── Simpan file fisik ke server ──
        # Nama file di disk dibuat unik (UUID) untuk menghindari
        # konflik nama antar mahasiswa/sesi, sementara nama_file
        # asli (identitas mahasiswa, Opsi C) disimpan di database.
        file.stream.seek(0)
        ext = os.path.splitext(filename)[1]
        disk_filename = f'{uuid.uuid4().hex}{ext}'
        disk_path = os.path.join(sesi_folder, disk_filename)
        file.save(disk_path)

        # ── Insert metadata ke dokumen_tugas ──
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

    # ── Update statistik sesi ──
    if berhasil:
        sesi.total_file_terunggah += len(berhasil)
        sesi.ukuran_terpakai_mb = round(sesi.ukuran_terpakai_mb + total_size_baru, 2)

    db.session.commit()

    # ── Feedback ke pengguna ──
    if berhasil:
        flash(f'{len(berhasil)} berkas berhasil diunggah.', 'success')
    if ditolak:
        for pesan in ditolak:
            flash(f'Ditolak: {pesan}', 'error')

    return redirect(url_for('sesi.form_upload', id_sesi=id_sesi))


# ============================================================
# Capture nilai threshold (bagian dari CO-03)
#
# CATATAN SCOPE: Route ini HANYA menyimpan nilai threshold.
# Logika analisis klaster penuh (commandClusterAnalysis,
# embedding SBERT, dst) dikerjakan di sprint analisis.
# ============================================================

@sesi_bp.route('/<int:id_sesi>/hasil-klaster', methods=['POST'])
@login_required
def update_threshold(id_sesi):
    """
    Menyimpan nilai threshold yang dipilih dosen melalui slider
    pada modal konfigurasi threshold (REQ-UI-07).

    Nilai dikirim dan disimpan dalam skala 0-100, konsisten
    dengan kolom threshold_awal di models.py.

    Validasi: nilai threshold harus berada di rentang 0-100
    (Extension 2a SRS). Jika tidak valid, dikembalikan ke
    DEFAULT_THRESHOLD.
    """
    sesi = SesiAnalisis.query.get_or_404(id_sesi)

    try:
        threshold_value = float(request.form.get('threshold', ''))
    except (ValueError, TypeError):
        flash('Nilai threshold tidak valid.', 'error')
        return redirect(url_for('sesi.form_upload', id_sesi=id_sesi))

    # ── Validasi rentang 0-100 (Extension 2a) ──
    if not (0 <= threshold_value <= 100):
        flash(
            'Nilai threshold harus berada di antara 0% - 100%. '
            'Nilai dikembalikan ke default.',
            'error'
        )
        threshold_value = current_app.config['DEFAULT_THRESHOLD']

    sesi.threshold_awal = threshold_value
    db.session.commit()

    flash(f'Threshold berhasil diatur ke {threshold_value:.0f}%.', 'success')

    # TODO (sprint analisis): redirect ke halaman hasil klaster
    # sebenarnya dan trigger commandClusterAnalysis()
    return redirect(url_for('sesi.form_upload', id_sesi=id_sesi))
# ============================================================
# FILE: app/analisis/routes.py
# Routes untuk UC-03 (Eksekusi Analisis Klaster)
#
# Cross reference SRS:
#   - CO-03: commandClusterAnalysis
#
# Pipeline yang dijalankan:
#   1. Validasi sesi dan dokumen
#   2. Cek apakah sudah pernah dianalisis (re-clustering)
#   3. Embed semua dokumen → hitung similarity → clustering
#   4. Simpan hasil klaster dengan skor_tertinggi & skor_terendah
#   5. Simpan detail kemiripan antar pasangan dalam klaster
#   6. Tandai dokumen outlier
#   7. Update status sesi
# ============================================================

from itertools import combinations
from flask import jsonify
from app.analisis import analisis_bp
from app.auth.routes import login_required
from services.highlight_service import proses_highlight
from models import (
    db, SesiAnalisis, DokumenTugas,
    Klaster, DokumenKlaster, DetailKemiripan
)
from services.embedding_service import embed_semua_dokumen
from services.similarity_service import hitung_similarity_matrix
from services.clustering_service import jalankan_clustering


@analisis_bp.route('/sesi/<int:id_sesi>/jalankan', methods=['POST'])
@login_required
def jalankan_analisis_klaster(id_sesi):
    """
    Endpoint utama untuk menjalankan pipeline analisis klaster.
    Cross ref: CO-03 commandClusterAnalysis()

    Menangani dua skenario:
        1. Analisis pertama kali: jalankan pipeline penuh
        2. Re-clustering (threshold diubah): hapus hasil lama
           lalu jalankan pipeline penuh kembali

    Returns:
        JSON response:
        {
            "status"           : "selesai",
            "jumlah_kelompok"  : 3,
            "jumlah_outlier"   : 5,
            "total_pasangan"   : 496,
            "edge_aktif"       : 12,
            "threshold_dipakai": 70.0
        }
    """
    # ── Validasi sesi ──
    sesi = SesiAnalisis.query.get_or_404(id_sesi)

    # ── Validasi dokumen ──
    dokumen_list = DokumenTugas.query.filter_by(
        id_sesi=id_sesi
    ).all()

    if len(dokumen_list) < 2:
        return jsonify({
            'status': 'error',
            'pesan' : 'Minimal 2 dokumen diperlukan untuk analisis.'
        }), 400

    # ── Cek apakah sudah pernah dianalisis (re-clustering) ──
    # Jika Klaster sudah ada untuk sesi ini, hapus semua hasil lama.
    # ondelete='CASCADE' di models.py memastikan DokumenKlaster dan
    # DetailKemiripan ikut terhapus otomatis saat Klaster dihapus.
    klaster_lama = Klaster.query.filter_by(id_sesi=id_sesi).all()
    if klaster_lama:
        Klaster.query.filter_by(id_sesi=id_sesi).delete()

        # Reset is_outlier semua dokumen ke False sebelum
        # ditentukan ulang oleh hasil clustering yang baru
        for dok in dokumen_list:
            dok.is_outlier = False

        db.session.flush()

    # ── Step 1: Embed semua dokumen ──
    # Mengubah setiap teks_ekstraksi menjadi vektor 768 dimensi
    # menggunakan pipeline chunking dari utils/chunking.py.
    embeddings = embed_semua_dokumen(dokumen_list)

    if len(embeddings) < 2:
        return jsonify({
            'status': 'error',
            'pesan' : 'Tidak cukup dokumen yang berhasil di-embed.'
        }), 400

    # ── Step 2: Hitung cosine similarity semua pasangan ──
    # Menghasilkan dict {(id_a, id_b): skor 0.0-1.0} untuk semua
    # kombinasi pasangan unik (complete graph sebelum threshold).
    similarity_matrix = hitung_similarity_matrix(embeddings)

    # ── Step 3: Jalankan graph-based clustering ──
    # Membangun graf, memangkas edge di bawah threshold,
    # mendeteksi connected components via BFS NetworkX.
    hasil = jalankan_clustering(
        similarity_matrix,
        sesi.threshold_awal  # skala 0-100, konversi di dalam fungsi
    )

    # ── Step 4: Simpan hasil kelompok ke DB ──
    for anggota_ids in hasil['kelompok']:

        # Hitung skor_tertinggi dan skor_terendah dari semua pasangan
        # dalam klaster ini SEBELUM membuat record Klaster.
        # Ini wajib karena kedua kolom adalah NOT NULL di models.py
        # dan ada CHECK constraint skor_tertinggi >= skor_terendah.
        skor_dalam_klaster = []
        for id_a, id_b in combinations(sorted(anggota_ids), 2):
            # Normalisasi key agar cocok dengan format similarity_matrix
            key = tuple(sorted([id_a, id_b]))
            skor = similarity_matrix.get(key, 0.0)
            # Konversi ke skala 0-100 sesuai kolom persentase di models
            skor_dalam_klaster.append(round(skor * 100, 2))

        # Ambil nilai tertinggi dan terendah dari semua skor pasangan
        # dalam klaster. Kedua nilai ini ditampilkan di halaman hasil
        # sebagai rentang kemiripan klaster (min-max bukan rata-rata,
        # sesuai masukan dosen pembimbing dan evaluator Seminar 2).
        skor_tertinggi = max(skor_dalam_klaster) if skor_dalam_klaster else 0.0
        skor_terendah  = min(skor_dalam_klaster) if skor_dalam_klaster else 0.0

        # Buat record Klaster dengan semua kolom wajib terisi
        klaster_baru = Klaster(
            id_sesi        =id_sesi,
            skor_tertinggi =skor_tertinggi,
            skor_terendah  =skor_terendah
        )
        db.session.add(klaster_baru)

        # flush() agar id_klaster tersedia sebelum dipakai
        # untuk insert DokumenKlaster dan DetailKemiripan
        db.session.flush()

        # Simpan anggota klaster ke tabel DokumenKlaster
        for id_dok in anggota_ids:
            db.session.add(DokumenKlaster(
                id_klaster=klaster_baru.id_klaster,
                id_dokumen=id_dok
            ))

        # Simpan detail kemiripan antar pasangan dalam klaster ini.
        # DetailKemiripan hanya untuk pasangan yang SATU KLASTER
        # karena id_klaster adalah FK NOT NULL di models.py.
        # kalimat_highlight diisi di sprint side-by-side.
        for id_a, id_b in combinations(sorted(anggota_ids), 2):
            key = tuple(sorted([id_a, id_b]))
            skor = similarity_matrix.get(key, 0.0)

            db.session.add(DetailKemiripan(
                id_klaster          =klaster_baru.id_klaster,
                id_dokumen1         =id_a,
                id_dokumen2         =id_b,
                persentase_kemiripan=round(skor * 100, 2),
                kalimat_highlight1  =None,
                kalimat_highlight2  =None,
            ))

    # ── Step 5: Tandai dokumen outlier ──
    for id_dok in hasil['outlier']:
        dok = DokumenTugas.query.get(id_dok)
        if dok:
            dok.is_outlier = True

    # ── Step 6: Update status sesi ──
    # 'analyzed' sesuai CHECK constraint di models.py:
    # status IN ('uploaded', 'analyzed', 'completed')
    sesi.status = 'analyzed'

    # ── Commit semua perubahan ke DB sekaligus ──
    db.session.commit()

    return jsonify({
        'status'            : 'selesai',
        'jumlah_kelompok'   : len(hasil['kelompok']),
        'jumlah_outlier'    : len(hasil['outlier']),
        'total_pasangan'    : hasil['total_edge'],
        'edge_aktif'        : hasil['edge_aktif'],
        'threshold_dipakai' : hasil['threshold_dipakai']
    }), 200 
    
@analisis_bp.route('/detail/<int:id_detail>/sidebyside', methods=['POST'])
@login_required
def sidebyside(id_detail):
    """
    Endpoint untuk memproses dan menampilkan perbandingan
    teks side-by-side antar dua dokumen dalam satu klaster.
 
    Dipanggil oleh frontend ketika user mengklik sel pada
    matrix kemiripan di halaman detail klaster.
 
    Menangani dua skenario:
        1. Highlight sudah ada di DB → return dari cache
        2. Highlight belum ada → proses SBERT → simpan → return
 
    Returns:
        JSON response:
        {
            "status": "selesai",
            "dokumen_1": {
                "nama_file": "Dhea_Tugas1.pdf",
                "kalimat": [
                    {"indeks": 2, "kalimat": "teks kalimat..."},
                ]
            },
            "dokumen_2": {
                "nama_file": "Berliana_Tugas1.pdf",
                "kalimat": [
                    {"indeks": 7, "kalimat": "teks kalimat..."},
                ]
            },
            "persentase_kemiripan": 87.32,
            "total_mirip": 5,
            "dari_cache": false
        }
    """
    # ── Ambil detail kemiripan dari DB ──
    detail = DetailKemiripan.query.get_or_404(id_detail)
 
    # ── Ambil kedua dokumen ──
    dokumen_1 = DokumenTugas.query.get_or_404(detail.id_dokumen1)
    dokumen_2 = DokumenTugas.query.get_or_404(detail.id_dokumen2)
 
    # ── Validasi teks dokumen tidak kosong ──
    if not dokumen_1.teks_ekstraksi or not dokumen_2.teks_ekstraksi:
        return jsonify({
            'status': 'error',
            'pesan' : 'Salah satu dokumen tidak memiliki teks yang bisa diproses.'
        }), 400
 
    # ── Ambil threshold dari sesi via klaster ──
    # Alur: detail_kemiripan → klaster → sesi_analisis → threshold_awal
    # Threshold ini dipakai konsisten untuk level dokumen maupun kalimat
    klaster = Klaster.query.get_or_404(detail.id_klaster)
    sesi    = SesiAnalisis.query.get_or_404(klaster.id_sesi)
 
    # ── Proses highlight ──
    # proses_highlight() menangani cek cache dan komputasi SBERT
    hasil = proses_highlight(
        detail,
        dokumen_1,
        dokumen_2,
        sesi.threshold_awal
    )
 
    # ── Commit jika ada perubahan (highlight baru disimpan) ──
    # Kalau dari cache, tidak ada perubahan di DB tapi commit
    # tidak masalah karena SQLAlchemy hanya commit yang berubah
    db.session.commit()
 
    return jsonify({
        'status': 'selesai',
        **hasil
        # **hasil menyebarkan semua key dari dict hasil:
        # dokumen_1, dokumen_2, persentase_kemiripan,
        # total_mirip, dari_cache
    }), 200
    
@analisis_bp.route('/klaster/<int:id_klaster>/matrix', methods=['GET'])
@login_required
def get_matrix_kemiripan(id_klaster):
    """
    Endpoint untuk mengambil data matrix kemiripan antar dokumen
    dalam satu klaster. Dipanggil frontend saat halaman detail
    klaster dibuka untuk merender tampilan matrix 2x2.
 
    Data yang dikembalikan:
        - Info klaster (skor tertinggi dan terendah)
        - Daftar dokumen dalam klaster (untuk header baris/kolom)
        - Semua pasangan kemiripan (untuk isi sel matrix)
          termasuk id_detail untuk trigger sidebyside saat diklik
 
    Returns:
        JSON response:
        {
            "status": "selesai",
            "id_klaster": 1,
            "skor_tertinggi": 99.0,
            "skor_terendah": 76.29,
            "dokumen": [
                {
                    "id_dokumen": 44,
                    "nama_file": "tugas_audit_dummy_1.pdf",
                    "nama_tampil": "tugas_audit_dummy_1"
                }
            ],
            "matrix": [
                {
                    "id_detail": 6,
                    "id_dokumen1": 44,
                    "id_dokumen2": 46,
                    "persentase_kemiripan": 99.0,
                    "sudah_diproses": true
                }
            ]
        }
    """
    # ── Ambil data klaster ──
    klaster = Klaster.query.get_or_404(id_klaster)
 
    # ── Ambil semua anggota klaster ──
    dokumen_klaster = DokumenKlaster.query.filter_by(
        id_klaster=id_klaster
    ).all()
 
    # Ambil objek DokumenTugas untuk setiap anggota
    dokumen_list = []
    for dk in dokumen_klaster:
        dok = DokumenTugas.query.get(dk.id_dokumen)
        if dok:
            dokumen_list.append(dok)
 
    # Susun data dokumen untuk header matrix
    # nama_tampil: nama file tanpa ekstensi untuk label yang lebih bersih
    data_dokumen = [
        {
            "id_dokumen" : dok.id_dokumen,
            "nama_file"  : dok.nama_file,
            "nama_tampil": dok.nama_file.rsplit('.', 1)[0]
            # rsplit('.', 1)[0] memisahkan nama file dari ekstensinya
            # "tugas_audit_dummy_1 (2).pdf" → "tugas_audit_dummy_1 (2)"
        }
        for dok in dokumen_list
    ]
 
    # ── Ambil semua detail kemiripan dalam klaster ini ──
    detail_list = DetailKemiripan.query.filter_by(
        id_klaster=id_klaster
    ).all()
 
    # Susun data matrix untuk isi sel
    # sudah_diproses: True jika highlight sudah ada di DB
    # Frontend bisa pakai info ini untuk memberi indikator visual
    # bahwa sel ini sudah pernah dibuka sebelumnya
    data_matrix = [
        {
            "id_detail"           : detail.id_detail,
            "id_dokumen1"         : detail.id_dokumen1,
            "id_dokumen2"         : detail.id_dokumen2,
            "persentase_kemiripan": detail.persentase_kemiripan,
            "sudah_diproses"      : detail.kalimat_highlight1 is not None
        }
        for detail in detail_list
    ]
 
    # Urutkan dari skor tertinggi ke terendah
    # agar pasangan paling mirip tampil pertama di list
    data_matrix.sort(
        key=lambda x: x["persentase_kemiripan"],
        reverse=True
    )
 
    return jsonify({
        "status"         : "selesai",
        "id_klaster"     : id_klaster,
        "skor_tertinggi" : klaster.skor_tertinggi,
        "skor_terendah"  : klaster.skor_terendah,
        "jumlah_dokumen" : len(data_dokumen),
        "dokumen"        : data_dokumen,
        "matrix"         : data_matrix
    }), 200
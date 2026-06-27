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
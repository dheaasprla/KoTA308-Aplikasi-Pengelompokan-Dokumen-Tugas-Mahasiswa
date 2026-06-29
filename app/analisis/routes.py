from itertools import combinations
from flask import jsonify, render_template, request, session as flask_session
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
    sesi = SesiAnalisis.query.get_or_404(id_sesi)
    dokumen_list = DokumenTugas.query.filter_by(id_sesi=id_sesi).all()

    if len(dokumen_list) < 2:
        return jsonify({
            'status': 'error',
            'pesan': 'Minimal 2 dokumen diperlukan untuk analisis.'
        }), 400

    klaster_lama = Klaster.query.filter_by(id_sesi=id_sesi).all()
    if klaster_lama:
        Klaster.query.filter_by(id_sesi=id_sesi).delete()
        for dok in dokumen_list:
            dok.is_outlier = False
        db.session.flush()

    embeddings = embed_semua_dokumen(dokumen_list)

    if len(embeddings) < 2:
        return jsonify({
            'status': 'error',
            'pesan': 'Tidak cukup dokumen yang berhasil di-embed.'
        }), 400

    similarity_matrix = hitung_similarity_matrix(embeddings)
    hasil = jalankan_clustering(similarity_matrix, sesi.threshold_awal)

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
    db.session.commit()

    return jsonify({
        'status': 'selesai',
        'jumlah_kelompok': len(hasil['kelompok']),
        'jumlah_outlier': len(hasil['outlier']),
        'total_pasangan': hasil['total_edge'],
        'edge_aktif': hasil['edge_aktif'],
        'threshold_dipakai': hasil['threshold_dipakai']
    }), 200


@analisis_bp.route('/detail/<int:id_detail>/sidebyside', methods=['POST'])
@login_required
def sidebyside(id_detail):
    detail = DetailKemiripan.query.get_or_404(id_detail)
    dokumen_1 = DokumenTugas.query.get_or_404(detail.id_dokumen1)
    dokumen_2 = DokumenTugas.query.get_or_404(detail.id_dokumen2)

    if not dokumen_1.teks_ekstraksi or not dokumen_2.teks_ekstraksi:
        return jsonify({
            'status': 'error',
            'pesan': 'Salah satu dokumen tidak memiliki teks yang bisa diproses.'
        }), 400

    klaster = Klaster.query.get_or_404(detail.id_klaster)
    sesi = SesiAnalisis.query.get_or_404(klaster.id_sesi)

    hasil = proses_highlight(detail, dokumen_1, dokumen_2, sesi.threshold_awal)
    db.session.commit()

    return jsonify({
        'status': 'selesai',
        **hasil
    }), 200


@analisis_bp.route('/detail/<int:id_detail>/fulltext', methods=['POST'])
@login_required
def fulltext_sidebyside(id_detail):
    from utils.chunking import split_into_sentences

    detail = DetailKemiripan.query.get_or_404(id_detail)
    dokumen_1 = DokumenTugas.query.get_or_404(detail.id_dokumen1)
    dokumen_2 = DokumenTugas.query.get_or_404(detail.id_dokumen2)

    if not dokumen_1.teks_ekstraksi or not dokumen_2.teks_ekstraksi:
        return jsonify({
            'status': 'error',
            'pesan': 'Salah satu dokumen tidak memiliki teks.'
        }), 400

    klaster = Klaster.query.get_or_404(detail.id_klaster)
    sesi = SesiAnalisis.query.get_or_404(klaster.id_sesi)

    hasil = proses_highlight(detail, dokumen_1, dokumen_2, sesi.threshold_awal)
    db.session.commit()

    request_data = request.get_json() or {}
    requested_doc1 = request_data.get('doc1')
    requested_doc2 = request_data.get('doc2')

    perlu_dibalik = (
        requested_doc1 and requested_doc2 and
        requested_doc1 == dokumen_2.nama_file and
        requested_doc2 == dokumen_1.nama_file
    )

    if perlu_dibalik:
        dok_kiri = dokumen_2
        dok_kanan = dokumen_1
        indeks_mirip_kiri = {k['indeks'] for k in hasil['dokumen_2']['kalimat']}
        indeks_mirip_kanan = {k['indeks'] for k in hasil['dokumen_1']['kalimat']}
    else:
        dok_kiri = dokumen_1
        dok_kanan = dokumen_2
        indeks_mirip_kiri = {k['indeks'] for k in hasil['dokumen_1']['kalimat']}
        indeks_mirip_kanan = {k['indeks'] for k in hasil['dokumen_2']['kalimat']}

    kalimat_kiri = split_into_sentences(dok_kiri.teks_ekstraksi)
    kalimat_kanan = split_into_sentences(dok_kanan.teks_ekstraksi)

    fulltext_kiri = [
        {'indeks': i, 'kalimat': k, 'is_highlight': i in indeks_mirip_kiri}
        for i, k in enumerate(kalimat_kiri)
    ]

    fulltext_kanan = [
        {'indeks': i, 'kalimat': k, 'is_highlight': i in indeks_mirip_kanan}
        for i, k in enumerate(kalimat_kanan)
    ]

    return jsonify({
        'status': 'selesai',
        'dokumen_1': {
            'nama_file': dok_kiri.nama_file,
            'kalimat': fulltext_kiri
        },
        'dokumen_2': {
            'nama_file': dok_kanan.nama_file,
            'kalimat': fulltext_kanan
        },
        'persentase_kemiripan': detail.persentase_kemiripan,
        'total_mirip': hasil['total_mirip']
    }), 200


@analisis_bp.route('/klaster/<int:id_klaster>/matrix', methods=['GET'])
@login_required
def get_matrix_kemiripan(id_klaster):
    klaster = Klaster.query.get_or_404(id_klaster)
    dokumen_klaster = DokumenKlaster.query.filter_by(id_klaster=id_klaster).all()

    dokumen_list = []
    for dk in dokumen_klaster:
        dok = DokumenTugas.query.get(dk.id_dokumen)
        if dok:
            dokumen_list.append(dok)

    data_dokumen = [
        {
            "id_dokumen": dok.id_dokumen,
            "nama_file": dok.nama_file,
            "nama_tampil": dok.nama_file.rsplit('.', 1)[0]
        }
        for dok in dokumen_list
    ]

    detail_list = DetailKemiripan.query.filter_by(id_klaster=id_klaster).all()

    data_matrix = [
        {
            "id_detail": detail.id_detail,
            "id_dokumen1": detail.id_dokumen1,
            "id_dokumen2": detail.id_dokumen2,
            "persentase_kemiripan": detail.persentase_kemiripan,
            "sudah_diproses": detail.kalimat_highlight1 is not None
        }
        for detail in detail_list
    ]

    data_matrix.sort(key=lambda x: x["persentase_kemiripan"], reverse=True)

    return jsonify({
        "status": "selesai",
        "id_klaster": id_klaster,
        "skor_tertinggi": klaster.skor_tertinggi,
        "skor_terendah": klaster.skor_terendah,
        "jumlah_dokumen": len(data_dokumen),
        "dokumen": data_dokumen,
        "matrix": data_matrix
    }), 200


@analisis_bp.route('/klaster/<int:id_klaster>/detail', methods=['GET'])
@login_required
def halaman_detail_klaster(id_klaster):
    klaster = Klaster.query.get_or_404(id_klaster)
    sesi = SesiAnalisis.query.get_or_404(klaster.id_sesi)

    dokumen_klaster = DokumenKlaster.query.filter_by(id_klaster=id_klaster).all()

    dokumen_list = []
    for dk in dokumen_klaster:
        dok = DokumenTugas.query.get(dk.id_dokumen)
        if dok:
            dokumen_list.append(dok)

    files = [d.nama_file for d in dokumen_list]
    detail_list = DetailKemiripan.query.filter_by(id_klaster=id_klaster).all()

    n = len(files)
    matrix = [[0.0] * n for _ in range(n)]
    id_detail_map = {}
    file_index = {f: i for i, f in enumerate(files)}

    for detail in detail_list:
        dok1 = DokumenTugas.query.get(detail.id_dokumen1)
        dok2 = DokumenTugas.query.get(detail.id_dokumen2)
        if dok1 and dok2:
            i = file_index.get(dok1.nama_file)
            j = file_index.get(dok2.nama_file)
            if i is not None and j is not None:
                skor = detail.persentase_kemiripan / 100
                matrix[i][j] = skor
                matrix[j][i] = skor
                id_detail_map[f"{dok1.nama_file}_{dok2.nama_file}"] = detail.id_detail
                id_detail_map[f"{dok2.nama_file}_{dok1.nama_file}"] = detail.id_detail

    skor_list = [d.persentase_kemiripan for d in detail_list]
    avg_similarity = sum(skor_list) / len(skor_list) if skor_list else 0.0

    return render_template(
        'detail_klaster.html',
        cluster_name=f'Klaster {id_klaster}',
        files=files,
        matrix=matrix,
        threshold=sesi.threshold_awal / 100,
        max_similarity=klaster.skor_tertinggi / 100,
        min_similarity=klaster.skor_terendah / 100,
        avg_similarity=avg_similarity / 100,
        id_klaster=id_klaster,
        id_sesi=klaster.id_sesi,
        id_detail_map=id_detail_map,
        text_pairs={}
    )


@analisis_bp.route('/sesi/<int:id_sesi>/hasil', methods=['GET'])
@login_required
def halaman_hasil_klaster(id_sesi):
    # Simpan id_sesi terakhir ke session untuk sidebar
    flask_session['last_id_sesi'] = id_sesi

    sesi = SesiAnalisis.query.get_or_404(id_sesi)
    klaster_list = Klaster.query.filter_by(id_sesi=id_sesi).all()

    clusters = []
    for idx, k in enumerate(klaster_list, start=1):
        dokumen_ids = [dk.id_dokumen for dk in k.dokumen_relations]
        dokumen_list = DokumenTugas.query.filter(
            DokumenTugas.id_dokumen.in_(dokumen_ids)
        ).all()
        clusters.append({
            'id_klaster': k.id_klaster,
            'name': f'Klaster {idx}',
            'score_min': round(k.skor_terendah / 100, 2),
            'score_max': round(k.skor_tertinggi / 100, 2),
            'score': round((k.skor_terendah + k.skor_tertinggi) / 200, 2),
            'files': [d.nama_file for d in dokumen_list]
        })

    outliers = DokumenTugas.query.filter_by(
        id_sesi=id_sesi,
        is_outlier=True
    ).all()
    outlier_list = [{'nama_file': d.nama_file} for d in outliers]

    # Ambil waktu proses dari Flask session
    waktu_proses_detik = flask_session.pop(f'waktu_proses_{id_sesi}', None)
    if waktu_proses_detik is not None:
        if waktu_proses_detik < 60:
            waktu_proses = f'{waktu_proses_detik}s'
        else:
            menit = int(waktu_proses_detik // 60)
            detik = round(waktu_proses_detik % 60, 1)
            waktu_proses = f'{menit}m {detik}s'
    else:
        waktu_proses = '-'
        
    return render_template(
        'hasil_klaster.html',
        sesi=sesi,
        clusters=clusters,
        outliers=outlier_list,
        threshold=sesi.threshold_awal / 100,
        total_dokumen=sesi.total_file_terunggah,
        total_klaster=len(clusters),
        total_outlier=len(outlier_list),
        waktu_proses=waktu_proses,
        id_sesi=id_sesi
    )
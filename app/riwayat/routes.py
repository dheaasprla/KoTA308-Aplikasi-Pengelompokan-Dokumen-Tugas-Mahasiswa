# ============================================================
# FILE: app/riwayat/routes.py
# Routes untuk fitur Riwayat Sesi
#
# Menampilkan semua sesi analisis milik dosen yang sedang
# login beserta ringkasan statusnya.
#
# Data yang ditampilkan per sesi:
#   - Nama sesi (mata kuliah + kelas)
#   - Tanggal sesi dibuat
#   - Jumlah dokumen
#   - Status duplikasi (Bersih / Duplikasi Sedang / Ada Duplikasi)
#   - Action: lihat sesi, hapus sesi
# ============================================================

from flask import jsonify, session
from app.riwayat import riwayat_bp
from app.auth.routes import login_required
from models import db, SesiAnalisis, DokumenTugas, Klaster


def hitung_status_duplikasi(id_sesi: int) -> str:
    """
    Menentukan status duplikasi satu sesi berdasarkan data
    klaster dan outlier yang tersimpan di database.

    Logika:
        - Tidak ada klaster → "Bersih"
          (tidak ada dokumen yang cukup mirip melewati threshold)
        - Ada klaster + ada outlier → "Duplikasi Sedang"
          (sebagian dokumen mirip, sebagian lagi unik)
        - Ada klaster + tidak ada outlier → "Ada Duplikasi"
          (semua dokumen terindikasi mirip satu sama lain)

    Args:
        id_sesi: primary key sesi analisis

    Returns:
        String status: "Bersih", "Duplikasi Sedang", atau
        "Ada Duplikasi"
    """
    # Cek apakah ada klaster yang terbentuk untuk sesi ini
    jumlah_klaster = Klaster.query.filter_by(
        id_sesi=id_sesi
    ).count()

    if jumlah_klaster == 0:
        # Tidak ada klaster → semua dokumen unik
        return "Bersih"

    # Ada klaster, cek apakah ada dokumen outlier
    jumlah_outlier = DokumenTugas.query.filter_by(
        id_sesi=id_sesi,
        is_outlier=True
    ).count()

    if jumlah_outlier > 0:
        # Ada klaster + ada outlier → sebagian mirip
        return "Duplikasi Sedang"

    # Ada klaster + tidak ada outlier → semua mirip
    return "Ada Duplikasi"


@riwayat_bp.route('/', methods=['GET'])
@login_required
def halaman_riwayat():
    from flask import render_template
    return render_template('riwayat_sesi.html')
    """
    Mengambil semua riwayat sesi analisis milik dosen
    yang sedang login, diurutkan dari yang terbaru.

    Returns:
        JSON response:
        {
            "status": "selesai",
            "total_sesi": 3,
            "total_dokumen": 45,
            "sesi_terakhir": {
                "nama_matkul": "PRPL",
                "kelas": "2C"
            },
            "riwayat": [
                {
                    "id_sesi": 1,
                    "nama_matkul": "Pemrograman Web",
                    "kelas": "TI-3A",
                    "tanggal_buat": "2026-04-21T10:30:00",
                    "jumlah_dokumen": 32,
                    "status_duplikasi": "Ada Duplikasi",
                    "status_sesi": "analyzed"
                }
            ]
        }
    """
    id_dosen = session.get('user_id')

    # Ambil semua sesi milik dosen yang login,
    # diurutkan dari yang paling baru (tanggal_buat DESC)
    semua_sesi = SesiAnalisis.query.filter_by(
        id_dosen=id_dosen
    ).order_by(
        SesiAnalisis.tanggal_buat.desc()
    ).all()

    # Hitung statistik ringkasan untuk header halaman riwayat
    total_sesi     = len(semua_sesi)
    total_dokumen  = sum(s.total_file_terunggah for s in semua_sesi)

    # Sesi terakhir adalah yang pertama di list (sudah diurutkan DESC)
    sesi_terakhir = None
    if semua_sesi:
        sesi_terakhir = {
            "nama_matkul": semua_sesi[0].nama_matkul,
            "kelas"      : semua_sesi[0].kelas,
            "tanggal"    : semua_sesi[0].tanggal_buat.isoformat()
        }

    # Susun data riwayat per sesi
    riwayat = []
    for sesi in semua_sesi:
        # Tentukan status duplikasi hanya untuk sesi yang
        # sudah dianalisis. Sesi yang belum dianalisis
        # tidak memiliki data klaster sehingga hasilnya
        # selalu "Bersih" yang tidak relevan.
        if sesi.status == 'analyzed' or sesi.status == 'completed':
            status_duplikasi = hitung_status_duplikasi(sesi.id_sesi)
        else:
            status_duplikasi = None

        riwayat.append({
            "id_sesi"         : sesi.id_sesi,
            "nama_matkul"     : sesi.nama_matkul,
            "kelas"           : sesi.kelas,
            "tanggal_buat"    : sesi.tanggal_buat.isoformat(),
            "jumlah_dokumen"  : sesi.total_file_terunggah,
            "status_duplikasi": status_duplikasi,
            "status_sesi"     : sesi.status
        })

    return jsonify({
        "status"       : "selesai",
        "total_sesi"   : total_sesi,
        "total_dokumen": total_dokumen,
        "sesi_terakhir": sesi_terakhir,
        "riwayat"      : riwayat
    }), 200

@riwayat_bp.route('/api', methods=['GET'])
@login_required
def api_get_riwayat():
    from flask import session as flask_session
    id_dosen = flask_session.get('user_id')
    
    semua_sesi = SesiAnalisis.query.filter_by(
        id_dosen=id_dosen
    ).order_by(SesiAnalisis.tanggal_buat.desc()).all()

    total_sesi = len(semua_sesi)
    total_dokumen = sum(s.total_file_terunggah for s in semua_sesi)

    sesi_terakhir = None
    if semua_sesi:
        sesi_terakhir = {
            "nama_matkul": semua_sesi[0].nama_matkul,
            "kelas": semua_sesi[0].kelas,
            "tanggal": semua_sesi[0].tanggal_buat.isoformat()
        }

    riwayat = []
    for sesi in semua_sesi:
        if sesi.status in ('analyzed', 'completed'):
            status_duplikasi = hitung_status_duplikasi(sesi.id_sesi)
        else:
            status_duplikasi = None

        riwayat.append({
            "id_sesi": sesi.id_sesi,
            "nama_matkul": sesi.nama_matkul,
            "kelas": sesi.kelas,
            "tanggal_buat": sesi.tanggal_buat.isoformat(),
            "jumlah_dokumen": sesi.total_file_terunggah,
            "status_duplikasi": status_duplikasi,
            "status_sesi": sesi.status
        })

    return jsonify({
        "status": "selesai",
        "total_sesi": total_sesi,
        "total_dokumen": total_dokumen,
        "sesi_terakhir": sesi_terakhir,
        "riwayat": riwayat
    }), 200

@riwayat_bp.route('/<int:id_sesi>', methods=['DELETE'])
@login_required
def hapus_sesi(id_sesi):
    """
    Menghapus satu sesi analisis beserta seluruh data
    yang terkait (dokumen, klaster, detail kemiripan).

    Cascade delete sudah dikonfigurasi di models.py sehingga
    menghapus SesiAnalisis otomatis menghapus semua data
    turunannya: DokumenTugas, Klaster, DokumenKlaster,
    DetailKemiripan, dan LaporanEvaluasi.

    Validasi kepemilikan: memastikan sesi yang dihapus
    memang milik dosen yang sedang login, bukan milik
    dosen lain.

    Returns:
        JSON response:
        {
            "status": "selesai",
            "pesan": "Sesi berhasil dihapus."
        }
    """
    id_dosen = session.get('user_id')

    sesi = SesiAnalisis.query.get_or_404(id_sesi)

    # Validasi kepemilikan: tolak jika sesi bukan milik
    # dosen yang sedang login
    if sesi.id_dosen != id_dosen:
        return jsonify({
            "status": "error",
            "pesan" : "Anda tidak memiliki akses untuk menghapus sesi ini."
        }), 403

    db.session.delete(sesi)
    db.session.commit()

    return jsonify({
        "status": "selesai",
        "pesan" : "Sesi berhasil dihapus."
    }), 200
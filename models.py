# ============================================================
# FILE: models.py
# Letakkan di ROOT project (sejajar app.py)
# Implementasi 7 entitas ERD ke SQLAlchemy ORM
# ============================================================

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# ╔══════════════════════════════════════════════════════════╗
# ║  1. DOSEN_PENGAMPU                                       ║
# ╚══════════════════════════════════════════════════════════╝
class DosenPengampu(db.Model):
    __tablename__ = 'dosen_pengampu'

    id_dosen      = db.Column(db.Integer,     primary_key=True, autoincrement=True)
    nama          = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at    = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)

    sesi_analisis = db.relationship(
        'SesiAnalisis',
        backref='dosen',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<DosenPengampu {self.email}>'


# ╔══════════════════════════════════════════════════════════╗
# ║  2. SESI_ANALISIS                                        ║
# ╚══════════════════════════════════════════════════════════╝
class SesiAnalisis(db.Model):
    __tablename__ = 'sesi_analisis'

    id_sesi              = db.Column(db.Integer,     primary_key=True, autoincrement=True)
    id_dosen             = db.Column(db.Integer,     db.ForeignKey('dosen_pengampu.id_dosen', ondelete='CASCADE'), nullable=False)
    nama_matkul          = db.Column(db.String(100), nullable=False)
    kelas                = db.Column(db.String(20),  nullable=False)
    threshold_awal       = db.Column(db.Float,       nullable=False, default=70.0)
    status               = db.Column(db.String(20),  nullable=False, default='uploaded')
    total_file_terunggah = db.Column(db.Integer,     nullable=False, default=0)
    ukuran_terpakai_mb   = db.Column(db.Float,       nullable=False, default=0.0)
    tanggal_buat         = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)
    tanggal_selesai      = db.Column(db.DateTime,    nullable=True)

    __table_args__ = (
        db.CheckConstraint('total_file_terunggah <= 35',  name='ck_max_file_per_sesi'),
        db.CheckConstraint(
            "status IN ('uploaded', 'analyzed', 'completed')",
            name='ck_status_sesi'
        ),
    )

    dokumen_tugas    = db.relationship('DokumenTugas',   backref='sesi', lazy='dynamic', cascade='all, delete-orphan')
    klaster          = db.relationship('Klaster',         backref='sesi', lazy='dynamic', cascade='all, delete-orphan')
    laporan_evaluasi = db.relationship('LaporanEvaluasi', backref='sesi', lazy='dynamic', cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<SesiAnalisis {self.nama_matkul} - {self.kelas}>'


# ╔══════════════════════════════════════════════════════════╗
# ║  3. DOKUMEN_TUGAS                                        ║
# ║  nama_file = identitas mahasiswa (Opsi C)                ║
# ║  is_outlier diisi oleh GraphClusteringService            ║
# ╚══════════════════════════════════════════════════════════╝
class DokumenTugas(db.Model):
    __tablename__ = 'dokumen_tugas'

    id_dokumen       = db.Column(db.Integer,     primary_key=True, autoincrement=True)
    id_sesi          = db.Column(db.Integer,     db.ForeignKey('sesi_analisis.id_sesi', ondelete='CASCADE'), nullable=False)
    nama_file        = db.Column(db.String(255), nullable=False)
    ukuran_file_mb   = db.Column(db.Float,       nullable=False)
    path_penyimpanan = db.Column(db.String(500), nullable=False)
    teks_ekstraksi   = db.Column(db.Text,        nullable=True)
    is_outlier       = db.Column(db.Boolean,     nullable=False, default=False)
    uploaded_at      = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)

    klaster_relations   = db.relationship('DokumenKlaster', backref='dokumen', lazy='dynamic', cascade='all, delete-orphan')
    detail_sebagai_dok1 = db.relationship('DetailKemiripan', foreign_keys='DetailKemiripan.id_dokumen1', backref='dokumen1', lazy='dynamic')
    detail_sebagai_dok2 = db.relationship('DetailKemiripan', foreign_keys='DetailKemiripan.id_dokumen2', backref='dokumen2', lazy='dynamic')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<DokumenTugas {self.nama_file}>'


# ╔══════════════════════════════════════════════════════════╗
# ║  4. KLASTER                                              ║
# ║  skor_tertinggi & skor_terendah dihitung oleh            ║
# ║  GraphClusteringService sebelum disimpan ke DB           ║
# ║  rata_rata_skor TIDAK disimpan (derived value)           ║
# ╚══════════════════════════════════════════════════════════╝
class Klaster(db.Model):
    __tablename__ = 'klaster'

    id_klaster     = db.Column(db.Integer,  primary_key=True, autoincrement=True)
    id_sesi        = db.Column(db.Integer,  db.ForeignKey('sesi_analisis.id_sesi', ondelete='CASCADE'), nullable=False)
    skor_tertinggi = db.Column(db.Float,    nullable=False)
    skor_terendah  = db.Column(db.Float,    nullable=False)
    created_at     = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.CheckConstraint('skor_tertinggi >= skor_terendah', name='ck_skor_klaster'),
        db.CheckConstraint('skor_tertinggi BETWEEN 0 AND 100', name='ck_skor_range'),
    )

    dokumen_relations = db.relationship('DokumenKlaster',  backref='klaster', lazy='dynamic', cascade='all, delete-orphan')
    detail_kemiripan  = db.relationship('DetailKemiripan', backref='klaster', lazy='dynamic', cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<Klaster {self.id_klaster} skor={self.skor_terendah}-{self.skor_tertinggi}>'


# ╔══════════════════════════════════════════════════════════╗
# ║  5. DOKUMEN_KLASTER (Junction Table)                     ║
# ║  Menjembatani relasi many-to-many Dokumen <-> Klaster    ║
# ╚══════════════════════════════════════════════════════════╝
class DokumenKlaster(db.Model):
    __tablename__ = 'dokumen_klaster'

    id_dokumen = db.Column(db.Integer, db.ForeignKey('dokumen_tugas.id_dokumen', ondelete='CASCADE'), primary_key=True)
    id_klaster = db.Column(db.Integer, db.ForeignKey('klaster.id_klaster',       ondelete='CASCADE'), primary_key=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<DokumenKlaster dok={self.id_dokumen} klaster={self.id_klaster}>'


# ╔══════════════════════════════════════════════════════════╗
# ║  6. DETAIL_KEMIRIPAN                                     ║
# ║  Data pairwise per klaster + highlight kalimat (JSON)    ║
# ║  rata_rata_skor dikalkulasi dari kolom persentase ini    ║
# ╚══════════════════════════════════════════════════════════╝
class DetailKemiripan(db.Model):
    __tablename__ = 'detail_kemiripan'

    id_detail            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_klaster           = db.Column(db.Integer, db.ForeignKey('klaster.id_klaster',       ondelete='CASCADE'), nullable=False)
    id_dokumen1          = db.Column(db.Integer, db.ForeignKey('dokumen_tugas.id_dokumen', ondelete='CASCADE'), nullable=False)
    id_dokumen2          = db.Column(db.Integer, db.ForeignKey('dokumen_tugas.id_dokumen', ondelete='CASCADE'), nullable=False)
    persentase_kemiripan = db.Column(db.Float,   nullable=False)
    kalimat_highlight1   = db.Column(db.Text,    nullable=True)
    kalimat_highlight2   = db.Column(db.Text,    nullable=True)

    __table_args__ = (
        db.CheckConstraint('id_dokumen1 <> id_dokumen2', name='ck_beda_dokumen'),
        db.CheckConstraint('persentase_kemiripan BETWEEN 0 AND 100', name='ck_persentase_range'),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<DetailKemiripan dok{self.id_dokumen1}-dok{self.id_dokumen2} {self.persentase_kemiripan}%>'


# ╔══════════════════════════════════════════════════════════╗
# ║  7. LAPORAN_EVALUASI                                     ║
# ╚══════════════════════════════════════════════════════════╝
class LaporanEvaluasi(db.Model):
    __tablename__ = 'laporan_evaluasi'

    id_laporan     = db.Column(db.Integer,     primary_key=True, autoincrement=True)
    id_sesi        = db.Column(db.Integer,     db.ForeignKey('sesi_analisis.id_sesi', ondelete='CASCADE'), nullable=False)
    format_file    = db.Column(db.String(10),  nullable=False)
    path_file      = db.Column(db.String(500), nullable=False)
    tanggal_ekspor = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.CheckConstraint("format_file IN ('pdf', 'xlsx')", name='ck_format_laporan'),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<LaporanEvaluasi sesi={self.id_sesi} format={self.format_file}>'


# ╔══════════════════════════════════════════════════════════╗
# ║  HELPER: Hitung rata_rata_skor on-the-fly                ║
# ║  Panggil fungsi ini di route Flask ketika halaman        ║
# ║  detail klaster dibuka — tidak disimpan di database      ║
# ╚══════════════════════════════════════════════════════════╝
def get_rata_rata_skor(id_klaster: int) -> float:
    """
    Hitung rata-rata kemiripan seluruh pasangan dalam satu klaster.
    Derived value — tidak disimpan di DB, dihitung saat dibutuhkan.

    Contoh penggunaan di route Flask:
        rata_rata = get_rata_rata_skor(klaster.id_klaster)
    """
    from sqlalchemy import func
    result = db.session.query(
        func.avg(DetailKemiripan.persentase_kemiripan)
    ).filter(
        DetailKemiripan.id_klaster == id_klaster
    ).scalar()
    return round(float(result), 2) if result is not None else 0.0
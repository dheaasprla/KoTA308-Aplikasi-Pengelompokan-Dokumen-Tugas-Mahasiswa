# ============================================================
# FILE: services/embedding_service.py
# Layanan embedding dokumen menggunakan model SBERT
#
# Tanggung jawab file ini:
#   - Load model SBERT sekali saat pertama dipanggil (lazy load)
#   - Menyediakan fungsi untuk mengubah teks dokumen menjadi
#     vektor embedding 768 dimensi menggunakan chunking
#
# Model yang digunakan:
#   paraphrase-multilingual-mpnet-base-v2
#   - Mendukung 50+ bahasa termasuk Bahasa Indonesia
#   - Mampu mengenali istilah teknis Inggris yang umum di
#     tugas mahasiswa Teknik Informatika
#   - Max seq length efektif: 128 token (sesuai data training)
#   - Output dimensi: 768
#
# Referensi:
#   Reimers & Gurevych (2019) - Sentence-BERT: EMNLP-IJCNLP
#   Reimers & Gurevych (2020) - Multilingual SBERT: EMNLP
#
# Dipanggil oleh: app/analisis/routes.py
# Memanggil    : utils/chunking.py
# ============================================================

import numpy as np
from sentence_transformers import SentenceTransformer
from utils.chunking import encode_document


# Nama model yang digunakan, sesuai hasil analisis empiris
# dan keputusan yang sudah dikonfirmasi ke dosen pembimbing
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

# Variabel global untuk menyimpan instance model yang sudah di-load.
# Nilai None berarti model belum di-load sama sekali.
# Setelah di-load pertama kali, instance disimpan di sini dan
# digunakan ulang untuk semua request berikutnya tanpa load ulang.
_model = None


def get_model() -> SentenceTransformer:
    """
    Mengembalikan instance model SBERT yang sudah di-load.

    Menggunakan pola lazy loading: model hanya di-load saat
    pertama kali fungsi ini dipanggil, bukan saat aplikasi
    Flask pertama kali dijalankan. Ini menghindari waktu
    startup yang lama karena model berukuran ~1.1GB.

    Setelah di-load, instance disimpan di variabel global
    _model sehingga request berikutnya langsung menggunakan
    model yang sudah ada di memori tanpa load ulang.

    Device dipaksa ke 'cpu' karena:
        - Server deployment kemungkinan tidak memiliki GPU
        - Konsisten dengan hasil pengujian empiris yang sudah
          dilakukan di Google Colab dengan device='cpu'
        - Skor cosine similarity tidak berubah antara CPU dan GPU,
          hanya kecepatan yang berbeda

    Returns:
        Instance SentenceTransformer yang siap digunakan
        untuk encoding dokumen.
    """
    global _model

    # Kalau model belum di-load, load sekarang
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME, device='cpu')

    return _model


def embed_dokumen(teks: str) -> np.ndarray:
    """
    Mengubah satu teks dokumen menjadi vektor embedding 768 dimensi.

    Fungsi ini adalah wrapper tipis di atas encode_document()
    dari utils/chunking.py. Alasan dipisah menjadi layer tersendiri:
        - embedding_service bertanggung jawab atas manajemen model
          (load, cache, device)
        - chunking bertanggung jawab atas logika pemrosesan teks
        - routes.py tidak perlu tahu cara model di-load atau
          bagaimana chunking bekerja, cukup panggil embed_dokumen()

    Args:
        teks: String teks dokumen yang sudah melalui clean_text().
              Nilai ini diambil dari kolom teks_ekstraksi di DB.

    Returns:
        np.ndarray berukuran (768,) yang merepresentasikan
        makna keseluruhan dokumen.
    """
    model = get_model()
    return encode_document(teks, model)


def embed_semua_dokumen(dokumen_list: list) -> dict:
    """
    Mengubah seluruh dokumen dalam satu sesi menjadi vektor embedding.

    Model di-load sekali di awal fungsi ini melalui get_model(),
    kemudian digunakan berulang untuk semua dokumen. Ini jauh lebih
    efisien dibanding load ulang model untuk setiap dokumen.

    Dokumen yang kolom teks_ekstraksiny kosong atau None dilewati
    dan tidak dimasukkan ke hasil. Ini menghindari error saat
    encode_document() menerima teks kosong.

    Args:
        dokumen_list: List objek DokumenTugas dari query database.
                      Setiap objek harus memiliki atribut:
                        - id_dokumen (int): primary key
                        - teks_ekstraksi (str): teks hasil preprocessing

    Returns:
        dict dengan format {id_dokumen (int): vektor (np.ndarray 768,)}
        Hanya berisi dokumen yang berhasil di-embed (teks tidak kosong).

    Contoh penggunaan di routes.py:
        dokumen_list = DokumenTugas.query.filter_by(id_sesi=id_sesi).all()
        embeddings = embed_semua_dokumen(dokumen_list)
        # embeddings = {1: array([...]), 2: array([...]), ...}
    """
    # Load model sekali sebelum loop, bukan di dalam loop
    model = get_model()

    hasil = {}

    for dokumen in dokumen_list:
        # Lewati dokumen yang tidak memiliki teks ekstraksi
        if not dokumen.teks_ekstraksi or not dokumen.teks_ekstraksi.strip():
            continue

        # encode_document() dari chunking.py menangani seluruh
        # pipeline: split kalimat → chunking → encode → mean pool
        vektor = encode_document(dokumen.teks_ekstraksi, model)

        # Simpan dengan id_dokumen sebagai key untuk dipakai
        # oleh similarity_service saat menghitung cosine similarity
        hasil[dokumen.id_dokumen] = vektor

    return hasil
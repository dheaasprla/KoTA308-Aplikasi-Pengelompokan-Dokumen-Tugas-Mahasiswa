# ============================================================
# FILE: services/similarity_service.py
# Layanan perhitungan cosine similarity antar dokumen
#
# Tanggung jawab file ini:
#   Menghitung skor kemiripan semantik antara semua pasangan
#   dokumen dalam satu sesi menggunakan cosine similarity.
#
# Metode:
#   Cosine similarity dari scikit-learn, sesuai yang tercantum
#   di laporan TA. Dipilih karena:
#   - Mengukur sudut antar vektor (bukan jarak absolut),
#     sehingga panjang dokumen tidak memengaruhi skor
#   - Efisien untuk vektor berdimensi tinggi (768 dimensi)
#   - Hasilnya dalam rentang 0.0-1.0 untuk vektor SBERT
#     yang selalu bernilai positif
#
# Referensi:
#   Syuja'i et al. (2026) - Deteksi Plagiarisme Tugas
#   Mahasiswa: Jurnal Algoritma Vol.23 No.1
#
# Dipanggil oleh: app/analisis/routes.py
# Memanggil    : sklearn.metrics.pairwise.cosine_similarity
# ============================================================

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from itertools import combinations


def hitung_similarity_matrix(embeddings: dict) -> dict:
    """
    Menghitung cosine similarity untuk semua pasangan unik dokumen.

    Menghasilkan complete graph dalam bentuk dict, di mana setiap
    pasangan dokumen memiliki skor kemiripannya. Disebut complete
    graph karena semua dokumen dibandingkan dengan semua dokumen
    lainnya tanpa terkecuali, sebelum nanti threshold diterapkan
    di clustering_service untuk membuang edge yang skornya rendah.

    Jumlah pasangan yang dihasilkan mengikuti rumus kombinasi:
        C(n,2) = n × (n-1) / 2
        Contoh: 32 dokumen → 32 × 31 / 2 = 496 pasangan

    Cara kerja sklearn cosine_similarity:
        - Menerima dua matrix 2D sebagai input
        - Menghitung dot product antar baris lalu dibagi
          perkalian magnitude-nya
        - Jauh lebih efisien dari menghitung satu per satu
          karena operasi matrix dilakukan secara vektorisasi

    Args:
        embeddings: dict {id_dokumen (int): vektor (np.ndarray 768,)}
                    Hasil dari embedding_service.embed_semua_dokumen()

    Returns:
        dict {(id_dok_a, id_dok_b): skor (float)}
        - Key adalah tuple dua id_dokumen, selalu (id_kecil, id_besar)
          untuk menghindari duplikasi pasangan (A,B) dan (B,A)
        - Value adalah skor cosine similarity dalam rentang 0.0-1.0
        - Skor sudah dibulatkan 4 desimal untuk efisiensi penyimpanan

    Contoh hasil:
        {
            (1, 2): 0.8732,
            (1, 3): 0.4521,
            (2, 3): 0.9103,
        }
    """
    hasil = {}

    # Ambil semua id_dokumen dari dict embeddings
    ids = list(embeddings.keys())

    # Perlu minimal 2 dokumen untuk bisa dibandingkan
    if len(ids) < 2:
        return hasil

    # combinations(ids, 2) menghasilkan semua pasangan unik tanpa
    # pengulangan. Misalnya [1,2,3] → (1,2), (1,3), (2,3)
    # Tidak ada (2,1) atau (3,1) karena itu pasangan yang sama.
    for id_a, id_b in combinations(ids, 2):

        # sklearn cosine_similarity() membutuhkan input 2D (matrix),
        # bukan 1D (vektor). Reshape dari (768,) menjadi (1, 768)
        # menggunakan np.array([[...]]) agar sesuai format sklearn.
        vektor_a = embeddings[id_a].reshape(1, -1)
        # reshape(1, -1): ubah shape dari (768,) menjadi (1, 768)
        # 1  = satu baris (satu dokumen)
        # -1 = kolom otomatis dihitung dari ukuran array (768)

        vektor_b = embeddings[id_b].reshape(1, -1)

        # cosine_similarity() mengembalikan matrix 2D (1x1) karena
        # kedua input hanya memiliki 1 baris masing-masing.
        # [0][0] mengambil nilai skalar dari matrix 1x1 tersebut.
        skor = cosine_similarity(vektor_a, vektor_b)[0][0]

        # Simpan skor dibulatkan 4 desimal.
        # Key tuple (id_a, id_b) sudah terurut karena combinations()
        # selalu menghasilkan pasangan dalam urutan yang sama dengan
        # urutan list ids di atas.
        hasil[(id_a, id_b)] = round(float(skor), 4)

    return hasil
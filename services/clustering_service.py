# ============================================================
# FILE: services/clustering_service.py
# Layanan graph-based clustering menggunakan NetworkX
#
# Tanggung jawab file ini:
#   Membangun graf kemiripan dokumen, menerapkan threshold
#   untuk memangkas edge yang skornya rendah, lalu mendeteksi
#   connected components sebagai hasil pengelompokan akhir.
#
# Alur kerja:
#   1. Bangun complete graph dari semua pasangan dokumen
#      (setiap pasangan = satu edge dengan bobot skor similarity)
#   2. Pangkas edge yang skornya di bawah threshold
#      (threshold dari konfigurasi sesi, skala 0-100)
#   3. Deteksi connected components menggunakan NetworkX BFS
#   4. Pisahkan hasil menjadi kelompok (>= 2 dokumen) dan
#      outlier (dokumen yang tidak terhubung ke manapun)
#
# Algoritma traversal:
#   BFS (Breadth-First Search) via nx.connected_components()
#   Dipilih karena NetworkX menggunakan BFS secara internal
#   dan menghasilkan output yang identik dengan DFS untuk
#   tujuan deteksi connected components.
#
# Terminologi yang digunakan (sesuai masukan dosen pembimbing):
#   - "Kelompok" atau "connected components": dokumen yang
#     saling terhubung setelah threshold diterapkan
#   - "Outlier": dokumen yang tidak terhubung ke manapun
#   - Hindari kata "cluster" karena bermakna teknis spesifik
#     (hasil algoritma K-Means/DBSCAN) yang berbeda konteks
#
# Dipanggil oleh: app/analisis/routes.py
# Memanggil    : networkx
# ============================================================

import networkx as nx


def bangun_complete_graph(similarity_matrix: dict) -> nx.Graph:
    """
    Membangun complete graph dari semua pasangan dokumen.

    Complete graph berarti semua node (dokumen) terhubung
    ke semua node lainnya sebelum threshold diterapkan.
    Setiap edge memiliki bobot (weight) berupa skor cosine
    similarity antara dua dokumen yang dihubungkannya.

    Args:
        similarity_matrix: dict {(id_a, id_b): skor}
                           Hasil dari similarity_service.
                           hitung_similarity_matrix()

    Returns:
        nx.Graph (undirected/tidak berarah) karena kemiripan
        dokumen A terhadap B sama dengan B terhadap A,
        sehingga edge tidak memerlukan arah.
        Bidireksional: jika A mirip B, maka B juga mirip A.
    """
    G = nx.Graph()

    for (id_a, id_b), skor in similarity_matrix.items():
        # Tambahkan node secara implisit saat menambahkan edge.
        # nx.Graph.add_edge() otomatis membuat node jika belum ada.
        # weight=skor menyimpan nilai similarity sebagai atribut edge
        # untuk keperluan tampilan atau analisis lebih lanjut.
        G.add_edge(id_a, id_b, weight=skor)

    return G


def pangkas_edge_bawah_threshold(
    G: nx.Graph,
    threshold_persen: float
) -> nx.Graph:
    """
    Membuang edge yang skor similarity-nya di bawah threshold.

    Setelah edge dibuang, node yang tidak lagi memiliki tetangga
    menjadi isolated node (outlier) yang akan dideteksi di tahap
    selanjutnya oleh deteksi_connected_components().

    Args:
        G               : complete graph hasil bangun_complete_graph()
        threshold_persen: nilai threshold dalam skala 0-100,
                          sesuai kolom threshold_awal di models.py.
                          Dikonversi ke 0.0-1.0 di dalam fungsi ini
                          untuk dibandingkan dengan skor similarity
                          yang juga dalam skala 0.0-1.0.

    Returns:
        nx.Graph yang sama dengan input tapi edge di bawah threshold
        sudah dibuang. Node tetap ada meskipun semua edge-nya dibuang
        agar outlier tetap bisa terdeteksi di tahap berikutnya.
    """
    # Konversi threshold dari skala 0-100 ke 0.0-1.0
    # karena skor cosine similarity dari sklearn dalam rentang 0.0-1.0
    threshold = threshold_persen / 100.0

    # Kumpulkan edge yang akan dibuang terlebih dahulu.
    # Tidak bisa langsung hapus saat iterasi karena akan
    # mengubah ukuran list yang sedang diiterasi (runtime error).
    edge_dibuang = [
        (u, v)
        for u, v, data in G.edges(data=True)
        if data['weight'] < threshold
        # data['weight'] adalah skor similarity yang disimpan
        # saat add_edge() dipanggil di bangun_complete_graph()
    ]

    # Hapus semua edge yang skornya di bawah threshold
    G.remove_edges_from(edge_dibuang)

    return G


def deteksi_connected_components(G: nx.Graph) -> dict:
    """
    Mendeteksi connected components setelah threshold diterapkan
    menggunakan BFS dari NetworkX.

    nx.connected_components() mengembalikan semua kelompok node
    yang saling terhubung, termasuk node yang terisolasi (tidak
    punya edge) sebagai komponen berukuran 1.

    Fungsi ini memisahkan hasil menjadi dua kategori:
        - kelompok: connected component dengan >= 2 dokumen
          (dokumen-dokumen ini saling mirip satu sama lain
          dan layak ditampilkan sebagai satu kelompok)
        - outlier: connected component dengan hanya 1 dokumen
          (dokumen ini tidak cukup mirip dengan dokumen manapun
          setelah threshold diterapkan)

    Args:
        G: nx.Graph setelah edge di bawah threshold dibuang,
           hasil dari pangkas_edge_bawah_threshold()

    Returns:
        dict dengan dua key:
            'kelompok': list of list[int], setiap sublist berisi
                        id_dokumen yang berada dalam satu kelompok.
                        Diurutkan berdasarkan ukuran kelompok
                        (terbesar lebih dulu) untuk kemudahan tampilan.
            'outlier' : list[int] berisi id_dokumen yang tidak
                        terhubung ke dokumen manapun.
    """
    # nx.connected_components() mengembalikan generator of set.
    # Setiap set berisi id_dokumen yang saling terhubung.
    # Ini menggunakan BFS secara internal.
    components = list(nx.connected_components(G))

    kelompok = []
    outlier = []

    for component in components:
        if len(component) >= 2:
            # Dokumen-dokumen ini saling mirip satu sama lain
            # setelah threshold diterapkan → masuk kelompok
            kelompok.append(sorted(list(component)))
            # sorted() agar urutan id_dokumen konsisten
        else:
            # Hanya satu dokumen, tidak terhubung ke manapun → outlier
            outlier.extend(list(component))

    # Urutkan kelompok dari yang paling banyak anggotanya
    # agar kelompok terbesar (paling banyak kemiripan) tampil duluan
    kelompok.sort(key=len, reverse=True)

    return {
        'kelompok': kelompok,
        'outlier' : sorted(outlier)
    }


def jalankan_clustering(
    similarity_matrix: dict,
    threshold_persen: float
) -> dict:
    """
    Fungsi utama yang dipanggil oleh app/analisis/routes.py.
    Mengorkestrasi seluruh pipeline graph-based clustering.

    Pipeline:
        1. Bangun complete graph dari similarity matrix
        2. Pangkas edge di bawah threshold
        3. Deteksi connected components (BFS via NetworkX)
        4. Pisahkan kelompok dan outlier

    Args:
        similarity_matrix: dict {(id_a, id_b): skor}
                           dari similarity_service
        threshold_persen : float dalam skala 0-100,
                           nilai dari sesi.threshold_awal di DB

    Returns:
        dict hasil lengkap siap diproses oleh routes.py:
        {
            'kelompok'        : [[id1, id2], [id3, id4, id5], ...],
            'outlier'         : [id6, id7, ...],
            'total_edge'      : 496,   ← jumlah edge complete graph
            'edge_aktif'      : 12,    ← jumlah edge setelah threshold
            'threshold_dipakai': 70.0  ← threshold yang digunakan
        }
    """
    # Step 1: Bangun complete graph
    G = bangun_complete_graph(similarity_matrix)
    total_edge = G.number_of_edges()

    # Step 2: Pangkas edge di bawah threshold
    G = pangkas_edge_bawah_threshold(G, threshold_persen)
    edge_aktif = G.number_of_edges()

    # Step 3 & 4: Deteksi connected components dan pisahkan
    hasil = deteksi_connected_components(G)

    # Tambahkan informasi statistik graf untuk kebutuhan
    # tampilan dan dokumentasi di laporan TA
    hasil['total_edge']       = total_edge
    hasil['edge_aktif']       = edge_aktif
    hasil['threshold_dipakai'] = threshold_persen

    return hasil
# ============================================================
# FILE: services/highlight_service.py
# Layanan deteksi kalimat mirip antar dua dokumen
# untuk fitur side-by-side comparison
#
# Tanggung jawab file ini:
#   Membandingkan setiap kalimat dari dokumen 1 dengan setiap
#   kalimat dari dokumen 2 menggunakan cosine similarity SBERT,
#   lalu menandai pasangan kalimat yang similarity-nya melewati
#   threshold sebagai kalimat yang terindikasi mirip.
#
# Threshold yang digunakan:
#   Mengikuti sesi.threshold_awal (skala 0-100) agar konsisten
#   dengan threshold pengelompokan dokumen. Tidak ada threshold
#   terpisah untuk level kalimat.
#
# Format output (disimpan sebagai JSON di DB):
#   kalimat_highlight1: list indeks kalimat di dokumen 1
#                       yang terindikasi mirip
#   kalimat_highlight2: list indeks kalimat di dokumen 2
#                       yang terindikasi mirip
#
# Dipanggil oleh: app/analisis/routes.py (endpoint sidebyside)
# Memanggil    : services/embedding_service.py, utils/chunking.py
# ============================================================

import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from services.embedding_service import get_model
from utils.chunking import (
    split_into_sentences,
    pecah_kalimat_super_panjang,
    CHUNK_SIZE
)


def encode_kalimat(kalimat_list: list[str]) -> np.ndarray:
    """
    Encode daftar kalimat menjadi matrix embedding.

    Berbeda dengan encode_document() di chunking.py yang
    menghasilkan SATU vektor per dokumen via mean pooling,
    fungsi ini menghasilkan SATU VEKTOR PER KALIMAT karena
    kita perlu membandingkan kalimat satu per satu.

    Args:
        kalimat_list: list string kalimat hasil split_into_sentences()

    Returns:
        np.ndarray berukuran (jumlah_kalimat x 768)
        Setiap baris adalah vektor embedding satu kalimat.
    """
    model = get_model()
    # model.encode() menerima list of string dan mengembalikan
    # matrix (n x 768) di mana n = jumlah kalimat
    
    tokenizer = model.tokenizer
    kalimat_aman = []
    
    for kalimat in kalimat_list:
        jumlah_token = len(tokenizer.tokenize(kalimat))
        if jumlah_token <= CHUNK_SIZE:
            kalimat_aman.append([kalimat])
        else:
            potongan = pecah_kalimat_super_panjang(kalimat, tokenizer, CHUNK_SIZE)
            kalimat_aman.append(potongan)
            
    semua_potongan_flat = [p for grup in kalimat_aman for p in grup]
    if not semua_potongan_flat:
        return np.zeros((0, model.get_sentence_embedding_dimension()))
 
    embeddings_flat = model.encode(
        semua_potongan_flat,
        show_progress_bar=False,
        convert_to_numpy=True
    )
    
    hasil = []
    idx = 0
    for grup in kalimat_aman:
        n = len(grup)
        vektor_grup = embeddings_flat[idx:idx + n]
        hasil.append(np.mean(vektor_grup, axis=0))
        idx += n
 
    return np.array(hasil)


def deteksi_kalimat_mirip(
    teks_1: str,
    teks_2: str,
    threshold_persen: float
) -> dict:
    """
    Mendeteksi pasangan kalimat yang terindikasi mirip antara
    dua dokumen menggunakan cosine similarity SBERT per kalimat.

    Algoritma:
        1. Split kedua teks menjadi kalimat
        2. Encode semua kalimat kedua dokumen dengan SBERT
        3. Hitung similarity matrix: setiap kalimat dok1
           dibandingkan dengan setiap kalimat dok2
           → matrix berukuran (len_kalimat1 x len_kalimat2)
        4. Untuk setiap kalimat di dok1, cari kalimat di dok2
           yang similarity-nya >= threshold
        5. Tandai indeks kalimat yang mirip di kedua dokumen

    Mengapa indeks bukan teks kalimatnya:
        Menyimpan indeks lebih efisien dari menyimpan teks
        kalimat penuh. Frontend cukup split teks dokumen
        lalu highlight kalimat di indeks yang diberikan.

    Args:
        teks_1          : teks_ekstraksi dokumen pertama dari DB
        teks_2          : teks_ekstraksi dokumen kedua dari DB
        threshold_persen: threshold dari sesi.threshold_awal (0-100)
                          dikonversi ke 0.0-1.0 di dalam fungsi ini

    Returns:
        dict dengan format:
        {
            "kalimat_1": [
                {"indeks": 2, "kalimat": "teks kalimat..."},
                {"indeks": 5, "kalimat": "teks kalimat..."},
            ],
            "kalimat_2": [
                {"indeks": 7, "kalimat": "teks kalimat..."},
                {"indeks": 1, "kalimat": "teks kalimat..."},
            ],
            "total_mirip": 2
        }
        Disimpan sebagai JSON string di kolom kalimat_highlight
        di tabel detail_kemiripan.
    """
    # Konversi threshold dari skala 0-100 ke 0.0-1.0
    threshold = threshold_persen / 100.0

    # ── Step 1: Split teks menjadi kalimat ──
    # Menggunakan fungsi yang sama dengan pipeline chunking
    # agar konsisten dalam cara memecah kalimat
    kalimat_dok1 = split_into_sentences(teks_1)
    kalimat_dok2 = split_into_sentences(teks_2)

    # Kalau salah satu dokumen tidak punya kalimat yang bisa
    # diparsing, return hasil kosong
    if not kalimat_dok1 or not kalimat_dok2:
        return {
            "kalimat_1"   : [],
            "kalimat_2"   : [],
            "total_mirip" : 0
        }

    # ── Step 2: Encode semua kalimat kedua dokumen ──
    # Menghasilkan matrix embedding per kalimat (bukan per dokumen)
    # Model sudah ter-cache dari pipeline analisis sebelumnya
    embeddings_1 = encode_kalimat(kalimat_dok1)
    # embeddings_1 shape: (len(kalimat_dok1), 768)

    embeddings_2 = encode_kalimat(kalimat_dok2)
    # embeddings_2 shape: (len(kalimat_dok2), 768)

    # ── Step 3: Hitung similarity matrix antar kalimat ──
    # cosine_similarity(A, B) menghasilkan matrix (len_A x len_B)
    # di mana [i][j] adalah similarity kalimat i dari dok1
    # terhadap kalimat j dari dok2
    similarity_matrix = cosine_similarity(embeddings_1, embeddings_2)
    # shape: (len(kalimat_dok1) x len(kalimat_dok2))

    # ── Step 4 & 5: Temukan pasangan kalimat yang mirip ──
    # Gunakan set untuk menghindari duplikasi indeks kalau
    # satu kalimat mirip dengan beberapa kalimat sekaligus
    indeks_mirip_1 = set()
    indeks_mirip_2 = set()

    for i in range(len(kalimat_dok1)):
        for j in range(len(kalimat_dok2)):
            if similarity_matrix[i][j] >= threshold:
                # Kalimat i di dok1 mirip dengan kalimat j di dok2
                indeks_mirip_1.add(i)
                indeks_mirip_2.add(j)

    # Susun hasil sebagai list dict dengan indeks dan teks kalimat
    # Diurutkan berdasarkan indeks agar urutan kalimat terjaga
    hasil_kalimat_1 = [
        {
            "indeks" : i,
            "kalimat": kalimat_dok1[i]
        }
        for i in sorted(indeks_mirip_1)
    ]

    hasil_kalimat_2 = [
        {
            "indeks" : j,
            "kalimat": kalimat_dok2[j]
        }
        for j in sorted(indeks_mirip_2)
    ]

    return {
        "kalimat_1"  : hasil_kalimat_1,
        "kalimat_2"  : hasil_kalimat_2,
        "total_mirip": len(indeks_mirip_1)
    }


def proses_highlight(
    detail_kemiripan,
    dokumen_1,
    dokumen_2,
    threshold_persen: float
) -> dict:
    """
    Fungsi utama yang dipanggil oleh routes.py.
    Mengorkestrasi deteksi kalimat mirip dan penyimpanan
    hasilnya ke kolom kalimat_highlight di DB.

    Menangani dua skenario:
        1. Highlight sudah ada di DB (sudah pernah diproses)
           → langsung return dari DB tanpa komputasi ulang
        2. Highlight belum ada (NULL, pertama kali diklik)
           → proses SBERT → simpan ke DB → return hasil

    Args:
        detail_kemiripan: objek DetailKemiripan dari DB
        dokumen_1       : objek DokumenTugas pertama
        dokumen_2       : objek DokumenTugas kedua
        threshold_persen: dari sesi.threshold_awal (0-100)

    Returns:
        dict hasil highlight siap dikirim ke frontend:
        {
            "dokumen_1": {
                "nama_file": "Dhea_Tugas1.pdf",
                "kalimat"  : [{"indeks": 2, "kalimat": "..."}]
            },
            "dokumen_2": {
                "nama_file": "Berliana_Tugas1.pdf",
                "kalimat"  : [{"indeks": 7, "kalimat": "..."}]
            },
            "persentase_kemiripan": 87.32,
            "total_mirip"         : 5,
            "dari_cache"          : True/False
        }
    """
    # ── Skenario 1: Highlight sudah ada di DB ──
    # kalimat_highlight1 dan kalimat_highlight2 sudah terisi
    # dari proses sebelumnya, langsung return tanpa komputasi
    if detail_kemiripan.kalimat_highlight1 is not None:
        highlight_1 = json.loads(detail_kemiripan.kalimat_highlight1)
        highlight_2 = json.loads(detail_kemiripan.kalimat_highlight2)

        return {
            "dokumen_1": {
                "nama_file": dokumen_1.nama_file,
                "kalimat"  : highlight_1.get("kalimat_1", [])
            },
            "dokumen_2": {
                "nama_file": dokumen_2.nama_file,
                "kalimat"  : highlight_2.get("kalimat_2", [])
            },
            "persentase_kemiripan": detail_kemiripan.persentase_kemiripan,
            "total_mirip"         : highlight_1.get("total_mirip", 0),
            "dari_cache"          : True
            # dari_cache=True memberi tahu frontend bahwa
            # data ini diambil dari DB, bukan diproses ulang
        }

    # ── Skenario 2: Highlight belum ada, perlu diproses ──
    hasil = deteksi_kalimat_mirip(
        dokumen_1.teks_ekstraksi,
        dokumen_2.teks_ekstraksi,
        threshold_persen
    )

    # Simpan hasil ke DB agar tidak perlu diproses ulang
    # kalimat_highlight1 menyimpan data kalimat dari dokumen 1
    # kalimat_highlight2 menyimpan data kalimat dari dokumen 2
    # Keduanya menyimpan total_mirip untuk referensi cepat
    detail_kemiripan.kalimat_highlight1 = json.dumps({
        "kalimat_1"  : hasil["kalimat_1"],
        "total_mirip": hasil["total_mirip"]
    }, ensure_ascii=False)
    # ensure_ascii=False agar karakter Bahasa Indonesia
    # (huruf berdiakritik) tersimpan dengan benar, bukan
    # dikonversi ke escape sequence \uXXXX

    detail_kemiripan.kalimat_highlight2 = json.dumps({
        "kalimat_2"  : hasil["kalimat_2"],
        "total_mirip": hasil["total_mirip"]
    }, ensure_ascii=False)

    # Commit dilakukan di routes.py setelah fungsi ini selesai
    # agar error handling tetap terpusat di routes

    return {
        "dokumen_1": {
            "nama_file": dokumen_1.nama_file,
            "kalimat"  : hasil["kalimat_1"]
        },
        "dokumen_2": {
            "nama_file": dokumen_2.nama_file,
            "kalimat"  : hasil["kalimat_2"]
        },
        "persentase_kemiripan": detail_kemiripan.persentase_kemiripan,
        "total_mirip"         : hasil["total_mirip"],
        "dari_cache"          : False
    }
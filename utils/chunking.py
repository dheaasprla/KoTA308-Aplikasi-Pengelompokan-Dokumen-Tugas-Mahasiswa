# ============================================================
# FILE: utils/chunking.py
# Implementasi sentence-aware sliding window chunking
#
# Tujuan:
#   Memecah teks dokumen panjang menjadi chunk-chunk berukuran
#   <= CHUNK_SIZE token agar bisa diproses model SBERT yang
#   memiliki batas maksimum 128 token per input.
#
# Strategi:
#   Sentence-aware sliding window dengan overlap 1 kalimat.
#   - "Sentence-aware": pemecahan dilakukan di batas kalimat
#     (titik, tanda tanya, tanda seru), bukan di batas token
#     tetap, agar tidak ada kalimat yang terpotong di tengah.
#   - "Sliding window overlap 1 kalimat": kalimat terakhir dari
#     chunk sebelumnya dijadikan kalimat pertama chunk berikutnya
#     sebagai jembatan konteks, sehingga chunk berikutnya tetap
#     memahami topik yang sedang dibahas.
#
# Pipeline encode_document():
#   1. Hitung jumlah token dokumen
#   2a. Jika <= 128 token: encode langsung tanpa chunking
#   2b. Jika >  128 token: chunking dulu, encode per chunk,
#       mean pool semua vektor chunk menjadi 1 vektor dokumen
#
# Referensi SRS: Constraint C-05
#   "Dokumen yang melebihi kapasitas masukan model bahasa secara
#    otomatis diolah melalui strategi chunking tanpa memotong
#    atau menghilangkan kalimat."
#
# Dipanggil oleh: services/embedding_service.py
# ============================================================

import re
import numpy as np
from sentence_transformers import SentenceTransformer


# Batas maksimum token per chunk, sesuai max_seq_length efektif
# model paraphrase-multilingual-mpnet-base-v2 berdasarkan data
# pelatihannya (NLI dataset dengan rata-rata kalimat pendek).
CHUNK_SIZE = 128

# Jumlah kata yang di-overlap antar potongan saat memecah SATU
# kalimat yang super panjang (lihat pecah_kalimat_super_panjang).
OVERLAP_KATA_KALIMAT_PANJANG = 5


def split_into_sentences(text: str) -> list[str]:
    """
    Memecah teks menjadi daftar kalimat berdasarkan tanda baca
    akhir kalimat: titik (.), tanda tanya (?), tanda seru (!).

    Pola regex yang digunakan:
        (?<=[.!?]) → lookbehind: posisi tepat setelah . atau ! atau ?
        \\s+       → diikuti satu atau lebih whitespace (spasi/tab)

    Artinya: pecah teks di setiap posisi yang tepat setelah
    tanda baca akhir kalimat dan diikuti whitespace. Tanda baca
    itu sendiri TIDAK ikut dihapus, tetap menempel di akhir
    kalimat sebelumnya (karena lookbehind tidak mengonsumsi karakter).

    Contoh:
        Input : "Kalimat pertama. Kalimat kedua? Kalimat ketiga!"
        Output: ["Kalimat pertama.", "Kalimat kedua?", "Kalimat ketiga!"]

    Hanya dipanggil oleh encode_document() ketika jumlah token
    dokumen > CHUNK_SIZE (jalur chunking).

    Args:
        text: Teks yang sudah melalui clean_text() dari preprocessor.

    Returns:
        List string, setiap elemen adalah satu kalimat.
        List kosong jika input kosong atau None.
    """
    if not text or not text.strip():
        return []

    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    return sentences

def pecah_kalimat_super_panjang(
    kalimat: str,
    tokenizer,
    chunk_size: int = CHUNK_SIZE,
    overlap_kata: int = OVERLAP_KATA_KALIMAT_PANJANG
) -> list[str]:
    """
    Memecah SATU kalimat yang ternyata masih melebihi chunk_size
    token menjadi beberapa potongan aman, dengan sedikit overlap
    antar potongan.
 
    Kasus ini terjadi ketika split_into_sentences() gagal memecah
    teks secara wajar (biasanya karena teks sumber dari PDF minim
    tanda baca, misalnya hasil ekstraksi tabel atau daftar), sehingga
    satu "kalimat" hasil pecahan bisa berukuran ratusan token.
 
    Pemecahan dilakukan per kata (bukan per sub-kalimat, karena
    memang tidak ada tanda baca yang bisa dijadikan acuan lagi
    di titik ini). Overlap antar potongan tetap diterapkan untuk
    menjaga sedikit jembatan konteks, konsisten dengan filosofi
    sliding window yang dipakai di seluruh pipeline chunking ini,
    meskipun potongan ini bukan lagi berbasis kalimat utuh.
 
    Args:
        kalimat    : teks kalimat yang terlalu panjang
        tokenizer  : tokenizer dari model SentenceTransformer
        chunk_size : batas maksimum token per potongan (default 128)
        overlap_kata: jumlah kata yang di-overlap antar potongan
 
    Returns:
        List string, setiap elemen adalah potongan kalimat yang
        aman di-encode (token count <= chunk_size). Kalau kalimat
        sudah aman dari awal, dikembalikan sebagai list berisi
        satu elemen (kalimat itu sendiri, tidak diubah).
    """
    kata_list = kalimat.split(' ')
    potongan = []
    kata_sekarang = []
    token_sekarang = 0
 
    for kata in kata_list:
        token_kata = len(tokenizer.tokenize(kata))
 
        if token_sekarang + token_kata > chunk_size and kata_sekarang:
            potongan.append(' '.join(kata_sekarang))
 
            # Sliding window di level kata: ambil beberapa kata
            # terakhir dari potongan yang baru selesai, jadikan
            # awal potongan berikutnya sebagai jembatan konteks.
            overlap = kata_sekarang[-overlap_kata:]
            kata_sekarang = overlap + [kata]
            token_sekarang = sum(len(tokenizer.tokenize(k)) for k in kata_sekarang)
        else:
            kata_sekarang.append(kata)
            token_sekarang += token_kata
 
    if kata_sekarang:
        potongan.append(' '.join(kata_sekarang))
 
    return potongan if potongan else [kalimat]

def group_sentences_into_chunks(
    sentences: list[str],
    tokenizer,
    chunk_size: int = CHUNK_SIZE
) -> list[str]:
    """
    Mengelompokkan daftar kalimat menjadi chunk-chunk teks dengan
    strategi sliding window overlap 1 kalimat.

    Hanya dipanggil oleh encode_document() ketika jumlah token
    dokumen > CHUNK_SIZE (jalur chunking).

    Algoritma per kalimat:
        1. Hitung jumlah token kalimat ini menggunakan tokenizer asli
           model (WordPiece), bukan estimasi kata/karakter.
        2. Jika kalimat + isi chunk saat ini masih <= chunk_size:
           → tambahkan kalimat ke chunk saat ini.
        3. Jika menambahkan kalimat ini akan melewati chunk_size:
           → simpan chunk saat ini ke daftar hasil.
           → mulai chunk baru dengan kalimat TERAKHIR dari chunk
             sebelumnya (overlap) + kalimat ini.
        4. Kasus khusus: satu kalimat saja sudah > chunk_size.
           Jadikan chunk sendiri agar tidak ada kalimat yang terbuang.

    Args:
        sentences : list kalimat dari split_into_sentences()
        tokenizer : tokenizer dari model SentenceTransformer
        chunk_size: batas maksimum token per chunk (default 128)

    Returns:
        List string, setiap elemen adalah satu chunk teks siap
        di-encode oleh model.encode().
    """
    if not sentences:
        return []

    chunks = []
    current_sentences = []
    current_token_count = 0

    for sentence in sentences:
        sentence_token_count = len(tokenizer.tokenize(sentence))

        # ── Kasus khusus: satu kalimat > chunk_size ──
        if sentence_token_count > chunk_size:
            if current_sentences:
                chunks.append(' '.join(current_sentences))
                current_sentences = []
                current_token_count = 0
            potongan_aman = pecah_kalimat_super_panjang(sentence, tokenizer, chunk_size)
            chunks.extend(potongan_aman)
            continue

        # ── Kalimat masih muat di chunk saat ini ──
        if current_token_count + sentence_token_count <= chunk_size:
            current_sentences.append(sentence)
            current_token_count += sentence_token_count

        # ── Kalimat tidak muat: simpan chunk, mulai chunk baru ──
        else:
            if current_sentences:
                chunks.append(' '.join(current_sentences))

                # Sliding window: kalimat terakhir chunk lama
                # menjadi kalimat pertama chunk baru sebagai
                # jembatan konteks antar chunk
                overlap_sentence = current_sentences[-1]
                overlap_token_count = len(tokenizer.tokenize(overlap_sentence))

                current_sentences = [overlap_sentence, sentence]
                current_token_count = overlap_token_count + sentence_token_count
            else:
                current_sentences = [sentence]
                current_token_count = sentence_token_count

    # Simpan chunk terakhir yang belum tersimpan
    if current_sentences:
        chunks.append(' '.join(current_sentences))

    return chunks


def encode_document(text: str, model: SentenceTransformer) -> np.ndarray:
    """
    Fungsi utama yang dipanggil oleh embedding_service.py.
    Mengubah satu dokumen teks menjadi satu vektor embedding
    768 dimensi sesuai pipeline yang dirancang.

    Pipeline (sesuai Constraint C-05 SRS):

        Teks dokumen masuk
                │
                ▼
        Hitung jumlah token
                │
                ├── <= 128 token ──────────────────────────────────┐
                │   Encode langsung tanpa chunking                  │
                │   model.encode(text) → vektor (768,)             │
                │                                                   │
                └── > 128 token                                     │
                    Pecah menjadi kalimat                           │
                            ↓                                       │
                    Kelompokkan ke chunk <= 128 token               │
                    dengan sliding window overlap 1 kalimat         │
                            ↓                                       │
                    Encode semua chunk dalam satu batch             │
                    model.encode([chunk1, chunk2, ...])             │
                    → matrix (jumlah_chunk x 768)                  │
                            ↓                                       │
                    Mean pooling antar chunk                        │
                    np.mean(axis=0) → vektor (768,) ───────────────┘
                                                        │
                                                        ▼
                                            Vektor dokumen final (768,)
                                            siap untuk cosine similarity

    Args:
        text : teks dokumen yang sudah melalui clean_text()
               (nilai dari kolom teks_ekstraksi di database)
        model: SentenceTransformer yang sudah di-load,
               dikirim dari embedding_service agar tidak
               di-load ulang setiap kali fungsi ini dipanggil

    Returns:
        np.ndarray berukuran (768,) yang merepresentasikan
        makna keseluruhan dokumen.
        Jika teks kosong, return vektor nol (768,).
    """
    if not text or not text.strip():
        return np.zeros(model.get_sentence_embedding_dimension())

    tokenizer = model.tokenizer

    # ── Step 1: Hitung jumlah token dokumen ──
    # Ini adalah pengecekan awal untuk menentukan jalur mana
    # yang akan diambil: encode langsung atau chunking dulu.
    # Menggunakan tokenizer asli model (bukan estimasi kata)
    # agar perhitungan token akurat sesuai WordPiece model.
    token_count = len(tokenizer.tokenize(text))

    # ── Jalur A: Dokumen pendek (<= 128 token) ──
    # Encode langsung tanpa melalui proses chunking.
    # Ini adalah jalur yang lebih cepat dan lebih sederhana.
    if token_count <= CHUNK_SIZE:
        embedding = model.encode(
            text,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        return embedding

    # ── Jalur B: Dokumen panjang (> 128 token) ──
    # Dokumen perlu dipecah dulu sebelum bisa di-encode karena
    # melebihi batas max_seq_length model (128 token).

    # Step 2: Pecah teks menjadi kalimat
    sentences = split_into_sentences(text)

    if not sentences:
        return np.zeros(model.get_sentence_embedding_dimension())

    # Step 3: Kelompokkan kalimat ke chunk dengan sliding window
    chunks = group_sentences_into_chunks(sentences, tokenizer)

    # Step 4: Encode semua chunk dalam satu batch sekaligus
    # model.encode() memproses semua chunk secara paralel,
    # menghasilkan matrix (jumlah_chunk x 768)
    chunk_embeddings = model.encode(
        chunks,
        show_progress_bar=False,
        convert_to_numpy=True
    )

    # Step 5: Mean pooling antar chunk
    # Rata-rata semua vektor chunk per dimensi menghasilkan
    # satu vektor (768,) yang merepresentasikan seluruh dokumen
    document_embedding = np.mean(chunk_embeddings, axis=0)

    return document_embedding
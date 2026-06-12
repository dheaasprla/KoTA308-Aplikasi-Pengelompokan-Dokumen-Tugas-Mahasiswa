# ============================================================
# FILE: utils/text_preprocessor.py
# Fungsi preprocessing teks sesuai FR-07 dan FR-08
#
# Tahap yang dilakukan (Case Folding):
#   1. Lowercase seluruh teks
#   2. Hapus URL (http://, https://, www.)
#   3. Hapus karakter newline (\n, \r), ganti jadi spasi
#   4. Reduksi spasi ganda menjadi satu spasi
#   5. Hapus karakter non-ASCII (artefak font/simbol PDF)
#
# Tanda baca ASCII standar (. , ! ? ; : ' " - ( ) dst) TETAP
# DIPERTAHANKAN karena memuat informasi struktural kalimat
# yang dibutuhkan model SBERT pada tahap analisis nanti.
#
# Tokenizing (WordPiece) TIDAK dilakukan di sini karena itu
# bawaan dari SBERT tokenizer yang baru di-load di sprint
# analisis (bukan fungsi independen yang kita tulis sendiri).
# ============================================================

import re


def clean_text(raw_text: str) -> str:
    """
    Membersihkan teks hasil ekstraksi PDF (case folding).

    Args:
        raw_text: Teks mentah hasil ekstraksi PyMuPDF.

    Returns:
        Teks yang sudah dibersihkan, siap disimpan ke kolom
        teks_ekstraksi. Jika input kosong/None, return string kosong.
    """
    if not raw_text:
        return ""

    text = raw_text

    # 1. Lowercase seluruh teks
    text = text.lower()

    # 2. Hapus URL (http://, https://, www.)
    text = re.sub(r'(https?://\S+|www\.\S+)', ' ', text)

    # 3. Hapus karakter newline dan carriage return, ganti spasi
    text = text.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')

    # 4. Hapus karakter non-ASCII (emoji, bullet •, artefak font, dll)
    #    Tanda baca ASCII standar (kode 32-126) lolos dari filter ini
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)

    # 5. Reduksi spasi ganda/berlebih menjadi satu spasi
    #    Dilakukan TERAKHIR karena langkah 2-4 berpotensi
    #    menyisakan multiple spaces
    text = re.sub(r'\s+', ' ', text)

    text = text.strip()

    return text
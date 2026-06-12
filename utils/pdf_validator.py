# ============================================================
# FILE: utils/pdf_validator.py
# Validasi dan ekstraksi teks dokumen PDF menggunakan PyMuPDF
#
# Mencakup:
#   - Validasi ekstensi file (.pdf)
#   - Deteksi dokumen scan / image-only tanpa OCR (C-02)
#   - Ekstraksi teks mentah dari seluruh halaman
#
# Install: pip install PyMuPDF
# Import name: fitz
# ============================================================

import fitz  # PyMuPDF


ALLOWED_EXTENSION = '.pdf'

# Ambang batas minimum jumlah karakter agar dokumen dianggap
# text-based. Mengatasi kasus PDF scan yang memiliki sedikit
# teks "sisa" (artefak stempel/watermark/font metadata) namun
# secara substansi tidak memiliki konten esai yang bisa
# dianalisis SBERT.
MIN_TEXT_LENGTH = 50


def is_allowed_extension(filename: str) -> bool:
    """
    Cek apakah nama file memiliki ekstensi .pdf (case-insensitive).
    """
    if not filename:
        return False
    return filename.lower().endswith(ALLOWED_EXTENSION)


def extract_text_from_pdf(file_stream) -> str:
    """
    Ekstrak seluruh teks dari file PDF menggunakan PyMuPDF.

    Args:
        file_stream: File-like object (request.files['x'].stream).

    Returns:
        String berisi gabungan teks dari seluruh halaman, dipisah
        spasi antar halaman. Return string kosong jika tidak ada
        teks yang bisa diekstrak.
    """
    extracted_pages = []

    with fitz.open(stream=file_stream.read(), filetype="pdf") as doc:
        for page in doc:
            page_text = page.get_text()
            if page_text:
                extracted_pages.append(page_text)

    return " ".join(extracted_pages)


def is_text_based_pdf(file_stream) -> bool:
    """
    Deteksi apakah PDF berbasis teks (selectable) atau hasil scan
    tanpa OCR (image-only / teks tidak substansial), sesuai
    constraint C-02.

    Dokumen dianggap text-based hanya jika hasil ekstraksi teks
    memiliki panjang >= MIN_TEXT_LENGTH karakter (setelah strip
    whitespace). PDF hasil scan yang sudah melalui OCR oleh
    aplikasi sumber tetap dianggap valid selama memiliki teks
    substansial.

    Note:
        Karena membaca stream akan menggerakkan posisi pointer
        file, pastikan untuk melakukan file_stream.seek(0) SEBELUM
        dan SESUDAH memanggil fungsi ini jika file_stream akan
        dibaca ulang (misalnya untuk extract_text_from_pdf atau
        file.save()).
    """
    try:
        text = extract_text_from_pdf(file_stream)
        return len(text.strip()) >= MIN_TEXT_LENGTH
    except Exception:
        return False
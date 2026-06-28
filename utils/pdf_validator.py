# ============================================================
# FILE: utils/pdf_validator.py
# Validasi dan ekstraksi teks dokumen PDF menggunakan PyMuPDF
#
# Mencakup:
#   - Validasi ekstensi file (.pdf)
#   - Validasi kandungan teks dokumen (C-02)
#   - Ekstraksi teks mentah dari seluruh halaman
#
# Install: pip install PyMuPDF
# Import name: fitz
# ============================================================

import os   # <-- BARU: dibutuhkan untuk membaca nilai MIN_TEXT_LENGTH dari .env

import fitz  # PyMuPDF


ALLOWED_EXTENSION = '.pdf'


# ============================================================
# ⚠️  TODO: GANTI NILAI INI SETELAH ANALISIS EMPIRIS SELESAI
#
# Nilai 50 di bawah hanyalah PLACEHOLDER SEMENTARA.
# Setelah tim selesai mengolah dataset dan mendapat nilai
# minimum karakter dari hasil_analisis.xlsx, tambahkan
# baris berikut di file .env lalu restart aplikasi:
#
#     MIN_TEXT_LENGTH=<nilai_dari_hasil_analisis>
#
# Contoh: jika minimum karakter dokumen valid dari data
# adalah 312, maka tulis di .env:
#     MIN_TEXT_LENGTH=312
#
# Nilai akan terbaca otomatis tanpa perlu ubah kode apapun.
# Jika .env tidak mengandung MIN_TEXT_LENGTH, nilai fallback
# 50 akan dipakai (baris di bawah ini).
# ============================================================
MIN_TEXT_LENGTH = int(os.getenv('MIN_TEXT_LENGTH', 50))
# os.getenv('MIN_TEXT_LENGTH', 50) → baca variabel MIN_TEXT_LENGTH dari .env.
# Argumen kedua (50) adalah nilai default jika variabel belum diset di .env.
# int(...) → konversi ke integer karena semua nilai dari .env bertipe string.


def is_allowed_extension(filename: str) -> bool:
    """
    Cek apakah nama file memiliki ekstensi .pdf (case-insensitive).

    Dipanggil pertama kali di routes sebelum validasi lainnya karena
    ini adalah pengecekan paling murah secara komputasi (tidak perlu
    membuka file sama sekali, cukup cek string nama file).
    """
    if not filename:
        return False
    return filename.lower().endswith(ALLOWED_EXTENSION)


def extract_text_from_pdf(file_stream) -> str:
    """
    Ekstrak seluruh teks dari file PDF menggunakan PyMuPDF.

    PyMuPDF (fitz) hanya mengekstrak lapisan teks dari PDF.
    Gambar yang tertanam di PDF (logo, foto, diagram) diabaikan
    secara otomatis dan tidak memengaruhi hasil ekstraksi.
    Ini berarti dokumen tugas dengan cover berlogo kampus tetap
    bisa diekstrak dengan normal karena logonya hanya gambar.

    Args:
        file_stream: File-like object (request.files['x'].stream).

    Returns:
        String berisi gabungan teks dari seluruh halaman, dipisah
        spasi antar halaman. Return string kosong jika tidak ada
        teks yang bisa diekstrak.
    """
    extracted_pages = []

    # fitz.open() membuka PDF langsung dari stream di memori,
    # tidak perlu menyimpan file ke disk terlebih dahulu.
    # filetype="pdf" diperlukan karena input berupa bytes, bukan path.
    with fitz.open(stream=file_stream.read(), filetype="pdf") as doc:
        for page in doc:
            # get_text() mengambil teks dari satu halaman.
            # Untuk PDF scan tanpa OCR, get_text() mengembalikan
            # string kosong karena tidak ada layer teks sama sekali.
            page_text = page.get_text()
            if page_text:
                extracted_pages.append(page_text)

    # Gabung semua halaman dengan spasi sebagai pemisah.
    # Hasil ini yang akan melalui clean_text() di routes.
    return " ".join(extracted_pages)


def is_text_based_pdf(file_stream) -> tuple[bool, int]:
    """
    Validasi apakah PDF memiliki konten teks yang mencukupi untuk
    diproses sistem, sesuai constraint C-02 SRS.

    Cara kerja:
        Ekstrak teks dari PDF, hitung jumlah karakternya.
        Dokumen dianggap valid jika karakter >= MIN_TEXT_LENGTH.

    Kenapa return tuple (bool, int) dan bukan hanya bool:
        char_count (int) dibutuhkan oleh routes.py untuk
        menampilkan pesan error yang informatif, misalnya:
        "teks terekstrak hanya 12 karakter, minimum 312 karakter."
        Tanpa char_count, routes harus membaca ulang file hanya
        untuk mendapatkan angka tersebut, yang tidak efisien.

    Kenapa pesan error tidak menyebut "scan":
        Sistem tidak bisa memastikan penyebab sedikitnya teks.
        Bisa karena scan tanpa OCR, PDF rusak, atau memang
        isinya sedikit. Menyebut "scan" ketika penyebabnya
        mungkin bukan scan akan menyesatkan user.

    Args:
        file_stream: File-like object yang akan dibaca PyMuPDF.
                     Pastikan file_stream.seek(0) dipanggil
                     SEBELUM dan SESUDAH fungsi ini di routes.py
                     agar pointer file tidak tergeser.

    Returns:
        Tuple (is_valid, char_count):
            - is_valid  (bool) : True jika karakter >= MIN_TEXT_LENGTH
            - char_count (int) : jumlah karakter hasil ekstraksi,
                                 digunakan untuk pesan error di routes
    """
    try:
        text = extract_text_from_pdf(file_stream)

        # strip() dulu untuk tidak menghitung spasi/newline berlebih
        # sebagai konten yang bermakna.
        char_count = len(text.strip())

        # Bandingkan dengan threshold dari .env (atau fallback 50).
        return char_count >= MIN_TEXT_LENGTH, char_count

    except Exception:
        # Jika PDF rusak/tidak bisa dibaca sama sekali,
        # kembalikan (False, 0) agar routes bisa menampilkan
        # pesan error yang sesuai.
        return False, 0
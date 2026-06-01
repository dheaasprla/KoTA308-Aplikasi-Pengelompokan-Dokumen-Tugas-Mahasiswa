def is_pdf_file(filename):
    """
    Memeriksa apakah berkas memiliki ekstensi .pdf
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

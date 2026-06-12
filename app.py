import os
import time
from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)
app.secret_key = "kota308_secret_key"
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # Max 50MB upload size

# Pastikan folder uploads tersedia
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    # Mengarahkan halaman utama ke formulir unggah dokumen
    return render_template('unggah_dokumen.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/profil')
def profil():
    return render_template('profile.html')

@app.route('/hasil-klaster', methods=['GET', 'POST'])
def halaman_hasil_klaster():
    # Ambil threshold dari form jika POST, default 0.70 (70%)
    threshold_val = 0.70
    if request.method == 'POST':
        raw_threshold = request.form.get('threshold')
        if raw_threshold:
            try:
                threshold_val = float(raw_threshold) / 100.0
            except ValueError:
                threshold_val = 0.70

    # Ubah nilai score menjadi angka desimal (float) agar bisa dihitung oleh HTML
    contoh_clusters = [
        {
            'name': 'Klaster 1', 
            'score': 0.82,  # Angka desimal murni, bukan teks '78%-86%'
            'files': ['Dhea.pdf', 'Berliana.pdf', 'Jihan.pdf']
        },
        {
            'name': 'Klaster 2', 
            'score': 0.88, 
            'files': ['Doni.pdf', 'Andi.pdf', 'Sari.pdf']
        }
    ]
    
    contoh_outliers = [
        {'nama_file': 'Budi.pdf', 'score': 0.55}, # Pakai float
        {'nama_file': 'Mira.pdf', 'score': 0.42}
    ]

    # Kirim juga nilai threshold pembandingnya jika HTML-nya meminta variabel itu
    return render_template(
        'hasil_klaster.html', 
        clusters=contoh_clusters, 
        outliers=contoh_outliers,
        threshold=threshold_val  # Kita sediakan angka threshold
    )

@app.route('/detail-klaster')
def detail_klaster():
    cluster_name = request.args.get('cluster', 'Klaster 1')
    files = ['Dhea.pdf', 'Berliana.pdf', 'Jihan.pdf']
    matrix = [
        [1.0, 0.78, 0.78],
        [0.78, 1.0, 0.78],
        [0.78, 0.78, 1.0]
    ]
    
    # Text pairs dengan penanda highlight HTML
    text_pairs = {
        "Dhea.pdf_Berliana.pdf": {
            "doc1Title": "Dhea.pdf",
            "doc2Title": "Berliana.pdf",
            "doc1Content": '<span class="highlight-direct">Pemrograman web merupakan salah satu bidang dalam ilmu komputer yang berfokus pada pengembangan aplikasi berbasis internet.</span> Dalam era digital saat ini, kebutuhan akan aplikasi web terus meningkat seiring berkembangnya teknologi informasi. Terdapat beberapa komponen utama dalam pemrograman web, yaitu HTML sebagai struktur, CSS sebagai tampilan, dan JavaScript sebagai logika interaktif. <span class="highlight-semantic">Ketiga komponen ini bekerja secara sinergis untuk menghasilkan antarmuka pengguna yang responsif dan fungsional.</span>',
            "doc2Content": '<span class="highlight-direct">Web programming adalah salah satu cabang ilmu komputer yang menitikberatkan pada pembuatan aplikasi yang berjalan di atas jaringan internet.</span> Di era digital seperti sekarang, permintaan terhadap aplikasi berbasis web terus bertumbuh. Ada tiga elemen pokok dalam web programming, yaitu HTML untuk struktur, CSS untuk gaya tampilan, dan JavaScript untuk interaksi dinamis. <span class="highlight-semantic">Ketiganya saling melengkapi untuk menciptakan antarmuka yang responsif dan memiliki fungsi yang lengkap.</span>'
        },
        "Dhea.pdf_Jihan.pdf": {
            "doc1Title": "Dhea.pdf",
            "doc2Title": "Jihan.pdf",
            "doc1Content": 'Pemrograman web merupakan salah satu bidang dalam ilmu komputer yang berfokus pada pengembangan aplikasi berbasis internet. <span class="highlight-semantic">Dalam era digital saat ini, kebutuhan akan aplikasi web terus meningkat seiring berkembangnya teknologi informasi.</span> Terdapat beberapa komponen utama dalam pemrograman web, yaitu HTML sebagai struktur, CSS sebagai tampilan, dan JavaScript sebagai logika interaktif. Ketiga komponen ini bekerja secara sinergis untuk menghasilkan antarmuka pengguna yang responsif dan fungsional.',
            "doc2Content": 'Teknologi web berkembang sangat pesat dalam beberapa tahun terakhir. <span class="highlight-semantic">Kebutuhan akan platform digital berbasis internet terus mengalami lonjakan yang signifikan di era modern.</span> Oleh karena itu, mempelajari pemrograman web menjadi sangat relevan bagi mahasiswa teknik informatika.'
        },
        "Berliana.pdf_Jihan.pdf": {
            "doc1Title": "Berliana.pdf",
            "doc2Title": "Jihan.pdf",
            "doc1Content": 'Web programming adalah salah satu cabang ilmu komputer yang menitikberatkan pada pembuatan aplikasi yang berjalan di atas jaringan internet. <span class="highlight-direct">Di era digital seperti sekarang, permintaan terhadap aplikasi berbasis web terus bertumbuh.</span> Ada tiga elemen pokok dalam web programming, yaitu HTML untuk struktur, CSS untuk gaya tampilan, dan JavaScript untuk interaksi dinamis. Ketiganya saling melengkapi untuk menciptakan antarmuka yang responsif dan memiliki fungsi yang lengkap.',
            "doc2Content": 'Kebutuhan akan platform digital berbasis internet terus mengalami lonjakan yang signifikan di era modern. <span class="highlight-direct">Permintaan terhadap pembuatan sistem aplikasi web terus mengalami kenaikan yang pesat di era teknologi saat ini.</span> Ada berbagai macam library dan framework JavaScript yang dapat digunakan untuk mempercepat proses pembangunan aplikasi.'
        }
    }

    return render_template(
        'detail_klaster.html',
        cluster_name=cluster_name,
        files=files,
        matrix=matrix,
        text_pairs=text_pairs,
        threshold=0.70
    )

@app.route('/riwayat-sesi')
def riwayat_sesi():
    return render_template('riwayat_sesi.html')

@app.route('/upload-dummy', methods=['POST'])
def upload_dummy():
    # Ambil metadata
    mata_kuliah = request.form.get('mata_kuliah', '').strip()
    kelas = request.form.get('kelas', '').strip()
    
    if not mata_kuliah or not kelas:
        return jsonify({"status": "error", "message": "Mata kuliah dan kelas wajib diisi."}), 400
        
    if 'pdf_files' not in request.files:
        return jsonify({"status": "error", "message": "Tidak ada file yang diunggah."}), 400
        
    files = request.files.getlist('pdf_files')
    
    # Validasi jumlah file (maks 32)
    if len(files) > 32:
        return jsonify({"status": "error", "message": "Jumlah file melebihi batas kuota (maksimal 32 file)."}), 400
        
    # Validasi tipe file (harus PDF)
    uploaded_filenames = []
    for file in files:
        if file.filename == '':
            continue
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({"status": "error", "message": f"Format file tidak valid: {file.filename}. Wajib format .pdf."}), 400
        
        # Simpan sementara file
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        uploaded_filenames.append(filename)

    if not uploaded_filenames:
        return jsonify({"status": "error", "message": "Tidak ada berkas valid yang dipilih."}), 400

    # Simulasi delay proses unggah (misal: 2 detik) untuk menampilkan progress bar di frontend
    time.sleep(2)

    return jsonify({
        "status": "success",
        "message": f"Berhasil mengunggah {len(uploaded_filenames)} dokumen.",
        "data": {
            "mata_kuliah": mata_kuliah,
            "kelas": kelas,
            "total_files": len(uploaded_filenames),
            "files": uploaded_filenames,
            "session_id": int(time.time())  # Sesi ID dummy berdasarkan timestamp
        }
    })

@app.route('/process-analysis-dummy', methods=['POST'])
def process_analysis_dummy():
    # Ambil threshold dan session_id
    data = request.get_json() or {}
    threshold = float(data.get('threshold', 0.70))
    session_id = data.get('session_id')
    
    # Data dummy untuk hasil klasterisasi
    dummy_clusters = [
        ["Tugas_Ahmad_Syukur.pdf", "Tugas_Ahmad_Syukur_Parafrase.pdf", "Tugas_Ahmad_Syukur_Copy.pdf"],
        ["Tugas_Dhea_Aprilia.pdf", "Tugas_Dhea_Aprilia_Parafrase.pdf"]
    ]
    dummy_outliers = [
        "Tugas_Budi_Setiawan.pdf",
        "Tugas_Citra_Lestari.pdf",
        "Tugas_Eko_Prasetyo.pdf"
    ]
    
    # Kirim hasil analisis dummy
    return jsonify({
        "status": "success",
        "threshold": threshold,
        "session_id": session_id,
        "clusters": dummy_clusters,
        "outliers": dummy_outliers
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

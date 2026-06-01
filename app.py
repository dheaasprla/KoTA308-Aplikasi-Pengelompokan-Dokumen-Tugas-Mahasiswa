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

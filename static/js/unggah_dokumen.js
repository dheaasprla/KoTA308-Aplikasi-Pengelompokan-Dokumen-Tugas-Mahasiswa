document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements - Metadata Inputs
    const mataKuliahInput = document.getElementById('mata_kuliah');
    const kelasInput = document.getElementById('kelas');
    
    // DOM Elements - Upload Zone
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('hiddenInput');
    const btnSelectTrigger = document.getElementById('btn-select-trigger');
    
    // DOM Elements - Quota Stats
    const quotaPctText = document.getElementById('quota-pct');
    const quotaFillBar = document.getElementById('quota-fill');
    const quotaCountText = document.getElementById('quota-count');
    const quotaRemainingText = document.getElementById('quota-remaining');

    // DOM Elements - Files List
    const filesSection = document.getElementById('files-section');
    const filesGrid = document.getElementById('filesGrid');
    const selectedCountLabel = document.getElementById('selected-count-label');
    const btnClearAll = document.getElementById('btn-clear-all');
    
    // DOM Elements - Form Actions
    const btnCancelForm = document.getElementById('btn-cancel-form');
    const btnNextStep = document.getElementById('btn-next-step');
    
    // DOM Elements - Loading Modal
    const modalLoading = document.getElementById('modal-loading');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const progressFiles = document.getElementById('progress-files');
    const btnCancelUpload = document.getElementById('btn-cancel-upload');
    const loadingTitle = document.getElementById('loading-title');
    const loadingSubtitle = document.getElementById('loading-subtitle');
    
    // DOM Elements - Threshold Modal
    const modalThreshold = document.getElementById('modal-threshold');
    const thresholdSlider = document.getElementById('threshold');
    const thresholdVal = document.getElementById('threshold-val');
    const thresholdCard = document.getElementById('threshold-status-card');
    const thresholdTitleDesc = document.getElementById('threshold-title-desc');
    const thresholdBodyDesc = document.getElementById('threshold-body-desc');
    
    const btnBackToUpload = document.getElementById('btn-back-to-upload');
    const btnStartAnalysis = document.getElementById('btn-start-analysis');
    const dummySessionInput = document.getElementById('dummy-session-id');

    // State Variables
    let selectedFiles = [];
    const MAX_FILES = 32;
    let currentXHR = null;

    // --- 1. Selection and Trigger Event Handlers ---

    // Click on dropzone triggers file dialog
    dropZone.addEventListener('click', (e) => {
        // Prevent trigger loop if clicked button itself
        if (e.target !== btnSelectTrigger) {
            fileInput.click();
        }
    });

    btnSelectTrigger.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.click();
    });

    // Handle cancel button on form resets inputs
    btnCancelForm.addEventListener('click', () => {
        if (confirm('Batalkan sesi analisis baru dan reset semua input?')) {
            mataKuliahInput.value = '';
            kelasInput.value = '';
            selectedFiles = [];
            updateUI();
        }
    });

    // Prevent default drag and drop behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // Toggle highlight class when dragging over
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove('dragover');
        }, false);
    });

    // Handle dropped files
    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFilesSelection(files);
    });

    // Handle selected files via file dialog
    fileInput.addEventListener('change', (e) => {
        handleFilesSelection(e.target.files);
    });

    // --- 2. Files Selection & Validation Logic ---

    function handleFilesSelection(filesListObj) {
        const incomingFiles = Array.from(filesListObj);
        let errorMessages = [];

        incomingFiles.forEach(file => {
            // Validasi format file PDF (Fixed `.endswith` syntax error to `.endsWith`)
            if (!file.name.toLowerCase().endsWith('.pdf')) {
                errorMessages.push(`Berkas "${file.name}" ditolak karena bukan berformat .pdf.`);
                return;
            }

            // Validasi duplikat berkas berdasarkan nama dan ukuran
            const isDuplicate = selectedFiles.some(existingFile => 
                existingFile.name === file.name && existingFile.size === file.size
            );

            if (isDuplicate) {
                return; // Lewati jika duplikat
            }

            // Validasi kapasitas maksimal 32 file
            if (selectedFiles.length >= MAX_FILES) {
                errorMessages.push(`Batas maksimal ${MAX_FILES} berkas terlampaui.`);
                return;
            }

            // Tambahkan ke array selectedFiles
            selectedFiles.push(file);
        });

        if (errorMessages.length > 0) {
            alert(errorMessages.join('\n'));
        }

        updateUI();
        fileInput.value = ''; // Reset input agar bisa memilih file yang sama lagi
    }

    // Remove single file
    window.removeFile = function(index) {
        selectedFiles.splice(index, 1);
        updateUI();
    };

    // Clear all files
    btnClearAll.addEventListener('click', (e) => {
        e.stopPropagation();
        if (confirm('Apakah Anda yakin ingin menghapus semua berkas terpilih?')) {
            selectedFiles = [];
            updateUI();
        }
    });

    // Update UI elements based on selectedFiles state
    function updateUI() {
        const fileCount = selectedFiles.length;
        
        // Update Quota Badge / Quota Card
        const pctUsed = Math.round((fileCount / MAX_FILES) * 100);
        quotaPctText.textContent = `${pctUsed}% dari kuota terpakai`;
        quotaFillBar.style.width = `${pctUsed}%`;
        quotaCountText.textContent = `${fileCount} / ${MAX_FILES} Berkas`;
        quotaRemainingText.textContent = `${MAX_FILES - fileCount} Berkas`;

        if (fileCount >= MAX_FILES) {
            quotaFillBar.style.backgroundColor = 'var(--danger)';
            quotaPctText.style.color = 'var(--danger)';
        } else {
            quotaFillBar.style.backgroundColor = '';
            quotaPctText.style.color = '';
        }

        // Selected Files List Container
        selectedCountLabel.textContent = `${fileCount} Berkas`;
        if (fileCount > 0) {
            filesSection.style.display = 'block';
            btnClearAll.style.display = 'inline-flex';
            
            // Render items in grid format
            filesGrid.innerHTML = selectedFiles.map((file, index) => `
                <div class="file-item">
                    <i class="fa-solid fa-file-lines fi-icon"></i>
                    <div class="fi-info">
                        <div class="fi-name" title="${file.name}">${file.name}</div>
                        <div class="fi-size">${formatBytes(file.size)}</div>
                    </div>
                    <button type="button" class="fi-del" onclick="removeFile(${index})" title="Hapus berkas">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                </div>
            `).join('');
        } else {
            filesSection.style.display = 'none';
            btnClearAll.style.display = 'none';
            filesGrid.innerHTML = '';
        }

        // Validate Form to Enable Submit Button
        validateForm();
    }

    // Format bytes to human readable format
    function formatBytes(bytes, decimals = 1) {
        if (!+bytes) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
    }

    // Validate form inputs
    function validateForm() {
        const isMetadataFilled = mataKuliahInput.value.trim() !== '' && kelasInput.value.trim() !== '';
        // Minimal 2 berkas untuk melakukan perbandingan kemiripan
        const hasMinFiles = selectedFiles.length >= 2;
        
        btnNextStep.disabled = !(isMetadataFilled && hasMinFiles);
    }

    // Listen to input metadata changes to instantly update submit state
    mataKuliahInput.addEventListener('input', validateForm);
    kelasInput.addEventListener('input', validateForm);

    // --- 3. Form Submit / Upload Handlers (AJAX Process) ---

    btnNextStep.addEventListener('click', () => {
        // Buat FormData
        const formData = new FormData();
        formData.append('mata_kuliah', mataKuliahInput.value.trim());
        formData.append('kelas', kelasInput.value.trim());
        
        selectedFiles.forEach(file => {
            formData.append('pdf_files', file);
        });

        // Tampilkan Modal Loading
        showLoadingModal(selectedFiles.length);

        // AJAX Upload menggunakan XMLHttpRequest untuk tracking progress
        currentXHR = new XMLHttpRequest();
        currentXHR.open('POST', '/upload-dummy', true);

        // Upload progress tracking
        currentXHR.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                // Skala progress upload berkas (0% sampai 80%)
                const percentComplete = Math.round((e.loaded / e.total) * 80);
                updateProgressBar(percentComplete, `Mengunggah berkas ke server...`);
            }
        });

        // Selesai upload, menunggu respon pemrosesan server
        currentXHR.addEventListener('load', () => {
            if (currentXHR.status === 200) {
                // Selesaikan progress bar ke 100%
                updateProgressBar(100, `Pemindahan berkas selesai!`);
                
                setTimeout(() => {
                    const response = JSON.parse(currentXHR.responseText);
                    hideLoadingModal();
                    
                    // Set dummy session id dan tampilkan modal config threshold
                    dummySessionInput.value = response.data.session_id;
                    showThresholdModal();
                }, 500);
            } else {
                hideLoadingModal();
                let errorMsg = 'Terjadi kesalahan saat mengunggah berkas.';
                try {
                    const response = JSON.parse(currentXHR.responseText);
                    errorMsg = response.message || errorMsg;
                } catch(e) {}
                alert(errorMsg);
            }
        });

        currentXHR.addEventListener('error', () => {
            hideLoadingModal();
            alert('Koneksi terputus. Gagal menghubungi server.');
        });

        currentXHR.addEventListener('abort', () => {
            hideLoadingModal();
            console.log('Upload dibatalkan oleh pengguna.');
        });

        currentXHR.send(formData);
    });

    // Cancel Button Click
    btnCancelUpload.addEventListener('click', () => {
        if (currentXHR) {
            currentXHR.abort();
            currentXHR = null;
        }
    });

    // Helper functions for Loading Modal UI
    function showLoadingModal(fileCount) {
        progressBar.style.width = '0%';
        progressText.textContent = '0% Selesai';
        progressFiles.textContent = `0 dari ${fileCount} Berkas`;
        modalLoading.classList.add('show');
    }

    function updateProgressBar(percentage, text) {
        progressBar.style.width = `${percentage}%`;
        progressText.textContent = `${percentage}% Selesai`;
        if (percentage >= 80 && percentage < 100) {
            loadingTitle.textContent = "Memproses Dokumen";
            loadingSubtitle.textContent = "Server sedang memvalidasi format teks berkas...";
        } else {
            loadingTitle.textContent = "Mengunggah Dokumen";
            loadingSubtitle.textContent = text;
        }
    }

    function hideLoadingModal() {
        modalLoading.classList.remove('show');
        currentXHR = null;
    }

    // --- 4. Threshold Config Modal Handlers ---

    function showThresholdModal() {
        // Reset slider ke default 70%
        thresholdSlider.value = 0.70;
        updateThresholdUI(0.70);
        modalThreshold.classList.add('show');
    }

    function hideThresholdModal() {
        modalThreshold.classList.remove('show');
    }

    // Back to upload button inside threshold modal
    btnBackToUpload.addEventListener('click', () => {
        hideThresholdModal();
    });

    // Update threshold UI & Description based on slider value
    thresholdSlider.addEventListener('input', (e) => {
        const val = parseFloat(e.target.value);
        updateThresholdUI(val);
    });

    function updateThresholdUI(value) {
        const percentage = Math.round(value * 100);
        thresholdVal.textContent = percentage;

        // Reset classes
        thresholdCard.className = 'threshold-info-card';
        
        if (value < 0.50) {
            // Low Threshold
            thresholdCard.classList.add('low');
            thresholdTitleDesc.textContent = "Kemiripan Topik Umum";
            thresholdBodyDesc.textContent = "Menyaring kemiripan kosa kata yang umum. Hasil klaster kemungkinan besar dan kurang spesifik (banyak false positive).";
        } else if (value >= 0.50 && value <= 0.70) {
            // Medium Threshold
            thresholdCard.classList.add('medium');
            thresholdTitleDesc.textContent = "Plagiarisme Sedang / Parafrasa Ringan";
            thresholdBodyDesc.textContent = "Mendeteksi kemiripan kalimat dengan struktur parafrasa moderat. Cocok untuk deteksi kecurangan tugas esai reguler.";
        } else {
            // High Threshold
            thresholdCard.classList.add('high');
            thresholdTitleDesc.textContent = "Plagiarisme Berat / Duplikasi Tinggi";
            thresholdBodyDesc.textContent = "Hanya mendeteksi kemiripan substansi sangat tinggi atau penyalinan murni (copy-paste langsung tanpa parafrasa berarti).";
        }
    }

    // --- 5. Final Process Trigger (Dummy Next Page) ---

    btnStartAnalysis.addEventListener('click', () => {
        const threshold = thresholdSlider.value;
        const sessionId = dummySessionInput.value;

        // Kirim trigger pemrosesan ke backend
        fetch('/process-analysis-dummy', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                threshold: threshold,
                session_id: sessionId
            })
        })
        .then(res => res.json())
        .then(data => {
            console.log('Dummy Analysis Result:', data);
            
            // Simulasikan masuk ke halaman hasil dengan mengirimkan data dummy lewat alert
            alert(`
=========================================
      SIMULASI HASIL KLASTERISASI SBERT
=========================================
Mata Kuliah: ${mataKuliahInput.value}
Kelas: ${kelasInput.value}
Threshold: ${Math.round(data.threshold * 100)}%
Sesi ID: ${data.session_id}

Hasil Pengelompokan:
- Klaster 1 (3 Dokumen Mirip):
  * ${data.clusters[0].join('\n  * ')}
- Klaster 2 (2 Dokumen Mirip):
  * ${data.clusters[1].join('\n  * ')}

Dokumen Unik / Aman (Outliers):
* ${data.outliers.join('\n* ')}
=========================================
Tampilan frontend sudah 100% benar dan interaktif!
            `);
            hideThresholdModal();
        })
        .catch(err => {
            alert('Gagal memulai analisis.');
            console.error(err);
        });
    });
});

/**
 * KoTA-308: Premium JavaScript Interactions (Hasil Klaster)
 */

document.addEventListener('DOMContentLoaded', function () {
    initAccordion();
    initOutliersToggle();
    initExportDropdown();
    initProgressBars();
    initReanalyze();
});

function initProgressBars() {
    const fills = document.querySelectorAll('.indicator-fill[data-score]');
    fills.forEach(fill => {
        const score = fill.getAttribute('data-score');
        if (score) {
            fill.style.width = score;
        }
    });
}

function initAccordion() {
    const headerRows = document.querySelectorAll('.cluster-header-row');

    headerRows.forEach(header => {
        header.addEventListener('click', function () {
            const card = this.closest('.cluster-card');
            const clusterId = card.querySelector('.cluster-title').getAttribute('data-klaster-id');

            window.location.href = `/analisis/klaster/${clusterId}/detail`;
        });
    });
}

function initOutliersToggle() {
    const viewAllBtn = document.getElementById('btn-view-all-outliers');
    const moreBadge = document.getElementById('btn-more-outliers');
    const hiddenContainer = document.getElementById('hidden-outliers-container');

    function toggleOutliers() {
        const isShown = hiddenContainer && hiddenContainer.style.display !== 'none';

        if (hiddenContainer) {
            hiddenContainer.style.display = isShown ? 'none' : 'flex';
        }
        if (viewAllBtn) {
            viewAllBtn.textContent = isShown ? 'Lihat Semua' : 'Sembunyikan';
        }
        if (moreBadge) {
            moreBadge.style.display = isShown ? 'flex' : 'none';
        }
    }

    if (viewAllBtn) {
        viewAllBtn.addEventListener('click', toggleOutliers);
    }
    if (moreBadge) {
        moreBadge.addEventListener('click', toggleOutliers);
    }
}

function initExportDropdown() {
    const dropdownToggle = document.getElementById('btn-export-dropdown');
    const dropdownMenu = document.getElementById('export-dropdown-menu');
    const btnExcelLink = document.getElementById('btn-export-excel');
    const btnPdfLink = document.getElementById('btn-export-pdf');
    const sesiId = document.getElementById('btn-reanalyze')?.getAttribute('data-sesi-id');

    // Set href dinamis berdasarkan id_sesi
    if (sesiId) {
        if (btnExcelLink) btnExcelLink.href = `/analisis/sesi/${sesiId}/ekspor/excel`;
        if (btnPdfLink) btnPdfLink.href = `/analisis/sesi/${sesiId}/ekspor/pdf`;
    }

    if (dropdownToggle && dropdownMenu) {
        dropdownToggle.addEventListener('click', function (e) {
            e.stopPropagation();

            // Loading state saat klik dropdown
            const originalContent = this.innerHTML;
            dropdownMenu.classList.toggle('show');
        });

        document.addEventListener('click', function () {
            dropdownMenu.classList.remove('show');
        });
    }

    // Loading state saat klik download Excel
    if (btnExcelLink) {
        btnExcelLink.addEventListener('click', function () {
            showToast('Mengunduh Excel...', 'File Excel sedang disiapkan, harap tunggu.', 'info');
        });
    }

    // Loading state saat klik download PDF
    if (btnPdfLink) {
        btnPdfLink.addEventListener('click', function () {
            showToast('Mengunduh PDF...', 'File PDF sedang disiapkan, harap tunggu.', 'info');
        });
    }
}

function initReanalyze() {
    const btnReanalyze = document.getElementById('btn-reanalyze');
    const modalThreshold = document.getElementById('modal-threshold');
    const formThreshold = document.getElementById('form-threshold');

    if (btnReanalyze && modalThreshold && formThreshold) {
        btnReanalyze.addEventListener('click', function () {
            const sesiId = this.getAttribute('data-sesi-id');
            formThreshold.action = '/sesi/' + sesiId + '/hasil-klaster';

            const inputThreshold = document.getElementById('input-threshold');
            const btnSubmitModal = document.getElementById('btn-submit-analysis');
            const iconSubmitModal = document.getElementById('icon-submit');
            const labelSubmitModal = document.getElementById('label-submit');

            if (inputThreshold) {
                inputThreshold.disabled = false;
                inputThreshold.style.pointerEvents = 'auto';
                inputThreshold.style.opacity = '1';
            }
            if (btnSubmitModal) {
                btnSubmitModal.disabled = false;
            }
            if (iconSubmitModal) {
                iconSubmitModal.className = 'fa-solid fa-play';
            }
            if (labelSubmitModal) {
                labelSubmitModal.textContent = 'Mulai Analisis';
            }

            modalThreshold.classList.add('active');
        });

        // formThreshold.addEventListener('submit', async function (e) {
        //     e.preventDefault(); // Blokir refresh halaman bawaan HTML

        //     const sesiId = btnReanalyze.getAttribute('data-sesi-id');
        //     const submitBtn = formThreshold.querySelector('button[type="submit"]');
                
        //     // Simpan teks asli tombol untuk dikembalikan nanti
        //     const originalBtnText = submitBtn ? submitBtn.innerHTML : 'Proses';
                
        //     // Ubah state tombol menjadi loading
        //     if (submitBtn) {
        //         submitBtn.disabled = true;
        //         submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Memproses...';
        //     }

        //     showToast('Memulai Analisis', 'Menyimpan nilai threshold baru...', 'info');

        //     try {
        //         // ── LANGKAH 1: Kirim data threshold ke Backend ──
        //         const formData = new FormData(formThreshold);
        //         const resThreshold = await fetch(`/sesi/${sesiId}/hasil-klaster`, {
        //             method: 'POST',
        //             body: formData
        //         });
                    
        //         const dataThreshold = await resThreshold.json();

        //         if (dataThreshold.status !== 'sukses') {
        //             throw new Error(dataThreshold.pesan || 'Gagal menyimpan threshold.');
        //         }

        //         // ── LANGKAH 2: Picu rekonstruksi graf (Instan via Cache) ──
        //         showToast('Sinkronisasi Graf', 'Mengeksekusi pengelompokan ulang dokumen...', 'info');
                    
        //         const resAnalisis = await fetch(`/analisis/sesi/${sesiId}/jalankan`, {
        //             method: 'POST'
        //         });

        //         const contentType = resAnalisis.headers.get("content-type");
        //         if (!resAnalisis.ok || !contentType || !contentType.includes("application/json")) {
        //             // Jika server melempar halaman HTML eror bawaan
        //             throw new Error(`Server melempar eror status ${resAnalisis.status}. Pastikan file terunggah dengan benar.`);
        //         }
                    
        //         const dataAnalisis = await resAnalisis.json();

        //         if (dataAnalisis.status === 'selesai') {
        //             showToast('Sukses', 'Analisis ulang berhasil diselesaikan.', 'success');
                        
        //             // Skenario penutupan modal & refresh halaman hasil agar grafik/matriks ter-render baru
        //             modalThreshold.classList.remove('active');
        //             setTimeout(() => {
        //                 window.location.reload();
        //             }, 1000);
        //         } else {
        //             throw new Error(dataAnalisis.pesan || 'Gagal menjalankan kalkulasi kelompok graf.');
        //         }

        //     } catch (error) {
        //         console.error('Error saat re-clustering:', error);
        //         showToast('Gagal Analisis', error.message || 'Terjadi kesalahan pada server.', 'error');
                    
        //         // Kembalikan state tombol jika gagal agar dosen bisa mencoba lagi
        //         if (submitBtn) {
        //             submitBtn.disabled = false;
        //             submitBtn.innerHTML = originalBtnText;
        //         }
        //     }
        // });
    }
}

function showToast(title, message, type = 'success') {
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        Object.assign(toastContainer.style, {
            position: 'fixed',
            bottom: '24px',
            right: '24px',
            zIndex: '9999',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
            maxWidth: '360px',
            width: '90%'
        });
        document.body.appendChild(toastContainer);
    }

    const toast = document.createElement('div');
    toast.className = `toast-card toast-${type}`;
    Object.assign(toast.style, {
        background: '#ffffff',
        borderLeft: `6px solid ${type === 'success' ? '#10B981' : '#3B82F6'}`,
        boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
        borderRadius: '8px',
        padding: '16px',
        display: 'flex',
        gap: '12px',
        alignItems: 'flex-start',
        transform: 'translateX(120%)',
        transition: 'transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275), opacity 0.3s ease',
        opacity: '0'
    });

    const icon = type === 'success' ? 'fa-circle-check' : 'fa-circle-info';
    const iconColor = type === 'success' ? '#10B981' : '#3B82F6';

    toast.innerHTML = `
        <div style="color: ${iconColor}; font-size: 20px; margin-top: 2px;">
            <i class="fa-solid ${icon}"></i>
        </div>
        <div style="flex-grow: 1;">
            <strong style="display: block; font-size: 13px; font-weight: 700; color: #1E293B; margin-bottom: 2px;">${title}</strong>
            <span style="font-size: 11px; color: #64748B; line-height: 1.4; display: block;">${message}</span>
        </div>
    `;

    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.style.transform = 'translateX(0)';
        toast.style.opacity = '1';
    }, 10);

    setTimeout(() => {
        toast.style.transform = 'translateX(120%)';
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}
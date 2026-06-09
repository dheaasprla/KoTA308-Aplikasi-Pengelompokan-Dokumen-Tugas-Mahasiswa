// State management
let selectedSessionId = null;

// Buka modal hapus
function openDeleteModal(sessionId, sessionTitle) {
    selectedSessionId = sessionId;
    document.getElementById('deleteTargetSession').textContent = sessionTitle;
    document.getElementById('deleteModalBackdrop').classList.add('active');
}

// Tutup modal hapus
function closeDeleteModal() {
    selectedSessionId = null;
    document.getElementById('deleteModalBackdrop').classList.remove('active');
}

// Konfirmasi Hapus (Simulasi Hapus di Frontend)
document.getElementById('btnConfirmDelete').addEventListener('click', function() {
    if (selectedSessionId !== null) {
        // Cari baris tabel dengan ID tersebut
        const row = document.querySelector(`tr[data-id="${selectedSessionId}"]`);
        if (row) {
            // Animasi hapus baris
            row.style.transition = 'all 0.3s ease';
            row.style.opacity = '0';
            setTimeout(() => {
                row.remove();
                // Update stats jika diperlukan
                updateStats();
            }, 300);
        }
        closeDeleteModal();
    }
});

// Close modal when clicking outside the confirm card
document.getElementById('deleteModalBackdrop').addEventListener('click', function(e) {
    if (e.target === this) {
        closeDeleteModal();
    }
});

// Keyboard support (ESC to close modal)
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeDeleteModal();
    }
});

// Fungsi Simulasi Update Statistik setelah hapus
function updateStats() {
    const tableBody = document.getElementById('historyTableBody');
    const totalRows = tableBody.querySelectorAll('tr').length;
    
    // Update stats
    const totalSesiNumber = document.querySelector('.stat-card.sesi .stat-number');
    if (totalSesiNumber) {
        totalSesiNumber.textContent = totalRows;
    }
    
    // Update total document estimate
    const totalDocsNumber = document.querySelector('.stat-card.dokumen .stat-number');
    if (totalDocsNumber) {
        let currentDocs = 0;
        tableBody.querySelectorAll('tr').forEach(tr => {
            const text = tr.cells[2].textContent;
            const count = parseInt(text) || 0;
            currentDocs += count;
        });
        totalDocsNumber.textContent = currentDocs;
    }
}

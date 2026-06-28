// ══════════════════════════════════════
// riwayat_sesi.js
// Fetch data riwayat dari backend dan render ke tabel
// ══════════════════════════════════════

document.addEventListener('DOMContentLoaded', function () {
    loadRiwayat();
});

function loadRiwayat() {
    fetch('/riwayat/api', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
    })
        .then(res => res.json())
        .then(data => {
            if (data.status !== 'selesai') {
                showError('Gagal memuat data riwayat.');
                return;
            }

            // Update stat cards
            document.getElementById('stat-total-sesi').textContent = data.total_sesi;
            document.getElementById('stat-total-dokumen').textContent = data.total_dokumen;
            document.getElementById('stat-sub-dokumen').textContent = `Dari ${data.total_sesi} Sesi`;

            if (data.sesi_terakhir) {
                document.getElementById('stat-sesi-terakhir').textContent =
                    `${data.sesi_terakhir.nama_matkul} ${data.sesi_terakhir.kelas}`;
                document.getElementById('stat-tanggal-terakhir').textContent =
                    formatTanggal(data.sesi_terakhir.tanggal);
            } else {
                document.getElementById('stat-sesi-terakhir').textContent = '-';
                document.getElementById('stat-tanggal-terakhir').textContent = 'Belum ada sesi';
            }

            // Render tabel
            renderTabel(data.riwayat);
        })
        .catch(err => {
            showError('Error: ' + err.message);
        });
}

function renderTabel(riwayat) {
    const tbody = document.getElementById('historyTableBody');

    if (!riwayat || riwayat.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align:center; color:#888; padding: 24px;">
                    Belum ada riwayat sesi analisis.
                </td>
            </tr>`;
        return;
    }

    tbody.innerHTML = riwayat.map(sesi => {
        const statusBadge = getStatusBadge(sesi.status_duplikasi, sesi.status_sesi);
        const tanggal = formatTanggal(sesi.tanggal_buat);
        const linkHasil = sesi.status_sesi === 'analyzed' || sesi.status_sesi === 'completed'
            ? `/analisis/sesi/${sesi.id_sesi}/hasil`
            : `/sesi/${sesi.id_sesi}/unggah`;

        return `
            <tr data-id="${sesi.id_sesi}">
                <td>
                    <div class="session-info">
                        <span class="session-title">${escHtml(sesi.nama_matkul)} ${escHtml(sesi.kelas)}</span>
                        <span class="session-desc">${escHtml(sesi.nama_matkul)} - Kelas ${escHtml(sesi.kelas)}</span>
                    </div>
                </td>
                <td>${tanggal}</td>
                <td>${sesi.jumlah_dokumen} File</td>
                <td>${statusBadge}</td>
                <td>
                    <div class="action-cell">
                        <a href="${linkHasil}" class="btn-action open" title="Buka Sesi">
                            <i class="fa-solid fa-arrow-up-right-from-square"></i>
                        </a>
                        <button class="btn-action delete" title="Hapus"
                            onclick="openDeleteModal(${sesi.id_sesi}, '${escHtml(sesi.nama_matkul)} ${escHtml(sesi.kelas)}')">
                            <i class="fa-solid fa-trash-can"></i>
                        </button>
                    </div>
                </td>
            </tr>`;
    }).join('');
}

function getStatusBadge(status_duplikasi, status_sesi) {
    if (status_sesi === 'uploaded') {
        return '<span class="status-badge belum">Belum Dianalisis</span>';
    }
    if (!status_duplikasi) {
        return '<span class="status-badge belum">-</span>';
    }
    const map = {
        'Ada Duplikasi': '<span class="status-badge duplikasi">Ada Duplikasi</span>',
        'Duplikasi Sedang': '<span class="status-badge sedang">Duplikasi Sedang</span>',
        'Bersih': '<span class="status-badge bersih">Bersih</span>'
    };
    return map[status_duplikasi] || '<span class="status-badge">-</span>';
}

function formatTanggal(isoString) {
    if (!isoString) return '-';
    const date = new Date(isoString);
    return date.toLocaleDateString('id-ID', {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
    });
}

function escHtml(s) {
    return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function showError(pesan) {
    document.getElementById('historyTableBody').innerHTML = `
        <tr>
            <td colspan="5" style="text-align:center; color:red; padding: 24px;">
                ${pesan}
            </td>
        </tr>`;
}

// ══ Modal Hapus ══
let deleteTargetId = null;

function openDeleteModal(id, nama) {
    deleteTargetId = id;
    document.getElementById('deleteTargetSession').textContent = nama;
    document.getElementById('deleteModalBackdrop').classList.add('active');
}

function closeDeleteModal() {
    deleteTargetId = null;
    document.getElementById('deleteModalBackdrop').classList.remove('active');
}

document.getElementById('btnConfirmDelete').addEventListener('click', function () {
    if (!deleteTargetId) return;

    fetch(`/riwayat/${deleteTargetId}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' }
    })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'selesai') {
                closeDeleteModal();
                loadRiwayat();
            } else {
                alert('Gagal menghapus sesi: ' + data.pesan);
            }
        })
        .catch(err => {
            alert('Error: ' + err.message);
        });
});
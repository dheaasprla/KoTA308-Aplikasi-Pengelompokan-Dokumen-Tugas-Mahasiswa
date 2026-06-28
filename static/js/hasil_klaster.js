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
            const sesiId = document.getElementById('btn-reanalyze').getAttribute('data-sesi-id');

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

    if (dropdownToggle && dropdownMenu) {
        dropdownToggle.addEventListener('click', function (e) {
            e.stopPropagation();
            dropdownMenu.classList.toggle('show');
        });

        document.addEventListener('click', function () {
            dropdownMenu.classList.remove('show');
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
            modalThreshold.classList.add('active');
        });
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
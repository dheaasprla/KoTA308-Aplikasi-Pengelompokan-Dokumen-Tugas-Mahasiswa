/**
 * KoTA-308: Premium JavaScript Interactions (Hasil Klaster)
 */

document.addEventListener('DOMContentLoaded', function () {
    initAccordion();
    initOutliersToggle();
    initExportDropdown();
    initProgressBars();
});

/**
 * Initialize progress bar fills from data-score attributes
 */
function initProgressBars() {
    const fills = document.querySelectorAll('.indicator-fill[data-score]');
    fills.forEach(fill => {
        const score = fill.getAttribute('data-score');
        if (score) {
            fill.style.width = score;
        }
    });
}


/**
 * Initialize Accordion Collapse/Expand for Cluster Cards
 */
function initAccordion() {
    const headerRows = document.querySelectorAll('.cluster-header-row');
    
    headerRows.forEach(header => {
        header.addEventListener('click', function () {
            const card = this.closest('.cluster-card');
            const clusterTitle = card.querySelector('.cluster-title').textContent.trim();
            
            // Arahkan ke halaman detail klaster dengan parameter nama klaster
            window.location.href = `/detail-klaster?cluster=${encodeURIComponent(clusterTitle)}`;
        });
    });
}

/**
 * Initialize dynamic toggle for hidden outlier documents
 */
function initOutliersToggle() {
    const viewAllBtn = document.getElementById('btn-view-all-outliers');
    const moreBadge = document.getElementById('btn-more-outliers');
    const outliersLeft = document.querySelector('.outliers-left');

    // Create a container for hidden outliers if it doesn't exist
    let hiddenContainer = document.querySelector('.hidden-outliers');
    if (!hiddenContainer) {
        hiddenContainer = document.createElement('div');
        hiddenContainer.className = 'hidden-outliers';
        
        // Add 5 more dummy outliers to render on expand
        const dummyOutliers = ['Citra_Lestari.pdf', 'Eko_Prasetyo.pdf', 'Farhan_Wibowo.pdf', 'Gita_Saraswati.pdf', 'Hadi_Kusuma.pdf'];
        
        dummyOutliers.forEach(filename => {
            const badge = document.createElement('span');
            badge.className = 'outlier-badge';
            badge.title = filename;
            badge.innerHTML = filename;
            hiddenContainer.appendChild(badge);
        });
        
        outliersLeft.appendChild(hiddenContainer);
    }

    function toggleOutliers() {
        const isShown = hiddenContainer.classList.toggle('show');
        
        if (isShown) {
            viewAllBtn.textContent = 'Sembunyikan';
            if (moreBadge) moreBadge.style.display = 'none';
        } else {
            viewAllBtn.textContent = 'Lihat Semua';
            if (moreBadge) moreBadge.style.display = 'flex';
        }
    }

    if (viewAllBtn) {
        viewAllBtn.addEventListener('click', toggleOutliers);
    }
    if (moreBadge) {
        moreBadge.addEventListener('click', toggleOutliers);
    }
}

/**
 * Handle Export Dropdown Menu Actions
 */
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

/**
 * Toast Notification System helper
 */
function showToast(title, message, type = 'success') {
    // Check if container exists, if not create it
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        
        // Add styling for toast container dynamically if not present
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
    
    // Create toast card
    const toast = document.createElement('div');
    toast.className = `toast-card toast-${type}`;
    
    // Base styling for toast cards
    Object.assign(toast.style, {
        background: '#ffffff',
        borderLeft: `6px solid ${type === 'success' ? '#10B981' : '#3B82F6'}`,
        boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        borderRadius: '8px',
        padding: '16px',
        display: 'flex',
        gap: '12px',
        alignItems: 'flex-start',
        transform: 'translateX(120%)',
        transition: 'transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275), opacity 0.3s ease',
        opacity: '0'
    });
    
    // Set text color/icon depending on type
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
    
    // Trigger transition
    setTimeout(() => {
        toast.style.transform = 'translateX(0)';
        toast.style.opacity = '1';
    }, 10);
    
    // Auto remove toast after 4 seconds
    setTimeout(() => {
        toast.style.transform = 'translateX(120%)';
        toast.style.opacity = '0';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 4000);
}

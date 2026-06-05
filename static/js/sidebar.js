// ══════════════════════════════════════
// sidebar.js
// Logika toggle sidebar (hamburger, overlay, collapse/expand)
// Panggil setelah DOM ready atau taruh di bawah body
// ══════════════════════════════════════

(function () {
    var sidebar = document.getElementById('sidebar');
    var mainContent = document.getElementById('mainContent');
    var menuBtn = document.getElementById('menuBtn');
    var hamburgerFixed = document.getElementById('hamburgerFixed');
    var overlay = document.getElementById('sidebarOverlay');

    if (!sidebar) return; // guard: jika sidebar tidak ada di halaman ini

    function closeSidebar() {
        sidebar.classList.add('collapsed');
        sidebar.classList.remove('active');
        if (mainContent) mainContent.classList.add('expanded');
        if (hamburgerFixed) hamburgerFixed.classList.add('show');
        if (overlay) overlay.classList.remove('active');
    }

    function openSidebar() {
        sidebar.classList.remove('collapsed');
        sidebar.classList.add('active');
        if (mainContent) mainContent.classList.remove('expanded');
        if (hamburgerFixed) hamburgerFixed.classList.remove('show'); // Hide fixed hamburger button when open
        if (overlay) overlay.classList.add('active');
    }

    // Toggle logic for the main sidebar button (desktop & mobile)
    menuBtn.addEventListener('click', function () {
        if (sidebar.classList.contains('collapsed')) {
            openSidebar();
        } else {
            closeSidebar();
        }
    });

    // Mobile trigger button and overlay
    if (hamburgerFixed) {
        hamburgerFixed.addEventListener('click', openSidebar);
    }
    if (overlay) {
        overlay.addEventListener('click', closeSidebar);
    }
})();
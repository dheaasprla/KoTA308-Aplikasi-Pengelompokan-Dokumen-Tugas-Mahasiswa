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
        mainContent.classList.add('expanded');
        hamburgerFixed.classList.add('show');
        overlay.classList.remove('active');
    }

    function openSidebar() {
        sidebar.classList.remove('collapsed');
        mainContent.classList.remove('expanded');
        hamburgerFixed.classList.remove('show');
        overlay.classList.add('active');
    }

    menuBtn.addEventListener('click', closeSidebar);
    hamburgerFixed.addEventListener('click', openSidebar);
    overlay.addEventListener('click', closeSidebar);
})();
// Database text comparison dummy yang reaktif
const dataEl = document.getElementById('text-pairs-data');
const backendPairs = dataEl && dataEl.getAttribute('data-pairs') ? JSON.parse(dataEl.getAttribute('data-pairs')) : null;

// Cek jika data kosong (empty object) dari JSON.parse
const hasBackendPairs = backendPairs && Object.keys(backendPairs).length > 0;
const comparisonDatabase = hasBackendPairs ? backendPairs : {
    "Dhea.pdf_Berliana.pdf": {
        doc1Title: "Dhea.pdf",
        doc2Title: "Berliana.pdf",
        doc1Content: `
            <span class="highlight-direct">Pemrograman web merupakan salah satu bidang dalam ilmu komputer yang berfokus pada pengembangan aplikasi berbasis internet.</span>
            Dalam era digital saat ini, kebutuhan akan aplikasi web terus meningkat seiring berkembangnya teknologi informasi.
            Terdapat beberapa komponen utama dalam pemrograman web, yaitu HTML sebagai struktur, CSS sebagai tampilan, dan JavaScript sebagai logika interaktif.
            <span class="highlight-semantic">Ketiga komponen ini bekerja secara sinergis untuk menghasilkan antarmuka pengguna yang responsif dan fungsional.</span>
        `,
        doc2Content: `
            <span class="highlight-direct">Web programming adalah salah satu cabang ilmu komputer yang menitikberatkan pada pembuatan aplikasi yang berjalan di atas jaringan internet.</span>
            Di era digital seperti sekarang, permintaan terhadap aplikasi berbasis web terus bertumbuh.
            Ada tiga elemen pokok dalam web programming, yaitu HTML untuk struktur, CSS untuk gaya tampilan, dan JavaScript untuk interaksi dinamis.
            <span class="highlight-semantic">Ketiganya saling melengkapi untuk menciptakan antarmuka yang responsif dan memiliki fungsi yang lengkap.</span>
        `
    },
    "Dhea.pdf_Jihan.pdf": {
        doc1Title: "Dhea.pdf",
        doc2Title: "Jihan.pdf",
        doc1Content: `
            Pemrograman web merupakan salah satu bidang dalam ilmu komputer yang berfokus pada pengembangan aplikasi berbasis internet.
            <span class="highlight-semantic">Dalam era digital saat ini, kebutuhan akan aplikasi web terus meningkat seiring berkembangnya teknologi informasi.</span>
            Terdapat beberapa komponen utama dalam pemrograman web, yaitu HTML sebagai struktur, CSS sebagai tampilan, dan JavaScript sebagai logika interaktif.
            Ketiga komponen ini bekerja secara sinergis untuk menghasilkan antarmuka pengguna yang responsif dan fungsional.
        `,
        doc2Content: `
            Teknologi web berkembang sangat pesat dalam beberapa tahun terakhir.
            <span class="highlight-semantic">Kebutuhan akan platform digital berbasis internet terus mengalami lonjakan yang signifikan di era modern.</span>
            Oleh karena itu, mempelajari pemrograman web menjadi sangat relevan bagi mahasiswa teknik informatika.
        `
    },
    "Berliana.pdf_Jihan.pdf": {
        doc1Title: "Berliana.pdf",
        doc2Title: "Jihan.pdf",
        doc1Content: `
            Web programming adalah salah satu cabang ilmu komputer yang menitikberatkan pada pembuatan aplikasi yang berjalan di atas jaringan internet.
            <span class="highlight-direct">Di era digital seperti sekarang, permintaan terhadap aplikasi berbasis web terus bertumbuh.</span>
            Ada tiga elemen pokok dalam web programming, yaitu HTML untuk struktur, CSS untuk gaya tampilan, dan JavaScript untuk interaksi dinamis.
            Ketiganya saling melengkapi untuk menciptakan antarmuka yang responsif dan memiliki fungsi yang lengkap.
        `,
        doc2Content: `
            Kebutuhan akan platform digital berbasis internet terus mengalami lonjakan yang signifikan di era modern.
            <span class="highlight-direct">Permintaan terhadap pembuatan sistem aplikasi web terus mengalami kenaikan yang pesat di era teknologi saat ini.</span>
            Ada berbagai macam library dan framework JavaScript yang dapat digunakan untuk mempercepat proses pembangunan aplikasi.
        `
    }
};

document.addEventListener('DOMContentLoaded', function () {
    const cells = document.querySelectorAll('.similarity-cell');
    const doc1TitleEl = document.getElementById('compare-doc1-title');
    const doc2TitleEl = document.getElementById('compare-doc2-title');
    const doc1BodyEl = document.getElementById('compare-doc1-body');
    const doc2BodyEl = document.getElementById('compare-doc2-body');

    // Set initial compared pair dynamically based on first cell
    const initialCell = document.querySelector('.similarity-cell');
    if (initialCell) {
        activateCell(initialCell);
    }

    cells.forEach(cell => {
        cell.addEventListener('click', function () {
            activateCell(this);
        });
    });

    function activateCell(cell) {
        // Hapus kelas aktif dari semua sel
        cells.forEach(c => c.classList.remove('active-cell'));
        
        // Tambah kelas aktif pada sel yang diklik
        cell.classList.add('active-cell');

        const doc1 = cell.getAttribute('data-doc1');
        const doc2 = cell.getAttribute('data-doc2');
        
        // Generate key pembanding untuk pencarian data
        let key = `${doc1}_${doc2}`;
        let reverseKey = `${doc2}_${doc1}`;
        
        let data = comparisonDatabase[key] || comparisonDatabase[reverseKey];
        
        if (data) {
            // Update UI Comparison
            doc1TitleEl.textContent = doc1;
            doc2TitleEl.textContent = doc2;
            
            // Jika urutan terbalik, pastikan isi kolom juga ikut dibalik
            if (doc1 === data.doc1Title) {
                doc1BodyEl.innerHTML = data.doc1Content;
                doc2BodyEl.innerHTML = data.doc2Content;
            } else {
                doc1BodyEl.innerHTML = data.doc2Content;
                doc2BodyEl.innerHTML = data.doc1Content;
            }
        } else {
            // Default jika data pembanding tidak ditemukan
            doc1TitleEl.textContent = doc1;
            doc2TitleEl.textContent = doc2;
            doc1BodyEl.innerHTML = `<p class="text-muted">Tidak ada data kemiripan kalimat detail yang tersedia untuk pasangan ini.</p>`;
            doc2BodyEl.innerHTML = `<p class="text-muted">Tidak ada data kemiripan kalimat detail yang tersedia untuk pasangan ini.</p>`;
        }
    }

});


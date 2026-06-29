document.addEventListener('DOMContentLoaded', function () {
    const cells = document.querySelectorAll('.similarity-cell');
    const doc1TitleEl = document.getElementById('compare-doc1-title');
    const doc2TitleEl = document.getElementById('compare-doc2-title');
    const doc1BodyEl = document.getElementById('compare-doc1-body');
    const doc2BodyEl = document.getElementById('compare-doc2-body');

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
        cells.forEach(c => c.classList.remove('active-cell'));
        cell.classList.add('active-cell');

        const doc1 = cell.getAttribute('data-doc1');
        const doc2 = cell.getAttribute('data-doc2');
        const idDetail = cell.getAttribute('data-id-detail');

        doc1TitleEl.textContent = doc1;
        doc2TitleEl.textContent = doc2;

        doc1BodyEl.innerHTML = '<p style="color:#888; font-style:italic;">Memuat perbandingan teks...</p>';
        doc2BodyEl.innerHTML = '<p style="color:#888; font-style:italic;">Memuat perbandingan teks...</p>';

        if (!idDetail) {
            doc1BodyEl.innerHTML = '<p style="color:#888;">Tidak ada data kemiripan untuk pasangan ini.</p>';
            doc2BodyEl.innerHTML = '<p style="color:#888;">Tidak ada data kemiripan untuk pasangan ini.</p>';
            return;
        }

        fetch(`/analisis/detail/${idDetail}/fulltext`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                doc1: doc1,
                doc2: doc2
            })
        })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'tidak_ada_kemiripan') {
                    doc1BodyEl.innerHTML = `<p style="color:#64748B; font-style:italic;">${escHtml(data.pesan)}</p>`;
                    doc2BodyEl.innerHTML = `<p style="color:#64748B; font-style:italic;">${escHtml(data.pesan)}</p>`;
                    return;
                }

                if (data.status !== 'selesai') {
                    doc1BodyEl.innerHTML = '<p style="color:red;">Gagal memuat data.</p>';
                    doc2BodyEl.innerHTML = '<p style="color:red;">Gagal memuat data.</p>';
                    return;
                }

                if (data.dokumen_1.kalimat && data.dokumen_1.kalimat.length > 0) {
                    doc1BodyEl.innerHTML = data.dokumen_1.kalimat
                        .map(k => k.is_highlight
                            ? `<span class="highlight-direct">${escHtml(k.kalimat)}</span> `
                            : `${escHtml(k.kalimat)} `
                        )
                        .join('');
                } else {
                    doc1BodyEl.innerHTML = '<p style="color:#888;">Tidak ada teks yang bisa ditampilkan.</p>';
                }

                if (data.dokumen_2.kalimat && data.dokumen_2.kalimat.length > 0) {
                    doc2BodyEl.innerHTML = data.dokumen_2.kalimat
                        .map(k => k.is_highlight
                            ? `<span class="highlight-direct">${escHtml(k.kalimat)}</span> `
                            : `${escHtml(k.kalimat)} `
                        )
                        .join('');
                } else {
                    doc2BodyEl.innerHTML = '<p style="color:#888;">Tidak ada teks yang bisa ditampilkan.</p>';
                }
            })
            .catch(err => {
                doc1BodyEl.innerHTML = `<p style="color:red;">Error: ${err.message}</p>`;
                doc2BodyEl.innerHTML = `<p style="color:red;">Error: ${err.message}</p>`;
            });
    }

    function escHtml(s) {
        return String(s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }
});
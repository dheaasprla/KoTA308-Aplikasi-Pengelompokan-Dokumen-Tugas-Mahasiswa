// ══════════════════════════════════════
// unggah_dokumen.js
// Logika utama halaman Unggah Dokumen
//
// ALUR BARU:
// 1. Pilih file → modal loading "Mengunggah Dokumen" muncul
// 2. Loading selesai (simulasi) → modal tutup, grid berkas + kuota tampil
// 3. Klik "Lanjutkan" → hanya modal konfigurasi threshold (tanpa loading)
// ══════════════════════════════════════

(function () {

  /* ══ KONFIGURASI ══ */
  var MAX_TOTAL_MB = 200;
  var MAX_FILE_MB = 50;
  var MAX_FILES = 32;
  var CIRCUMFERENCE = 2 * Math.PI * 48; // r=48

  /* ══ STATE ══ */
  var usedMB = 0;
  var fileList = [];
  // sessionId disimpan setelah "upload" dummy selesai
  var currentSessionId = '';

  /* ══ DOM REFS ══ */
  var dropZone = document.getElementById('dropZone');
  var hiddenInput = document.getElementById('hiddenInput');
  var btnSelect = document.getElementById('btn-select-trigger');
  var filesSection = document.getElementById('files-section');
  var filesGrid = document.getElementById('filesGrid');
  var btnClearAll = document.getElementById('btn-clear-all');
  var btnNext = document.getElementById('btn-next-step');
  var btnCancel = document.getElementById('btn-cancel-form');
  var quotaCard = document.getElementById('quotaCard');

  var elQuotaPct = document.getElementById('quota-pct');
  var elQuotaFill = document.getElementById('quota-fill');
  var elSizeUsed = document.getElementById('quota-size-used');
  var elSizeRem = document.getElementById('quota-size-rem');
  var elDonutArc = document.getElementById('donut-arc');
  var elDonutCount = document.getElementById('donut-count');

  // Modal loading (Mengunggah Dokumen)
  var modalLoading = document.getElementById('modal-loading');
  var elProgressBar = document.getElementById('progress-bar');
  var elProgressText = document.getElementById('progress-text');
  var btnCloseUpload = document.getElementById('btn-close-upload');
  var btnBatalUnggah = document.getElementById('btn-batal-unggah');

  // Modal threshold
  var modalThreshold = document.getElementById('modal-threshold');

  /* ══ INIT DONUT ══ */
  function initDonut() {
    elDonutArc.style.fill = 'none';
    elDonutArc.style.stroke = '#B00505';
    elDonutArc.style.strokeWidth = '13';
    elDonutArc.style.strokeLinecap = 'round';
    elDonutArc.style.strokeDasharray = CIRCUMFERENCE.toFixed(2);
    elDonutArc.style.strokeDashoffset = CIRCUMFERENCE.toFixed(2);
    elDonutArc.style.transition = 'stroke-dashoffset 0.5s ease, stroke 0.4s ease';
  }

  /* ══ DRAG & DROP ══ */
  dropZone.addEventListener('dragover', function (e) {
    e.preventDefault();
    dropZone.classList.add('drag');
  });
  dropZone.addEventListener('dragleave', function () {
    dropZone.classList.remove('drag');
  });
  dropZone.addEventListener('drop', function (e) {
    e.preventDefault();
    dropZone.classList.remove('drag');
    handleFilesSelected(e.dataTransfer.files);
  });
  dropZone.addEventListener('click', function (e) {
    if (e.target === btnSelect || btnSelect.contains(e.target)) return;
    hiddenInput.click();
  });
  btnSelect.addEventListener('click', function (e) {
    e.stopPropagation();
    hiddenInput.click();
  });
  hiddenInput.addEventListener('change', function () {
    handleFilesSelected(this.files);
    this.value = '';
  });

  /* ══ HANDLE FILE SELECTED → langsung tampilkan loading ══ */
  function handleFilesSelected(rawFiles) {
    // Validasi dulu sebelum loading
    var toAdd = [];
    var hasError = false;

    Array.from(rawFiles).forEach(function (f) {
      if (!f.name.toLowerCase().endsWith('.pdf')) {
        alert('File "' + f.name + '" bukan PDF. Hanya file .pdf yang diterima.');
        hasError = true; return;
      }
      if (fileList.length + toAdd.length >= MAX_FILES) {
        alert('Batas maksimal ' + MAX_FILES + ' file tercapai.');
        hasError = true; return;
      }
      var sizeMB = f.size / (1024 * 1024);
      if (sizeMB > MAX_FILE_MB) {
        alert('File "' + f.name + '" melebihi batas 50MB.');
        hasError = true; return;
      }
      if (usedMB + toAdd.reduce(function (a, b) { return a + b.sizeMB; }, 0) + sizeMB > MAX_TOTAL_MB) {
        alert('Kuota penuh! Tidak bisa menambah "' + f.name + '".');
        hasError = true; return;
      }
      toAdd.push({ name: f.name, sizeMB: sizeMB, fileObj: f });
    });

    if (toAdd.length === 0) return;

    // Tampilkan modal loading, lalu simulasikan proses
    showUploadLoading(toAdd, function (success) {
      if (!success) return;
      // Tambahkan ke fileList setelah loading selesai
      toAdd.forEach(function (item) {
        fileList.push(item);
        usedMB += item.sizeMB;
      });
      renderGrid();
      updateQuota();
    });
  }

  /* ══ MODAL LOADING: simulasi progress upload ══ */
  var cancelFlag = false;
  var loadingTimer = null;

  function showUploadLoading(files, callback) {
    cancelFlag = false;
    modalLoading.classList.add('active');
    elProgressBar.style.width = '0%';
    elProgressText.textContent = '0%';

    var pct = 0;
    // Kecepatan simulasi: selesai dalam ~1.5 detik
    var step = 4;
    var interval = 60; // ms

    loadingTimer = setInterval(function () {
      if (cancelFlag) {
        clearInterval(loadingTimer);
        modalLoading.classList.remove('active');
        callback(false);
        return;
      }
      pct += step + Math.random() * 3;
      if (pct >= 100) {
        pct = 100;
        clearInterval(loadingTimer);
        elProgressBar.style.width = '100%';
        elProgressText.textContent = '100%';
        setTimeout(function () {
          modalLoading.classList.remove('active');
          // Reset progress untuk next kali
          elProgressBar.style.width = '0%';
          elProgressText.textContent = '0%';
          callback(true);
        }, 400);
        return;
      }
      elProgressBar.style.width = pct.toFixed(0) + '%';
      elProgressText.textContent = pct.toFixed(0) + '%';
    }, interval);
  }

  function cancelUpload() {
    cancelFlag = true;
    if (loadingTimer) clearInterval(loadingTimer);
    modalLoading.classList.remove('active');
  }

  btnCloseUpload.addEventListener('click', cancelUpload);
  btnBatalUnggah.addEventListener('click', cancelUpload);

  /* ══ RENDER GRID ══ */
  function renderGrid() {
    filesGrid.innerHTML = '';
    if (fileList.length === 0) {
      filesSection.style.display = 'none';
      btnNext.disabled = true;
      return;
    }
    filesSection.style.display = 'block';
    btnNext.disabled = false;

    fileList.forEach(function (item, idx) {
      var sz = item.sizeMB < 1
        ? (item.sizeMB * 1024).toFixed(0) + ' KB'
        : item.sizeMB.toFixed(1) + 'MB';
      var div = document.createElement('div');
      div.className = 'file-item';
      div.innerHTML =
        '<i class="fa-solid fa-file-lines fi-icon"></i>' +
        '<div class="fi-info">' +
        '<div class="fi-name" title="' + escHtml(item.name) + '">' + escHtml(item.name) + '</div>' +
        '<div class="fi-size">' + sz + '</div>' +
        '</div>' +
        '<button class="fi-del" data-idx="' + idx + '" title="Hapus">' +
        '<i class="fa-solid fa-trash-can"></i>' +
        '</button>';
      filesGrid.appendChild(div);
    });

    filesGrid.querySelectorAll('.fi-del').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var i = parseInt(this.getAttribute('data-idx'));
        usedMB -= fileList[i].sizeMB;
        if (usedMB < 0) usedMB = 0;
        fileList.splice(i, 1);
        renderGrid();
        updateQuota();
      });
    });
  }

  function escHtml(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  /* ══ UPDATE KUOTA + DONUT ══ */
  function updateQuota() {
    var total = fileList.length;
    var pctMB = Math.min((usedMB / MAX_TOTAL_MB) * 100, 100);
    var pctF = Math.min(total / MAX_FILES, 1);
    var rem = Math.max(MAX_TOTAL_MB - usedMB, 0);
    var isHigh = pctMB >= 80;

    elQuotaPct.textContent = Math.round(pctMB) + '% dari kuota digunakan';
    elQuotaFill.style.width = pctMB.toFixed(1) + '%';
    elSizeUsed.textContent = usedMB.toFixed(1) + 'MB/200MB';
    elSizeRem.textContent = rem.toFixed(1) + 'MB';

    elDonutArc.style.strokeDashoffset = (CIRCUMFERENCE * (1 - pctF)).toFixed(2);
    elDonutCount.textContent = total + '/32';
    elDonutArc.style.stroke = '#B00505';
    elQuotaFill.style.background = '#B00505';

    if (isHigh) { quotaCard.classList.add('warn'); }
    else { quotaCard.classList.remove('warn'); }
  }

  /* ══ HAPUS SEMUA ══ */
  btnClearAll.addEventListener('click', function () {
    fileList = []; usedMB = 0;
    renderGrid(); updateQuota();
  });

  /* ══ BATALKAN ══ */
  btnCancel.addEventListener('click', function () {
    fileList = []; usedMB = 0;
    document.getElementById('mata_kuliah').value = '';
    document.getElementById('kelas').value = '';
    renderGrid(); updateQuota();
  });

  /* ══ LANJUTKAN → hanya buka modal threshold ══ */
  btnNext.addEventListener('click', function () {
    var matkul = document.getElementById('mata_kuliah').value.trim();
    var kelas = document.getElementById('kelas').value.trim();
    if (!matkul || !kelas) {
      alert('Harap isi Nama Mata Kuliah dan Kelas terlebih dahulu.');
      return;
    }
    if (fileList.length === 0) {
      alert('Belum ada berkas yang dipilih.');
      return;
    }
    // Langsung buka modal threshold — tidak ada loading lagi
    if (window.initThresholdModal) window.initThresholdModal(currentSessionId);
    modalThreshold.classList.add('active');
  });

  /* ══ INIT ══ */
  initDonut();
  updateQuota();

})();
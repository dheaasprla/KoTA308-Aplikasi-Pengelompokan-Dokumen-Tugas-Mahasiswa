(function () {

  var MAX_TOTAL_MB = 175;
  var MAX_FILE_MB = 5;
  var MAX_FILES = 35;
  var CIRCUMFERENCE = 2 * Math.PI * 48;

  var usedMB = 0;
  var fileList = [];
  var currentSessionId = null;

  var dropZone     = document.getElementById('dropZone');
  var hiddenInput  = document.getElementById('hiddenInput');
  var btnSelect    = document.getElementById('btn-select-trigger');
  var filesSection = document.getElementById('files-section');
  var filesGrid    = document.getElementById('filesGrid');
  var btnClearAll  = document.getElementById('btn-clear-all');
  var btnNext      = document.getElementById('btn-next-step');
  var btnCancel    = document.getElementById('btn-cancel-form');
  var quotaCard    = document.getElementById('quotaCard');

  var elQuotaPct   = document.getElementById('quota-pct');
  var elQuotaFill  = document.getElementById('quota-fill');
  var elSizeUsed   = document.getElementById('quota-size-used');
  var elSizeRem    = document.getElementById('quota-size-rem');
  var elDonutArc   = document.getElementById('donut-arc');
  var elDonutCount = document.getElementById('donut-count');

  var modalLoading   = document.getElementById('modal-loading');
  var elProgressBar  = document.getElementById('progress-bar');
  var elProgressText = document.getElementById('progress-text');
  var btnCloseUpload = document.getElementById('btn-close-upload');
  var btnBatalUnggah = document.getElementById('btn-batal-unggah');

  var modalThreshold = document.getElementById('modal-threshold');
  var formThreshold  = document.getElementById('form-threshold');

  var matkulInput = document.getElementById('mata_kuliah');
  var kelasInput  = document.getElementById('kelas');
  var matkulError = document.getElementById('matkulRequiredError');
  var kelasError  = document.getElementById('kelasRequiredError');

  function initDonut() {
    elDonutArc.style.fill             = 'none';
    elDonutArc.style.stroke           = '#B00505';
    elDonutArc.style.strokeWidth      = '13';
    elDonutArc.style.strokeLinecap    = 'round';
    elDonutArc.style.strokeDasharray  = CIRCUMFERENCE.toFixed(2);
    elDonutArc.style.strokeDashoffset = CIRCUMFERENCE.toFixed(2);
    elDonutArc.style.transition       = 'stroke-dashoffset 0.5s ease, stroke 0.4s ease';
  }

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

  function handleFilesSelected(rawFiles) {
    var toAdd = [];
    Array.from(rawFiles).forEach(function (f) {
      if (!f.name.toLowerCase().endsWith('.pdf')) {
        alert('File "' + f.name + '" bukan PDF. Hanya file .pdf yang diterima.');
        return;
      }

      var sizeMB = f.size / (1024 * 1024);

      if (sizeMB > MAX_FILE_MB) {
        var fileSizeError = document.getElementById('fileSizeError');
        if (fileSizeError) {
          fileSizeError.textContent = 'File "' + f.name + '" melebihi batas ' + MAX_FILE_MB + 'MB.';
          fileSizeError.style.display = 'block';
          setTimeout(function() {
            fileSizeError.style.display = 'none';
          }, 4000);
        }
        return;
      }

      if (fileList.length + toAdd.length >= MAX_FILES) {
        var maxFileError = document.getElementById('maxFileError');
        if (maxFileError) {
          maxFileError.style.display = 'block';
          setTimeout(function() {
            maxFileError.style.display = 'none';
          }, 4000);
        }
        return;
      }

      var totalBaru = toAdd.reduce(function (a, b) { return a + b.sizeMB; }, 0);
      if (usedMB + totalBaru + sizeMB > MAX_TOTAL_MB) {
        alert('Kuota penuh! Tidak bisa menambah "' + f.name + '".');
        return;
      }

      toAdd.push({ name: f.name, sizeMB: sizeMB, fileObj: f });
    });

    if (toAdd.length === 0) return;

    showUploadLoading(toAdd, function (success) {
      if (!success) return;
      toAdd.forEach(function (item) {
        fileList.push(item);
        usedMB += item.sizeMB;
      });
      renderGrid();
      updateQuota();
    });
  }

  var cancelFlag  = false;
  var loadingTimer = null;

  function showUploadLoading(files, callback) {
    cancelFlag = false;
    modalLoading.classList.add('active');
    elProgressBar.style.width = '0%';
    elProgressText.textContent = '0%';

    var pct = 0;
    loadingTimer = setInterval(function () {
      if (cancelFlag) {
        clearInterval(loadingTimer);
        modalLoading.classList.remove('active');
        callback(false);
        return;
      }
      pct += 4 + Math.random() * 3;
      if (pct >= 100) {
        pct = 100;
        clearInterval(loadingTimer);
        elProgressBar.style.width = '100%';
        elProgressText.textContent = '100%';
        setTimeout(function () {
          modalLoading.classList.remove('active');
          elProgressBar.style.width = '0%';
          elProgressText.textContent = '0%';
          callback(true);
        }, 400);
        return;
      }
      elProgressBar.style.width  = pct.toFixed(0) + '%';
      elProgressText.textContent = pct.toFixed(0) + '%';
    }, 60);
  }

  function cancelUpload() {
    cancelFlag = true;
    if (loadingTimer) clearInterval(loadingTimer);
    modalLoading.classList.remove('active');
  }

  btnCloseUpload.addEventListener('click', cancelUpload);
  btnBatalUnggah.addEventListener('click', cancelUpload);

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
        : item.sizeMB.toFixed(1) + ' MB';
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
    return s
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function updateQuota() {
    var total  = fileList.length;
    var pctMB  = Math.min((usedMB / MAX_TOTAL_MB) * 100, 100);
    var pctF   = Math.min(total / MAX_FILES, 1);
    var rem    = Math.max(MAX_TOTAL_MB - usedMB, 0);
    var isHigh = pctMB >= 80;

    elQuotaPct.textContent  = Math.round(pctMB) + '% dari kuota digunakan';
    elQuotaFill.style.width = pctMB.toFixed(1) + '%';
    elSizeUsed.textContent  = usedMB.toFixed(1) + 'MB/175MB';
    elSizeRem.textContent   = rem.toFixed(1) + 'MB';

    elDonutArc.style.strokeDashoffset = (CIRCUMFERENCE * (1 - pctF)).toFixed(2);
    elDonutCount.textContent          = total + '/35';
    elDonutArc.style.stroke           = '#B00505';
    elQuotaFill.style.background      = '#B00505';

    if (isHigh) quotaCard.classList.add('warn');
    else quotaCard.classList.remove('warn');
  }

  btnClearAll.addEventListener('click', function () {
    fileList = [];
    usedMB = 0;
    currentSessionId = null;
    renderGrid();
    updateQuota();
  });

  btnCancel.addEventListener('click', function () {
    fileList = [];
    usedMB = 0;
    currentSessionId = null;
    matkulInput.value = '';
    kelasInput.value = '';
    hideFieldError(matkulError, matkulInput);
    hideFieldError(kelasError, kelasInput);
    renderGrid();
    updateQuota();
  });

  function showFieldError(errorEl, inputEl) {
    errorEl.style.display = 'block';
    inputEl.style.boxShadow = '0 0 0 2px #B00505';
  }

  function hideFieldError(errorEl, inputEl) {
    errorEl.style.display = 'none';
    inputEl.style.boxShadow = '';
  }

  btnNext.addEventListener('click', function () {
    var matkul = matkulInput.value.trim();
    var kelas  = kelasInput.value.trim();
    var hasError = false;

    if (!matkul) {
      showFieldError(matkulError, matkulInput);
      hasError = true;
    } else {
      hideFieldError(matkulError, matkulInput);
    }

    if (!kelas) {
      showFieldError(kelasError, kelasInput);
      hasError = true;
    } else {
      hideFieldError(kelasError, kelasInput);
    }

    if (hasError) {
      return;
    }

    if (fileList.length === 0) {
      return;
    }

    btnNext.disabled = true;
    btnNext.textContent = 'Memproses...';

    var formSesi = new FormData();
    formSesi.append('mata_kuliah', matkul);
    formSesi.append('kelas', kelas);

    fetch('/sesi/baru/api', {
      method: 'POST',
      body: formSesi
    })
    .then(function (res) { return res.json(); })
    .then(function (data) {
      if (data.status !== 'success') {
        throw new Error(data.messages ? data.messages.join(', ') : 'Gagal membuat sesi.');
      }
      currentSessionId = data.id_sesi;

      var formFiles = new FormData();
      fileList.forEach(function (item) {
        formFiles.append('files[]', item.fileObj, item.name);
      });

      return fetch('/sesi/' + currentSessionId + '/unggah/api', {
        method: 'POST',
        body: formFiles
      });
    })
    .then(function (res) { return res.json(); })
    .then(function (data) {
      if (data.status !== 'success') {
        throw new Error(data.message || 'Gagal mengunggah berkas.');
      }
      if (data.ditolak && data.ditolak.length > 0) {
        alert('Beberapa file ditolak backend:\n' + data.ditolak.join('\n'));
      }
      if (formThreshold) {
        formThreshold.action = '/sesi/' + currentSessionId + '/hasil-klaster';
      }
      modalThreshold.classList.add('active');
    })
    .catch(function (err) {
      alert('Terjadi kesalahan: ' + err.message);
    })
    .finally(function () {
      btnNext.disabled = false;
      btnNext.textContent = 'Lanjutkan';
    });
  });

  initDonut();
  updateQuota();

})();
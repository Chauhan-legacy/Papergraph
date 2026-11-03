/**
 * Research Paper Directory Import Controller
 * Allows users to configure, scan, preview, and import local PDF, TXT, MD, and JSON papers.
 */
const FolderImportModule = {
  scanData: null,
  activeFolderPath: '',

  init() {
    this.bindEvents();
  },

  bindEvents() {
    // Open modal triggers
    const triggerIds = [
      'btn-quick-import-folder',
      'btn-folder-import',
      'btn-settings-scan-source'
    ];

    triggerIds.forEach((id) => {
      const btn = document.getElementById(id);
      if (btn) {
        btn.addEventListener('click', () => this.showModal());
      }
    });

    // Close modal
    const closeBtn = document.getElementById('btn-close-folder-modal');
    if (closeBtn) closeBtn.addEventListener('click', () => this.closeModal());

    const cancelBtn = document.getElementById('btn-cancel-folder-modal');
    if (cancelBtn) cancelBtn.addEventListener('click', () => this.closeModal());

    // Scan form submit
    const scanForm = document.getElementById('form-scan-folder');
    if (scanForm) {
      scanForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const pathInput = document.getElementById('folder-path-input');
        const path = pathInput ? pathInput.value.trim() : '';
        if (!path) {
          App.showToast('Please enter a valid directory path.', 'warning');
          return;
        }
        await this.performScan(path);
      });
    }

    // Import execution button
    const importBtn = document.getElementById('btn-import-folder-execute');
    if (importBtn) {
      importBtn.addEventListener('click', () => this.executeImport());
    }

    // Select all checkbox
    const selectAllCb = document.getElementById('folder-select-all-cb');
    if (selectAllCb) {
      selectAllCb.addEventListener('change', (e) => {
        const isChecked = e.target.checked;
        document.querySelectorAll('.folder-file-cb:not(:disabled)').forEach((cb) => {
          cb.checked = isChecked;
        });
        this.updateSelectedCount();
      });
    }
  },

  showModal(presetPath = '') {
    const modal = document.getElementById('folder-import-modal');
    if (!modal) return;

    modal.classList.add('active');

    // Populate collections dropdown
    this.populateCollectionsDropdown();

    const pathInput = document.getElementById('folder-path-input');
    if (pathInput && presetPath) {
      pathInput.value = presetPath;
    } else if (pathInput && !pathInput.value && this.activeFolderPath) {
      pathInput.value = this.activeFolderPath;
    }
  },

  closeModal() {
    const modal = document.getElementById('folder-import-modal');
    if (modal) modal.classList.remove('active');
  },

  async populateCollectionsDropdown() {
    const select = document.getElementById('folder-target-collection');
    if (!select) return;

    try {
      const res = await API.listCollections();
      const cols = res.collections || [];
      select.innerHTML = '<option value="">(Default: General Library)</option>';
      cols.forEach((c) => {
        select.innerHTML += `<option value="${c.id}">${c.name}</option>`;
      });
    } catch (_) {}
  },

  async performScan(folderPath) {
    const scanBtn = document.getElementById('btn-scan-folder-submit');
    const resultsContainer = document.getElementById('folder-scan-results');
    const tableBody = document.getElementById('folder-files-table-body');
    const importBtn = document.getElementById('btn-import-folder-execute');

    if (scanBtn) {
      scanBtn.disabled = true;
      scanBtn.textContent = 'Scanning...';
    }

    if (resultsContainer) resultsContainer.style.display = 'block';
    if (tableBody) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="5" style="text-align: center; padding: 24px; color: var(--text-muted);">
            Scanning directory and extracting metadata from PDF/TXT/MD files...
          </td>
        </tr>
      `;
    }

    try {
      const data = await API.scanFolder(folderPath);
      this.scanData = data;
      this.activeFolderPath = folderPath;

      this.renderScanSummary(data);
      this.renderFilesTable(data.discovered_papers || []);

      if (importBtn) {
        importBtn.disabled = (data.ready_to_import_count === 0);
      }
    } catch (err) {
      if (tableBody) {
        tableBody.innerHTML = `
          <tr>
            <td colspan="5" style="text-align: center; padding: 24px; color: var(--color-danger);">
              Scan failed: ${err.message}
            </td>
          </tr>
        `;
      }
      App.showToast(`Scan error: ${err.message}`, 'error');
    } finally {
      if (scanBtn) {
        scanBtn.disabled = false;
        scanBtn.textContent = 'Scan Directory';
      }
    }
  },

  renderScanSummary(data) {
    const summaryEl = document.getElementById('folder-scan-summary');
    if (!summaryEl) return;

    const unsupportedNote = data.unsupported_count > 0
      ? `<div style="font-size: 11.5px; color: var(--text-muted); margin-top: 4px;">
           Ignored ${data.unsupported_count} unsupported files (supported formats: PDF, TXT, Markdown, JSON).
         </div>`
      : '';

    summaryEl.innerHTML = `
      <div style="background: var(--bg-canvas); border: 1px solid var(--border-subtle); padding: 12px 16px; border-radius: var(--radius-sm); margin-bottom: 14px;">
        <div style="display: flex; gap: 16px; font-size: 12.5px;">
          <span><strong>Total Files:</strong> ${data.total_files_scanned}</span>
          <span><strong>Supported Papers:</strong> <span style="color: var(--brand-forest); font-weight: 600;">${data.supported_count}</span></span>
          <span><strong>Ready to Import:</strong> <span style="color: var(--brand-sage); font-weight: 600;">${data.ready_to_import_count}</span></span>
          <span><strong>Already in Library:</strong> <span style="color: var(--text-muted);">${data.already_imported_count}</span></span>
        </div>
        ${unsupportedNote}
      </div>
    `;
  },

  renderFilesTable(papers) {
    const tableBody = document.getElementById('folder-files-table-body');
    if (!tableBody) return;

    if (papers.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="5" style="text-align: center; padding: 24px; color: var(--text-muted);">
            No supported research papers found in this directory.
          </td>
        </tr>
      `;
      return;
    }

    tableBody.innerHTML = '';
    papers.forEach((p, idx) => {
      const tr = document.createElement('tr');
      const isDup = p.is_already_imported;

      const formatPill = p.extension.toUpperCase().replace('.', '');
      const authors = (p.authors || []).slice(0, 2).join(', ') + ((p.authors || []).length > 2 ? ' et al.' : '');

      tr.innerHTML = `
        <td style="width: 32px; text-align: center;">
          <input type="checkbox" class="folder-file-cb" data-filename="${p.filename}" ${isDup ? 'disabled' : 'checked'}>
        </td>
        <td>
          <div style="font-weight: 500; color: var(--text-primary); font-size: 12.5px;">${p.title}</div>
          <div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;">
            ${authors || 'Not listed'} &bull; ${p.filename}
          </div>
        </td>
        <td>
          <span class="badge-tag ${formatPill === 'PDF' ? 'accent' : ''}">${formatPill}</span>
        </td>
        <td style="font-family: var(--font-mono); font-size: 11px; color: var(--text-secondary);">
          ${p.file_size_formatted}
        </td>
        <td>
          ${isDup
            ? `<span class="badge-tag" style="color: var(--text-muted);" title="${p.duplicate_reason}">Already in Library</span>`
            : `<span class="badge-tag accent">Ready</span>`}
        </td>
      `;

      const cb = tr.querySelector('.folder-file-cb');
      if (cb && !isDup) {
        cb.addEventListener('change', () => this.updateSelectedCount());
      }

      tableBody.appendChild(tr);
    });

    this.updateSelectedCount();
  },

  updateSelectedCount() {
    const checked = document.querySelectorAll('.folder-file-cb:checked');
    const label = document.getElementById('folder-selected-count-label');
    const importBtn = document.getElementById('btn-import-folder-execute');

    if (label) {
      label.textContent = `${checked.length} selected`;
    }
    if (importBtn) {
      importBtn.disabled = checked.length === 0;
    }
  },

  async executeImport() {
    if (!this.scanData || !this.activeFolderPath) return;

    const checked = Array.from(document.querySelectorAll('.folder-file-cb:checked'))
      .map((cb) => cb.dataset.filename);

    if (checked.length === 0) {
      App.showToast('Please select at least one paper to import.', 'warning');
      return;
    }

    const colSelect = document.getElementById('folder-target-collection');
    const targetCollection = colSelect && colSelect.value ? colSelect.value : null;

    const importBtn = document.getElementById('btn-import-folder-execute');
    if (importBtn) {
      importBtn.disabled = true;
      importBtn.textContent = `Importing ${checked.length} papers...`;
    }

    try {
      const res = await API.importFolder(this.activeFolderPath, checked, targetCollection);
      App.showToast(`Successfully imported ${res.imported_count} papers into workspace!`);

      // Refresh overview status and library
      await WorkspaceModule.refreshStatus();
      if (App.activeScreen === 'library') {
        LibraryModule.loadPapers();
      }

      this.closeModal();
    } catch (err) {
      App.showToast(`Import error: ${err.message}`, 'error');
    } finally {
      if (importBtn) {
        importBtn.disabled = false;
        importBtn.textContent = 'Import Selected Papers';
      }
    }
  }
};


/**
 * Settings & System Diagnostics Controller
 */
const SettingsModule = {
  init() {
    this.bindEvents();
    this.loadSavedSourceDir();
  },

  loadSavedSourceDir() {
    const saved = localStorage.getItem("papergraph_source_dir");
    const input = document.getElementById("settings-source-dir");
    if (saved && input) {
      input.value = saved;
    }
  },

  bindEvents() {
    // Scan source directory button
    const scanSourceBtn = document.getElementById("btn-settings-scan-source");
    if (scanSourceBtn) {
      scanSourceBtn.addEventListener("click", () => {
        const input = document.getElementById("settings-source-dir");
        const path = input ? input.value.trim() : "";
        if (!path) {
          App.showToast("Please provide your research paper folder path.", "warning");
          return;
        }
        localStorage.setItem("papergraph_source_dir", path);
        FolderImportModule.showModal(path);
        FolderImportModule.performScan(path);
      });
    }

    // Open workspace
    const openBtn = document.getElementById("btn-settings-open-ws");
    if (openBtn) {
      openBtn.addEventListener("click", () => {
        const pathInput = document.getElementById("settings-ws-path");
        const path = pathInput ? pathInput.value.trim() : "";
        if (!path) {
          App.showToast("Please provide a valid workspace directory path.", "warning");
          return;
        }
        WorkspaceModule.openExistingWorkspace(path);
      });
    }

    // Backup button
    const backupBtn = document.getElementById("btn-settings-backup");
    if (backupBtn) {
      backupBtn.addEventListener("click", async () => {
        try {
          const res = await API.triggerBackup();
          App.showToast(`Backup created: ${res.backup.filename}`);
          this.loadBackupsList();
        } catch (err) {
          App.showToast(`Backup failed: ${err.message}`, "error");
        }
      });
    }

    // Rebuild index button
    const rebuildBtn = document.getElementById("btn-settings-rebuild-index");
    if (rebuildBtn) {
      rebuildBtn.addEventListener("click", async () => {
        try {
          await API.rebuildIndex();
          await WorkspaceModule.refreshStatus();
          App.showToast("Workspace file index successfully rescanned and refreshed.");
        } catch (err) {
          App.showToast(`Error rebuilding index: ${err.message}`, "error");
        }
      });
    }
  },

  async loadBackupsList() {
    const container = document.getElementById("settings-backups-list");
    if (!container) return;

    try {
      const res = await API.listBackups();
      const backups = res.backups || [];
      if (backups.length === 0) {
        container.innerHTML = `<p style="font-size: 12px; color: var(--color-text-muted);">No archive snapshots created yet.</p>`;
        return;
      }

      container.innerHTML = backups.map((b) => `
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: 4px; margin-bottom: 6px; font-size: 12px;">
          <div>
            <strong>${b.filename}</strong>
            <span style="color: var(--color-text-muted); margin-left: 8px;">(${(b.size_bytes / 1024).toFixed(1)} KB)</span>
          </div>
          <button class="btn btn-sm btn-outline restore-btn" data-fn="${b.filename}">Restore</button>
        </div>
      `).join("");

      container.querySelectorAll(".restore-btn").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const fn = btn.dataset.fn;
          if (confirm(`Restore workspace snapshot from ${fn}? Current files will be replaced.`)) {
            try {
              await API.restoreBackup(fn);
              App.showToast(`Restored snapshot ${fn}`);
              await WorkspaceModule.refreshStatus();
            } catch (err) {
              App.showToast(`Restore error: ${err.message}`, "error");
            }
          }
        });
      });
    } catch (err) {
      console.warn("Could not load backups:", err);
    }
  }
};


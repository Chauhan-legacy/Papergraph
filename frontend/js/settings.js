/**
 * Settings & System Diagnostics Controller
 */
const SettingsModule = {
  init() {
    this.bindEvents();
    this.loadSavedSourceDir();
    this.loadAIConfig();
  },

  async loadAIConfig() {
    try {
      const cfg = await API.getAIConfig();
      const typeSelect = document.getElementById('settings-ai-provider-type');
      const urlInput = document.getElementById('settings-ai-base-url');
      const modelInput = document.getElementById('settings-ai-model-name');
      const keyInput = document.getElementById('settings-ai-api-key');

      if (typeSelect && cfg.provider_type) typeSelect.value = cfg.provider_type;
      if (urlInput && cfg.base_url) urlInput.value = cfg.base_url;
      if (modelInput && cfg.model_name) modelInput.value = cfg.model_name;
      if (keyInput && cfg.api_key) keyInput.value = cfg.api_key;
      this.updateAIFieldsVisibility();
    } catch (err) {
      console.warn("Could not load AI configuration:", err);
    }
  },

  updateAIFieldsVisibility() {
    const typeSelect = document.getElementById('settings-ai-provider-type');
    const extraFields = document.getElementById('settings-ai-extra-fields');
    if (!typeSelect || !extraFields) return;
    if (typeSelect.value === 'local') {
      extraFields.style.display = 'none';
    } else {
      extraFields.style.display = 'block';
    }
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

    // AI Configuration Provider toggle
    const aiTypeSelect = document.getElementById("settings-ai-provider-type");
    if (aiTypeSelect) {
      aiTypeSelect.addEventListener("change", () => this.updateAIFieldsVisibility());
    }

    // Save AI Config
    const saveAiBtn = document.getElementById("btn-settings-save-ai");
    if (saveAiBtn) {
      saveAiBtn.addEventListener("click", async () => {
        const provider_type = document.getElementById("settings-ai-provider-type").value;
        const base_url = document.getElementById("settings-ai-base-url").value.trim();
        const model_name = document.getElementById("settings-ai-model-name").value.trim();
        const api_key = document.getElementById("settings-ai-api-key").value.trim() || null;

        try {
          const res = await API.setAIConfig({ provider_type, base_url, model_name, api_key });
          App.showToast(`AI engine set to: ${res.active_provider}`, "success");
        } catch (err) {
          App.showToast(`Failed to update AI settings: ${err.message}`, "error");
        }
      });
    }

    // Test AI Connection
    const testAiBtn = document.getElementById("btn-settings-test-ai");
    if (testAiBtn) {
      testAiBtn.addEventListener("click", async () => {
        const feedback = document.getElementById("settings-ai-test-feedback");
        if (feedback) feedback.textContent = "Testing connection...";
        try {
          const res = await API.testAIConnection();
          if (feedback) {
            feedback.textContent = res.message;
            feedback.style.color = res.success ? "var(--accent-jade)" : "var(--accent-terracotta)";
          }
          App.showToast(res.message, res.success ? "success" : "warning");
        } catch (err) {
          if (feedback) {
            feedback.textContent = `Connection error: ${err.message}`;
            feedback.style.color = "var(--accent-terracotta)";
          }
          App.showToast(`Connection test failed: ${err.message}`, "error");
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


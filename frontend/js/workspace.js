/**
 * Workspace Management Controller
 */
const WorkspaceModule = {
  currentInfo: null,

  async init() {
    this.bindEvents();
    await this.refreshStatus();
  },

  bindEvents() {
    const wsSelect = document.getElementById("sidebar-ws-select");
    if (wsSelect) {
      wsSelect.addEventListener("change", () => {
        if (wsSelect.value) {
          this.switchWorkspace(wsSelect.value);
        }
      });
    }

    const addWsBtn = document.getElementById("btn-sidebar-add-ws");
    if (addWsBtn) {
      addWsBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        this.showModal(true);
      });
    }

    const removeWsBtn = document.getElementById("btn-sidebar-remove-ws");
    if (removeWsBtn) {
      removeWsBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        if (this.currentInfo) {
          this.removeWorkspace(this.currentInfo.workspace_path, this.currentInfo.workspace_name);
        }
      });
    }

    const cancelBtn = document.getElementById("btn-cancel-workspace-modal");
    if (cancelBtn) {
      cancelBtn.addEventListener("click", () => this.closeModal());
    }

    const formCreate = document.getElementById("form-create-workspace");
    if (formCreate) {
      formCreate.addEventListener("submit", async (e) => {
        e.preventDefault();
        const name = document.getElementById("modal-ws-name").value.trim();
        const path = document.getElementById("modal-ws-path").value.trim();
        if (!name) return;
        await this.createNewWorkspace(name, path || null);
      });
    }
  },

  async refreshStatus() {
    try {
      const info = await API.getWorkspaceStatus();
      this.currentInfo = info;
      this.updateUI(info);
      await this.refreshSidebarSelect(info);
      return info;
    } catch (err) {
      console.warn("Could not load workspace status:", err);
      return null;
    }
  },

  async refreshSidebarSelect(activeInfo) {
    const select = document.getElementById("sidebar-ws-select");
    if (!select) return;

    try {
      const res = await API.listWorkspaces();
      const workspaces = (res && res.workspaces) || [];
      select.innerHTML = "";

      workspaces.forEach((ws) => {
        const opt = document.createElement("option");
        opt.value = ws.path;
        opt.textContent = `${ws.name} (${ws.paper_count} papers)`;
        if (ws.is_active || (activeInfo && activeInfo.workspace_path === ws.path)) {
          opt.selected = true;
        }
        select.appendChild(opt);
      });

      const paperCountEl = document.getElementById("sidebar-ws-paper-count");
      if (paperCountEl && activeInfo) {
        paperCountEl.textContent = `${activeInfo.paper_count || 0} papers`;
      }
    } catch (err) {
      console.warn("Could not refresh sidebar workspace select:", err);
    }
  },

  updateUI(info) {
    if (!info) return;

    // Sidebar badge
    const badgeEl = document.getElementById("sidebar-ws-name");
    if (badgeEl) badgeEl.textContent = info.workspace_name || "Research Workspace";

    // Overview counters
    const countEl = document.getElementById("stat-total-papers");
    if (countEl) countEl.textContent = info.paper_count || 0;

    const completedEl = document.getElementById("stat-completed-analyses");
    if (completedEl) completedEl.textContent = info.completed_analyses || 0;

    const pendingEl = document.getElementById("stat-pending-analyses");
    if (pendingEl) pendingEl.textContent = info.pending_analyses || 0;

    const colEl = document.getElementById("stat-collections-count");
    if (colEl) colEl.textContent = info.collections_count || 0;

    // Settings screen fields
    const pathInput = document.getElementById("settings-ws-path");
    if (pathInput) pathInput.value = info.workspace_path || "";

    // Populate Overview Recent Literature Desk Table
    this.renderRecentOverviewPapers();
  },

  async renderRecentOverviewPapers() {
    const tableBody = document.getElementById("overview-recent-papers-list");
    if (!tableBody) return;

    try {
      const response = await API.listPapers({ limit: 5, sort_by: "retrieval_date", sort_desc: true });
      const papers = (response && response.papers) || [];

      if (papers.length === 0) {
        tableBody.innerHTML = `
          <tr>
            <td colspan="5" style="text-align: center; padding: 28px; color: var(--text-muted);">
              No papers imported yet. Click "Discover Papers" to search OpenAlex.
            </td>
          </tr>
        `;
        return;
      }

      tableBody.innerHTML = "";
      papers.slice(0, 5).forEach((paper) => {
        const tr = document.createElement("tr");

        const authors = (paper.authors || [])
          .map((a) => (typeof a === "object" ? a.name : a))
          .slice(0, 2)
          .join(", ") + ((paper.authors || []).length > 2 ? " et al." : "");

        const status = paper.processing_status || "Imported";
        const statusClass = status.includes("Analysis") || status.includes("Completed") ? "Completed" : status.split(" ")[0];

        tr.innerHTML = `
          <td style="max-width: 320px;">
            <div class="desk-paper-title">${paper.title}</div>
            <div class="desk-paper-meta">${authors || "Not specified"} &bull; ${paper.venue || "Academic Venue"}</div>
          </td>
          <td style="font-family: var(--font-mono); font-size: 11.5px; color: var(--text-secondary);">${paper.publication_year || "N/A"}</td>
          <td style="font-family: var(--font-mono); font-size: 11.5px; color: var(--text-secondary);">${paper.citation_count || 0}</td>
          <td><span class="status-chip ${statusClass}">${status}</span></td>
          <td style="text-align: right;">
            <button class="btn btn-sm btn-outline inspect-desk-btn">Inspect</button>
          </td>
        `;

        const inspectBtn = tr.querySelector(".inspect-desk-btn");
        if (inspectBtn) {
          inspectBtn.addEventListener("click", () => App.openPaperInspector(paper));
        }

        const titleDiv = tr.querySelector(".desk-paper-title");
        if (titleDiv) {
          titleDiv.addEventListener("click", () => App.openPaperInspector(paper));
        }

        tableBody.appendChild(tr);
      });
    } catch (err) {
      console.warn("Could not load recent papers for overview:", err);
    }
  },

  async reloadAllModules() {
    await this.refreshStatus();
    if (typeof LibraryModule !== "undefined" && LibraryModule.loadPapers) {
      LibraryModule.loadPapers();
    }
    if (typeof GraphModule !== "undefined" && GraphModule.loadGraph) {
      GraphModule.loadGraph();
    }
    if (typeof AnalyzerModule !== "undefined" && AnalyzerModule.checkProgress) {
      AnalyzerModule.checkProgress();
    }
    if (typeof IntersectionsModule !== "undefined" && IntersectionsModule.loadIntersections) {
      IntersectionsModule.loadIntersections();
    }
    if (typeof TrendsModule !== "undefined" && TrendsModule.loadTrends) {
      TrendsModule.loadTrends();
    }
  },

  async createNewWorkspace(name, path) {
    try {
      const res = await API.createWorkspace(name, path);
      App.showToast(`Workspace '${name}' created and activated!`, "success");
      await this.reloadAllModules();
      this.closeModal();
      App.switchScreen("overview");
      return res;
    } catch (err) {
      App.showToast(`Error creating workspace: ${err.message}`, "error");
      throw err;
    }
  },

  async switchWorkspace(target) {
    try {
      await API.switchWorkspace(target);
      App.showToast("Switched active workspace!", "success");
      await this.reloadAllModules();
      this.closeModal();
      App.switchScreen("overview");
    } catch (err) {
      App.showToast(`Error switching workspace: ${err.message}`, "error");
    }
  },

  async removeWorkspace(target, name) {
    if (!confirm(`Are you sure you want to remove the workspace '${name || target}' from PaperGraph?\n\n(Original directory files on your computer will remain intact.)`)) {
      return;
    }

    try {
      await API.removeWorkspace(target, false);
      App.showToast(`Workspace removed.`, "success");
      await this.reloadAllModules();
      await this.renderWorkspaceList();
    } catch (err) {
      App.showToast(`Error removing workspace: ${err.message}`, "error");
    }
  },

  async renderWorkspaceList() {
    const container = document.getElementById("workspace-list-container");
    const countBadge = document.getElementById("ws-count-badge");
    if (!container) return;

    try {
      container.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 12px; font-size: 12px;">Loading workspaces...</div>`;
      const res = await API.listWorkspaces();
      const workspaces = (res && res.workspaces) || [];

      if (countBadge) {
        countBadge.textContent = `${workspaces.length} Workspace${workspaces.length === 1 ? '' : 's'}`;
      }

      if (workspaces.length === 0) {
        container.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 12px; font-size: 12px;">No workspaces registered.</div>`;
        return;
      }

      container.innerHTML = "";
      workspaces.forEach((ws) => {
        const item = document.createElement("div");
        item.style.display = "flex";
        item.style.alignItems = "center";
        item.style.justifyContent = "space-between";
        item.style.padding = "10px 12px";
        item.style.background = ws.is_active ? "var(--color-bg-surface)" : "transparent";
        item.style.border = ws.is_active ? "1px solid var(--brand-sage)" : "1px solid var(--border-color)";
        item.style.borderRadius = "var(--radius-sm)";
        item.style.gap = "10px";

        item.innerHTML = `
          <div style="flex: 1; min-width: 0;">
            <div style="display: flex; align-items: center; gap: 8px;">
              <strong style="font-size: 13px; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${App.escapeHtml(ws.name)}</strong>
              ${ws.is_active ? '<span class="badge badge-in-library" style="font-size: 10px; padding: 2px 6px;">Active</span>' : ''}
              <span style="font-family: var(--font-mono); font-size: 11px; color: var(--text-muted);">${ws.paper_count} papers</span>
            </div>
            <div style="font-family: var(--font-mono); font-size: 11px; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 3px;" title="${App.escapeHtml(ws.path)}">
              ${App.escapeHtml(ws.path)}
            </div>
          </div>
          <div style="display: flex; align-items: center; gap: 6px; flex-shrink: 0;">
            ${!ws.is_active ? `<button class="btn btn-sm btn-outline btn-act-switch" style="padding: 4px 10px; font-size: 11.5px;">Switch</button>` : ''}
            <button class="btn btn-sm btn-outline btn-act-remove" style="padding: 4px 8px; font-size: 11.5px; color: var(--color-danger); border-color: rgba(220, 53, 69, 0.4);" title="Remove workspace">&times; Remove</button>
          </div>
        `;

        const switchBtn = item.querySelector(".btn-act-switch");
        if (switchBtn) {
          switchBtn.addEventListener("click", () => this.switchWorkspace(ws.path));
        }

        const removeBtn = item.querySelector(".btn-act-remove");
        if (removeBtn) {
          removeBtn.addEventListener("click", () => this.removeWorkspace(ws.path, ws.name));
        }

        container.appendChild(item);
      });
    } catch (err) {
      container.innerHTML = `<div style="color: var(--color-danger); padding: 10px; font-size: 12px;">Failed to load workspaces: ${err.message}</div>`;
    }
  },

  async showModal(focusNew = false) {
    const modal = document.getElementById("workspace-modal");
    if (modal) {
      modal.classList.add("active");
      await this.renderWorkspaceList();
      if (focusNew) {
        const nameInput = document.getElementById("modal-ws-name");
        if (nameInput) {
          nameInput.value = "";
          nameInput.focus();
        }
      }
    }
  },

  closeModal() {
    const modal = document.getElementById("workspace-modal");
    if (modal) modal.classList.remove("active");
  }
};


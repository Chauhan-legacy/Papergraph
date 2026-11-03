/**
 * Workspace Management Controller
 */
const WorkspaceModule = {
  currentInfo: null,

  async init() {
    await this.refreshStatus();
  },

  async refreshStatus() {
    try {
      const info = await API.getWorkspaceStatus();
      this.currentInfo = info;
      this.updateUI(info);
      return info;
    } catch (err) {
      console.warn("Could not load workspace status:", err);
      return null;
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

  async createNewWorkspace(name, path) {
    try {
      const res = await API.createWorkspace(name, path);
      App.showToast("Workspace initialized successfully!");
      await this.refreshStatus();
      this.closeModal();
      App.switchScreen("overview");
      return res;
    } catch (err) {
      App.showToast(`Error creating workspace: ${err.message}`, "error");
      throw err;
    }
  },

  async openExistingWorkspace(path) {
    try {
      const res = await API.openWorkspace(path);
      App.showToast("Workspace opened successfully!");
      await this.refreshStatus();
      this.closeModal();
      App.switchScreen("overview");
      return res;
    } catch (err) {
      App.showToast(`Error opening workspace: ${err.message}`, "error");
      throw err;
    }
  },

  showModal() {
    const modal = document.getElementById("workspace-modal");
    if (modal) modal.classList.add("active");
  },

  closeModal() {
    const modal = document.getElementById("workspace-modal");
    if (modal) modal.classList.remove("active");
  }
};


/**
 * Research Library and Collections Controller
 */
const LibraryModule = {
  papers: [],
  collections: [],
  activeCollectionId: null,
  activeSort: "retrieval_date",
  sortDesc: true,

  init() {
    this.bindEvents();
  },

  bindEvents() {
    // Filter input
    const filterInput = document.getElementById("library-filter-input");
    if (filterInput) {
      filterInput.addEventListener("input", () => this.filterAndRender());
    }

    // Sort select
    const sortSelect = document.getElementById("library-sort-select");
    if (sortSelect) {
      sortSelect.addEventListener("change", (e) => {
        this.activeSort = e.target.value;
        this.loadPapers();
      });
    }

    // New collection button
    const newColBtn = document.getElementById("btn-new-collection");
    if (newColBtn) {
      newColBtn.addEventListener("click", () => this.promptNewCollection());
    }

    // Export button in library
    const exportBtn = document.getElementById("btn-export-library");
    if (exportBtn) {
      exportBtn.addEventListener("click", () => this.showExportModal());
    }
  },

  async loadPapers() {
    try {
      const response = await API.listPapers({
        collection_id: this.activeCollectionId,
        sort_by: this.activeSort,
        sort_desc: this.sortDesc
      });
      this.papers = response.papers || [];
      await this.loadCollections();
      this.filterAndRender();
    } catch (err) {
      console.error("Error loading library papers:", err);
      App.showToast(`Could not load library: ${err.message}`, "error");
    }
  },

  async loadCollections() {
    try {
      const response = await API.listCollections();
      this.collections = response.collections || [];
      this.renderCollectionTabs();
    } catch (err) {
      console.warn("Error loading collections:", err);
    }
  },

  renderCollectionTabs() {
    const tabsContainer = document.getElementById("library-collection-tabs");
    if (!tabsContainer) return;

    tabsContainer.innerHTML = "";

    // "All Papers" tab
    const allTab = document.createElement("button");
    allTab.className = `tab-btn ${this.activeCollectionId === null ? "active" : ""}`;
    allTab.textContent = `All Papers (${this.papers.length})`;
    allTab.addEventListener("click", () => {
      this.activeCollectionId = null;
      this.loadPapers();
    });
    tabsContainer.appendChild(allTab);

    this.collections.forEach((col) => {
      const tabWrap = document.createElement("div");
      tabWrap.style.display = "inline-flex";
      tabWrap.style.alignItems = "center";
      
      const btn = document.createElement("button");
      btn.className = `tab-btn ${this.activeCollectionId === col.id ? "active" : ""}`;
      btn.textContent = `${col.name} (${(col.paper_ids || []).length})`;
      btn.addEventListener("click", () => {
        this.activeCollectionId = col.id;
        this.loadPapers();
      });
      tabWrap.appendChild(btn);

      if (col.id !== "general") {
        const delBtn = document.createElement("button");
        delBtn.innerHTML = `<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;
        delBtn.title = `Delete collection "${col.name}"`;
        delBtn.style.cssText = "background: none; border: none; font-size: 10px; color: var(--color-text-faint); cursor: pointer; padding: 2px 4px; margin-left: -6px; margin-right: 4px; display: inline-flex; align-items: center;";
        delBtn.addEventListener("click", async (e) => {
          e.stopPropagation();
          if (confirm(`Delete collection "${col.name}"? Papers in this collection will remain in your library.`)) {
            try {
              await API.deleteCollection(col.id);
              App.showToast(`Deleted collection "${col.name}"`);
              if (this.activeCollectionId === col.id) {
                this.activeCollectionId = null;
              }
              await this.loadPapers();
            } catch (err) {
              App.showToast(`Error: ${err.message}`, "error");
            }
          }
        });
        tabWrap.appendChild(delBtn);
      }
      tabsContainer.appendChild(tabWrap);
    });
  },

  filterAndRender() {
    const filterInput = document.getElementById("library-filter-input");
    const query = filterInput ? filterInput.value.toLowerCase().trim() : "";

    const container = document.getElementById("library-paper-list");
    if (!container) return;

    const filtered = this.papers.filter((p) => {
      if (!query) return true;
      const titleMatch = (p.title || "").toLowerCase().includes(query);
      const venueMatch = (p.venue || "").toLowerCase().includes(query);
      const authorMatch = (p.authors || []).some((a) => {
        const name = typeof a === "object" ? a.name : a;
        return (name || "").toLowerCase().includes(query);
      });
      return titleMatch || venueMatch || authorMatch;
    });

    if (filtered.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
            </svg>
          </div>
          <h3>${this.papers.length === 0 ? "Library is Empty" : "No Matching Papers Found"}</h3>
          <p>${this.papers.length === 0 ? "Search academic literature to import papers into your local workspace." : "Try clearing the search filter."}</p>
        </div>
      `;
      return;
    }

    container.innerHTML = "";
    filtered.forEach((paper) => {
      const card = document.createElement("div");
      card.className = "paper-card";

      const authors = (paper.authors || [])
        .map((a) => (typeof a === "object" ? a.name : a))
        .slice(0, 3)
        .join(", ") + ((paper.authors || []).length > 3 ? " et al." : "");

      const status = paper.processing_status || "Imported";
      const statusClass = status.includes("Analysis") || status.includes("Completed") ? "Completed" : status.split(" ")[0];

      card.innerHTML = `
        <div class="paper-card-header">
          <div style="flex: 1;">
            <div class="paper-card-title">${paper.title}</div>
            <div class="paper-card-meta" style="margin-top: 4px;">
              <span><strong>Authors:</strong> ${authors || "Not specified"}</span>
              <span><strong>Venue:</strong> ${paper.venue || "Academic Venue"}</span>
              <span><strong>Year:</strong> ${paper.publication_year || "N/A"}</span>
              <span><strong>Citations:</strong> ${paper.citation_count || 0}</span>
              <span class="status-chip ${statusClass}">${status}</span>
            </div>
          </div>
          <div style="display: flex; gap: 6px;">
            <button class="btn btn-sm btn-outline open-detail-btn">Open Detail</button>
          </div>
        </div>
        ${paper.abstract ? `<p class="paper-card-abstract">${paper.abstract}</p>` : `<p class="paper-card-abstract" style="color: var(--color-text-faint); font-style: italic;">Abstract not yet downloaded or processed.</p>`}
        <div class="paper-card-tags">
          ${(paper.topics || []).map((t) => `<span class="badge-tag accent">${t}</span>`).join("")}
          ${(paper.collections || []).map((c) => `<span class="badge-tag peach">${c}</span>`).join("")}
        </div>
      `;

      card.querySelector(".open-detail-btn").addEventListener("click", (e) => {
        e.stopPropagation();
        App.openPaperInspector(paper);
      });

      card.addEventListener("click", () => {
        App.openPaperInspector(paper);
      });

      container.appendChild(card);
    });
  },

  async promptNewCollection() {
    const name = prompt("Enter a name for the new research collection:");
    if (!name || !name.trim()) return;

    const desc = prompt("Enter a short description (optional):") || "";
    try {
      await API.createCollection(name.trim(), desc.trim());
      App.showToast(`Created collection: ${name}`);
      await this.loadCollections();
    } catch (err) {
      App.showToast(`Error creating collection: ${err.message}`, "error");
    }
  },

  showExportModal() {
    const modal = document.getElementById("export-modal");
    if (modal) modal.classList.add("active");
  }
};


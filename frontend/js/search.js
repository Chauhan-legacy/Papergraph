/**
 * Literature Search Controller
 */
const SearchModule = {
  currentResults: [],
  currentPage: 1,
  totalPages: 1,
  perPage: 20,
  activeFilterType: "all",

  init() {
    this.bindEvents();
  },

  bindEvents() {
    const searchForm = document.getElementById("search-form");
    if (searchForm) {
      searchForm.addEventListener("submit", (e) => {
        e.preventDefault();
        this.performSearch(1);
      });
    }

    // Filter type chips
    document.querySelectorAll(".search-type-chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        document.querySelectorAll(".search-type-chip").forEach((c) => c.classList.remove("active"));
        chip.classList.add("active");
        this.activeFilterType = chip.dataset.type || "all";
      });
    });

    // Import all button
    const importAllBtn = document.getElementById("btn-import-all-search");
    if (importAllBtn) {
      importAllBtn.addEventListener("click", () => this.importAllCurrentResults());
    }
  },

  async performSearch(page = 1) {
    const queryInput = document.getElementById("search-query-input");
    const query = queryInput ? queryInput.value.trim() : "";
    if (!query) {
      App.showToast("Please enter a search topic, author, DOI, or title.", "warning");
      return;
    }

    const yearMinInput = document.getElementById("search-year-min");
    const yearMaxInput = document.getElementById("search-year-max");
    const yearMin = yearMinInput && yearMinInput.value ? parseInt(yearMinInput.value) : null;
    const yearMax = yearMaxInput && yearMaxInput.value ? parseInt(yearMaxInput.value) : null;

    const resultsContainer = document.getElementById("search-results-list");
    if (resultsContainer) {
      resultsContainer.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
          </div>
          <h3>Querying Academic Literature</h3>
          <p>Connecting to OpenAlex repositories and retrieving scientific metadata...</p>
        </div>
      `;
    }

    this.currentPage = page;

    try {
      const response = await API.searchLiterature({
        query: query,
        filter_type: this.activeFilterType,
        year_min: yearMin,
        year_max: yearMax,
        page: this.currentPage,
        per_page: this.perPage
      });

      this.currentResults = response.papers || [];
      const totalCount = response.total_count || this.currentResults.length;
      this.totalPages = Math.ceil(totalCount / this.perPage) || 1;

      this.renderResults();
      this.renderPagination(totalCount);
    } catch (err) {
      if (resultsContainer) {
        resultsContainer.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                <line x1="12" y1="9" x2="12" y2="13"></line>
                <line x1="12" y1="17" x2="12.01" y2="17"></line>
              </svg>
            </div>
            <h3>Search Request Failed</h3>
            <p>${err.message}</p>
          </div>
        `;
      }
      App.showToast(`Search error: ${err.message}`, "error");
    }
  },

  renderResults() {
    const container = document.getElementById("search-results-list");
    if (!container) return;

    if (this.currentResults.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
          </div>
          <h3>No Publications Found</h3>
          <p>Try broadening your query, adjusting the year range, or searching by DOI.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = "";
    this.currentResults.forEach((paper, idx) => {
      const card = document.createElement("div");
      card.className = "paper-card";

      const authors = (paper.authors || [])
        .map((a) => (typeof a === "object" ? a.name : a))
        .slice(0, 3)
        .join(", ") + ((paper.authors || []).length > 3 ? " et al." : "");

      const isImported = paper.already_in_library;

      card.innerHTML = `
        <div class="paper-card-header">
          <div style="flex: 1;">
            <div class="paper-card-title">${paper.title}</div>
            <div class="paper-card-meta" style="margin-top: 4px;">
              <span><strong>Authors:</strong> ${authors || "Not specified"}</span>
              <span><strong>Venue:</strong> ${paper.venue || "Academic Venue"}</span>
              <span><strong>Year:</strong> ${paper.publication_year || "N/A"}</span>
              <span><strong>Citations:</strong> ${paper.citation_count || 0}</span>
              ${paper.doi ? `<span><strong>DOI:</strong> ${paper.doi}</span>` : ""}
            </div>
          </div>
          <button class="btn btn-sm ${isImported ? "btn-outline" : "btn-primary"} import-single-btn" data-idx="${idx}">
            ${isImported ? "In Library" : "+ Import to Library"}
          </button>
        </div>
        ${paper.abstract ? `<p class="paper-card-abstract">${paper.abstract}</p>` : `<p class="paper-card-abstract" style="color: var(--color-text-faint); font-style: italic;">Abstract not indexed in OpenAlex for this entry.</p>`}
      `;

      const importBtn = card.querySelector(".import-single-btn");
      if (importBtn && !isImported) {
        importBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          this.importSinglePaper(idx, importBtn);
        });
      }

      card.addEventListener("click", () => {
        App.openPaperInspector(paper);
      });

      container.appendChild(card);
    });
  },

  renderPagination(totalCount) {
    const container = document.getElementById("search-pagination");
    if (!container) return;

    container.innerHTML = `
      <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px 0;">
        <span style="font-size: 12px; color: var(--color-text-muted);">
          Showing ${this.currentResults.length} of ${totalCount.toLocaleString()} results (Page ${this.currentPage} of ${this.totalPages})
        </span>
        <div style="display: flex; gap: 8px;">
          <button class="btn btn-sm btn-outline" id="search-prev-btn" ${this.currentPage <= 1 ? "disabled" : ""}>Previous</button>
          <button class="btn btn-sm btn-outline" id="search-next-btn" ${this.currentPage >= this.totalPages ? "disabled" : ""}>Next</button>
        </div>
      </div>
    `;

    const prevBtn = document.getElementById("search-prev-btn");
    const nextBtn = document.getElementById("search-next-btn");

    if (prevBtn) prevBtn.addEventListener("click", () => this.performSearch(this.currentPage - 1));
    if (nextBtn) nextBtn.addEventListener("click", () => this.performSearch(this.currentPage + 1));
  },

  async importSinglePaper(idx, buttonEl) {
    const paper = this.currentResults[idx];
    if (!paper) return;

    buttonEl.disabled = true;
    buttonEl.textContent = "Importing...";

    try {
      await API.importPapers([paper]);
      paper.already_in_library = true;
      buttonEl.className = "btn btn-sm btn-outline";
      buttonEl.textContent = "In Library";
      App.showToast(`Imported: "${paper.title.slice(0, 35)}..."`);
      await WorkspaceModule.refreshStatus();
    } catch (err) {
      buttonEl.disabled = false;
      buttonEl.textContent = "+ Import to Library";
      App.showToast(`Import failed: ${err.message}`, "error");
    }
  },

  async importAllCurrentResults() {
    const unimported = this.currentResults.filter((p) => !p.already_in_library);
    if (unimported.length === 0) {
      App.showToast("All current results are already in your library.", "warning");
      return;
    }

    try {
      const res = await API.importPapers(unimported);
      App.showToast(`Successfully imported ${res.imported_count} papers!`);
      this.currentResults.forEach((p) => (p.already_in_library = true));
      this.renderResults();
      await WorkspaceModule.refreshStatus();
    } catch (err) {
      App.showToast(`Import error: ${err.message}`, "error");
    }
  }
};


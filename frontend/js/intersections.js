/**
 * Research Intersections Controller
 * Renders Candidate Research Intersections between scientific domains.
 */
const IntersectionsModule = {
  intersections: [],

  init() {
    this.bindEvents();
  },

  bindEvents() {
    const refreshBtn = document.getElementById("btn-refresh-intersections");
    if (refreshBtn) refreshBtn.addEventListener("click", () => this.loadIntersections());
  },

  async loadIntersections() {
    const container = document.getElementById("intersections-list");
    if (!container) return;

    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="12 6 12 12 16 14"></polyline>
          </svg>
        </div>
        <h3>Synthesizing Interdisciplinary Evidence</h3>
        <p>Evaluating cross-domain semantic embeddings and citation linkages...</p>
      </div>
    `;

    try {
      const response = await API.getIntersections();
      this.intersections = response.intersections || [];
      this.render();
    } catch (err) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
              <line x1="12" y1="9" x2="12" y2="13"></line>
              <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
          </div>
          <h3>Analysis Failed</h3>
          <p>${err.message}</p>
        </div>
      `;
      App.showToast(`Error loading intersections: ${err.message}`, "error");
    }
  },

  render() {
    const container = document.getElementById("intersections-list");
    if (!container) return;

    if (this.intersections.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75">
              <circle cx="9" cy="12" r="6"></circle>
              <circle cx="15" cy="12" r="6"></circle>
            </svg>
          </div>
          <h3>No Candidate Intersections Identified</h3>
          <p>Import and analyze papers from multiple distinct scientific domains to discover cross-disciplinary intersections.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = "";
    this.intersections.forEach((item) => {
      const card = document.createElement("div");
      card.className = "paper-card";
      card.style.borderLeft = "4px solid var(--color-peach)";

      const topics = (item.candidate_topics || []).map((t) => `<span class="badge-tag accent">${t}</span>`).join(" ");
      const keywords = (item.relevant_keywords || []).map((k) => `<span class="badge-tag peach">${k}</span>`).join(" ");

      const supportingPapers = (item.supporting_papers || []).map((p) => `
        <li style="margin-bottom: 4px;">
          <a href="#" class="supporting-paper-link" data-id="${p.id}" style="color: var(--color-forest); text-decoration: underline; font-weight: 500;">
            ${p.title}
          </a>
          <span style="font-size: 11px; color: var(--color-text-muted);">(${p.domain || "Cross-domain"})</span>
        </li>
      `).join("");

      card.innerHTML = `
        <div class="paper-card-header">
          <div>
            <span class="badge-tag" style="background: var(--color-peach-light); color: var(--color-deep-brown); margin-bottom: 6px; font-weight: 600;">
              Confidence: ${Math.round(item.confidence_score * 100)}%
            </span>
            <h3 style="font-size: 16px; font-weight: 600; color: var(--color-text-main); margin-top: 4px;">
              ${item.title}
            </h3>
          </div>
        </div>

        <div style="font-size: 13.5px; color: var(--color-text-main); margin: 8px 0; line-height: 1.5;">
          <strong>Why Suggested:</strong> ${item.reason_suggested}
        </div>

        <div style="margin: 8px 0; display: flex; flex-direction: column; gap: 4px; font-size: 12.5px;">
          <div><strong>Semantic Evidence:</strong> ${item.semantic_evidence}</div>
          <div><strong>Citation Evidence:</strong> ${item.citation_evidence}</div>
        </div>

        <div style="margin-top: 6px;">
          <strong style="font-size: 12px; color: var(--color-text-muted);">Candidate Research Topics:</strong>
          <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px;">${topics}</div>
        </div>

        <div style="margin-top: 8px;">
          <strong style="font-size: 12px; color: var(--color-text-muted);">Shared Concepts & Keywords:</strong>
          <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px;">${keywords}</div>
        </div>

        ${supportingPapers ? `
          <div style="margin-top: 10px; background: var(--color-mist); padding: 10px 14px; border-radius: 4px;">
            <strong style="font-size: 12px; color: var(--color-text-main);">Supporting Library Papers:</strong>
            <ul style="margin-top: 6px; padding-left: 18px; font-size: 12px;">
              ${supportingPapers}
            </ul>
          </div>
        ` : ""}

        <div style="margin-top: 10px; font-size: 11.5px; color: var(--color-clay); font-style: italic; background: #FFF9F3; padding: 8px 12px; border-radius: 4px;">
          <strong>Limitations & Scope Note:</strong> ${item.limitations}
        </div>
      `;

      card.querySelectorAll(".supporting-paper-link").forEach((link) => {
        link.addEventListener("click", (e) => {
          e.preventDefault();
          const paperId = link.dataset.id;
          if (paperId) App.openPaperInspectorById(paperId);
        });
      });

      container.appendChild(card);
    });
  }
};


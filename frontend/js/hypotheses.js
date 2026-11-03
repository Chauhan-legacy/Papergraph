/**
 * PaperGraph Research Questions & Scientific Hypotheses Controller
 * Zero emojis, rigorous academic criteria, transparent epistemic boundaries.
 */
const HypothesesModule = {
  currentQuestions: [],
  activeCategory: 'all',

  async init() {
    this.bindEvents();
  },

  bindEvents() {
    const filterTabs = document.querySelectorAll('.hypo-filter-tab');
    filterTabs.forEach(tab => {
      tab.addEventListener('click', () => {
        filterTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        this.activeCategory = tab.dataset.category;
        this.renderQuestions();
      });
    });

    const btnRefresh = document.getElementById('btn-refresh-hypotheses');
    if (btnRefresh) {
      btnRefresh.addEventListener('click', () => this.loadScreen());
    }
  },

  async loadScreen() {
    const container = document.getElementById('hypotheses-cards-container');
    if (container) {
      container.innerHTML = '<p class="text-muted" style="font-size: 13px;">Analyzing literature bottlenecks, common limitations, and cross-pollination opportunities...</p>';
    }

    try {
      const questions = await API.getHypotheses(20);
      this.currentQuestions = questions || [];
      this.renderQuestions();
    } catch (err) {
      console.error('Failed to load hypotheses:', err);
      if (container) {
        container.innerHTML = `<p class="text-muted" style="font-size: 13px;">Error generating research questions: ${err.message}</p>`;
      }
    }
  },

  renderQuestions() {
    const container = document.getElementById('hypotheses-cards-container');
    if (!container) return;

    let filtered = this.currentQuestions;
    if (this.activeCategory !== 'all') {
      filtered = this.currentQuestions.filter(q => q.category.toLowerCase().includes(this.activeCategory.toLowerCase()));
    }

    if (filtered.length === 0) {
      container.innerHTML = `
        <div class="stat-card text-center" style="padding: 36px 20px;">
          <h4 style="font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 6px;">No Candidate Questions in this Category</h4>
          <p class="text-muted" style="font-size: 12px; max-width: 440px; margin: 0 auto;">
            Import and analyze additional research papers across complementary scientific domains to surface new cross-pollination opportunities.
          </p>
        </div>
      `;
      return;
    }

    container.innerHTML = filtered.map(q => {
      const suppPapersHtml = (q.supporting_papers || []).map(p => `
        <a href="#" class="hypo-paper-link" data-id="${p.id}" style="display: inline-block; font-size: 11.5px; background: var(--color-bg-base); border: 1px solid var(--border-subtle); padding: 3px 8px; border-radius: 3px; color: var(--accent-jade); text-decoration: none; margin-right: 6px; margin-bottom: 4px;">
          ${App.escapeHtml(p.title)} (${p.year || 'N/A'})
        </a>
      `).join('');

      const suppEvidenceHtml = (q.supporting_evidence || []).map(e => `
        <li style="font-size: 12px; color: var(--text-secondary); margin-bottom: 4px;">
          <strong style="color: var(--accent-jade);">&#8226;</strong> ${App.escapeHtml(e)}
        </li>
      `).join('');

      const contraEvidenceHtml = (q.contradictory_or_limiting_evidence || []).map(c => `
        <li style="font-size: 12px; color: var(--text-secondary); margin-bottom: 4px;">
          <strong style="color: var(--accent-terracotta);">&#8226;</strong> ${App.escapeHtml(c)}
        </li>
      `).join('');

      const methodsHtml = (q.possible_methodological_approaches || []).map(m => `
        <li style="font-size: 12px; color: var(--text-secondary); margin-bottom: 4px;">
          <strong>&#8226;</strong> ${App.escapeHtml(m)}
        </li>
      `).join('');

      const addlResearchHtml = (q.additional_research_required || []).map(a => `
        <li style="font-size: 11.5px; color: var(--text-muted); margin-bottom: 3px;">
          &#9633; ${App.escapeHtml(a)}
        </li>
      `).join('');

      return `
        <div class="stat-card" style="padding: 22px; margin-bottom: 20px; border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 12px;">
            <div>
              <span class="badge ${q.category === 'Methodological Cross-Pollination' ? 'badge-in-library' : 'badge-discovered'}" style="margin-bottom: 8px; font-size: 10.5px; letter-spacing: 0.04em;">
                ${App.escapeHtml(q.category)}
              </span>
              <h3 style="font-size: 16px; font-weight: 600; color: var(--text-primary); line-height: 1.4; margin-top: 4px;">
                ${App.escapeHtml(q.title)}
              </h3>
            </div>
            <span style="font-size: 11px; color: var(--text-muted); font-family: var(--font-mono); white-space: nowrap;">
              ${App.escapeHtml(q.id)}
            </span>
          </div>

          <!-- Suggested Hypothesis -->
          <div style="background: var(--color-bg-base); border-left: 3px solid var(--accent-jade); padding: 12px 14px; border-radius: var(--radius-sm); margin-bottom: 14px;">
            <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--accent-jade); margin-bottom: 4px;">Testable Scientific Hypothesis</div>
            <div style="font-size: 13px; font-weight: 500; color: var(--text-primary); line-height: 1.5;">
              "${App.escapeHtml(q.suggested_hypothesis)}"
            </div>
          </div>

          <!-- Rationale & Supporting Literature -->
          <div style="margin-bottom: 14px;">
            <div style="font-size: 12px; color: var(--text-secondary); line-height: 1.5; margin-bottom: 8px;">
              <strong>Scientific Motivation:</strong> ${App.escapeHtml(q.why_suggested)}
            </div>
            <div style="display: flex; align-items: center; flex-wrap: wrap; gap: 4px;">
              <span style="font-size: 11.5px; color: var(--text-muted); margin-right: 4px;">Supporting Papers:</span>
              ${suppPapersHtml}
            </div>
          </div>

          <!-- Evidence Grid -->
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 14px;">
            <div style="background: rgba(45, 106, 93, 0.03); border: 1px solid rgba(45, 106, 93, 0.15); border-radius: var(--radius-sm); padding: 12px;">
              <div style="font-size: 11.5px; font-weight: 600; color: var(--accent-jade); margin-bottom: 6px;">Supporting Empirical Evidence</div>
              <ul style="list-style: none; padding: 0; margin: 0;">${suppEvidenceHtml}</ul>
            </div>
            <div style="background: rgba(168, 88, 60, 0.03); border: 1px solid rgba(168, 88, 60, 0.15); border-radius: var(--radius-sm); padding: 12px;">
              <div style="font-size: 11.5px; font-weight: 600; color: var(--accent-terracotta); margin-bottom: 6px;">Contradictory / Bounding Factors</div>
              <ul style="list-style: none; padding: 0; margin: 0;">${contraEvidenceHtml}</ul>
            </div>
          </div>

          <!-- Methodological Approaches & Validation -->
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 14px;">
            <div>
              <div style="font-size: 11.5px; font-weight: 600; color: var(--text-secondary); margin-bottom: 6px;">Proposed Experimental Designs</div>
              <ul style="list-style: none; padding: 0; margin: 0;">${methodsHtml}</ul>
            </div>
            <div>
              <div style="font-size: 11.5px; font-weight: 600; color: var(--text-secondary); margin-bottom: 6px;">Additional Empirical Research Required</div>
              <ul style="list-style: none; padding: 0; margin: 0;">${addlResearchHtml}</ul>
            </div>
          </div>

          <!-- Epistemic Boundary Notice -->
          <div style="border-top: 1px dashed var(--border-subtle); padding-top: 10px; display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: var(--text-muted);">
            <div>
              <strong>Epistemic Boundary:</strong> ${App.escapeHtml(q.epistemic_boundary)}
            </div>
            <div style="font-style: italic; white-space: nowrap;">
              ${App.escapeHtml(q.confidence_and_uncertainty)}
            </div>
          </div>
        </div>
      `;
    }).join('');

    // Bind clicks to open Inspector
    container.querySelectorAll('.hypo-paper-link').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        App.openInspector(link.dataset.id);
      });
    });
  }
};

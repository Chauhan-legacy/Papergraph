/**
 * PaperGraph Cross-Paper Synthesis & Evidence Matrix Controller
 * Zero emojis, clean editorial layout, rigorous multi-paper comparison.
 */
const SynthesisModule = {
  currentMatrix: null,
  allPapers: [],
  selectedForCompare: new Set(),

  async init() {
    this.bindEvents();
  },

  bindEvents() {
    const filterInput = document.getElementById('matrix-filter-input');
    if (filterInput) {
      filterInput.addEventListener('input', (e) => {
        this.filterMatrixTable(e.target.value.toLowerCase());
      });
    }

    const btnExportCsv = document.getElementById('btn-export-matrix-csv');
    if (btnExportCsv) {
      btnExportCsv.addEventListener('click', () => this.downloadMatrix('csv'));
    }

    const btnExportMd = document.getElementById('btn-export-matrix-md');
    if (btnExportMd) {
      btnExportMd.addEventListener('click', () => this.downloadMatrix('markdown'));
    }

    const btnRunCompare = document.getElementById('btn-run-compare-action');
    if (btnRunCompare) {
      btnRunCompare.addEventListener('click', () => this.executeComparison());
    }
  },

  async loadScreen() {
    try {
      const papersData = await API.listPapers();
      this.allPapers = papersData.papers || [];
      this.renderCompareSelector();

      // Load Evidence Matrix
      await this.loadEvidenceMatrix();

      // Load Corpus Patterns
      await this.loadCorpusPatterns();
    } catch (err) {
      console.error('Failed to load synthesis screen:', err);
      App.showToast(`Error loading synthesis data: ${err.message}`, 'error');
    }
  },

  renderCompareSelector() {
    const container = document.getElementById('compare-paper-checkboxes');
    if (!container) return;

    if (this.allPapers.length === 0) {
      container.innerHTML = '<p class="text-muted" style="font-size: 12px;">No papers in library to compare.</p>';
      return;
    }

    container.innerHTML = this.allPapers.map((p, idx) => `
      <label style="display: flex; align-items: flex-start; gap: 8px; font-size: 12px; cursor: pointer; padding: 4px 0;">
        <input type="checkbox" class="compare-item-cb" data-id="${p.id}" ${idx < 3 ? 'checked' : ''} style="margin-top: 2px;">
        <div>
          <span style="font-weight: 600; color: var(--text-primary);">${App.escapeHtml(p.title)}</span>
          <span style="color: var(--text-muted); font-size: 11px;"> (${p.publication_year || 'N/A'}, ${App.escapeHtml(p.venue || 'Academic')})</span>
        </div>
      </label>
    `).join('');
  },

  async executeComparison() {
    const checkboxes = document.querySelectorAll('.compare-item-cb:checked');
    const selectedIds = Array.from(checkboxes).map(cb => cb.dataset.id);

    if (selectedIds.length < 2) {
      App.showToast('Please select at least 2 papers to compare.', 'warning');
      return;
    }

    const grid = document.getElementById('comparison-results-grid');
    if (grid) {
      grid.innerHTML = '<p class="text-muted" style="font-size: 13px;">Synthesizing cross-paper dimensions and analyzing consensus...</p>';
    }

    try {
      const cmp = await API.comparePapers(selectedIds);
      this.renderComparisonResult(cmp);
    } catch (err) {
      App.showToast(`Comparison failed: ${err.message}`, 'error');
    }
  },

  renderComparisonResult(cmp) {
    const grid = document.getElementById('comparison-results-grid');
    if (!grid) return;

    const paperIds = cmp.paper_ids;
    const dimensions = cmp.dimensions;
    const titles = cmp.paper_titles;

    const consensusHtml = (cmp.consensus_points || []).map(c => `
      <li style="margin-bottom: 6px; font-size: 12.5px; color: var(--text-primary);">
        <strong style="color: var(--accent-jade);">&#8226;</strong> ${App.escapeHtml(c)}
      </li>
    `).join('');

    const conflictsHtml = (cmp.disagreement_points || []).map(d => `
      <div style="background: var(--color-bg-base); border-left: 3px solid var(--accent-terracotta); padding: 10px 14px; margin-bottom: 10px; border-radius: var(--radius-sm);">
        <div style="font-weight: 600; font-size: 12px; color: var(--text-primary); margin-bottom: 4px;">${App.escapeHtml(d.topic)}</div>
        <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 4px;">
          <strong>${App.escapeHtml(d.paper_a)}:</strong> ${App.escapeHtml(d.claim_a)}
        </div>
        <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 6px;">
          <strong>${App.escapeHtml(d.paper_b)}:</strong> ${App.escapeHtml(d.claim_b)}
        </div>
        <div style="font-size: 11.5px; color: var(--text-muted); font-style: italic;">
          Contextual Rationale: ${App.escapeHtml(d.plausible_reason)}
        </div>
      </div>
    `).join('');

    const colsHeader = paperIds.map(pid => `
      <th style="min-width: 220px; font-size: 12px; font-weight: 600; color: var(--text-primary);">
        ${App.escapeHtml(titles[pid] || pid)}
      </th>
    `).join('');

    const renderRow = (dimensionName, key) => `
      <tr>
        <td style="font-weight: 600; font-size: 11.5px; color: var(--text-secondary); background: var(--color-bg-base); width: 140px; text-transform: uppercase; letter-spacing: 0.04em;">
          ${dimensionName}
        </td>
        ${paperIds.map(pid => `
          <td style="font-size: 12px; line-height: 1.5; color: var(--text-primary); vertical-align: top;">
            ${App.escapeHtml(dimensions[pid]?.[key] || 'Not specified')}
          </td>
        `).join('')}
      </tr>
    `;

    grid.innerHTML = `
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px;">
        <div class="stat-card" style="padding: 18px;">
          <h4 style="font-size: 13px; font-weight: 600; margin-bottom: 10px; color: var(--accent-jade);">Empirical Consensus Across Selected Literature</h4>
          <ul style="list-style: none; padding: 0; margin: 0;">${consensusHtml}</ul>
        </div>
        <div class="stat-card" style="padding: 18px;">
          <h4 style="font-size: 13px; font-weight: 600; margin-bottom: 10px; color: var(--accent-terracotta);">Methodological Divergences & Comparative Context</h4>
          <div>${conflictsHtml || '<p class="text-muted" style="font-size: 12px;">No major empirical discrepancies detected across selected papers.</p>'}</div>
        </div>
      </div>

      <div style="overflow-x: auto; border: 1px solid var(--border-subtle); border-radius: var(--radius-sm);">
        <table class="desk-table" style="width: 100%;">
          <thead>
            <tr>
              <th style="width: 140px;">Dimension</th>
              ${colsHeader}
            </tr>
          </thead>
          <tbody>
            ${renderRow('Research Objective', 'objective')}
            ${renderRow('Methodology', 'methodology')}
            ${renderRow('Datasets & Scale', 'dataset')}
            ${renderRow('Experimental Setup', 'setup')}
            ${renderRow('Main Observations', 'results')}
            ${renderRow('Assumptions', 'assumptions')}
            ${renderRow('Critical Limitations', 'limitations')}
            ${renderRow('Contributions', 'contributions')}
            ${renderRow('Future Directions', 'future_directions')}
          </tbody>
        </table>
      </div>
    `;
  },

  async loadEvidenceMatrix() {
    try {
      const res = await API.getEvidenceMatrix();
      this.currentMatrix = res;
      this.renderMatrixRows(res.rows || []);
      const countLabel = document.getElementById('matrix-paper-count-badge');
      if (countLabel) {
        countLabel.textContent = `${res.total_papers || 0} Papers Synthesized`;
      }
    } catch (err) {
      console.error('Failed to load evidence matrix:', err);
    }
  },

  renderMatrixRows(rows) {
    const tbody = document.getElementById('matrix-table-body');
    if (!tbody) return;

    if (rows.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted" style="padding: 24px;">No papers matched the evidence criteria.</td></tr>';
      return;
    }

    tbody.innerHTML = rows.map(r => `
      <tr>
        <td style="font-weight: 600; font-size: 12px; color: var(--text-primary); max-width: 220px;">
          <a href="#" class="matrix-paper-link" data-id="${r.paper_id}" style="color: var(--text-primary); text-decoration: none;">
            ${App.escapeHtml(r.title)}
          </a>
          <div style="font-size: 11px; color: var(--text-muted); font-weight: normal;">${r.year || 'N/A'} &#8226; ${App.escapeHtml(r.authors)}</div>
        </td>
        <td style="font-size: 12px; color: var(--text-secondary); max-width: 180px;">
          ${App.escapeHtml(r.method)}
        </td>
        <td style="font-size: 12px; color: var(--text-secondary); max-width: 140px;">
          ${App.escapeHtml(r.dataset)}
        </td>
        <td style="font-size: 12px; color: var(--text-primary); max-width: 220px;">
          ${App.escapeHtml(r.main_finding)}
        </td>
        <td style="font-size: 11.5px; color: var(--text-muted); max-width: 180px;">
          ${App.escapeHtml(r.key_limitation)}
        </td>
        <td>
          <span class="badge ${r.epistemic_grade === 'High' ? 'badge-in-library' : 'badge-discovered'}" style="font-size: 10.5px;">
            ${r.epistemic_grade}
          </span>
        </td>
        <td style="font-size: 11.5px; color: var(--text-muted); text-align: right;">
          ${(r.confidence_score * 100).toFixed(0)}%
        </td>
      </tr>
    `).join('');

    // Bind click to open Inspector
    tbody.querySelectorAll('.matrix-paper-link').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const pid = link.dataset.id;
        App.openInspector(pid);
      });
    });
  },

  filterMatrixTable(query) {
    if (!this.currentMatrix || !this.currentMatrix.rows) return;
    if (!query) {
      this.renderMatrixRows(this.currentMatrix.rows);
      return;
    }
    const filtered = this.currentMatrix.rows.filter(r =>
      r.title.toLowerCase().includes(query) ||
      r.method.toLowerCase().includes(query) ||
      r.dataset.toLowerCase().includes(query) ||
      r.main_finding.toLowerCase().includes(query) ||
      r.authors.toLowerCase().includes(query)
    );
    this.renderMatrixRows(filtered);
  },

  downloadMatrix(format) {
    window.location.href = `/api/synthesis/matrix/export?format_type=${format}`;
  },

  async loadCorpusPatterns() {
    try {
      const patterns = await API.getCorpusPatterns();
      const container = document.getElementById('corpus-patterns-container');
      if (!container) return;

      const methodsHtml = (patterns.repeated_methods || []).map(m => `
        <div style="display: flex; justify-content: space-between; font-size: 12px; padding: 3px 0;">
          <span style="font-weight: 500; color: var(--text-primary);">${App.escapeHtml(m.method)}</span>
          <span class="badge" style="font-size: 10px;">${m.count} papers</span>
        </div>
      `).join('') || '<div class="text-muted" style="font-size: 12px;">No recurring methods indexed yet.</div>';

      const datasetsHtml = (patterns.recurring_datasets || []).map(d => `
        <div style="display: flex; justify-content: space-between; font-size: 12px; padding: 3px 0;">
          <span style="font-weight: 500; color: var(--text-primary);">${App.escapeHtml(d.dataset)}</span>
          <span class="badge" style="font-size: 10px;">${d.count} papers</span>
        </div>
      `).join('') || '<div class="text-muted" style="font-size: 12px;">No recurring datasets indexed yet.</div>';

      const limitsHtml = (patterns.common_limitations || []).map(l => `
        <div style="font-size: 11.5px; color: var(--text-secondary); padding: 3px 0; border-bottom: 1px dashed var(--border-subtle);">
          &#8226; ${App.escapeHtml(l.limitation)} <span style="color: var(--text-muted);">(${l.count})</span>
        </div>
      `).join('') || '<div class="text-muted" style="font-size: 12px;">No common limitations indexed yet.</div>';

      container.innerHTML = `
        <div class="stat-card" style="padding: 16px;">
          <h4 style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); margin-bottom: 10px;">Dominant Methods</h4>
          <div>${methodsHtml}</div>
        </div>
        <div class="stat-card" style="padding: 16px;">
          <h4 style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); margin-bottom: 10px;">Benchmark Datasets</h4>
          <div>${datasetsHtml}</div>
        </div>
        <div class="stat-card" style="padding: 16px;">
          <h4 style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); margin-bottom: 10px;">Common Literature Constraints</h4>
          <div>${limitsHtml}</div>
        </div>
      `;
    } catch (err) {
      console.error('Failed to load corpus patterns:', err);
    }
  }
};


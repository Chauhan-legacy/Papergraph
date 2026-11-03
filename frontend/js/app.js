/**
 * PaperGraph Application Orchestrator
 */
const App = {
  activeScreen: 'overview',
  selectedPaper: null,

  async init() {
    this.bindNavigation();
    this.bindInspector();
    this.bindModals();

    // Initialize modules
    SearchModule.init();
    LibraryModule.init();
    FolderImportModule.init();
    AnalyzerModule.init();
    GraphModule.init();
    SynthesisModule.init();
    HypothesesModule.init();
    ReviewModule.init();
    IntersectionsModule.init();
    TrendsModule.init();
    SettingsModule.init();

    // Check workspace status
    const status = await WorkspaceModule.init();
    if (!status) {
      WorkspaceModule.showModal();
    } else {
      this.switchScreen('overview');
    }
  },

  bindNavigation() {
    document.querySelectorAll('.nav-item').forEach((item) => {
      item.addEventListener('click', () => {
        const screen = item.dataset.screen;
        if (screen) {
          this.switchScreen(screen);
        }
      });
    });

    // Quick action buttons on overview screen
    const quickSearchBtn = document.getElementById('btn-quick-search');
    if (quickSearchBtn) quickSearchBtn.addEventListener('click', () => this.switchScreen('search'));

    const quickAnalyzeBtn = document.getElementById('btn-quick-analyze');
    if (quickAnalyzeBtn) quickAnalyzeBtn.addEventListener('click', () => this.switchScreen('analyzer'));

    const quickGraphBtn = document.getElementById('btn-quick-graph');
    if (quickGraphBtn) quickGraphBtn.addEventListener('click', () => this.switchScreen('graph'));

    // Sidebar workspace badge click to manage workspace
    const wsBadge = document.getElementById('sidebar-ws-badge');
    if (wsBadge) {
      wsBadge.style.cursor = 'pointer';
      wsBadge.title = 'Click to switch or create workspace';
      wsBadge.addEventListener('click', () => WorkspaceModule.showModal());
    }
  },

  switchScreen(screenName) {
    this.activeScreen = screenName;

    // Update navigation active state
    document.querySelectorAll('.nav-item').forEach((item) => {
      if (item.dataset.screen === screenName) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });

    // Update visible screen container
    document.querySelectorAll('.view-screen').forEach((view) => {
      if (view.id === `screen-${screenName}`) {
        view.classList.add('active');
      } else {
        view.classList.remove('active');
      }
    });

    // Update topbar breadcrumb text
    const breadcrumbEl = document.getElementById('topbar-breadcrumb-current');
    if (breadcrumbEl) {
      const titles = {
        overview: 'Overview',
        search: 'Literature Search',
        library: 'Research Library',
        analyzer: 'Paper Analyzer',
        graph: 'Knowledge Graph',
        synthesis: 'Cross-Paper Synthesis',
        hypotheses: 'Questions & Hypotheses',
        review: 'Literature Review Studio',
        intersections: 'Research Intersections',
        trends: 'Corpus Trends',
        settings: 'Settings'
      };
      breadcrumbEl.textContent = titles[screenName] || 'Overview';
    }

    // Screen-specific triggers
    if (screenName === 'library') {
      LibraryModule.loadPapers();
    } else if (screenName === 'graph') {
      setTimeout(() => GraphModule.loadGraph(), 100);
    } else if (screenName === 'synthesis') {
      SynthesisModule.loadScreen();
    } else if (screenName === 'hypotheses') {
      HypothesesModule.loadScreen();
    } else if (screenName === 'review') {
      ReviewModule.loadScreen();
    } else if (screenName === 'intersections') {
      IntersectionsModule.loadIntersections();
    } else if (screenName === 'trends') {
      TrendsModule.loadTrends();
    } else if (screenName === 'settings') {
      SettingsModule.loadBackupsList();
    } else if (screenName === 'overview') {
      WorkspaceModule.refreshStatus();
    }
  },

  bindInspector() {
    const closeBtn = document.getElementById('btn-close-inspector');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.closeInspector());
    }

    const toggleBtn = document.getElementById('btn-inspector-toggle');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => {
        const panel = document.getElementById('inspector-panel');
        if (panel) {
          panel.classList.toggle('collapsed');
        }
      });
    }

    // Inspector Tab Switching
    document.querySelectorAll('.inspector-tab-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.inspector-tab-btn').forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');

        const tab = btn.dataset.tab;
        document.querySelectorAll('.inspector-tab-content').forEach((c) => {
          if (c.id === `inspector-tab-${tab}`) {
            c.style.display = 'block';
          } else {
            c.style.display = 'none';
          }
        });
      });
    });

    // Save Notes Button
    const saveNotesBtn = document.getElementById('btn-save-notes');
    if (saveNotesBtn) {
      saveNotesBtn.addEventListener('click', async () => {
        if (!this.selectedPaper) return;
        const textarea = document.getElementById('inspector-notes-input');
        const notes = textarea ? textarea.value : '';
        try {
          await API.saveNotes(this.selectedPaper.id, notes);
          this.showToast('Notes saved successfully!');
        } catch (err) {
          this.showToast(`Error saving notes: ${err.message}`, 'error');
        }
      });
    }
  },

  bindModals() {
    // Workspace Setup Modal Form
    const wsForm = document.getElementById('form-create-workspace');
    if (wsForm) {
      wsForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('modal-ws-name').value.trim();
        const path = document.getElementById('modal-ws-path').value.trim();
        await WorkspaceModule.createNewWorkspace(name, path || null);
      });
    }

    const cancelWsBtn = document.getElementById('btn-cancel-workspace-modal');
    if (cancelWsBtn) {
      cancelWsBtn.addEventListener('click', () => WorkspaceModule.closeModal());
    }

    // Export Modal Form
    const exportForm = document.getElementById('form-export-data');
    if (exportForm) {
      exportForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const format = document.getElementById('export-format-select').value;
        try {
          const res = await API.exportResearch(format);
          this.showToast(`Export generated: ${res.filename}`);
          
          // Trigger browser download
          const blob = new Blob([res.content], { type: res.mime_type || 'text/plain' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = res.filename;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);

          document.getElementById('export-modal').classList.remove('active');
        } catch (err) {
          this.showToast(`Export error: ${err.message}`, 'error');
        }
      });
    }

    const cancelExportBtn = document.getElementById('btn-cancel-export-modal');
    if (cancelExportBtn) {
      cancelExportBtn.addEventListener('click', () => {
        document.getElementById('export-modal').classList.remove('active');
      });
    }
  },

  async openPaperInspectorById(paperId) {
    try {
      const detail = await API.getPaperDetail(paperId);
      if (detail && detail.metadata) {
        this.openPaperInspector(detail.metadata, detail);
      }
    } catch (err) {
      this.showToast(`Could not open paper: ${err.message}`, 'error');
    }
  },

  openPaperInspector(paper, detail = null) {
    this.selectedPaper = paper;
    const panel = document.getElementById('inspector-panel');
    if (!panel) return;

    panel.classList.remove('collapsed');

    // Title & Authors
    const titleEl = document.getElementById('inspector-title');
    if (titleEl) titleEl.textContent = paper.title || 'Untitled';

    const authors = (paper.authors || [])
      .map((a) => (typeof a === 'object' ? a.name : a))
      .join(', ');
    const authorsEl = document.getElementById('inspector-authors');
    if (authorsEl) authorsEl.textContent = authors || 'Not listed';

    const venueEl = document.getElementById('inspector-venue');
    if (venueEl) venueEl.textContent = `${paper.venue || 'Academic Venue'} (${paper.publication_year || 'N/A'})`;

    const doiEl = document.getElementById('inspector-doi');
    if (doiEl) {
      if (paper.doi) {
        doiEl.innerHTML = `<a href="https://doi.org/${paper.doi.replace('https://doi.org/', '')}" target="_blank" style="color: var(--color-forest); text-decoration: underline;">${paper.doi}</a>`;
      } else {
        doiEl.textContent = 'None';
      }
    }

    // Collections
    const colContainer = document.getElementById('inspector-collections-list');
    if (colContainer) {
      const cols = paper.collections || [];
      if (cols.length > 0) {
        colContainer.innerHTML = cols.map(c => `<span class="badge-tag peach">${c}</span>`).join(' ');
      } else {
        colContainer.innerHTML = `<span class="badge-tag" style="font-size: 10px; color: var(--color-text-faint);">General Library</span>`;
      }
    }

    // Abstract
    const abstractEl = document.getElementById('inspector-abstract-text');
    if (abstractEl) {
      abstractEl.textContent = (detail && detail.abstract) || paper.abstract || 'Abstract unavailable.';
    }

    // Summary
    const summaryEl = document.getElementById('inspector-summary-text');
    if (summaryEl) {
      const summaryContent = (detail && detail.summary) || 'Run the Paper Analyzer to generate the 8-section structured summary.';
      summaryEl.innerHTML = summaryContent.replace(/\n/g, '<br>');
    }

    // Keywords & NLP
    const kwContainer = document.getElementById('inspector-keywords-list');
    if (kwContainer) {
      const kw = (detail && detail.analysis && detail.analysis.keywords) || [];
      if (kw.length > 0) {
        kwContainer.innerHTML = kw.map((k) => {
          const kwStr = typeof k === 'object' ? k.keyword : k;
          return `<span class="badge-tag accent">${kwStr}</span>`;
        }).join(' ');
      } else {
        kwContainer.innerHTML = `<span style="color: var(--color-text-faint); font-size: 12px;">No keywords extracted yet.</span>`;
      }
    }

    // Notes
    const notesInput = document.getElementById('inspector-notes-input');
    if (notesInput) {
      notesInput.value = (detail && detail.notes) || '';
    }

    // Load and Render Professor Analysis & Claims
    this.loadProfessorAnalysisForInspector(paper.id);

    // Default to summary tab if available, else overview tab
    document.querySelector('.inspector-tab-btn[data-tab="overview"]').click();
  },

  async loadProfessorAnalysisForInspector(paperId) {
    const profContainer = document.getElementById('inspector-professor-content');
    const claimsContainer = document.getElementById('inspector-claims-table-body');
    if (!profContainer) return;

    profContainer.innerHTML = '<p class="text-muted" style="font-size: 12px; padding: 12px;">Loading academic analysis...</p>';
    if (claimsContainer) {
      claimsContainer.innerHTML = '<tr><td colspan="4" class="text-muted text-center" style="font-size: 11.5px; padding: 12px;">Loading claims...</td></tr>';
    }

    try {
      const prof = await API.getProfessorAnalysis(paperId);
      const pe = prof.professor_explanation || {};
      const rp = prof.research_problem || {};
      const meth = prof.methodology || {};
      const res = prof.results || {};
      const ce = prof.critical_evaluation || {};
      const ss = prof.scientific_significance || {};

      profContainer.innerHTML = `
        <div style="margin-bottom: 16px; border-bottom: 1px solid var(--border-subtle); padding-bottom: 12px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span class="badge badge-in-library" style="font-size: 10px;">${this.escapeHtml(prof.scope || 'Abstract-only')}</span>
            <span style="font-size: 10.5px; color: var(--text-muted);">${this.escapeHtml(prof.model_used || 'Local Engine')}</span>
          </div>
          <div style="font-weight: 600; font-size: 12px; color: var(--accent-jade); margin-bottom: 4px;">Professor's Pedagogical Explanation</div>
          <div style="background: var(--color-bg-base); border-left: 3px solid var(--accent-jade); padding: 8px 12px; border-radius: var(--radius-sm); font-size: 12.5px; line-height: 1.5; color: var(--text-primary); margin-bottom: 8px;">
            <em>"${this.escapeHtml(pe.pedagogical_intuition || pe.core_concept || '')}"</em>
          </div>
          <div style="font-size: 12px; color: var(--text-secondary); line-height: 1.5; margin-bottom: 6px;">
            <strong>Technical Approach:</strong> ${this.escapeHtml(pe.technical_approach || '')}
          </div>
          <div style="font-size: 11.5px; color: var(--text-muted); line-height: 1.5; margin-bottom: 6px;">
            <strong>Mathematical Formalism:</strong> ${this.escapeHtml(pe.mathematical_formalism || '')}
          </div>
          <div style="font-size: 11.5px; color: var(--accent-terracotta); line-height: 1.5;">
            <strong>What Could Go Wrong:</strong> ${this.escapeHtml(pe.potential_pitfalls || '')}
          </div>
        </div>

        <div style="margin-bottom: 12px;">
          <div style="font-weight: 600; font-size: 11.5px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 4px;">Research Problem</div>
          <div style="font-size: 12px; line-height: 1.5; color: var(--text-primary);">${this.escapeHtml(rp.exact_problem || '')}</div>
        </div>

        <div style="margin-bottom: 12px;">
          <div style="font-weight: 600; font-size: 11.5px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 4px;">Methodology & Experimental Design</div>
          <div style="font-size: 12px; line-height: 1.5; color: var(--text-primary);">${this.escapeHtml(meth.intuitive_explanation || '')}</div>
          <div style="font-size: 11.5px; color: var(--text-muted); margin-top: 3px;"><strong>Dataset / Variables:</strong> ${this.escapeHtml(meth.datasets_and_variables || 'Standard benchmark')}</div>
        </div>

        <div style="margin-bottom: 12px;">
          <div style="font-weight: 600; font-size: 11.5px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 4px;">Empirical Results & Rigor</div>
          <div style="font-size: 12px; line-height: 1.5; color: var(--text-primary);">${this.escapeHtml(res.actual_observations || '')}</div>
          <div style="font-size: 11.5px; color: var(--text-muted); margin-top: 3px;"><strong>Distinction:</strong> ${this.escapeHtml(res.results_vs_interpretations || '')}</div>
        </div>

        <div style="margin-bottom: 12px;">
          <div style="font-weight: 600; font-size: 11.5px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 4px;">Critical Evaluation & Confounders</div>
          <div style="font-size: 12px; line-height: 1.5; color: var(--text-primary);">${this.escapeHtml(ce.limitations || '')}</div>
          <div style="font-size: 11.5px; color: var(--text-muted); margin-top: 3px;"><strong>Reproducibility:</strong> ${this.escapeHtml(ce.reproducibility_threats || '')}</div>
        </div>

        <div>
          <div style="font-weight: 600; font-size: 11.5px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 4px;">Scientific Significance</div>
          <div style="font-size: 12px; line-height: 1.5; color: var(--text-primary);">${this.escapeHtml(ss.primary_contributions || '')}</div>
        </div>
      `;

      // Render Claims Table
      if (claimsContainer) {
        const claims = prof.claims || [];
        if (claims.length === 0) {
          claimsContainer.innerHTML = '<tr><td colspan="4" class="text-muted text-center" style="font-size: 11.5px; padding: 12px;">No claims indexed.</td></tr>';
        } else {
          claimsContainer.innerHTML = claims.map(c => `
            <tr>
              <td style="font-size: 10.5px; font-weight: 600; text-transform: uppercase; color: var(--text-muted);">${this.escapeHtml(c.category)}</td>
              <td><span class="badge ${c.epistemic_status === 'REPORTED' ? 'badge-in-library' : (c.epistemic_status === 'DERIVED' ? 'badge-discovered' : 'badge-general')}" style="font-size: 9.5px;">${this.escapeHtml(c.epistemic_status)}</span></td>
              <td style="font-size: 11.5px; color: var(--text-primary); line-height: 1.4;">${this.escapeHtml(c.claim_text)}</td>
              <td style="font-size: 10.5px; color: var(--text-muted); text-align: right;">${(c.confidence * 100).toFixed(0)}%</td>
            </tr>
          `).join('');
        }
      }
    } catch (err) {
      console.warn('Could not load professor analysis for inspector:', err);
      profContainer.innerHTML = `<p class="text-muted" style="font-size: 12px; padding: 12px;">Analysis not yet generated. Run the Paper Analyzer pipeline to create it.</p>`;
    }
  },

  openInspector(paperId) {
    this.openPaperInspectorById(paperId);
  },

  escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  },

  closeInspector() {
    const panel = document.getElementById('inspector-panel');
    if (panel) panel.classList.add('collapsed');
    this.selectedPaper = null;
  },

  showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }
};

window.addEventListener('DOMContentLoaded', () => {
  App.init();
});


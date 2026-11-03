/**
 * PaperGraph Literature Review Studio Controller
 * Generates evidence-backed literature review outlines and drafts with academic citations.
 */
const ReviewModule = {
  currentReview: null,

  async init() {
    this.bindEvents();
  },

  bindEvents() {
    const btnGenerate = document.getElementById('btn-generate-review');
    if (btnGenerate) {
      btnGenerate.addEventListener('click', () => this.generateReview());
    }

    const btnDownloadMd = document.getElementById('btn-download-review-md');
    if (btnDownloadMd) {
      btnDownloadMd.addEventListener('click', () => this.downloadDraft());
    }

    const btnDownloadBib = document.getElementById('btn-download-review-bib');
    if (btnDownloadBib) {
      btnDownloadBib.addEventListener('click', () => this.downloadBibtex());
    }

    const btnCopyMd = document.getElementById('btn-copy-review-md');
    if (btnCopyMd) {
      btnCopyMd.addEventListener('click', () => this.copyDraft());
    }
  },

  async loadScreen() {
    // Populate collection options if needed
    try {
      const collections = await API.listCollections();
      const select = document.getElementById('review-collection-select');
      if (select) {
        select.innerHTML = '<option value="">(All Library Literature)</option>' +
          collections.map(c => `<option value="${c.id}">${App.escapeHtml(c.name)} (${c.paper_ids.length} papers)</option>`).join('');
      }
    } catch (err) {
      console.error('Error loading review collections:', err);
    }
  },

  async generateReview() {
    const topicInput = document.getElementById('review-topic-input');
    const topic = topicInput ? topicInput.value.trim() : '';

    const container = document.getElementById('review-output-container');
    if (container) {
      container.innerHTML = '<p class="text-muted" style="font-size: 13px; padding: 24px 0;">Synthesizing literature outline, clustering themes, and formulating evidence-backed academic draft...</p>';
    }

    try {
      const review = await API.generateLiteratureReview(topic);
      this.currentReview = review;
      this.renderReview(review);
    } catch (err) {
      console.error('Review generation failed:', err);
      if (container) {
        container.innerHTML = `<p class="text-muted" style="font-size: 13px;">Error synthesizing literature review: ${err.message}</p>`;
      }
    }
  },

  renderReview(review) {
    const container = document.getElementById('review-output-container');
    if (!container) return;

    const actionButtons = document.getElementById('review-action-buttons');
    if (actionButtons) {
      actionButtons.style.display = 'flex';
    }

    const themesHtml = (review.thematic_groups || []).map(t => `
      <div style="background: var(--color-bg-base); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); padding: 10px 14px;">
        <div style="font-weight: 600; font-size: 12px; color: var(--accent-jade); margin-bottom: 4px;">
          ${App.escapeHtml(t.theme)}
        </div>
        <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 6px;">${t.papers_count} papers grouped</div>
        <div style="font-size: 11.5px; color: var(--text-secondary);">
          ${(t.papers || []).map(p => `<span style="display: inline-block; margin-right: 6px;">${App.escapeHtml(p.citation)}</span>`).join('')}
        </div>
      </div>
    `).join('');

    const outlineHtml = (review.outline || []).map(o => `
      <div style="margin-bottom: 8px;">
        <div style="font-weight: 600; font-size: 12.5px; color: var(--text-primary);">${App.escapeHtml(o.section)}</div>
        <ul style="list-style: none; padding-left: 14px; margin: 4px 0 0 0;">
          ${(o.subsections || []).map(sub => `<li style="font-size: 11.5px; color: var(--text-secondary); margin-bottom: 2px;">&#8226; ${App.escapeHtml(sub)}</li>`).join('')}
        </ul>
      </div>
    `).join('');

    container.innerHTML = `
      <!-- Thematic Clusters & Outline -->
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px;">
        <div class="stat-card" style="padding: 18px;">
          <h4 style="font-size: 13px; font-weight: 600; color: var(--text-primary); margin-bottom: 12px;">Identified Thematic Clusters</h4>
          <div style="display: flex; flex-direction: column; gap: 8px;">${themesHtml || '<p class="text-muted" style="font-size: 12px;">No distinct thematic clusters identified.</p>'}</div>
        </div>
        <div class="stat-card" style="padding: 18px;">
          <h4 style="font-size: 13px; font-weight: 600; color: var(--text-primary); margin-bottom: 12px;">Academic Outline Structure</h4>
          <div>${outlineHtml}</div>
        </div>
      </div>

      <!-- Synthesized Draft Panel -->
      <div class="stat-card" style="padding: 24px; border: 1px solid var(--border-subtle); border-radius: var(--radius-sm);">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-subtle); padding-bottom: 12px; margin-bottom: 18px;">
          <h3 style="font-size: 15px; font-weight: 600; color: var(--text-primary);">Synthesized Academic Literature Review Draft</h3>
          <span class="badge badge-in-library" style="font-size: 11px;">Evidence-Backed</span>
        </div>
        <div id="review-markdown-rendered" style="font-size: 13px; line-height: 1.7; color: var(--text-primary); white-space: pre-wrap; font-family: var(--font-sans); max-height: 520px; overflow-y: auto; padding: 12px; background: var(--color-bg-base); border-radius: var(--radius-sm);">
${App.escapeHtml(review.markdown_draft)}
        </div>
      </div>
    `;
  },

  downloadDraft() {
    if (!this.currentReview || !this.currentReview.markdown_draft) return;
    const blob = new Blob([this.currentReview.markdown_draft], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `literature_review_${Date.now()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    App.showToast('Literature review draft downloaded.', 'success');
  },

  downloadBibtex() {
    if (!this.currentReview || !this.currentReview.bibtex_entries) return;
    const blob = new Blob([this.currentReview.bibtex_entries], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `references_${Date.now()}.bib`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    App.showToast('BibTeX references downloaded.', 'success');
  },

  copyDraft() {
    if (!this.currentReview || !this.currentReview.markdown_draft) return;
    navigator.clipboard.writeText(this.currentReview.markdown_draft).then(() => {
      App.showToast('Literature review draft copied to clipboard.', 'success');
    }).catch(err => {
      App.showToast('Failed to copy to clipboard.', 'error');
    });
  }
};

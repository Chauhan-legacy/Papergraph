/**
 * Research Trends Controller
 * Renders temporal publication charts, topic growth, and scientific domain distributions.
 */
const TrendsModule = {
  trendsData: null,

  init() {
    this.bindEvents();
  },

  bindEvents() {
    const refreshBtn = document.getElementById("btn-refresh-trends");
    if (refreshBtn) refreshBtn.addEventListener("click", () => this.loadTrends());
  },

  async loadTrends() {
    const container = document.getElementById("trends-container");
    if (!container) return;

    try {
      const data = await API.getTrends();
      this.trendsData = data;
      this.render(data);
    } catch (err) {
      console.error("Trends error:", err);
      App.showToast(`Error loading trends: ${err.message}`, "error");
    }
  },

  render(data) {
    const container = document.getElementById("trends-container");
    if (!container) return;

    if (!data || data.total_analyzed === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
              <polyline points="17 6 23 6 23 12"></polyline>
            </svg>
          </div>
          <h3>Corpus Empty</h3>
          <p>Import papers into your research library to analyze publication trends and topic distributions.</p>
        </div>
      `;
      return;
    }

    // Warnings if small corpus
    const warningHtml = (data.warnings || []).map((w) => `
      <div style="background: #FDF9F3; border: 1px solid #EFE0CC; border-left: 3px solid var(--brand-peach-border); padding: 10px 14px; font-size: 12.5px; color: #5C4532; margin-bottom: 20px; border-radius: var(--radius-sm); display: flex; align-items: center; gap: 8px;">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink: 0;">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
          <line x1="12" y1="9" x2="12" y2="13"></line>
          <line x1="12" y1="17" x2="12.01" y2="17"></line>
        </svg>
        <span><strong>Notice:</strong> ${w}</span>
      </div>
    `).join("");

    // 1. Publications by Year (Horizontal / Vertical CSS Bar Chart)
    const pubYears = data.publications_by_year || {};
    const years = Object.keys(pubYears).sort();
    const maxPub = Math.max(...Object.values(pubYears), 1);

    const yearBarsHtml = years.map((y) => {
      const count = pubYears[y];
      const pct = Math.round((count / maxPub) * 100);
      return `
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
          <span style="width: 50px; font-size: 12px; font-weight: 600; color: var(--color-text-muted);">${y}</span>
          <div style="flex: 1; background: var(--color-mist-alt); height: 20px; border-radius: 4px; overflow: hidden;">
            <div style="width: ${pct}%; background: var(--color-sage); height: 100%; border-radius: 4px; transition: width 0.3s ease;"></div>
          </div>
          <span style="width: 35px; text-align: right; font-size: 12px; font-weight: 600;">${count}</span>
        </div>
      `;
    }).join("");

    // 2. Top Topics
    const topTopics = data.top_topics || [];
    const maxTopic = topTopics.length > 0 ? Math.max(...topTopics.map((t) => t.count), 1) : 1;
    const topicBarsHtml = topTopics.map((t) => {
      const pct = Math.round((t.count / maxTopic) * 100);
      return `
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
          <span style="width: 140px; font-size: 12px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${t.topic}">${t.topic}</span>
          <div style="flex: 1; background: var(--color-mist-alt); height: 16px; border-radius: 4px; overflow: hidden;">
            <div style="width: ${pct}%; background: var(--color-teal); height: 100%; border-radius: 4px;"></div>
          </div>
          <span style="width: 25px; text-align: right; font-size: 12px; font-weight: 600;">${t.count}</span>
        </div>
      `;
    }).join("");

    // 3. Domain Distributions
    const domains = data.domain_distributions || [];
    const maxDomain = domains.length > 0 ? Math.max(...domains.map((d) => d.count), 1) : 1;
    const domainBarsHtml = domains.map((d) => {
      const pct = Math.round((d.count / maxDomain) * 100);
      return `
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
          <span style="width: 150px; font-size: 12px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${d.domain}">${d.domain}</span>
          <div style="flex: 1; background: var(--color-mist-alt); height: 16px; border-radius: 4px; overflow: hidden;">
            <div style="width: ${pct}%; background: var(--color-forest); height: 100%; border-radius: 4px;"></div>
          </div>
          <span style="width: 25px; text-align: right; font-size: 12px; font-weight: 600;">${d.count}</span>
        </div>
      `;
    }).join("");

    // 4. Keywords cloud / chips
    const kwHtml = (data.top_keywords || []).map((k) => `
      <span class="badge-tag peach" style="font-size: 12px; padding: 4px 10px;">
        ${k.keyword} <strong style="margin-left: 4px; opacity: 0.7;">(${k.count})</strong>
      </span>
    `).join("");

    container.innerHTML = `
      ${warningHtml}
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 20px;">
        <div class="stat-card" style="padding: 20px;">
          <h4 style="font-size: 14px; font-weight: 600; margin-bottom: 14px; color: var(--color-text-main);">
            Publications by Chronological Year
          </h4>
          ${yearBarsHtml || "<p style='color: var(--color-text-muted); font-size: 12px;'>No year data available.</p>"}
        </div>

        <div class="stat-card" style="padding: 20px;">
          <h4 style="font-size: 14px; font-weight: 600; margin-bottom: 14px; color: var(--color-text-main);">
            Top Scientific Domains Represented
          </h4>
          ${domainBarsHtml || "<p style='color: var(--color-text-muted); font-size: 12px;'>No domain data available.</p>"}
        </div>

        <div class="stat-card" style="padding: 20px;">
          <h4 style="font-size: 14px; font-weight: 600; margin-bottom: 14px; color: var(--color-text-main);">
            Leading Research Topics & Methodologies
          </h4>
          ${topicBarsHtml || "<p style='color: var(--color-text-muted); font-size: 12px;'>No topic data available.</p>"}
        </div>

        <div class="stat-card" style="padding: 20px;">
          <h4 style="font-size: 14px; font-weight: 600; margin-bottom: 14px; color: var(--color-text-main);">
            Prominent Literature Keywords
          </h4>
          <div style="display: flex; flex-wrap: wrap; gap: 8px;">
            ${kwHtml || "<p style='color: var(--color-text-muted); font-size: 12px;'>No keywords extracted yet.</p>"}
          </div>
        </div>
      </div>
    `;
  }
};


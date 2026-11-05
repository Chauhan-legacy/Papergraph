/**
 * Research Engineering Tools Controller
 * Handles Literature Copilot, Benchmark Matrix, and Contradiction Radar.
 */
const ToolsModule = {
  init() {
    this.bindCopilot();
    this.bindBenchmarks();
    this.bindGaps();
  },

  // ==========================================
  // 1. LITERATURE COPILOT
  // ==========================================
  bindCopilot() {
    const askBtn = document.getElementById("btn-copilot-ask");
    const input = document.getElementById("copilot-input");

    if (askBtn && input) {
      const runQuery = () => {
        const query = input.value.trim();
        if (query) this.askCopilot(query);
      };

      askBtn.addEventListener("click", runQuery);
      input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") runQuery();
      });
    }

    document.querySelectorAll(".copilot-chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        if (input) {
          input.value = chip.textContent.trim();
          this.askCopilot(chip.textContent.trim());
        }
      });
    });
  },

  async askCopilot(query) {
    const container = document.getElementById("copilot-results-container");
    if (!container) return;

    container.innerHTML = `
      <div style="padding: 32px; text-align: center; color: var(--text-secondary); background: var(--color-bg-surface); border: 1px solid var(--border-color); border-radius: var(--radius-sm);">
        <p style="font-size: 13px; font-weight: 500;">Synthesizing evidence across active workspace literature...</p>
      </div>
    `;

    try {
      const res = await API.askLiterature(query);
      const confPct = Math.round((res.confidence || 0.8) * 100);

      const sourcesHtml = (res.sources || []).map((s) => `
        <div style="background: var(--color-bg-base); border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 12px 14px; margin-top: 8px;">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 10px;">
            <strong style="font-size: 12.5px; color: var(--text-primary);">${App.escapeHtml(s.title)}</strong>
            <span class="badge" style="font-family: var(--font-mono); font-size: 10px;">Relevance ${(s.score * 100).toFixed(0)}%</span>
          </div>
          <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">
            ${(s.authors || []).slice(0, 2).join(", ")} &bull; ${s.year} &bull; Methods: ${(s.methods || []).join(", ") || "Standard"}
          </div>
          <div style="font-size: 11.5px; color: var(--text-secondary); line-height: 1.5; margin-top: 6px; border-left: 2px solid var(--brand-sage); padding-left: 8px;">
            ${App.escapeHtml(s.abstract || s.summary)}
          </div>
        </div>
      `).join("");

      const findingsHtml = (res.key_findings || []).map((f) => `
        <li style="margin-bottom: 6px; font-size: 12.5px; color: var(--text-primary); line-height: 1.5;">${App.escapeHtml(f)}</li>
      `).join("");

      container.innerHTML = `
        <div style="background: var(--color-bg-surface); border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 22px;">
          <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 12px; margin-bottom: 16px;">
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--brand-forest);">Synthesized Synthesis</span>
            </div>
            <span class="badge badge-in-library" style="font-size: 11px; font-family: var(--font-mono);">${confPct}% Corpus Confidence</span>
          </div>

          <div style="font-size: 13.5px; line-height: 1.7; color: var(--text-primary); margin-bottom: 18px; font-weight: 400;">
            ${App.escapeHtml(res.answer)}
          </div>

          ${findingsHtml ? `
            <div style="margin-bottom: 18px;">
              <h4 style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); margin-bottom: 8px;">Extracted Empirical Claims</h4>
              <ul style="padding-left: 18px; margin: 0;">${findingsHtml}</ul>
            </div>
          ` : ''}

          <div>
            <h4 style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); margin-bottom: 8px;">Direct Literature Evidence (${(res.sources || []).length} papers cited)</h4>
            ${sourcesHtml || '<div style="color: var(--text-muted); font-size: 12px;">No direct paper sources.</div>'}
          </div>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `
        <div style="padding: 20px; color: var(--color-danger); background: var(--color-bg-surface); border: 1px solid var(--color-danger); border-radius: var(--radius-sm);">
          Error querying literature: ${err.message}
        </div>
      `;
    }
  },

  // ==========================================
  // 2. BENCHMARK MATRIX
  // ==========================================
  bindBenchmarks() {
    const refreshBtn = document.getElementById("btn-refresh-benchmarks");
    if (refreshBtn) {
      refreshBtn.addEventListener("click", () => this.loadBenchmarks());
    }
  },

  async loadBenchmarks() {
    const container = document.getElementById("benchmarks-container");
    if (!container) return;

    container.innerHTML = `<div style="padding: 24px; text-align: center; color: var(--text-muted);">Extracting empirical metrics across papers...</div>`;

    try {
      const data = await API.getBenchmarks();
      const benchmarks = data.benchmarks || [];

      if (benchmarks.length === 0) {
        container.innerHTML = `<div style="padding: 32px; text-align: center; color: var(--text-muted);">No benchmark metrics extracted in this workspace yet.</div>`;
        return;
      }

      const rowsHtml = benchmarks.map((b) => `
        <tr style="border-bottom: 1px solid var(--border-color);">
          <td style="padding: 10px 14px; font-size: 12.5px; font-weight: 600; color: var(--text-primary); max-width: 260px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${App.escapeHtml(b.paper_title)}">
            ${App.escapeHtml(b.paper_title)}
          </td>
          <td style="padding: 10px 14px; font-size: 11.5px; font-family: var(--font-mono); color: var(--text-secondary);">${b.year}</td>
          <td style="padding: 10px 14px; font-size: 12px; font-weight: 500;"><span class="badge" style="background: rgba(255,255,255,0.06);">${App.escapeHtml(b.dataset)}</span></td>
          <td style="padding: 10px 14px; font-size: 12px; color: var(--text-secondary);">${App.escapeHtml(b.domain)}</td>
          <td style="padding: 10px 14px; font-size: 12px; color: var(--brand-forest); font-family: var(--font-mono);">${App.escapeHtml(b.method)}</td>
          <td style="padding: 10px 14px; font-size: 11.5px; color: var(--text-primary); font-family: var(--font-mono);">${App.escapeHtml(b.metric)}</td>
          <td style="padding: 10px 14px; font-size: 11px;"><span class="badge badge-in-library">${App.escapeHtml(b.reported_result)}</span></td>
        </tr>
      `).join("");

      container.innerHTML = `
        <div style="overflow-x: auto;">
          <table style="width: 100%; border-collapse: collapse; text-align: left;">
            <thead>
              <tr style="background: var(--color-bg-base); border-bottom: 1px solid var(--border-color);">
                <th style="padding: 10px 14px; font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-secondary);">Scientific Paper</th>
                <th style="padding: 10px 14px; font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-secondary);">Year</th>
                <th style="padding: 10px 14px; font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-secondary);">Benchmark Dataset</th>
                <th style="padding: 10px 14px; font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-secondary);">Domain</th>
                <th style="padding: 10px 14px; font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-secondary);">Evaluated Architecture</th>
                <th style="padding: 10px 14px; font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-secondary);">Evaluation Metric</th>
                <th style="padding: 10px 14px; font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-secondary);">Finding Status</th>
              </tr>
            </thead>
            <tbody>${rowsHtml}</tbody>
          </table>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div style="padding: 20px; color: var(--color-danger);">Failed to load benchmarks: ${err.message}</div>`;
    }
  },

  // ==========================================
  // 3. CONTRADICTION & GAP RADAR
  // ==========================================
  bindGaps() {
    const refreshBtn = document.getElementById("btn-refresh-gaps");
    if (refreshBtn) {
      refreshBtn.addEventListener("click", () => this.loadGaps());
    }
  },

  async loadGaps() {
    const container = document.getElementById("gaps-container");
    if (!container) return;

    container.innerHTML = `<div style="padding: 24px; text-align: center; color: var(--text-muted);">Detecting literature contradictions and research gaps...</div>`;

    try {
      const data = await API.getLiteratureGaps();
      const conflicts = data.contradictions || [];
      const gaps = data.research_gaps || [];
      const limitations = data.shared_limitations || [];

      const conflictsHtml = conflicts.map((c) => `
        <div style="background: var(--color-bg-surface); border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 18px; margin-bottom: 14px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <strong style="font-size: 14px; color: var(--text-primary);">${App.escapeHtml(c.topic)}</strong>
            <span class="badge" style="background: rgba(220,53,69,0.15); color: #ff6b6b; font-size: 10.5px;">Severity: ${c.severity}</span>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 14px;">
            <div style="background: var(--color-bg-base); padding: 12px; border-radius: var(--radius-xs); border-left: 3px solid #ff6b6b;">
              <div style="font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 4px;">Claim A (${App.escapeHtml(c.claim_a.paper)})</div>
              <p style="font-size: 12px; line-height: 1.5; color: var(--text-primary); margin: 0;">${App.escapeHtml(c.claim_a.claim)}</p>
            </div>
            <div style="background: var(--color-bg-base); padding: 12px; border-radius: var(--radius-xs); border-left: 3px solid #e0a800;">
              <div style="font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 4px;">Claim B (${App.escapeHtml(c.claim_b.paper)})</div>
              <p style="font-size: 12px; line-height: 1.5; color: var(--text-primary); margin: 0;">${App.escapeHtml(c.claim_b.claim)}</p>
            </div>
          </div>

          <div style="font-size: 12px; color: var(--brand-forest); background: rgba(123, 150, 105, 0.1); padding: 10px 12px; border-radius: var(--radius-xs);">
            <strong>Synthesis Resolution:</strong> ${App.escapeHtml(c.synthesis_advice)}
          </div>
        </div>
      `).join("");

      const gapsHtml = gaps.map((g) => `
        <div style="background: var(--color-bg-surface); border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 16px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span class="badge" style="font-size: 10.5px; font-family: var(--font-mono);">${App.escapeHtml(g.domain)}</span>
            <span class="badge badge-in-library" style="font-size: 10.5px;">Impact Score: ${g.impact_score}/10</span>
          </div>
          <h4 style="font-size: 13.5px; font-weight: 600; color: var(--text-primary); margin: 6px 0;">${App.escapeHtml(g.title)}</h4>
          <p style="font-size: 12px; color: var(--text-secondary); line-height: 1.5; margin: 0;">${App.escapeHtml(g.description)}</p>
        </div>
      `).join("");

      const limHtml = limitations.map((l) => `<li style="margin-bottom: 6px; font-size: 12.5px; color: var(--text-primary);">${App.escapeHtml(l)}</li>`).join("");

      container.innerHTML = `
        <div>
          <h3 style="font-size: 14px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-primary); margin-bottom: 12px;">Detected Cross-Paper Contradictions</h3>
          ${conflictsHtml || '<div style="color: var(--text-muted); font-size: 12px;">No contradictions detected.</div>'}
        </div>

        <div style="margin-top: 14px;">
          <h3 style="font-size: 14px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-primary); margin-bottom: 12px;">High-Potential Research Gaps</h3>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px;">
            ${gapsHtml}
          </div>
        </div>

        <div style="margin-top: 14px; background: var(--color-bg-surface); border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 18px;">
          <h3 style="font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-primary); margin-bottom: 10px;">Corpus-Wide Unaddressed Limitations</h3>
          <ul style="padding-left: 20px; margin: 0;">${limHtml}</ul>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div style="padding: 20px; color: var(--color-danger);">Failed to load radar: ${err.message}</div>`;
    }
  }
};


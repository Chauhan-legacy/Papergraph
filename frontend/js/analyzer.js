/**
 * Paper Analyzer Controller
 * Coordinates multi-stage processing pipeline with start, pause, resume, cancel, and retry.
 */
const AnalyzerModule = {
  pollInterval: null,
  currentStatus: null,

  init() {
    this.bindEvents();
    this.checkProgress();
  },

  bindEvents() {
    const startBtn = document.getElementById("btn-analyzer-start");
    if (startBtn) startBtn.addEventListener("click", () => this.startPipeline());

    const pauseBtn = document.getElementById("btn-analyzer-pause");
    if (pauseBtn) pauseBtn.addEventListener("click", () => this.pausePipeline());

    const resumeBtn = document.getElementById("btn-analyzer-resume");
    if (resumeBtn) resumeBtn.addEventListener("click", () => this.resumePipeline());

    const cancelBtn = document.getElementById("btn-analyzer-cancel");
    if (cancelBtn) cancelBtn.addEventListener("click", () => this.cancelPipeline());

    const retryBtn = document.getElementById("btn-analyzer-retry");
    if (retryBtn) retryBtn.addEventListener("click", () => this.retryPipeline());
  },

  async startPipeline(forceReanalyze = false) {
    try {
      const wsStatus = await API.getWorkspaceStatus();
      if (!wsStatus || wsStatus.paper_count === 0) {
        App.showToast("No papers found in current workspace. Please import papers first.", "warning");
        return;
      }
      await API.startAnalysis(null, forceReanalyze);
      App.showToast("Analysis pipeline started.");
      this.startPolling();
    } catch (err) {
      App.showToast(`Error starting analysis: ${err.message}`, "error");
    }
  },

  async pausePipeline() {
    try {
      await API.pauseAnalysis();
      App.showToast("Analysis paused.");
      await this.checkProgress();
    } catch (err) {
      App.showToast(`Error: ${err.message}`, "error");
    }
  },

  async resumePipeline() {
    try {
      await API.resumeAnalysis();
      App.showToast("Analysis resumed.");
      this.startPolling();
    } catch (err) {
      App.showToast(`Error: ${err.message}`, "error");
    }
  },

  async cancelPipeline() {
    try {
      await API.cancelAnalysis();
      App.showToast("Analysis cancelled safely.", "warning");
      this.stopPolling();
      await this.checkProgress();
    } catch (err) {
      App.showToast(`Error: ${err.message}`, "error");
    }
  },

  async retryPipeline() {
    try {
      const res = await API.retryAnalysis();
      if (res.status === "none") {
        App.showToast("No failed papers to retry.", "warning");
      } else {
        App.showToast(`Retrying ${res.retrying_count} failed papers.`);
        this.startPolling();
      }
    } catch (err) {
      App.showToast(`Error retrying: ${err.message}`, "error");
    }
  },

  startPolling() {
    this.stopPolling();
    this.pollInterval = setInterval(() => this.checkProgress(), 1000);
    this.checkProgress();
  },

  stopPolling() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
  },

  async checkProgress() {
    try {
      const status = await API.getAnalyzerProgress();
      this.currentStatus = status;
      this.updateUI(status);

      if (!status.active && this.pollInterval) {
        this.stopPolling();
        await WorkspaceModule.refreshStatus();
        if (LibraryModule.loadPapers) LibraryModule.loadPapers();
      }
    } catch (err) {
      console.warn("Analyzer progress poll failed:", err);
    }
  },

  updateUI(status) {
    if (!status) return;

    // Progress bar
    const bar = document.getElementById("analyzer-progress-bar");
    if (bar) bar.style.width = `${status.percent_complete}%`;

    const pctText = document.getElementById("analyzer-percent-text");
    if (pctText) pctText.textContent = `${status.percent_complete}%`;

    // Counters
    const procEl = document.getElementById("analyzer-processed-count");
    if (procEl) procEl.textContent = status.processed_papers;

    const totalEl = document.getElementById("analyzer-total-count");
    if (totalEl) totalEl.textContent = status.total_papers;

    const failedEl = document.getElementById("analyzer-failed-count");
    if (failedEl) failedEl.textContent = status.failed_papers;

    // Current paper & stage
    const currPaperEl = document.getElementById("analyzer-current-paper");
    if (currPaperEl) {
      currPaperEl.textContent = status.current_paper_title || (status.active ? "Initializing papers..." : "Idle / Standing by");
    }

    const currStageEl = document.getElementById("analyzer-current-stage");
    if (currStageEl) {
      currStageEl.textContent = status.current_stage || (status.active ? "Analyzing..." : "Ready");
    }

    // Button states
    const startBtn = document.getElementById("btn-analyzer-start");
    const pauseBtn = document.getElementById("btn-analyzer-pause");
    const resumeBtn = document.getElementById("btn-analyzer-resume");
    const cancelBtn = document.getElementById("btn-analyzer-cancel");

    if (startBtn) startBtn.style.display = status.active ? "none" : "inline-flex";
    if (pauseBtn) pauseBtn.style.display = status.active && !status.paused ? "inline-flex" : "none";
    if (resumeBtn) resumeBtn.style.display = status.active && status.paused ? "inline-flex" : "none";
    if (cancelBtn) cancelBtn.style.display = status.active ? "inline-flex" : "none";

    // Stage timeline steps
    const stages = [
      "Discovery",
      "Import",
      "Abstract Processing",
      "Structured Summary",
      "NLP Analysis & Embeddings",
      "Semantic Relationships",
      "Citation Relationships",
      "Completed"
    ];

    stages.forEach((stageName, idx) => {
      const stepEl = document.getElementById(`stage-step-${idx + 1}`);
      if (!stepEl) return;

      const isCompleted = status.stages_completed && status.stages_completed.includes(stageName);
      const isCurrent = status.current_stage === stageName;

      stepEl.className = "stage-step";
      if (isCompleted) stepEl.classList.add("complete");
      if (isCurrent) stepEl.classList.add("active");
    });
  }
};


/**
 * PaperGraph API Client
 * Clean, centralized fetch abstraction for all backend endpoints.
 */
const API = {
  baseUrl: '',

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    };

    try {
      const response = await fetch(url, { ...options, headers });
      if (!response.ok) {
        let errorData = {};
        try {
          errorData = await response.json();
        } catch (_) {}
        const msg = errorData.detail || errorData.error || `HTTP error ${response.status}`;
        throw new Error(msg);
      }
      return await response.json();
    } catch (err) {
      console.error(`API Error [${endpoint}]:`, err);
      throw err;
    }
  },

  // Health
  getHealth() {
    return this.request('/api/health');
  },

  // Workspace
  getWorkspaceStatus() {
    return this.request('/api/workspace/status');
  },
  createWorkspace(name, path) {
    return this.request('/api/workspace/create', {
      method: 'POST',
      body: JSON.stringify({ name, path })
    });
  },
  openWorkspace(path) {
    return this.request('/api/workspace/open', {
      method: 'POST',
      body: JSON.stringify({ path })
    });
  },
  triggerBackup() {
    return this.request('/api/workspace/backup', { method: 'POST' });
  },
  listBackups() {
    return this.request('/api/workspace/backups');
  },
  restoreBackup(filename) {
    return this.request('/api/workspace/restore', {
      method: 'POST',
      body: JSON.stringify({ filename })
    });
  },
  rebuildIndex() {
    return this.request('/api/workspace/rebuild-index', { method: 'POST' });
  },

  // Search
  searchLiterature(queryObj) {
    return this.request('/api/search', {
      method: 'POST',
      body: JSON.stringify(queryObj)
    });
  },

  // Papers & Library
  listPapers(params = {}) {
    const query = new URLSearchParams();
    if (params.q) query.append('q', params.q);
    if (params.year) query.append('year', params.year);
    if (params.author) query.append('author', params.author);
    if (params.topic) query.append('topic', params.topic);
    if (params.collection_id) query.append('collection_id', params.collection_id);
    if (params.sort_by) query.append('sort_by', params.sort_by);
    if (params.sort_desc !== undefined) query.append('sort_desc', params.sort_desc);

    return this.request(`/api/papers?${query.toString()}`);
  },
  getPaperDetail(paperId) {
    return this.request(`/api/papers/${encodeURIComponent(paperId)}`);
  },
  importPapers(papers, targetCollection = null) {
    return this.request('/api/papers/import', {
      method: 'POST',
      body: JSON.stringify({ papers, target_collection: targetCollection })
    });
  },
  scanFolder(folderPath) {
    return this.request('/api/papers/scan-folder', {
      method: 'POST',
      body: JSON.stringify({ folder_path: folderPath })
    });
  },
  importFolder(folderPath, selectedFilenames = null, targetCollection = null) {
    return this.request('/api/papers/import-folder', {
      method: 'POST',
      body: JSON.stringify({
        folder_path: folderPath,
        selected_filenames: selectedFilenames,
        target_collection: targetCollection
      })
    });
  },
  saveNotes(paperId, notes) {
    return this.request(`/api/papers/${encodeURIComponent(paperId)}/notes`, {
      method: 'PUT',
      body: JSON.stringify({ notes })
    });
  },

  // Collections
  listCollections() {
    return this.request('/api/collections');
  },
  createCollection(name, description = '') {
    return this.request('/api/collections', {
      method: 'POST',
      body: JSON.stringify({ name, description })
    });
  },
  deleteCollection(collectionId) {
    return this.request(`/api/collections/${encodeURIComponent(collectionId)}`, {
      method: 'DELETE'
    });
  },
  addPaperToCollection(collectionId, paperId) {
    return this.request(`/api/collections/${encodeURIComponent(collectionId)}/papers`, {
      method: 'POST',
      body: JSON.stringify({ paper_id: paperId })
    });
  },
  removePaperFromCollection(collectionId, paperId) {
    return this.request(`/api/collections/${encodeURIComponent(collectionId)}/papers/${encodeURIComponent(paperId)}`, {
      method: 'DELETE'
    });
  },

  // Analyzer
  getAnalyzerProgress() {
    return this.request('/api/analyzer/progress');
  },
  startAnalysis(paperIds = null, forceReanalyze = false) {
    return this.request('/api/analyzer/start', {
      method: 'POST',
      body: JSON.stringify({ paper_ids: paperIds, force_reanalyze: forceReanalyze })
    });
  },
  pauseAnalysis() {
    return this.request('/api/analyzer/pause', { method: 'POST' });
  },
  resumeAnalysis() {
    return this.request('/api/analyzer/resume', { method: 'POST' });
  },
  cancelAnalysis() {
    return this.request('/api/analyzer/cancel', { method: 'POST' });
  },
  retryAnalysis() {
    return this.request('/api/analyzer/retry', { method: 'POST' });
  },

  // Graph
  getKnowledgeGraph(params = {}) {
    const query = new URLSearchParams();
    if (params.collection_id) query.append('collection_id', params.collection_id);
    if (params.citations !== undefined) query.append('citations', params.citations);
    if (params.semantics !== undefined) query.append('semantics', params.semantics);
    if (params.authors !== undefined) query.append('authors', params.authors);
    if (params.topics !== undefined) query.append('topics', params.topics);
    if (params.min_similarity !== undefined) query.append('min_similarity', params.min_similarity);
    if (params.max_nodes !== undefined) query.append('max_nodes', params.max_nodes);

    return this.request(`/api/graph?${query.toString()}`);
  },
  getPaperEgoGraph(paperId) {
    return this.request(`/api/graph/${encodeURIComponent(paperId)}`);
  },

  // Intersections
  getIntersections() {
    return this.request('/api/intersections');
  },

  // Trends
  getTrends() {
    return this.request('/api/trends');
  },

  // Export
  exportResearch(format, paperIds = null, collectionId = null) {
    return this.request('/api/export', {
      method: 'POST',
      body: JSON.stringify({ format, paper_ids: paperIds, collection_id: collectionId })
    });
  }
};


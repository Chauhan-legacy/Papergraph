/**
 * Knowledge Graph Explorer Controller using Cytoscape.js
 * Comprehensive scientific graph architecture with multi-layout switching,
 * citation mapping, dynamic semantic similarity, author/concept nodes, and export.
 */
const GraphModule = {
  cy: null,
  graphData: null,
  showCitations: true,
  showSemantics: true,
  showAuthors: false,
  showTopics: false,
  showMethods: false,
  showDatasets: false,
  minSimilarity: 0.35,
  activeLayout: 'cose',

  init() {
    this.bindEvents();
  },

  bindEvents() {
    // Zoom controls
    const zoomInBtn = document.getElementById("btn-graph-zoomin");
    if (zoomInBtn) zoomInBtn.addEventListener("click", () => this.cy && this.cy.zoom(this.cy.zoom() * 1.25));

    const zoomOutBtn = document.getElementById("btn-graph-zoomout");
    if (zoomOutBtn) zoomOutBtn.addEventListener("click", () => this.cy && this.cy.zoom(this.cy.zoom() * 0.8));

    const fitBtn = document.getElementById("btn-graph-fit");
    if (fitBtn) fitBtn.addEventListener("click", () => this.fitView());

    const resetBtn = document.getElementById("btn-graph-reset");
    if (resetBtn) resetBtn.addEventListener("click", () => this.loadGraph());

    // Layout selector
    const layoutSelect = document.getElementById("graph-layout-select");
    if (layoutSelect) {
      layoutSelect.addEventListener("change", (e) => {
        this.activeLayout = e.target.value;
        this.applyLayout(this.activeLayout);
      });
    }

    // Edge & Node toggles
    const citToggle = document.getElementById("toggle-citations");
    if (citToggle) {
      citToggle.addEventListener("change", (e) => {
        this.showCitations = e.target.checked;
        this.loadGraph();
      });
    }

    const semToggle = document.getElementById("toggle-semantics");
    if (semToggle) {
      semToggle.addEventListener("change", (e) => {
        this.showSemantics = e.target.checked;
        this.loadGraph();
      });
    }

    const authToggle = document.getElementById("toggle-authors");
    if (authToggle) {
      authToggle.addEventListener("change", (e) => {
        this.showAuthors = e.target.checked;
        this.loadGraph();
      });
    }

    const topToggle = document.getElementById("toggle-topics");
    if (topToggle) {
      topToggle.addEventListener("change", (e) => {
        this.showTopics = e.target.checked;
        this.loadGraph();
      });
    }

    const methToggle = document.getElementById("toggle-methods");
    if (methToggle) {
      methToggle.addEventListener("change", (e) => {
        this.showMethods = e.target.checked;
        this.loadGraph();
      });
    }

    const dataToggle = document.getElementById("toggle-datasets");
    if (dataToggle) {
      dataToggle.addEventListener("change", (e) => {
        this.showDatasets = e.target.checked;
        this.loadGraph();
      });
    }

    // Similarity slider
    const simSlider = document.getElementById("slider-similarity");
    const simVal = document.getElementById("similarity-value-label");
    if (simSlider) {
      simSlider.addEventListener("input", (e) => {
        this.minSimilarity = parseFloat(e.target.value);
        if (simVal) simVal.textContent = this.minSimilarity.toFixed(2);
      });
      simSlider.addEventListener("change", () => this.loadGraph());
    }

    // Search inside graph
    const searchGraph = document.getElementById("graph-search-input");
    if (searchGraph) {
      searchGraph.addEventListener("input", (e) => this.filterGraphNodes(e.target.value.toLowerCase().trim()));
    }

    // Export buttons
    const exportPngBtn = document.getElementById("btn-graph-export-png");
    if (exportPngBtn) {
      exportPngBtn.addEventListener("click", () => this.exportPng());
    }

    const exportJsonBtn = document.getElementById("btn-graph-export-json");
    if (exportJsonBtn) {
      exportJsonBtn.addEventListener("click", () => this.exportJson());
    }

    // Window resize handler to maintain proper Cytoscape viewport bounds
    window.addEventListener("resize", () => {
      if (this.cy && App.activeScreen === "graph") {
        this.cy.resize();
      }
    });
  },

  async loadGraph() {
    const container = document.getElementById("cy");
    if (!container) return;

    try {
      const data = await API.getKnowledgeGraph({
        citations: this.showCitations,
        semantics: this.showSemantics,
        authors: this.showAuthors,
        topics: this.showTopics,
        methods: this.showMethods,
        datasets: this.showDatasets,
        min_similarity: this.minSimilarity,
        max_nodes: 250
      });

      this.graphData = data;
      this.updateStateUI(data);
      this.renderGraph(data);
      this.renderLegend(data.clusters || []);
    } catch (err) {
      console.error("Error loading knowledge graph:", err);
      App.showToast(`Graph load error: ${err.message}`, "error");
    }
  },

  updateStateUI(data) {
    const stats = data.stats || {};
    const badge = document.getElementById("graph-stats-badge");
    if (badge) {
      const paperCount = stats.paper_nodes || stats.total_nodes || 0;
      const citCount = stats.citation_edges || 0;
      const semCount = stats.semantic_edges || 0;
      const clusterCount = stats.clusters || 0;
      badge.textContent = `${paperCount} Papers • ${citCount} Citations • ${semCount} Semantic • ${clusterCount} Clusters`;
    }

    const noticeBanner = document.getElementById("graph-notice-banner");
    const emptyOverlay = document.getElementById("graph-empty-overlay");

    if (data.graph_state === "empty_library") {
      if (emptyOverlay) emptyOverlay.style.display = "flex";
      if (noticeBanner) noticeBanner.style.display = "none";
    } else if (data.graph_state === "no_edges") {
      if (emptyOverlay) emptyOverlay.style.display = "none";
      if (noticeBanner) {
        noticeBanner.style.display = "block";
        noticeBanner.textContent = data.state_message || "Showing papers as nodes. Run the Paper Analyzer to calculate semantic similarity edges.";
      }
    } else {
      if (emptyOverlay) emptyOverlay.style.display = "none";
      if (noticeBanner) noticeBanner.style.display = "none";
    }
  },

  renderGraph(data) {
    const container = document.getElementById("cy");
    if (!container || !window.cytoscape) return;

    if (this.cy) {
      this.cy.destroy();
      this.cy = null;
    }

    const elements = data.elements || { nodes: [], edges: [] };
    if (!elements.nodes || elements.nodes.length === 0) {
      return;
    }

    // Determine layout: if no edges, force 'concentric' or 'grid' so nodes don't pile up
    const totalEdges = (elements.edges || []).length;
    let chosenLayout = this.activeLayout;
    if (totalEdges === 0 && chosenLayout === "cose") {
      chosenLayout = "concentric";
    }

    const layoutConfig = this.getLayoutConfig(chosenLayout);

    this.cy = window.cytoscape({
      container: container,
      elements: elements,
      boxSelectionEnabled: true,
      autounselectify: false,
      style: [
        // Base Node Style (Paper)
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'font-family': 'Inter, sans-serif',
            'font-size': '11px',
            'font-weight': 500,
            'color': '#20261F',
            'text-valign': 'bottom',
            'text-margin-y': 6,
            'background-color': 'data(color)',
            'width': 'data(size)',
            'height': 'data(size)',
            'border-width': 2,
            'border-color': '#FFFFFF',
            'transition-property': 'background-color, line-color, target-arrow-color, opacity, border-width',
            'transition-duration': '0.18s'
          }
        },
        // Author Nodes
        {
          selector: 'node[type="author"]',
          style: {
            'shape': 'diamond',
            'background-color': '#CCBEB1',
            'border-color': '#997E67',
            'border-width': 1.5,
            'color': '#4A3B2F',
            'font-size': '10px',
            'font-weight': 600
          }
        },
        // Topic / Concept Nodes
        {
          selector: 'node[type="topic"]',
          style: {
            'shape': 'round-rectangle',
            'background-color': '#6C8480',
            'border-color': '#4E6662',
            'border-width': 1.5,
            'color': '#FFFFFF',
            'font-size': '10px',
            'font-weight': 500,
            'text-valign': 'center',
            'text-margin-y': 0,
            'padding': '6px'
          }
        },
        // Selected Node
        {
          selector: 'node:selected',
          style: {
            'border-width': 3,
            'border-color': '#404E3B',
            'font-weight': 600
          }
        },
        // Citation Edges (Directed solid arrow)
        {
          selector: 'edge[type="citation"]',
          style: {
            'width': 2,
            'line-color': '#7B9669',
            'target-arrow-color': '#7B9669',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'arrow-scale': 0.85,
            'opacity': 0.8
          }
        },
        // Semantic Edges (Undirected dashed line with thickness mapped to score)
        {
          selector: 'edge[type="semantic"]',
          style: {
            'width': 'mapData(weight, 0.3, 1.0, 1.5, 4.5)',
            'line-color': '#6C8480',
            'line-style': 'dashed',
            'curve-style': 'bezier',
            'opacity': 0.85
          }
        },
        // Authorship Edges
        {
          selector: 'edge[type="authorship"]',
          style: {
            'width': 1.2,
            'line-color': '#CCBEB1',
            'line-style': 'dotted',
            'curve-style': 'bezier',
            'opacity': 0.75
          }
        },
        // Concept Edges
        {
          selector: 'edge[type="concept"]',
          style: {
            'width': 1.2,
            'line-color': '#BAC8B1',
            'line-style': 'solid',
            'curve-style': 'bezier',
            'opacity': 0.75
          }
        },
        // Method Nodes
        {
          selector: 'node[type="method"]',
          style: {
            'shape': 'hexagon',
            'background-color': '#2D6A5D',
            'border-color': '#1F2826',
            'border-width': 1.5,
            'color': '#FFFFFF',
            'font-size': '10px',
            'font-weight': 600,
            'text-valign': 'center',
            'padding': '6px'
          }
        },
        // Dataset Nodes
        {
          selector: 'node[type="dataset"]',
          style: {
            'shape': 'triangle',
            'background-color': '#A8583C',
            'border-color': '#FFFFFF',
            'border-width': 1.5,
            'color': '#FFFFFF',
            'font-size': '10px',
            'font-weight': 600,
            'text-valign': 'center',
            'padding': '6px'
          }
        },
        // Method Edges
        {
          selector: 'edge[type="method"]',
          style: {
            'width': 1.5,
            'line-color': '#2D6A5D',
            'line-style': 'dotted',
            'curve-style': 'bezier',
            'opacity': 0.8
          }
        },
        // Dataset Edges
        {
          selector: 'edge[type="dataset"]',
          style: {
            'width': 1.5,
            'line-color': '#A8583C',
            'line-style': 'dashed',
            'curve-style': 'bezier',
            'opacity': 0.8
          }
        },
        // Highlight & Fade classes
        {
          selector: '.faded',
          style: {
            'opacity': 0.12
          }
        },
        {
          selector: '.highlighted',
          style: {
            'border-width': 3.5,
            'border-color': '#FFDBBB',
            'opacity': 1.0,
            'font-weight': 700
          }
        }
      ],
      layout: layoutConfig
    });

    // Node click handler -> Open in Inspector or highlight
    this.cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      const nodeType = node.data('type');
      const nodeId = node.data('id');

      this.cy.elements().removeClass('highlighted faded');
      node.addClass('highlighted');
      node.neighborhood().addClass('highlighted');
      this.cy.elements().not(node.neighborhood().add(node)).addClass('faded');

      if (nodeType === 'paper') {
        App.openPaperInspectorById(nodeId);
      } else if (nodeType === 'author') {
        const connectedPapers = node.neighborhood('node[type="paper"]').length;
        App.showToast(`Author: ${node.data('label')} (${connectedPapers} connected publications)`);
      } else if (nodeType === 'topic') {
        const connectedPapers = node.neighborhood('node[type="paper"]').length;
        App.showToast(`Research Concept: ${node.data('label')} (${connectedPapers} publications)`);
      } else if (nodeType === 'method') {
        const connectedPapers = node.neighborhood('node[type="paper"]').length;
        App.showToast(`Algorithmic Method: ${node.data('label')} (${connectedPapers} papers apply this)`);
      } else if (nodeType === 'dataset') {
        const connectedPapers = node.neighborhood('node[type="paper"]').length;
        App.showToast(`Benchmark Dataset: ${node.data('label')} (${connectedPapers} papers evaluate on this)`);
      }
    });

    // Edge click handler -> Show relationship evidence explanation
    this.cy.on('tap', 'edge', (evt) => {
      const edge = evt.target;
      const explanation = edge.data('explanation') || `${edge.data('type')}: ${edge.data('label')}`;
      App.showToast(`Relationship: ${explanation}`);
    });

    // Canvas click -> Reset highlight and selection
    this.cy.on('tap', (evt) => {
      if (evt.target === this.cy) {
        this.cy.elements().removeClass('highlighted faded');
      }
    });

    // Initial fit view with comfortable padding
    setTimeout(() => {
      if (this.cy) {
        this.cy.resize();
        this.cy.fit(null, 36);
      }
    }, 150);
  },

  getLayoutConfig(layoutName) {
    if (layoutName === 'concentric') {
      return {
        name: 'concentric',
        concentric: (node) => node.data('citations') || 1,
        levelWidth: () => 2,
        padding: 40,
        animate: true,
        animationDuration: 400
      };
    } else if (layoutName === 'circle') {
      return {
        name: 'circle',
        padding: 40,
        animate: true,
        animationDuration: 400
      };
    } else if (layoutName === 'breadthfirst') {
      return {
        name: 'breadthfirst',
        directed: true,
        padding: 40,
        animate: true,
        animationDuration: 400
      };
    } else if (layoutName === 'grid') {
      return {
        name: 'grid',
        padding: 40,
        animate: true,
        animationDuration: 300
      };
    } else {
      // Default: 'cose' (Compound Spring Embedder)
      return {
        name: 'cose',
        animate: true,
        animationDuration: 450,
        nodeDimensionsIncludeLabels: true,
        idealEdgeLength: 120,
        nodeOverlap: 25,
        componentSpacing: 100,
        randomize: false,
        padding: 40
      };
    }
  },

  applyLayout(layoutName) {
    if (!this.cy) return;
    const config = this.getLayoutConfig(layoutName);
    const layout = this.cy.layout(config);
    layout.run();
  },

  fitView() {
    if (this.cy) {
      this.cy.resize();
      this.cy.fit(null, 36);
    }
  },

  filterGraphNodes(query) {
    if (!this.cy) return;
    if (!query) {
      this.cy.elements().removeClass('faded highlighted');
      return;
    }

    this.cy.batch(() => {
      this.cy.elements().addClass('faded');
      this.cy.nodes().forEach((n) => {
        const title = (n.data('title') || '').toLowerCase();
        const author = (n.data('author') || '').toLowerCase();
        const label = (n.data('label') || '').toLowerCase();
        if (title.includes(query) || author.includes(query) || label.includes(query)) {
          n.removeClass('faded').addClass('highlighted');
          n.neighborhood().removeClass('faded');
        }
      });
    });
  },

  renderLegend(clusters) {
    const legendEl = document.getElementById("graph-cluster-legend");
    if (!legendEl) return;

    if (!clusters || clusters.length === 0) {
      legendEl.innerHTML = `<div style="color: var(--text-muted); font-size: 11px;">No community clusters computed.</div>`;
      return;
    }

    legendEl.innerHTML = clusters.slice(0, 6).map((c) => `
      <div class="legend-item">
        <div class="legend-swatch" style="background: ${c.color};"></div>
        <span>${c.name} (${c.count})</span>
      </div>
    `).join("");
  },

  exportPng() {
    if (!this.cy) {
      App.showToast("No active graph to export.", "warning");
      return;
    }
    try {
      const png64 = this.cy.png({
        full: true,
        bg: '#F8FAF8',
        scale: 2.0
      });
      const a = document.createElement('a');
      a.href = png64;
      a.download = `PaperGraph_Export_${Date.now()}.png`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      App.showToast("Graph exported as high-resolution PNG!");
    } catch (err) {
      App.showToast(`Export error: ${err.message}`, "error");
    }
  },

  exportJson() {
    if (!this.cy || !this.graphData) {
      App.showToast("No active graph to export.", "warning");
      return;
    }
    try {
      const jsonStr = JSON.stringify(this.graphData, null, 2);
      const blob = new Blob([jsonStr], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `PaperGraph_Data_${Date.now()}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      App.showToast("Graph elements exported as JSON!");
    } catch (err) {
      App.showToast(`Export error: ${err.message}`, "error");
    }
  }
};

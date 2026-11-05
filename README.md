# PaperGraph V3: Scientific Literature Intelligence Platform

PaperGraph V3 is an autonomous, local-first research intelligence platform designed for comprehensive analysis, knowledge graph synthesis, and evidence extraction from scientific literature.

---

## 1. Executive Summary

PaperGraph operates entirely on local hardware without requiring external cloud databases or mandatory API keys. The system combines high-precision document parsing (Surya OCR 2 with PyMuPDF fallback) with cognitive extraction, Louvain community graph clustering, cross-paper synthesis, hypothesis discovery, and multi-workspace management.

### Key Capabilities

- **Deterministic Multi-Stage Document Ingestion**: Dual-engine text extraction utilizing Surya OCR 2 for primary processing and PyMuPDF as an instant deterministic fallback.
- **Cognitive Analyzer Pipeline**: Autonomous extraction of research objectives, methodologies, empirical findings, foundational assumptions, limitations, and future work.
- **Interactive Scientific Knowledge Graph**: Cytoscape.js-powered interactive network mapping papers, methods, datasets, topics, and authors with Louvain community detection.
- **Cross-Paper Synthesis & Evidence Matrix**: Structured side-by-side comparative analysis grids, agreement/disagreement detection, and CSV/Markdown matrix exports.
- **Literature Review Studio**: Automated generation of structured literature review outlines and complete academic markdown drafts with standard BibTeX citations.
- **Multi-Workspace Architecture**: Seamless switching, creation, and isolation of independent research workspaces with zero database dependencies.
- **Academic Export Suite**: Direct export to BibTeX, JSON, CSV, and formatted Markdown.

---

## 2. System Architecture

```
PaperGraph-v3/
├── app/
│   ├── analysis/           # Pattern extraction and corpus heuristics
│   ├── api/                # FastAPI REST endpoints
│   ├── core/               # File-based storage, progress, and workspace management
│   ├── models/             # Pydantic schemas and data contracts
│   ├── plugins/            # Plugin architecture and registry
│   └── services/           # Cognitive analyzer, graph, synthesis, review services
├── frontend/               # Local-first user interface
│   ├── assets/             # Vendor assets (Cytoscape.js)
│   ├── css/                # Main styles, graph theme, component styles
│   └── js/                 # Screen controllers and API client
├── ocr/                    # Surya OCR 2 backend and PyMuPDF fallbacks
├── tests/                  # Section 9 acceptance test suite
└── run_extreme_test_25_papers.py  # 25-paper end-to-end audit suite
```

---

## 3. Quick Start

### 3.1 Prerequisites

- Python 3.11 or higher
- Windows 10/11, Linux, or macOS

### 3.2 Running via Windows Command Prompt (CMD)

Open Command Prompt (`cmd.exe`) and execute:

```cmd
cd C:\Users\Priyansh\Desktop\PaperGraph-v3
..\PaperGraph\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3.3 Running via Windows PowerShell

Open PowerShell and execute:

```powershell
Set-Location "C:\Users\Priyansh\Desktop\PaperGraph-v3"
& "..\PaperGraph\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Once running, navigate to the web dashboard in your browser:
- Application UI: http://127.0.0.1:8000
- Interactive OpenAPI Documentation: http://127.0.0.1:8000/docs
- Alternative API Documentation (ReDoc): http://127.0.0.1:8000/redoc

---

## 4. Multi-Workspace Management

PaperGraph supports concurrent, isolated research workspaces:

1. **Active Workspace Selector**: Displayed at the top of the sidebar. Shows the current active repository name and paper count.
2. **Add Workspace Button (`+`)**: Positioned next to the workspace selector. Clicking opens the Multi-Workspace Manager to configure a new project workspace.
3. **Switching Workspaces**: Selecting any registered workspace instantly redirects the active session without requiring server restarts.
4. **Removing Workspaces**: Click the remove button to unregister a workspace. Underlying document files remain untouched on disk.

Default workspace path: `%USERPROFILE%\Documents\PaperGraph_Workspace`

---

## 5. REST API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/workspace/status` | GET | Returns current active workspace statistics |
| `/api/workspace/list` | GET | Lists all registered research workspaces |
| `/api/workspace/create` | POST | Creates and activates a new research workspace |
| `/api/workspace/switch` | POST | Switches the active research workspace |
| `/api/workspace/remove` | POST | Unregisters or deletes a workspace |
| `/api/papers/scan-folder` | POST | Scans local folders with auto-resolving fuzzy path matching |
| `/api/papers/import-folder` | POST | Ingests selected research papers into workspace library |
| `/api/analyzer/start` | POST | Launches multi-stage cognitive analysis pipeline |
| `/api/analyzer/progress` | GET | Real-time progress tracking of active analysis |
| `/api/analyzer/paper/{id}` | POST | On-demand single-paper analysis |
| `/api/graph` | GET | Cytoscape-formatted graph with Louvain clusters |
| `/api/graph/{id}` | GET | Ego network centered on a target paper |
| `/api/synthesis/compare` | POST | Generates multi-paper 9-dimension comparative grid |
| `/api/synthesis/matrix` | GET | Dynamic evidence matrix across literature |
| `/api/hypotheses` | GET | Synthesizes open candidate research questions |
| `/api/review/generate` | POST | Generates literature review outline, draft, and BibTeX |
| `/api/export` | POST | Exports literature in BibTeX, JSON, CSV, or Markdown |

---

## 6. Verification and Acceptance Testing

### 6.1 Run Section 9 Acceptance Test Suite

Verifies workspace isolation, UI design locks, OCR pipeline contracts, zero-model pattern engine, bundled model constraints, plugin registry, and licensing compliance:

```cmd
cd C:\Users\Priyansh\Desktop\PaperGraph-v3
..\PaperGraph\.venv\Scripts\python.exe -m pytest tests/test_v3_acceptance.py -v
```

### 6.2 Run Extreme 25-Paper Benchmark

Executes an exhaustive 15-stage pipeline across 25 foundational scientific papers:

```cmd
cd C:\Users\Priyansh\Desktop\PaperGraph-v3
..\PaperGraph\.venv\Scripts\python.exe run_extreme_test_25_papers.py
```

### 6.3 Verify Parent Repository Integrity

Ensures that the original `PaperGraph` directory remains bit-for-bit identical to baseline:

```cmd
cd C:\Users\Priyansh\Desktop\PaperGraph-v3
..\PaperGraph\.venv\Scripts\python.exe verify_parent_integrity.py
```

---

## 7. License

PaperGraph V3 is licensed under the MIT License. Refer to the `LICENSE` file for full terms. Third-party dependency notices are documented in `THIRD_PARTY_LICENSES.md`.

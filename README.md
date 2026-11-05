# PaperGraph

PaperGraph is a local-first research platform to organize, analyze, and visualize scientific literature. It extracts insights from research papers, builds interactive citation networks, and assists with literature reviews—all running locally on your machine.

---

## Features

- **Document Analysis & OCR**: Ingest PDFs using local OCR (Surya OCR) and text extraction with automatic fallbacks.
- **Interactive Knowledge Graph**: Visualize citation networks, research topics, and connections between papers using Cytoscape.js.
- **Research Copilot & Synthesis**: Query your paper collection, extract benchmark results, and identify open research gaps.
- **Multi-Workspace Support**: Organize papers into isolated workspaces with seamless switching from the sidebar.
- **Local & Private**: All documents, metadata, and analyses remain strictly on your local disk.
- **Academic Export**: Export literature summaries and citations to BibTeX, Markdown, CSV, and JSON.

---

## Quick Start

### Option 1: Windows Automated Setup

1. **Clone the repository:**
   ```cmd
   git clone https://github.com/Chauhan-legacy/Papergraph.git
   cd Papergraph
   ```

2. **Run Setup:**
   Double-click `setup_windows.bat` (or run it in Command Prompt). This creates a virtual environment and installs all dependencies.

3. **Start the Application:**
   Double-click `run_windows.bat`. PaperGraph will launch and open in your default browser at `http://127.0.0.1:8000`.

---

### Option 2: Manual Installation (Windows, macOS, Linux)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Chauhan-legacy/Papergraph.git
   cd Papergraph
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # macOS / Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the server:**
   ```bash
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

5. **Open in browser:**
   - Application: [http://127.0.0.1:8000](http://127.0.0.1:8000)
   - Interactive API Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Project Structure

```
PaperGraph/
├── app/
│   ├── analysis/       # Text pattern heuristics and extraction logic
│   ├── api/            # FastAPI routes and endpoints
│   ├── core/           # Workspace and file management
│   ├── models/         # Pydantic data schemas
│   ├── ocr/            # OCR engine and PDF text extractors
│   ├── plugins/        # Extensible plugin system
│   └── services/       # Graph, copilot, and benchmark services
├── frontend/           # Web interface (HTML, CSS, JavaScript)
├── tests/              # Test suite
├── setup_windows.bat   # Windows automated installer
└── run_windows.bat     # Windows launcher script
```

---

## Key API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/workspace/list` | GET | List available workspaces |
| `/api/workspace/switch` | POST | Switch active workspace |
| `/api/papers/import-folder` | POST | Import PDF papers into library |
| `/api/analyzer/start` | POST | Analyze papers in the active workspace |
| `/api/graph` | GET | Fetch knowledge graph data |
| `/api/tools/copilot` | POST | Query the research copilot |
| `/api/tools/benchmarks` | GET | Extract benchmarks and dataset metrics |
| `/api/tools/gaps` | GET | Identify research gaps and conflicts |
| `/api/export` | POST | Export library data (BibTeX, JSON, CSV) |

---

## License & Credits

- **License**: Released under the [MIT License](LICENSE).
- **Literature Data**: Metadata provided by [OpenAlex](https://openalex.org/).
- **Graph Visualization**: [Cytoscape.js](https://js.cytoscape.org/).
- **Author**: Priyansh Chauhan

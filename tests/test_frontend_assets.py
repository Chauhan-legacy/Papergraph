import os
import re
from pathlib import Path

def test_frontend_files_exist_and_non_empty():
    workspace = Path(__file__).resolve().parent.parent
    frontend_dir = workspace / "frontend"

    required_files = [
        "index.html",
        "css/main.css",
        "css/components.css",
        "css/graph.css",
        "js/api.js",
        "js/app.js",
        "js/workspace.js",
        "js/search.js",
        "js/library.js",
        "js/analyzer.js",
        "js/graph.js",
        "js/intersections.js",
        "js/trends.js",
        "js/settings.js",
    ]

    for rel_path in required_files:
        f = frontend_dir / rel_path
        assert f.exists(), f"Missing frontend asset: {rel_path}"
        assert f.stat().st_size > 100, f"Frontend asset too small or empty: {rel_path}"

def test_index_html_dom_ids_and_structure():
    workspace = Path(__file__).resolve().parent.parent
    index_file = workspace / "frontend" / "index.html"
    content = index_file.read_text(encoding="utf-8")

    # Verify critical screen IDs
    expected_screens = [
        "screen-overview",
        "screen-search",
        "screen-library",
        "screen-analyzer",
        "screen-graph",
        "screen-intersections",
        "screen-trends",
        "screen-settings"
    ]
    for s_id in expected_screens:
        assert f'id="{s_id}"' in content, f"Missing screen container #{s_id}"

    # Verify Topbar & Breadcrumb
    assert 'id="topbar-breadcrumb-current"' in content
    assert 'id="btn-inspector-toggle"' in content

    # Verify Sidebar IDs & brand
    assert 'id="sidebar-ws-badge"' in content
    assert 'id="sidebar-ws-name"' in content

    # Verify Overview desk table
    assert 'id="overview-recent-papers-list"' in content
    assert 'id="stat-total-papers"' in content
    assert 'id="stat-completed-analyses"' in content
    assert 'id="stat-pending-analyses"' in content
    assert 'id="stat-collections-count"' in content

    # Verify Inspector IDs
    assert 'id="inspector-panel"' in content
    assert 'id="btn-close-inspector"' in content
    assert 'id="inspector-title"' in content
    assert 'id="inspector-authors"' in content
    assert 'id="inspector-venue"' in content
    assert 'id="inspector-doi"' in content
    assert 'id="inspector-collections-list"' in content
    assert 'id="inspector-notes-input"' in content
    assert 'id="btn-save-notes"' in content

    # Verify Modals
    assert 'id="workspace-modal"' in content
    assert 'id="form-create-workspace"' in content
    assert 'id="export-modal"' in content
    assert 'id="form-export-data"' in content
    assert 'id="toast-container"' in content

def test_zero_emojis_in_frontend():
    workspace = Path(__file__).resolve().parent.parent
    frontend_dir = workspace / "frontend"

    # Emoji regex matching emoji unicode ranges
    emoji_pattern = re.compile(r"[\u2600-\u27BF\U0001F300-\U0001FAD6\U0001F600-\U0001F64F\U0001F680-\U0001F6FF]")

    for path in frontend_dir.rglob("*"):
        if path.suffix in [".html", ".css", ".js"]:
            text = path.read_text(encoding="utf-8")
            matches = emoji_pattern.findall(text)
            assert len(matches) == 0, f"Found emojis in {path.name}: {matches}"

def test_css_variables_and_typography():
    workspace = Path(__file__).resolve().parent.parent
    main_css = (workspace / "frontend" / "css" / "main.css").read_text(encoding="utf-8")

    # Jade Pebble Morning & Neutral Elegance palette tokens
    assert "--brand-sage:" in main_css
    assert "--brand-forest:" in main_css
    assert "--brand-teal:" in main_css
    assert "--brand-peach:" in main_css
    assert "--font-editorial:" in main_css
    assert "--font-ui:" in main_css


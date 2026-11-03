"""
Integration and Route Tests for FastAPI Backend Endpoints
Directly executes all API endpoint logic, schema validations, and responses.
"""
import pytest
from unittest.mock import MagicMock
from fastapi import BackgroundTasks

from app.main import health_check
from app.api.workspace import (
    get_workspace_status,
    create_workspace,
    trigger_backup,
    list_backups,
    rebuild_index,
    CreateWorkspaceRequest
)
from app.api.search import search_literature
from app.api.papers import (
    import_papers,
    list_papers,
    get_paper_detail,
    update_notes,
    list_collections,
    create_or_update_collection,
    delete_collection,
    NotesUpdateRequest,
    CollectionCreateRequest
)
from app.api.analyzer import (
    get_progress,
    start_analysis,
    pause_analysis,
    resume_analysis,
    cancel_analysis,
    retry_failed,
    StartAnalysisRequest
)
from app.api.graph import get_knowledge_graph, get_paper_ego_graph
from app.api.intersections import get_candidate_intersections
from app.api.trends import get_trends
from app.api.export import export_research, ExportRequest
from app.models.schemas import SearchQuery, ImportRequest, PaperMetadata

def test_api_health_endpoint():
    res = health_check()
    assert res["status"] == "healthy"
    assert res["app"] == "PaperGraph"
    assert "version" in res
    assert "active_workspace" in res

def test_api_workspace_endpoints(temp_workspace):
    status = get_workspace_status()
    assert "paper_count" in status
    assert "workspace_path" in status

    # Backup & list
    backup_res = trigger_backup()
    assert backup_res["status"] == "success"
    assert "backup" in backup_res

    backups_list = list_backups()
    assert len(backups_list["backups"]) >= 1

    # Rebuild index
    rebuild_res = rebuild_index()
    assert rebuild_res["status"] == "success"

def test_api_search_endpoint(sample_raw_paper):
    query = SearchQuery(query="few-shot learning", filter_type="all")
    with pytest.MonkeyPatch.context() as m:
        from app.services.literature_service import literature_service
        literature_service.search_literature = MagicMock(return_value={"papers": [sample_raw_paper], "total_count": 1})
        res = search_literature(query)
        assert res["total_count"] == 1
        assert len(res["papers"]) == 1

def test_api_papers_and_collections(temp_workspace, sample_raw_paper):
    paper_meta = PaperMetadata(**sample_raw_paper)
    req = ImportRequest(papers=[paper_meta], target_collection="test_col")
    
    # Import
    import_res = import_papers(req)
    assert import_res["status"] == "success"
    assert import_res["imported_count"] == 1

    # List
    list_res = list_papers()
    assert list_res["total"] >= 1
    assert any(p["id"] == sample_raw_paper["id"] for p in list_res["papers"])

    # Detail
    detail_res = get_paper_detail(sample_raw_paper["id"])
    assert detail_res["metadata"]["title"] == sample_raw_paper["title"]

    # Notes
    notes_req = NotesUpdateRequest(notes="Excellent reference on language models.")
    note_res = update_notes(sample_raw_paper["id"], notes_req)
    assert note_res["status"] == "success"

    # Collections
    col_req = CollectionCreateRequest(name="Foundations", description="Fundamental works.")
    create_col_res = create_or_update_collection(col_req)
    assert create_col_res["status"] == "success"
    assert create_col_res["collection"]["name"] == "Foundations"

    cols_res = list_collections()
    assert any(c["name"] == "Foundations" for c in cols_res["collections"])

    # Delete collection
    del_res = delete_collection(create_col_res["collection"]["id"])
    assert del_res["status"] == "success"

def test_api_analyzer_controls(temp_workspace):
    # Progress
    prog = get_progress()
    assert hasattr(prog, "percent_complete")

    # Start
    bg_tasks = BackgroundTasks()
    start_res = start_analysis(StartAnalysisRequest(), bg_tasks)
    assert start_res["status"] in ["started", "already_running"]

    # Pause / Resume / Cancel
    pause_res = pause_analysis()
    assert pause_res["status"] == "paused"

    resume_res = resume_analysis()
    assert resume_res["status"] == "resumed"

    cancel_res = cancel_analysis()
    assert cancel_res["status"] == "cancelled"

    # Retry
    retry_res = retry_failed(bg_tasks)
    assert "status" in retry_res

def test_api_graph_and_analytics(temp_workspace, sample_raw_paper):
    from app.services.paper_service import paper_service
    paper_service.import_paper(sample_raw_paper)

    # Graph
    graph_data = get_knowledge_graph()
    assert "elements" in graph_data
    assert "stats" in graph_data

    # Ego Graph
    ego_data = get_paper_ego_graph(sample_raw_paper["id"])
    assert ego_data["stats"]["center_paper_id"] == sample_raw_paper["id"]

    # Intersections
    inter_data = get_candidate_intersections()
    assert "intersections" in inter_data

    # Trends
    trends_data = get_trends()
    assert "total_analyzed" in trends_data

def test_api_export_endpoint(temp_workspace, sample_raw_paper):
    from app.services.paper_service import paper_service
    paper_service.import_paper(sample_raw_paper)

    export_req = ExportRequest(format="json")
    res = export_research(export_req)
    assert res["format"] == "json"
    assert "filename" in res
    assert "content" in res

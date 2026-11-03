"""
PaperGraph API Submodule
"""
from app.api.workspace import router as workspace_router
from app.api.search import router as search_router
from app.api.papers import router as papers_router
from app.api.analyzer import router as analyzer_router
from app.api.graph import router as graph_router
from app.api.intersections import router as intersections_router
from app.api.trends import router as trends_router
from app.api.export import router as export_router

__all__ = [
    "workspace_router",
    "search_router",
    "papers_router",
    "analyzer_router",
    "graph_router",
    "intersections_router",
    "trends_router",
    "export_router"
]


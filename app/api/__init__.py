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
from app.api.synthesis import router as synthesis_router
from app.api.hypotheses import router as hypotheses_router
from app.api.review import router as review_router
from app.api.ai_config import router as ai_config_router

__all__ = [
    "workspace_router",
    "search_router",
    "papers_router",
    "analyzer_router",
    "graph_router",
    "intersections_router",
    "trends_router",
    "export_router",
    "synthesis_router",
    "hypotheses_router",
    "review_router",
    "ai_config_router"
]


"""
PaperGraph V3 Main Application Server
Unified server providing:
- Baseline API compatibility for pixel-identical UI (Workspace, Folder Scanner, Papers, Analyzer, Graph, Hypotheses)
- V3 Autonomous OCR-First & Plugin Endpoints (/api/v3)
"""
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import config
from app.core.workspace_manager import workspace_manager
from app.api import (
    workspace_router,
    search_router,
    papers_router,
    analyzer_router,
    graph_router,
    intersections_router,
    trends_router,
    export_router,
    synthesis_router,
    hypotheses_router,
    review_router,
    ai_config_router,
    v3_router,
    tools_router
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("papergraph.v3")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        active_ws = config.get_active_workspace()
        if not (active_ws / "workspace.json").exists():
            workspace_manager.create_workspace(path=active_ws, name="PaperGraph V3 Research Workspace")
            logger.info(f"Initialized default workspace at {active_ws}")
        else:
            logger.info(f"Loaded existing workspace at {active_ws}")
    except Exception as e:
        logger.warning(f"Failed to auto-initialize default workspace: {e}")
    yield

app = FastAPI(
    title=config.app_name,
    version=config.version,
    description="PaperGraph V3 - Local-first research intelligence, autonomous Surya OCR 2, and evidence graph.",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": config.app_name,
        "version": config.version,
        "active_workspace": str(workspace_manager.workspace_path)
    }

# Include All API Routers (Full Baseline Compatibility + V3 Extensions)
app.include_router(workspace_router)
app.include_router(search_router)
app.include_router(papers_router)
app.include_router(analyzer_router)
app.include_router(graph_router)
app.include_router(intersections_router)
app.include_router(trends_router)
app.include_router(export_router)
app.include_router(synthesis_router)
app.include_router(hypotheses_router)
app.include_router(review_router)
app.include_router(ai_config_router)
app.include_router(v3_router)
app.include_router(tools_router)

# Mount frontend directory for static assets
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(frontend_dir / "index.html")

    @app.get("/favicon.ico")
    def serve_favicon():
        fav = frontend_dir / "favicon.ico"
        if fav.exists():
            return FileResponse(fav)
        return FileResponse(frontend_dir / "index.html")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred.", "error": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

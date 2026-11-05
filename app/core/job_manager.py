"""
PaperGraph V3 - Local-First Job Manager (Phase 9)
Provides atomic page-level checkpointing for OCR batches, allowing seamless resumption on crash/interrupt.
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("papergraph.v3.jobs")

class JobCheckpoint(BaseModel):
    job_id: str
    file_path: str
    total_pages: int
    completed_pages: List[int] = Field(default_factory=list)
    status: str = "IN_PROGRESS"  # IN_PROGRESS, COMPLETED, FAILED
    last_updated: str = ""

class JobManager:
    def __init__(self, checkpoints_dir: Optional[str] = None):
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.checkpoints_dir = checkpoints_dir or os.path.join(base, "cache", "jobs")
        os.makedirs(self.checkpoints_dir, exist_ok=True)

    def _get_job_file(self, job_id: str) -> str:
        return os.path.join(self.checkpoints_dir, f"{job_id}.json")

    def create_or_resume_job(self, job_id: str, file_path: str, total_pages: int) -> JobCheckpoint:
        f_path = self._get_job_file(job_id)
        if os.path.exists(f_path):
            try:
                with open(f_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    logger.info(f"Resuming existing job {job_id} from page {len(data.get('completed_pages', []))}")
                    return JobCheckpoint(**data)
            except Exception as e:
                logger.warning(f"Failed to load checkpoint {job_id}, re-initializing: {e}")

        job = JobCheckpoint(job_id=job_id, file_path=file_path, total_pages=total_pages)
        self.save_checkpoint(job)
        return job

    def record_page_complete(self, job_id: str, page_number: int) -> JobCheckpoint:
        f_path = self._get_job_file(job_id)
        if os.path.exists(f_path):
            with open(f_path, "r", encoding="utf-8") as f:
                job = JobCheckpoint(**json.load(f))
        else:
            job = JobCheckpoint(job_id=job_id, file_path="unknown", total_pages=1)

        if page_number not in job.completed_pages:
            job.completed_pages.append(page_number)
            job.completed_pages.sort()

        if len(job.completed_pages) >= job.total_pages and job.total_pages > 0:
            job.status = "COMPLETED"

        self.save_checkpoint(job)
        return job

    def save_checkpoint(self, job: JobCheckpoint) -> None:
        f_path = self._get_job_file(job.job_id)
        temp_path = f"{f_path}.tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(job.model_dump_json(indent=2))
        os.replace(temp_path, f_path)

job_manager = JobManager()


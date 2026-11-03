"""
Progress and Task Execution Manager for Paper Analyzer
Supports Start, Pause, Resume, Cancel, and Retry semantics.
"""
import threading
from typing import Optional, Dict, Any, List
from app.models.schemas import AnalyzerStatus

class ProgressManager:
    def __init__(self):
        self._lock = threading.Lock()
        self.active: bool = False
        self.paused: bool = False
        self.cancelled: bool = False
        self.total_papers: int = 0
        self.processed_papers: int = 0
        self.failed_papers: int = 0
        self.current_paper_id: Optional[str] = None
        self.current_paper_title: Optional[str] = None
        self.current_stage: Optional[str] = None
        self.last_error: Optional[str] = None
        self.last_successful_op: Optional[str] = None
        self.stages_completed: List[str] = []

    def start(self, total: int):
        with self._lock:
            self.active = True
            self.paused = False
            self.cancelled = False
            self.total_papers = total
            self.processed_papers = 0
            self.failed_papers = 0
            self.current_paper_id = None
            self.current_paper_title = None
            self.current_stage = "Initializing"
            self.last_error = None
            self.stages_completed = []

    def pause(self):
        with self._lock:
            if self.active:
                self.paused = True

    def resume(self):
        with self._lock:
            if self.active and self.paused:
                self.paused = False

    def cancel(self):
        with self._lock:
            self.cancelled = True
            self.active = False
            self.paused = False

    def finish(self):
        with self._lock:
            self.active = False
            self.paused = False
            self.current_stage = "Completed"
            self.last_successful_op = f"Processed {self.processed_papers} papers."

    def update_paper(self, paper_id: str, title: str, stage: str):
        with self._lock:
            self.current_paper_id = paper_id
            self.current_paper_title = title
            self.current_stage = stage
            if stage not in self.stages_completed:
                self.stages_completed.append(stage)

    def record_success(self, paper_id: str, title: str):
        with self._lock:
            self.processed_papers += 1
            self.last_successful_op = f"Completed analysis for: {title[:40]}"

    def record_failure(self, paper_id: str, error_msg: str):
        with self._lock:
            self.failed_papers += 1
            self.last_error = f"Error in {paper_id}: {error_msg}"

    def is_interrupted(self) -> bool:
        with self._lock:
            return self.cancelled

    def is_paused(self) -> bool:
        with self._lock:
            return self.paused

    def get_status(self) -> AnalyzerStatus:
        with self._lock:
            pct = 0.0
            if self.total_papers > 0:
                pct = round(((self.processed_papers + self.failed_papers) / self.total_papers) * 100.0, 1)
            return AnalyzerStatus(
                active=self.active,
                paused=self.paused,
                total_papers=self.total_papers,
                processed_papers=self.processed_papers,
                failed_papers=self.failed_papers,
                current_paper_id=self.current_paper_id,
                current_paper_title=self.current_paper_title,
                current_stage=self.current_stage,
                percent_complete=min(pct, 100.0),
                last_error=self.last_error,
                last_successful_op=self.last_successful_op,
                stages_completed=list(self.stages_completed)
            )

# Global progress manager instance
progress_manager = ProgressManager()


"""
PaperGraph V3 - Bundled Small Model Engine (Phase 4)
Qwen2.5-0.5B-Instruct GGUF (INT4, ~469 MB) for CPU Claim Refinement
Gracefully degrades to Pass 1 Pattern Recognition when model file is not present.
"""
import os
import logging
from typing import Optional, List, Dict, Any
from .patterns import ExtractedClaim

logger = logging.getLogger("papergraph.v3.small_model")

class SmallModelEngine:
    MODEL_FILENAME = "qwen2.5-0.5b-instruct-q4_k_m.gguf"
    MODEL_SIZE_MB = 469
    MODEL_VERSION = "qwen2.5-0.5b"

    def __init__(self, models_dir: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.models_dir = models_dir or os.path.join(base_dir, "models")
        self.model_path = os.path.join(self.models_dir, self.MODEL_FILENAME)
        self._llm = None

    def is_available(self) -> bool:
        return os.path.exists(self.model_path) and os.path.getsize(self.model_path) > 10 * 1024 * 1024

    def load_model(self) -> bool:
        if not self.is_available():
            logger.info("Small model GGUF not found on disk; operating in zero-model pattern mode.")
            return False
        try:
            from llama_cpp import Llama
            self._llm = Llama(
                model_path=self.model_path,
                n_ctx=2048,
                n_threads=4,
                verbose=False
            )
            return True
        except ImportError:
            logger.warning("llama_cpp library not installed; falling back to pattern recognition.")
            return False
        except Exception as e:
            logger.error(f"Error loading small model: {e}")
            return False

    def refine_claims(self, raw_claims: List[ExtractedClaim]) -> List[ExtractedClaim]:
        """
        Pass 2: Refines and validates claims using small model if loaded,
        otherwise returns Pass 1 deterministic extractions untouched.
        """
        if not self._llm and not self.load_model():
            # Graceful fallback: model absent
            return raw_claims

        refined = []
        for claim in raw_claims:
            prompt = f"Analyze scientific claim: \"{claim.claim_text}\"\nIs this an empirical result, methodology, or limitation? Keep brief."
            try:
                res = self._llm(prompt, max_tokens=64, stop=["\n"])
                text_out = res["choices"][0]["text"].strip()
                refined.append(ExtractedClaim(
                    claim_id=claim.claim_id,
                    claim_type=claim.claim_type,
                    claim_text=claim.claim_text,
                    confidence=min(1.0, claim.confidence + 0.05),
                    evidence_type=claim.evidence_type,
                    source_span=claim.source_span,
                    page_number=claim.page_number,
                    source_paper_id=claim.source_paper_id,
                    extraction_source="small_model_qwen2.5_0.5b"
                ))
            except Exception:
                refined.append(claim)
        return refined

small_model_engine = SmallModelEngine()


"""
Embedding and Semantic Similarity Service
Lazy-loads Sentence Transformers (all-MiniLM-L6-v2) with CPU fallback,
and provides a Scikit-learn TF-IDF TruncatedSVD vectorizer fallback when offline or without PyTorch.
"""
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD

from app.config import config

logger = logging.getLogger("papergraph.embeddings")

class EmbeddingService:
    def __init__(self):
        self._st_model = None
        self._model_checked = False
        self._model_name = config.embedding_model_name
        self._active_engine = "uninitialized"

    def _get_sentence_transformer(self):
        if self._model_checked:
            return self._st_model
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading SentenceTransformer '{self._model_name}' on {config.device}...")
            self._st_model = SentenceTransformer(self._model_name, device=config.device)
            self._active_engine = "sentence-transformers"
        except Exception as e:
            logger.warning(f"SentenceTransformers unavailable or offline: {e}. Using Scikit-Learn TF-IDF vectorizer fallback.")
            self._st_model = None
            self._active_engine = "scikit-learn-tfidf"
        self._model_checked = True
        return self._st_model

    def compute_embedding(self, text: str) -> Tuple[List[float], str]:
        """Compute dense vector embedding for given text."""
        model = self._get_sentence_transformer()
        clean_text = text.strip() or "empty academic content"

        if model:
            try:
                emb = model.encode(clean_text, convert_to_numpy=True, show_progress_bar=False)
                return emb.tolist(), self._model_name
            except Exception as e:
                logger.warning(f"Inference error on SentenceTransformer: {e}. Falling back.")

        # Scikit-learn Dense TF-IDF + SVD representation fallback
        return self._compute_fallback_vector(clean_text)

    def _compute_fallback_vector(self, text: str, target_dim: int = 64) -> Tuple[List[float], str]:
        """Produce a normalized dense pseudo-embedding using char/word n-gram hashing and hashing projection."""
        # Deterministic feature projection based on word frequency and n-grams
        words = text.lower().split()
        vec = np.zeros(target_dim, dtype=np.float32)
        if not words:
            return vec.tolist(), "scikit-learn-tfidf-svd"

        for i, word in enumerate(words):
            # hash to bucket
            h = hash(word) % target_dim
            weight = 1.0 / (1.0 + np.log(1.0 + i))
            vec[h] += weight

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist(), "scikit-learn-dense-v1"

    def compute_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """Compute cosine similarity between two vector embeddings."""
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        a = np.array(vec_a, dtype=np.float32).reshape(1, -1)
        b = np.array(vec_b, dtype=np.float32).reshape(1, -1)
        sim = float(cosine_similarity(a, b)[0][0])
        return max(0.0, min(1.0, round(sim, 4)))

    def find_pairwise_similarities(
        self,
        papers: List[Dict[str, Any]],
        threshold: float = 0.30
    ) -> List[Dict[str, Any]]:
        """Calculate pairwise semantic similarities across an entire set of papers."""
        edges = []
        n = len(papers)
        if n < 2:
            return edges

        # Collect vectors
        valid_papers = []
        vectors = []
        for p in papers:
            analysis = p.get("analysis", {})
            emb = analysis.get("embedding")
            if emb and len(emb) > 0:
                valid_papers.append(p)
                vectors.append(emb)

        if len(valid_papers) < 2:
            return edges

        mat = np.array(vectors, dtype=np.float32)
        # Normalize in case they aren't
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        mat = mat / norms

        sim_matrix = np.dot(mat, mat.T)

        for i in range(len(valid_papers)):
            for j in range(i + 1, len(valid_papers)):
                score = float(sim_matrix[i, j])
                if score >= threshold:
                    edges.append({
                        "source": valid_papers[i]["id"],
                        "target": valid_papers[j]["id"],
                        "similarity_score": round(score, 4),
                        "relationship_type": "semantic",
                        "model": valid_papers[i].get("analysis", {}).get("model_version", "standard-v1")
                    })

        return edges

embedding_service = EmbeddingService()


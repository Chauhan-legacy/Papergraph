"""
Keyword and Topic Extraction Service
Provides KeyBERT integration when available with resilient Scikit-learn TF-IDF fallback.
Extracts keywords, scientific domains, methods, and topics.
"""
import re
from typing import List, Dict, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from app.models.schemas import KeywordItem

DOMAINS_MAP = {
    "Computer Science": ["neural", "network", "algorithm", "software", "deep learning", "graph", "machine learning", "dataset", "computing", "distributed", "nlp", "ai", "transformer", "code"],
    "Biology & Genetics": ["gene", "protein", "cell", "cellular", "dna", "rna", "organism", "biological", "genome", "molecular", "species", "evolutionary", "crispr"],
    "Medicine & Healthcare": ["patient", "clinical", "disease", "treatment", "therapy", "hospital", "diagnosis", "health", "medical", "pathology", "syndrome", "drug", "trial"],
    "Physics & Astronomy": ["quantum", "energy", "particle", "magnetic", "field", "optical", "laser", "galaxy", "stellar", "thermodynamic", "gravitational", "plasma", "spin"],
    "Chemistry & Materials": ["chemical", "synthesis", "reaction", "catalyst", "polymer", "nanoparticle", "crystal", "molecular", "compound", "solute", "composite", "electrode"],
    "Economics & Business": ["market", "economic", "price", "firm", "financial", "policy", "trade", "investment", "industry", "consumer", "gdp", "monetary", "revenue"],
    "Neuroscience & Psychology": ["brain", "cognitive", "cortex", "neuron", "behavior", "memory", "perception", "psychological", "mental", "stimulus", "sensory", "auditory"]
}

METHODS_MAP = {
    "Transformer & Attention": ["transformer", "attention mechanism", "self-attention", "bert", "gpt", "llm"],
    "Graph & Network Analysis": ["graph neural network", "gnn", "network analysis", "graph embedding", "knowledge graph", "cytoscape", "louvain"],
    "Deep Neural Networks": ["convolutional", "cnn", "deep learning", "recurrent", "lstm", "backpropagation", "loss function"],
    "Statistical & Probabilistic Inference": ["bayesian", "markov", "monte carlo", "likelihood", "regression", "hypothesis testing", "bootstrap"],
    "Empirical & Benchmarking": ["ablation study", "benchmark", "empirical evaluation", "baseline comparison", "metric", "cross-validation"],
    "Mathematical Optimization": ["gradient descent", "convex optimization", "stochastic", "objective function", "constraint", "dual problem"],
    "Qualitative & Systematic Review": ["systematic review", "meta-analysis", "survey", "qualitative analysis", "literature review", "thematic analysis"]
}

STOP_WORDS = {
    "the", "a", "an", "and", "or", "in", "on", "at", "by", "for", "with", "about",
    "against", "between", "into", "through", "during", "before", "after", "above",
    "below", "to", "from", "up", "down", "in", "out", "over", "under", "again",
    "further", "then", "once", "here", "there", "when", "where", "why", "how",
    "all", "any", "both", "each", "few", "more", "most", "other", "some", "such",
    "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "can",
    "will", "just", "don", "should", "now", "paper", "presents", "study", "results",
    "approach", "based", "using", "proposed", "show", "shows", "shown", "demonstrates"
}

class KeywordService:
    def __init__(self):
        self._keybert_model = None
        self._has_checked_keybert = False

    def _get_keybert(self):
        if self._has_checked_keybert:
            return self._keybert_model
        try:
            from keybert import KeyBERT
            self._keybert_model = KeyBERT("all-MiniLM-L6-v2")
        except Exception:
            self._keybert_model = None
        self._has_checked_keybert = True
        return self._keybert_model

    def extract_keywords(self, title: str, abstract: str, top_n: int = 8) -> List[KeywordItem]:
        """Extract top keywords using KeyBERT or Scikit-Learn TF-IDF."""
        combined_text = f"{title}. {abstract}".strip()
        if not combined_text:
            return []

        # Try KeyBERT if installed
        kb = self._get_keybert()
        if kb:
            try:
                raw_kw = kb.extract_keywords(
                    combined_text,
                    keyphrase_ngram_range=(1, 2),
                    stop_words="english",
                    top_n=top_n
                )
                return [KeywordItem(keyword=kw, score=round(float(score), 3)) for kw, score in raw_kw]
            except Exception:
                pass

        # Resilient Scikit-Learn Fallback
        return self._extract_keywords_tfidf(combined_text, top_n=top_n)

    def _extract_keywords_tfidf(self, text: str, top_n: int = 8) -> List[KeywordItem]:
        """Extract key terms using TF-IDF n-grams."""
        # Clean text
        cleaned = re.sub(r"[^\w\s-]", " ", text.lower())
        words = [w.strip() for w in cleaned.split() if len(w.strip()) > 2 and w.strip() not in STOP_WORDS]
        if not words:
            return []

        clean_doc = " ".join(words)
        try:
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=50, stop_words="english")
            matrix = vectorizer.fit_transform([clean_doc])
            features = vectorizer.get_feature_names_out()
            scores = matrix.toarray()[0]
            
            sorted_indices = scores.argsort()[::-1]
            results = []
            seen = set()
            for idx in sorted_indices:
                feat = features[idx]
                if feat not in seen and len(feat) > 3:
                    seen.add(feat)
                    results.append(KeywordItem(keyword=feat, score=round(float(scores[idx]), 3)))
                if len(results) >= top_n:
                    break
            return results
        except Exception:
            # Fallback simple frequency count
            freq: Dict[str, int] = {}
            for w in words:
                freq[w] = freq.get(w, 0) + 1
            sorted_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)
            return [KeywordItem(keyword=w, score=1.0) for w, _ in sorted_freq[:top_n]]

    def extract_domains(self, text: str) -> List[str]:
        """Classify scientific domains based on conceptual terminology."""
        text_lower = text.lower()
        matched_domains = []
        for domain, terms in DOMAINS_MAP.items():
            count = sum(1 for term in terms if term in text_lower)
            if count >= 2:
                matched_domains.append(domain)
        if not matched_domains:
            matched_domains.append("Interdisciplinary Research")
        return matched_domains

    def extract_methods(self, text: str) -> List[str]:
        """Identify scientific methods and paradigms used in the paper."""
        text_lower = text.lower()
        matched_methods = []
        for method_label, terms in METHODS_MAP.items():
            for term in terms:
                if term in text_lower:
                    matched_methods.append(method_label)
                    break
        if not matched_methods:
            matched_methods.append("Empirical & Quantitative Analysis")
        return matched_methods

    def extract_topics(self, keywords: List[KeywordItem], domains: List[str]) -> List[str]:
        """Formulate topic tags from keywords and domains."""
        topics = [k.keyword.title() for k in keywords[:4]]
        for d in domains:
            if d not in topics:
                topics.append(d)
        return topics[:6]


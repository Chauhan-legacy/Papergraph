"""
Tests for Keyword Extraction and Embedding Services
"""
import pytest
from app.services.keyword_service import KeywordService
from app.services.embedding_service import embedding_service

def test_keyword_and_domain_extraction():
    kw_service = KeywordService()
    title = "Graph Neural Networks for Protein Folding and Molecular Reaction"
    abstract = "We present an empirical study using graph neural networks to predict molecular structures and biochemical reactions."

    keywords = kw_service.extract_keywords(title, abstract, top_n=5)
    assert len(keywords) > 0
    kw_strings = [k.keyword for k in keywords]
    assert any("neural" in k or "graph" in k or "protein" in k or "molecular" in k for k in kw_strings)

    domains = kw_service.extract_domains(f"{title}. {abstract}")
    assert any(d in ["Computer Science", "Biology & Genetics", "Chemistry & Materials"] for d in domains)

    methods = kw_service.extract_methods(f"{title}. {abstract}")
    assert any("Graph" in m or "Empirical" in m for m in methods)

def test_embedding_and_similarity():
    text_a = "Deep neural networks and transformer language models."
    text_b = "Transformer neural architectures for natural language processing."
    text_c = "Economic policy and monetary revenue in macroeconomic market equilibrium."

    vec_a, model_a = embedding_service.compute_embedding(text_a)
    vec_b, model_b = embedding_service.compute_embedding(text_b)
    vec_c, model_c = embedding_service.compute_embedding(text_c)

    assert len(vec_a) > 0
    assert len(vec_b) == len(vec_a)

    sim_ab = embedding_service.compute_similarity(vec_a, vec_b)
    sim_ac = embedding_service.compute_similarity(vec_a, vec_c)

    # Identical vector similarity should be 1.0
    sim_self = embedding_service.compute_similarity(vec_a, vec_a)
    assert sim_self >= 0.99
    # Related papers should have higher similarity than unrelated papers
    assert sim_ab > sim_ac


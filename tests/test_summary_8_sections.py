import pytest
from app.services.summary_service import SummaryService

def test_summary_8_sections_from_abstract():
    meta = {
        "id": "test_p1",
        "title": "Scaling Laws for Autoregressive Generative Models",
        "authors": ["Tom Henighan", "Jared Kaplan"],
        "venue": "arXiv",
        "publication_year": 2020
    }
    abstract = (
        "We investigate empirical scaling laws for language, video, and audio autoregressive modeling. "
        "Performance improves as a power-law with model size and computation across all data modalities. "
        "Our methodology evaluates diverse Transformer architectures under controlled compute budgets. "
        "Experiments on multimodal benchmarks show consistent power-law coefficients. "
        "However, our analysis is limited to dense architectures and does not address mixture-of-experts."
    )
    keywords = ["Scaling Laws", "Autoregressive Models", "Transformers", "Compute Efficiency"]

    summary = SummaryService.generate_structured_summary(meta, abstract, keywords)

    assert summary.paper_id == "test_p1"
    assert "Abstract-only" in summary.scope
    assert len(summary.research_objective) > 10
    assert len(summary.research_problem) > 10
    assert len(summary.methodology) > 10
    assert len(summary.dataset_or_materials) > 10
    assert len(summary.main_findings) > 10
    assert len(summary.contributions) > 10
    assert len(summary.limitations) > 10
    assert len(summary.future_directions) > 10

def test_summary_8_sections_from_full_text():
    meta = {
        "id": "test_p2",
        "title": "Efficient Zero-Shot Classification via Semantic Nearest Neighbors",
        "authors": ["Elena Weber"],
        "venue": "ICLR",
        "publication_year": 2023
    }
    abstract = "We present an efficient zero-shot classification framework."
    full_text = (
        "We present an efficient zero-shot classification framework for text and images. "
        "The problem of excessive latency in zero-shot inference remains a barrier to real-time deployment. "
        "Our proposed methodology employs hierarchical semantic nearest neighbors on pre-trained embedding spaces. "
        "We evaluate on ImageNet-1K and Stanford Sentiment Treebank datasets across multiple model sizes. "
        "The results demonstrate an 8x throughput improvement while retaining 99.2% of baseline accuracy. "
        "We contribute an open-source indexing pipeline and formal complexity bounds. "
        "A primary limitation is increased RAM footprint required for the spatial kd-tree structure. "
        "Promising future research directions include quantization and disk-backed memory mapping."
    )
    keywords = ["Zero-Shot", "Nearest Neighbors", "ImageNet", "Inference Optimization"]

    summary = SummaryService.generate_structured_summary(meta, abstract, keywords, full_text=full_text)

    assert "Full Paper Text" in summary.scope
    assert "methodology" in summary.methodology.lower() or "propose" in summary.methodology.lower() or len(summary.methodology) > 10
    assert "limitation" in summary.limitations.lower() or len(summary.limitations) > 10
    assert len(summary.future_directions) > 10

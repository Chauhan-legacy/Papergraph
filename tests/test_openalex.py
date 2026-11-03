"""
Tests for OpenAlex Provider and Abstract Reconstruction
"""
import pytest
from unittest.mock import MagicMock
from app.providers.openalex import OpenAlexProvider, reconstruct_abstract

def test_reconstruct_abstract():
    inverted_index = {
        "is": [2],
        "Artificial": [0],
        "Intelligence": [1],
        "transforming": [3],
        "science.": [4]
    }
    reconstructed = reconstruct_abstract(inverted_index)
    assert reconstructed == "Artificial Intelligence is transforming science."

def test_reconstruct_abstract_empty_and_none():
    assert reconstruct_abstract({}) == ""
    assert reconstruct_abstract(None) == ""
    assert reconstruct_abstract("not a dict") == ""

def test_openalex_provider_mocked_search(sample_raw_paper):
    provider = OpenAlexProvider()
    
    mock_response = {
        "meta": {"count": 1, "page": 1, "per_page": 20},
        "results": [
            {
                "id": "https://openalex.org/W2741809807",
                "doi": "https://doi.org/10.1038/s41586-020-2649-2",
                "title": "Language Models are Few-Shot Learners",
                "authorships": [
                    {
                        "author": {"display_name": "Tom Brown", "orcid": None},
                        "institutions": [{"display_name": "OpenAI"}]
                    }
                ],
                "publication_year": 2020,
                "publication_date": "2020-07-22",
                "primary_location": {
                    "source": {"display_name": "NeurIPS"},
                    "landing_page_url": "https://doi.org/10.1038/s41586-020-2649-2"
                },
                "cited_by_count": 14500,
                "referenced_works": ["https://openalex.org/W2145678901"],
                "abstract_inverted_index": {
                    "Recent": [0],
                    "advances": [1],
                    "in": [2],
                    "NLP.": [3]
                }
            }
        ]
    }

    provider._request_with_retry = MagicMock(return_value=mock_response)

    results = provider.search(query="few-shot learners")
    assert results["total_count"] == 1
    assert len(results["papers"]) == 1
    paper = results["papers"][0]
    assert paper["id"] == "W2741809807"
    assert paper["title"] == "Language Models are Few-Shot Learners"
    assert paper["authors"][0]["name"] == "Tom Brown"
    assert paper["abstract"] == "Recent advances in NLP."
    assert paper["citation_count"] == 14500
    assert "W2145678901" in paper["referenced_works"]


"""
Data Models and Schemas for PaperGraph
"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field

class AuthorInfo(BaseModel):
    name: str
    institution: Optional[str] = None
    orcid: Optional[str] = None

class PaperMetadata(BaseModel):
    id: str
    openalex_id: Optional[str] = None
    doi: Optional[str] = None
    title: str
    authors: List[Union[AuthorInfo, str]] = Field(default_factory=list)
    publication_year: Optional[int] = None
    publication_date: Optional[str] = None
    venue: Optional[str] = "Unknown Venue"
    source_provider: str = "openalex"
    source_url: Optional[str] = None
    citation_count: int = 0
    referenced_works: List[str] = Field(default_factory=list)
    abstract_available: bool = False
    retrieval_date: str = ""
    processing_status: str = "Discovered"  # Discovered, Imported, Abstract Processed, Summary Generated, Analysis Completed, Graph Processed, Failed, Awaiting Retry
    collections: List[str] = Field(default_factory=list)
    stage_history: List[Dict[str, Any]] = Field(default_factory=list)

class KeywordItem(BaseModel):
    keyword: str
    score: float = 1.0

class PaperSummary(BaseModel):
    paper_id: str
    title: str
    research_objective: str = ""
    research_problem: str = ""
    methodology: str = ""
    dataset_or_materials: str = ""
    main_findings: str = ""
    contributions: str = ""
    limitations: str = ""
    future_directions: str = ""
    important_keywords: List[str] = Field(default_factory=list)
    potential_connections: List[str] = Field(default_factory=list)
    scope: str = "Abstract-only"
    generated_at: str = ""
    model_used: str = "Rule-based/NLP"

class PaperAnalysis(BaseModel):
    paper_id: str
    keywords: List[KeywordItem] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    methods: List[str] = Field(default_factory=list)
    scientific_domains: List[str] = Field(default_factory=list)
    concepts: List[str] = Field(default_factory=list)
    embedding: Optional[List[float]] = None
    embedding_dim: Optional[int] = None
    model_version: str = "standard-v1"
    processing_timestamp: str = ""
    semantic_similarities: List[Dict[str, Any]] = Field(default_factory=list)

class Collection(BaseModel):
    id: str
    name: str
    description: str = ""
    paper_ids: List[str] = Field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

class WorkspaceInfo(BaseModel):
    workspace_path: str
    workspace_name: str
    version: str = "1.0.0"
    paper_count: int = 0
    completed_analyses: int = 0
    pending_analyses: int = 0
    collections_count: int = 0
    created_at: str = ""
    updated_at: str = ""
    settings: Dict[str, Any] = Field(default_factory=dict)

class SearchQuery(BaseModel):
    query: str
    filter_type: str = "all"  # all, topic, keyword, author, doi, title
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    page: int = 1
    per_page: int = 20
    sort: Optional[str] = None

class ImportRequest(BaseModel):
    papers: List[PaperMetadata]
    target_collection: Optional[str] = None

class AnalyzerStatus(BaseModel):
    active: bool = False
    paused: bool = False
    total_papers: int = 0
    processed_papers: int = 0
    failed_papers: int = 0
    current_paper_id: Optional[str] = None
    current_paper_title: Optional[str] = None
    current_stage: Optional[str] = None
    percent_complete: float = 0.0
    last_error: Optional[str] = None
    last_successful_op: Optional[str] = None
    stages_completed: List[str] = Field(default_factory=list)

class GraphData(BaseModel):
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)
    clusters: List[Dict[str, Any]] = Field(default_factory=list)
    stats: Dict[str, Any] = Field(default_factory=dict)

class ResearchIntersection(BaseModel):
    id: str
    domain_a: str
    domain_b: str
    candidate_topics: List[str] = Field(default_factory=list)
    supporting_papers: List[Dict[str, Any]] = Field(default_factory=list)
    relevant_keywords: List[str] = Field(default_factory=list)
    semantic_evidence: str = ""
    citation_evidence: Optional[str] = None
    reason_suggested: str = ""
    limitations: str = ""
    confidence_score: float = 0.0

class TrendSummary(BaseModel):
    publications_by_year: Dict[str, int] = Field(default_factory=dict)
    top_topics: List[Dict[str, Any]] = Field(default_factory=list)
    top_keywords: List[Dict[str, Any]] = Field(default_factory=list)
    domain_distributions: List[Dict[str, Any]] = Field(default_factory=list)
    total_analyzed: int = 0
    warnings: List[str] = Field(default_factory=list)

# -------------------------------------------------------------
# Research Intelligence Evolution Models
# -------------------------------------------------------------

class ScientificClaim(BaseModel):
    claim_id: str
    paper_id: str
    paper_title: str
    claim_text: str
    category: str = "result"  # problem, methodology, result, limitation, contribution
    epistemic_status: str = "REPORTED"  # REPORTED, DERIVED, INFERRED, SPECULATION, HYPOTHESIS
    source_excerpt: str = ""
    section_hint: Optional[str] = None
    confidence: float = 0.85

class ProfessorAnalysis(BaseModel):
    paper_id: str
    title: str
    scope: str = "Abstract-only"
    research_problem: Dict[str, str] = Field(default_factory=dict)
    methodology: Dict[str, str] = Field(default_factory=dict)
    results: Dict[str, str] = Field(default_factory=dict)
    critical_evaluation: Dict[str, str] = Field(default_factory=dict)
    scientific_significance: Dict[str, str] = Field(default_factory=dict)
    professor_explanation: Dict[str, str] = Field(default_factory=dict)
    claims: List[ScientificClaim] = Field(default_factory=list)
    generated_at: str = ""
    model_used: str = "PaperGraph Rigorous Academic Engine v4.0"

class CrossPaperComparison(BaseModel):
    comparison_id: str
    paper_ids: List[str]
    paper_titles: Dict[str, str] = Field(default_factory=dict)
    dimensions: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    consensus_points: List[str] = Field(default_factory=list)
    disagreement_points: List[Dict[str, Any]] = Field(default_factory=list)
    methodological_divergence: List[str] = Field(default_factory=list)
    created_at: str = ""

class EvidenceMatrixRow(BaseModel):
    paper_id: str
    title: str
    year: Optional[int] = None
    authors: str = "Unknown"
    method: str = "Not specified"
    dataset: str = "Not specified"
    main_finding: str = ""
    key_limitation: str = ""
    epistemic_grade: str = "High"  # High, Moderate, Preliminary, Theoretical
    confidence_score: float = 0.85

class EvidenceMatrixResponse(BaseModel):
    rows: List[EvidenceMatrixRow] = Field(default_factory=list)
    total_papers: int = 0
    filters_applied: Dict[str, Any] = Field(default_factory=dict)

class CorpusPatterns(BaseModel):
    repeated_methods: List[Dict[str, Any]] = Field(default_factory=list)
    recurring_datasets: List[Dict[str, Any]] = Field(default_factory=list)
    common_limitations: List[Dict[str, Any]] = Field(default_factory=list)
    frequently_studied_variables: List[Dict[str, Any]] = Field(default_factory=list)
    emerging_techniques: List[Dict[str, Any]] = Field(default_factory=list)
    foundational_citations: List[Dict[str, Any]] = Field(default_factory=list)
    total_analyzed_papers: int = 0

class CandidateResearchQuestion(BaseModel):
    id: str
    title: str
    category: str = "Unanswered Question"  # Unanswered Question, Methodological Cross-Pollination, Limitation Resolution, Frontier Synthesis
    suggested_hypothesis: str = ""
    why_suggested: str = ""
    supporting_papers: List[Dict[str, Any]] = Field(default_factory=list)
    supporting_evidence: List[str] = Field(default_factory=list)
    contradictory_or_limiting_evidence: List[str] = Field(default_factory=list)
    relevant_existing_literature: List[str] = Field(default_factory=list)
    possible_methodological_approaches: List[str] = Field(default_factory=list)
    confidence_and_uncertainty: str = ""
    additional_research_required: List[str] = Field(default_factory=list)
    epistemic_boundary: str = "Candidate Research Question / Potential Opportunity — Not verified novelty without external literature search."

class LiteratureReview(BaseModel):
    id: str
    topic: str
    paper_ids: List[str] = Field(default_factory=list)
    thematic_groups: List[Dict[str, Any]] = Field(default_factory=list)
    outline: List[Dict[str, Any]] = Field(default_factory=list)
    markdown_draft: str = ""
    bibtex_entries: str = ""
    created_at: str = ""

class AIProviderConfig(BaseModel):
    provider_type: str = "local"  # "local", "ollama", "openai_compatible"
    base_url: Optional[str] = "http://localhost:11434"
    model_name: Optional[str] = "llama3:latest"
    api_key: Optional[str] = None
    temperature: float = 0.2



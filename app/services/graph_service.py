"""
Interactive Knowledge Graph Service for Cytoscape.js
Builds nodes (Papers, Authors, Topics), edges (Citations, Semantics, Authorship, Concepts),
and Louvain community clusters with robust citation mapping and fallback layouts.
"""
import networkx as nx
from typing import Dict, Any, List, Optional, Set, Tuple
import community as community_louvain
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.core.workspace_manager import workspace_manager
from app.core.file_store import sanitize_id
from app.config import config

# Palette colors for research clusters (Jade Pebble Morning & Neutral Elegance)
CLUSTER_COLORS = [
    "#7B9669",  # Sage Green
    "#6C8480",  # Muted Teal
    "#BAC8B1",  # Pale Sage
    "#404E3B",  # Forest Green
    "#FFDBBB",  # Soft Peach
    "#CCBEB1",  # Warm Taupe
    "#997E67",  # Muted Clay
    "#8B5A2B",  # Earth Amber
    "#5A7D7C",  # Slate Sage
    "#A3B18A"   # Soft Olive
]

class GraphService:
    def __init__(self, ws_manager=None):
        self.ws = ws_manager or workspace_manager

    def build_graph(
        self,
        collection_id: Optional[str] = None,
        include_citations: bool = True,
        include_semantics: bool = True,
        include_authors: bool = False,
        include_topics: bool = False,
        include_methods: bool = False,
        include_datasets: bool = False,
        min_similarity: float = 0.35,
        max_nodes: int = 300
    ) -> Dict[str, Any]:
        """Build Cytoscape-formatted graph with Louvain community detection."""
        all_papers = self.ws.list_all_papers()
        if collection_id:
            all_papers = [p for p in all_papers if collection_id in p.get("collections", [])]

        if not all_papers:
            return {
                "elements": {"nodes": [], "edges": []},
                "clusters": [],
                "stats": {
                    "total_nodes": 0,
                    "paper_nodes": 0,
                    "author_nodes": 0,
                    "topic_nodes": 0,
                    "method_nodes": 0,
                    "dataset_nodes": 0,
                    "citation_edges": 0,
                    "semantic_edges": 0,
                    "author_edges": 0,
                    "topic_edges": 0,
                    "method_edges": 0,
                    "dataset_edges": 0,
                    "clusters": 0,
                    "isolated_nodes": 0
                },
                "graph_state": "empty_library",
                "state_message": "No research papers found in workspace. Discover papers via OpenAlex or import from your local paper directory to construct the knowledge graph."
            }

        # Bounded nodes
        target_papers = all_papers[:max_nodes]
        paper_id_set: Set[str] = {p["id"] for p in target_papers}

        # Build multi-key index for citation mapping
        # Maps (id, openalex_id, clean_oa, doi, sanitized_id) -> paper_id
        citation_index: Dict[str, str] = {}
        for p in target_papers:
            pid = p["id"]
            citation_index[pid.lower()] = pid
            sanitized = sanitize_id(pid).lower()
            citation_index[sanitized] = pid

            oa_id = p.get("openalex_id")
            if oa_id:
                citation_index[oa_id.lower()] = pid
                clean_oa = oa_id.split("/")[-1].lower() if "/" in oa_id else oa_id.lower()
                citation_index[clean_oa] = pid

            doi = p.get("doi")
            if doi:
                clean_doi = doi.lower().replace("https://doi.org/", "").strip()
                citation_index[clean_doi] = pid

        # Load details (for embeddings and semantic similarities)
        details: Dict[str, Dict[str, Any]] = {}
        embeddings_matrix = []
        embeddings_paper_ids = []

        for p in target_papers:
            d = self.ws.get_paper_detail(p["id"])
            if d:
                details[p["id"]] = d
                analysis = d.get("analysis", {})
                emb = analysis.get("embedding")
                if emb and len(emb) > 0:
                    embeddings_matrix.append(emb)
                    embeddings_paper_ids.append(p["id"])

        # Build NetworkX undirected graph for Louvain clustering
        nx_graph = nx.Graph()
        for p_id in paper_id_set:
            nx_graph.add_node(p_id)

        citation_edges: List[Dict[str, Any]] = []
        semantic_edges: List[Dict[str, Any]] = []
        author_edges: List[Dict[str, Any]] = []
        topic_edges: List[Dict[str, Any]] = []
        method_edges: List[Dict[str, Any]] = []
        dataset_edges: List[Dict[str, Any]] = []

        author_nodes_dict: Dict[str, Dict[str, Any]] = {}
        topic_nodes_dict: Dict[str, Dict[str, Any]] = {}
        method_nodes_dict: Dict[str, Dict[str, Any]] = {}
        dataset_nodes_dict: Dict[str, Dict[str, Any]] = {}

        # -------------------------------------------------------------------
        # 1. Build Citation Edges (from referenced_works)
        # -------------------------------------------------------------------
        if include_citations:
            seen_citation_pairs = set()
            for p in target_papers:
                src_id = p["id"]
                ref_works = p.get("referenced_works", [])
                for ref in ref_works:
                    ref_clean = ref.strip().lower()
                    if "/" in ref_clean:
                        ref_clean = ref_clean.split("/")[-1]

                    target_pid = citation_index.get(ref_clean) or citation_index.get(ref.strip().lower())
                    if target_pid and target_pid != src_id and target_pid in paper_id_set:
                        edge_pair = (src_id, target_pid)
                        if edge_pair not in seen_citation_pairs:
                            seen_citation_pairs.add(edge_pair)
                            edge_id = f"cite_{src_id}_{target_pid}"
                            citation_edges.append({
                                "data": {
                                    "id": edge_id,
                                    "source": src_id,
                                    "target": target_pid,
                                    "type": "citation",
                                    "label": "cites",
                                    "explanation": f"Paper '{p.get('title', src_id)[:40]}' explicitly references '{target_pid}' in its published bibliography.",
                                    "weight": 1.0
                                }
                            })
                            nx_graph.add_edge(src_id, target_pid, weight=1.0)

        # -------------------------------------------------------------------
        # 2. Build Semantic Edges
        # -------------------------------------------------------------------
        if include_semantics:
            seen_semantic_pairs = set()

            # First, check if pre-computed similarities exist in analysis.json
            precomputed_found = False
            for p_id, d in details.items():
                analysis = d.get("analysis", {})
                sims = analysis.get("semantic_similarities", [])
                if sims:
                    precomputed_found = True
                    for sim in sims:
                        tgt_id = sim.get("target_paper_id")
                        score = float(sim.get("similarity_score", 0.0))
                        if tgt_id in paper_id_set and tgt_id != p_id and score >= min_similarity:
                            pair_key = tuple(sorted([p_id, tgt_id]))
                            if pair_key not in seen_semantic_pairs:
                                seen_semantic_pairs.add(pair_key)
                                edge_id = f"sem_{p_id}_{tgt_id}"
                                semantic_edges.append({
                                    "data": {
                                        "id": edge_id,
                                        "source": p_id,
                                        "target": tgt_id,
                                        "type": "semantic",
                                        "label": f"similarity: {score:.2f}",
                                        "similarity": score,
                                        "explanation": f"Calculated semantic similarity of {score:.2f} between respective literature embeddings.",
                                        "weight": score
                                    }
                                })
                                if not nx_graph.has_edge(p_id, tgt_id):
                                    nx_graph.add_edge(p_id, tgt_id, weight=score)

            # If no precomputed similarities were stored, but embeddings exist, compute on-the-fly!
            if not precomputed_found and len(embeddings_matrix) >= 2:
                try:
                    emb_arr = np.array(embeddings_matrix, dtype=np.float32)
                    sim_matrix = cosine_similarity(emb_arr, emb_arr)
                    num_emb = len(embeddings_paper_ids)
                    for i in range(num_emb):
                        for j in range(i + 1, num_emb):
                            score = float(sim_matrix[i, j])
                            if score >= min_similarity:
                                pid_a = embeddings_paper_ids[i]
                                pid_b = embeddings_paper_ids[j]
                                pair_key = tuple(sorted([pid_a, pid_b]))
                                if pair_key not in seen_semantic_pairs:
                                    seen_semantic_pairs.add(pair_key)
                                    edge_id = f"sem_{pid_a}_{pid_b}"
                                    semantic_edges.append({
                                        "data": {
                                            "id": edge_id,
                                            "source": pid_a,
                                            "target": pid_b,
                                            "type": "semantic",
                                            "label": f"similarity: {score:.2f}",
                                            "similarity": score,
                                            "explanation": f"On-the-fly cosine similarity of {score:.2f} across dense feature vectors.",
                                            "weight": score
                                        }
                                    })
                                    if not nx_graph.has_edge(pid_a, pid_b):
                                        nx_graph.add_edge(pid_a, pid_b, weight=score)
                except Exception:
                    pass

        # -------------------------------------------------------------------
        # 3. Optional Author Nodes & Edges
        # -------------------------------------------------------------------
        if include_authors:
            for p in target_papers:
                pid = p["id"]
                authors = p.get("authors", [])
                for a in authors[:3]:  # Top authors per paper
                    aname = a.get("name", "Unknown") if isinstance(a, dict) else str(a)
                    if not aname or aname.lower() == "unknown author":
                        continue
                    aid = f"author_{sanitize_id(aname)}"
                    if aid not in author_nodes_dict:
                        author_nodes_dict[aid] = {
                            "data": {
                                "id": aid,
                                "label": aname,
                                "type": "author",
                                "color": "#CCBEB1",
                                "size": 22,
                                "node_type": "Author"
                            }
                        }
                    edge_id = f"auth_{pid}_{aid}"
                    author_edges.append({
                        "data": {
                            "id": edge_id,
                            "source": pid,
                            "target": aid,
                            "type": "authorship",
                            "label": "authored by",
                            "explanation": f"Paper '{p.get('title', pid)[:40]}' co-authored by researcher '{aname}'.",
                            "weight": 0.5
                        }
                    })

        # -------------------------------------------------------------------
        # 4. Optional Topic / Concept Nodes & Edges
        # -------------------------------------------------------------------
        if include_topics:
            for p in target_papers:
                pid = p["id"]
                topics = p.get("topics", [])
                if not topics and pid in details:
                    topics = details[pid].get("analysis", {}).get("topics", [])
                for topic in topics[:3]:
                    if not topic:
                        continue
                    tid = f"topic_{sanitize_id(topic)}"
                    if tid not in topic_nodes_dict:
                        topic_nodes_dict[tid] = {
                            "data": {
                                "id": tid,
                                "label": topic,
                                "type": "topic",
                                "color": "#6C8480",
                                "size": 20,
                                "node_type": "Concept"
                            }
                        }
                    edge_id = f"top_{pid}_{tid}"
                    topic_edges.append({
                        "data": {
                            "id": edge_id,
                            "source": pid,
                            "target": tid,
                            "type": "concept",
                            "label": "related concept",
                            "explanation": f"Paper investigates scientific concept '{topic}'.",
                            "weight": 0.5
                        }
                    })

        # -------------------------------------------------------------------
        # 4b. Optional Method Nodes & Edges
        # -------------------------------------------------------------------
        if include_methods:
            for p in target_papers:
                pid = p["id"]
                methods = p.get("methods", [])
                if not methods and pid in details:
                    methods = details[pid].get("analysis", {}).get("methods", [])
                for method in methods[:3]:
                    if not method:
                        continue
                    mid = f"method_{sanitize_id(method)}"
                    if mid not in method_nodes_dict:
                        method_nodes_dict[mid] = {
                            "data": {
                                "id": mid,
                                "label": method,
                                "type": "method",
                                "color": "#2D6A5D",
                                "size": 20,
                                "node_type": "Method"
                            }
                        }
                    edge_id = f"meth_{pid}_{mid}"
                    method_edges.append({
                        "data": {
                            "id": edge_id,
                            "source": pid,
                            "target": mid,
                            "type": "method",
                            "label": "uses method",
                            "explanation": f"Paper applies algorithmic method '{method}'.",
                            "weight": 0.5
                        }
                    })

        # -------------------------------------------------------------------
        # 4c. Optional Dataset Nodes & Edges
        # -------------------------------------------------------------------
        if include_datasets:
            for p in target_papers:
                pid = p["id"]
                p_dir = self.ws.get_paper_dir(pid)
                d_file = p_dir / "professor_analysis.json"
                if d_file.exists():
                    d_data = safe_read_json(d_file)
                    ds_text = (d_data.get("methodology", {}).get("datasets_and_variables", "") if d_data else "")
                    if ds_text and "not enumerated" not in ds_text.lower():
                        ds_name = ds_text.split(",")[0][:30].strip()
                        did = f"dataset_{sanitize_id(ds_name)}"
                        if did not in dataset_nodes_dict:
                            dataset_nodes_dict[did] = {
                                "data": {
                                    "id": did,
                                    "label": ds_name,
                                    "type": "dataset",
                                    "color": "#A8583C",
                                    "size": 20,
                                    "node_type": "Dataset"
                                }
                            }
                        edge_id = f"data_{pid}_{did}"
                        dataset_edges.append({
                            "data": {
                                "id": edge_id,
                                "source": pid,
                                "target": did,
                                "type": "dataset",
                                "label": "uses dataset",
                                "explanation": f"Paper evaluates experimental results on benchmark '{ds_name}'.",
                                "weight": 0.5
                            }
                        })

        # -------------------------------------------------------------------
        # 5. Community Detection (Louvain)
        # -------------------------------------------------------------------
        cluster_assignment: Dict[str, int] = {}
        if nx_graph.number_of_nodes() > 0:
            try:
                if nx_graph.number_of_edges() > 0:
                    cluster_assignment = community_louvain.best_partition(nx_graph)
                else:
                    cluster_assignment = {n: 0 for n in nx_graph.nodes()}
            except Exception:
                comps = list(nx.connected_components(nx_graph))
                for idx, comp in enumerate(comps):
                    for n in comp:
                        cluster_assignment[n] = idx

        # Cluster metadata
        cluster_counts: Dict[int, int] = {}
        for c in cluster_assignment.values():
            cluster_counts[c] = cluster_counts.get(c, 0) + 1

        clusters_info = []
        for c_id, count in sorted(cluster_counts.items(), key=lambda x: x[1], reverse=True):
            color = CLUSTER_COLORS[c_id % len(CLUSTER_COLORS)]
            clusters_info.append({
                "cluster_id": c_id,
                "name": f"Research Cluster {c_id + 1}",
                "count": count,
                "color": color
            })

        # -------------------------------------------------------------------
        # 6. Cytoscape Paper Nodes
        # -------------------------------------------------------------------
        paper_nodes = []
        isolated_nodes = 0
        all_edges = citation_edges + semantic_edges + author_edges + topic_edges + method_edges + dataset_edges
        connected_node_ids = set()
        for e in all_edges:
            connected_node_ids.add(e["data"]["source"])
            connected_node_ids.add(e["data"]["target"])

        for p in target_papers:
            p_id = p["id"]
            citations = p.get("citation_count", 0)
            size = max(24, min(64, int(24 + (citations ** 0.5) * 3)))
            c_id = cluster_assignment.get(p_id, 0)
            node_color = CLUSTER_COLORS[c_id % len(CLUSTER_COLORS)]

            authors = p.get("authors", [])
            first_author = "Unknown"
            if authors:
                first_author = authors[0].get("name", "Unknown") if isinstance(authors[0], dict) else str(authors[0])

            is_isolated = p_id not in connected_node_ids
            if is_isolated:
                isolated_nodes += 1

            paper_nodes.append({
                "data": {
                    "id": p_id,
                    "title": p.get("title", "Untitled"),
                    "label": (p.get("title")[:28] + "...") if len(p.get("title", "")) > 30 else p.get("title", "Untitled"),
                    "author": first_author,
                    "year": p.get("publication_year") or "",
                    "venue": p.get("venue", "Academic Venue"),
                    "citations": citations,
                    "cluster": c_id,
                    "color": node_color,
                    "size": size,
                    "status": p.get("processing_status", "Imported"),
                    "type": "paper",
                    "node_type": "Paper"
                }
            })

        all_nodes = paper_nodes + list(author_nodes_dict.values()) + list(topic_nodes_dict.values()) + list(method_nodes_dict.values()) + list(dataset_nodes_dict.values())

        # Determine graph state and message
        total_edges_count = len(all_edges)
        if total_edges_count == 0:
            graph_state = "no_edges"
            state_message = f"Displaying {len(paper_nodes)} papers as nodes. No citation links or semantic similarities have been identified yet. Run the Paper Analyzer to calculate semantic similarities."
        elif len(target_papers) <= 2:
            graph_state = "small_corpus"
            state_message = f"Displaying {len(all_nodes)} nodes with {total_edges_count} relationships. Import additional literature to enrich community cluster detection."
        else:
            graph_state = "ready"
            state_message = f"Scientific knowledge graph active with {len(paper_nodes)} papers, {len(clusters_info)} Louvain clusters, {len(citation_edges)} citation links, and {len(semantic_edges)} semantic relationships."

        return {
            "elements": {
                "nodes": all_nodes,
                "edges": all_edges
            },
            "clusters": clusters_info,
            "stats": {
                "total_nodes": len(all_nodes),
                "paper_nodes": len(paper_nodes),
                "author_nodes": len(author_nodes_dict),
                "topic_nodes": len(topic_nodes_dict),
                "method_nodes": len(method_nodes_dict),
                "dataset_nodes": len(dataset_nodes_dict),
                "citation_edges": len(citation_edges),
                "semantic_edges": len(semantic_edges),
                "author_edges": len(author_edges),
                "topic_edges": len(topic_edges),
                "method_edges": len(method_edges),
                "dataset_edges": len(dataset_edges),
                "clusters": len(clusters_info),
                "isolated_nodes": isolated_nodes
            },
            "graph_state": graph_state,
            "state_message": state_message
        }

    def get_ego_graph(self, paper_id: str, depth: int = 1) -> Dict[str, Any]:
        """Return graph centered around a single paper."""
        full_graph = self.build_graph(max_nodes=config.max_graph_nodes, include_citations=True, include_semantics=True)
        nodes = full_graph["elements"]["nodes"]
        edges = full_graph["elements"]["edges"]

        target_ids = {paper_id}
        for edge in edges:
            src = edge["data"]["source"]
            tgt = edge["data"]["target"]
            if src == paper_id:
                target_ids.add(tgt)
            elif tgt == paper_id:
                target_ids.add(src)

        ego_nodes = [n for n in nodes if n["data"]["id"] in target_ids]
        ego_edges = [e for e in edges if e["data"]["source"] in target_ids and e["data"]["target"] in target_ids]

        return {
            "elements": {"nodes": ego_nodes, "edges": ego_edges},
            "clusters": full_graph["clusters"],
            "stats": {
                "center_paper_id": paper_id,
                "total_nodes": len(ego_nodes),
                "total_edges": len(ego_edges)
            }
        }

graph_service = GraphService()

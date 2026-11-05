"""
PaperGraph V3 - Autonomous Pattern Recognition Engine (Phase 3)
Operates with ZERO AI model requirements using deterministic discourse heuristics.
Extracts empirical claims, categorizes claim types, and assigns evidence confidence.
"""
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ExtractedClaim(BaseModel):
    claim_id: str
    claim_type: str  # result, method, limitation, comparison, dataset
    claim_text: str
    confidence: float  # 0.0 - 1.0
    evidence_type: str  # direct_text, inferred, contradiction
    source_span: str
    page_number: int
    source_paper_id: str
    extraction_source: str  # surya_ocr_2, pymupdf, pattern_engine

class PatternRecognitionEngine:
    def __init__(self):
        self.patterns = {
            "result": [
                (r"(?:we\s+found\s+that|results?\s+show\s+that|demonstrates?\s+that|achieves?\s+(?:a|an)?\s*\d+%?|observations?\s+indicate|empirically\s+validates?)\s+([^.?!;]+[.?!])", 0.92),
                (r"(?:our\s+findings?\s+reveal|significant\s+improvement\s+of\s+[^.?!;]+|consistently\s+outperformed|reduces?\s+(?:memory|overhead|latency)\s+by)\s+([^.?!;]+[.?!])", 0.88)
            ],
            "method": [
                (r"(?:we\s+(?:use|used|employ|employed|propose|introduce|present)\s+[^.?!;]+|our\s+approach\s+(?:relies|is\s+based)\s+on)\s+([^.?!;]+[.?!])", 0.85),
                (r"(?:the\s+proposed\s+pipeline\s+consists\s+of|formulated\s+as\s+follows:?)\s+([^.?!;]+[.?!])", 0.80)
            ],
            "limitation": [
                (r"(?:however,?\s+[^.?!;]*fails?\s+when|a\s+limitation\s+of\s+(?:this|our)\s+approach|is\s+bounded\s+by|does\s+not\s+scale\s+to|remains\s+unresolved|degrades?\s+(?:under|when))\s+([^.?!;]+[.?!])", 0.95),
                (r"(?:constrained\s+by\s+memory|vulnerable\s+to|inability\s+to\s+handle)\s+([^.?!;]+[.?!])", 0.90)
            ],
            "comparison": [
                (r"(?:([^.?!;]+)\s+outperforms?\s+([^.?!;]+)\s+by\s+\d+%?|compared\s+to\s+baseline|yields?\s+higher\s+(?:accuracy|throughput)\s+than)\s+([^.?!;]+[.?!])", 0.93),
                (r"(?:in\s+contrast\s+to\s+prior\s+work|surpassing\s+state-of-the-art\s+by|dense\s+models\s+outperform)\s+([^.?!;]+[.?!])", 0.89)
            ],
            "dataset": [
                (r"(?:the\s+dataset\s+consists\s+of|we\s+collected\s+\d+\s+samples?|evaluated\s+on\s+(?:the|standard)?\s*([A-Z0-9_\-]+)\s+benchmark)\s*([^.?!;]+[.?!])", 0.86),
                (r"(?:corpus\s+contains|tested\s+across\s+\d+\s+public\s+datasets?)\s+([^.?!;]+[.?!])", 0.82)
            ]
        }

    def extract_claims(self, text: str, paper_id: str, page_number: int, extraction_source: str = "pymupdf") -> List[ExtractedClaim]:
        claims: List[ExtractedClaim] = []
        claim_counter = 0

        sentences = [s.strip() for s in re.split(r"(?<=[.?!])\s+", text) if len(s.strip()) > 15]

        for sentence in sentences:
            sentence_matched = False
            for c_type, regex_list in self.patterns.items():
                for pattern, conf in regex_list:
                    match = re.search(pattern, sentence, re.IGNORECASE)
                    if match:
                        claim_counter += 1
                        claims.append(ExtractedClaim(
                            claim_id=f"{paper_id}_p{page_number}_c{claim_counter}",
                            claim_type=c_type,
                            claim_text=sentence,
                            confidence=conf,
                            evidence_type="direct_text",
                            source_span=match.group(0).strip(),
                            page_number=page_number,
                            source_paper_id=paper_id,
                            extraction_source=extraction_source
                        ))
                        sentence_matched = True
                        break
                if sentence_matched:
                    break

        return claims

    def detect_contradictions(self, claims: List[ExtractedClaim]) -> List[Dict[str, Any]]:
        contradictions = []
        
        pos_stems = ["outperform", "improv", "effectiv", "superior", "enhanc", "scalab", "reduc", "higher"]
        neg_stems = ["fail", "degrad", "bottleneck", "limit", "underperform", "ineffectiv", "overhead", "vulnerab"]

        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                c1, c2 = claims[i], claims[j]
                text1, text2 = c1.claim_text.lower(), c2.claim_text.lower()
                
                has_pos1 = any(k in text1 for k in pos_stems)
                has_neg1 = any(k in text1 for k in neg_stems)
                has_pos2 = any(k in text2 for k in pos_stems)
                has_neg2 = any(k in text2 for k in neg_stems)

                # Polarity clash
                is_polar = (has_pos1 and has_neg2) or (has_neg1 and has_pos2) or (
                    ("outperform" in text1 or "contrast" in text1) and ("outperform" in text2 or "contrast" in text2)
                )

                stopwords = {"that", "with", "from", "this", "across", "under", "over", "were", "been", "have", "then", "into"}
                words1 = set(w for w in re.findall(r"\b[a-zA-Z]{4,}\b", text1) if w not in stopwords)
                words2 = set(w for w in re.findall(r"\b[a-zA-Z]{4,}\b", text2) if w not in stopwords)
                common = words1.intersection(words2)

                if is_polar and len(common) >= 1:
                    contradictions.append({
                        "claim_a_id": c1.claim_id,
                        "claim_b_id": c2.claim_id,
                        "claim_a_text": c1.claim_text,
                        "claim_b_text": c2.claim_text,
                        "shared_entities": list(common),
                        "evidence_type": "contradiction",
                        "confidence": min(c1.confidence, c2.confidence)
                    })
        return contradictions

pattern_engine = PatternRecognitionEngine()

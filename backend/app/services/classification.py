import re
from typing import Tuple

# CLASSIFICATION STRATEGY:
# Deterministic rule-based classification based exclusively on observable metadata (filename and declared type).
# NO OCR, machine learning, computer vision, or probabilistic models are used.
# The classification_score is an explicit heuristic rule score (0.85 = keyword match, 0.60 = declared fallback, 0.0 = unmatched)
# and MUST NOT be interpreted or presented as a statistical probability or calibrated ML confidence.

KEYWORD_RULES = [
    (
        "STRUCTURAL_DRAWING",
        [r"\bstruct", r"structural", r"rebar", r"reinforcement", r"\bbeam", r"\bcolumn", r"\bslab", r"foundation", r"footing", r"\brcc\b"]
    ),
    (
        "ARCHITECTURAL_DRAWING",
        [r"\barch", r"architectural", r"floor_?plan", r"elevation", r"section", r"layout"]
    ),
    (
        "BOQ",
        [r"\bboq\b", r"bill_?of_?quantities", r"schedule_?of_?quantities", r"\bsoq\b", r"measurement_?sheet"]
    ),
    (
        "SPECIFICATION",
        [r"\bspec\b", r"specification", r"tech_?spec"]
    ),
    (
        "GEOTECHNICAL",
        [r"\bgeo\b", r"geotech", r"geotechnical", r"soil", r"borehole", r"\bsbc\b"]
    ),
    (
        "TENDER_PROJECT_INFO",
        [r"tender", r"\bnit\b", r"notice_?inviting_?tender", r"project_?info", r"contract", r"\brfp\b"]
    ),
]

def classify_document(filename: str, declared_type: str) -> Tuple[str, float, str]:
    """
    Returns (classified_document_type, classification_score, classification_method).
    Never fabricates confidence or guesses without explicit rule signals.
    """
    # Normalize filename: replace punctuation, underscores, and dashes with spaces
    cleaned_name = f" {re.sub(r'[^a-z0-9]+', ' ', filename.lower())} "
    
    # 1. Evaluate explicit keyword rules against filename
    for doc_type, patterns in KEYWORD_RULES:
        for pat in patterns:
            if re.search(pat, cleaned_name):
                return doc_type, 0.85, "RULE_BASED"
                
    # 2. Check if a non-generic declared document type was provided
    if declared_type and declared_type not in ["UNKNOWN", "OTHER"]:
        return declared_type, 0.60, "RULE_BASED"
        
    # 3. Default to UNKNOWN when no confident rule matches
    return "UNKNOWN", 0.0, "RULE_BASED"

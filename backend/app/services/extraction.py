from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.db.models import Evidence, ExtractedFact, FactVerification, Document, DocumentPage
from app.services.audit import log_action
from app.services.unit_normalization import normalize_dimension

EXTRACTION_VERSION = "phase-1c-v1"

class ExtractionEngine(ABC):
    """
    Contract interface for pluggable extraction engines.
    Takes an Evidence record and returns extracted facts.
    Future engines (e.g. OCR, vision) can implement this interface without modifying provenance logic.
    """
    @abstractmethod
    def extract(self, evidence: Evidence) -> List[Dict[str, Any]]:
        pass

class ManualExtractionEngine(ExtractionEngine):
    """
    Default Phase 1C engine for human-reviewed / manual data entry with provenance.
    """
    def extract(self, evidence: Evidence) -> List[Dict[str, Any]]:
        return []

def create_evidence_record(
    db: Session,
    project_id: str,
    document_id: str,
    user_id: str,
    evidence_type: str,
    source_reference: str,
    page_id: Optional[str] = None,
    locator: Optional[Any] = None,
    raw_content: Optional[str] = None,
    metadata_json: Optional[Dict[str, Any]] = None
) -> Evidence:
    # 1. Enforce Document existence & project ownership
    doc = db.query(Document).filter(Document.id == document_id, Document.project_id == project_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 2. Enforce Page existence if page_id is provided
    if page_id:
        page = db.query(DocumentPage).filter(DocumentPage.id == page_id, DocumentPage.document_id == document_id).first()
        if not page:
            raise HTTPException(status_code=400, detail="Referenced DocumentPage does not exist for this document")

    # 3. Duplicate check based on document_scoped composite identity
    candidates = db.query(Evidence).filter(
        Evidence.document_id == document_id,
        Evidence.evidence_type == evidence_type,
        Evidence.source_reference == source_reference
    ).all()
    for existing in candidates:
        if existing.locator == locator:
            raise HTTPException(status_code=409, detail="Identical evidence record already exists for this document")

    evidence = Evidence(
        document_id=document_id,
        page_id=page_id,
        evidence_type=evidence_type,
        source_reference=source_reference,
        locator=locator,
        raw_content=raw_content,
        metadata_json=metadata_json,
        created_by=user_id,
        verification_status="UNVERIFIED"
    )
    db.add(evidence)
    db.flush()

    log_action(db, user_id, "EVIDENCE_CREATED", "Evidence", evidence.id, f"{evidence_type} from {source_reference}")
    return evidence

def create_fact_record(
    db: Session,
    project_id: str,
    document_id: str,
    evidence_id: str,
    user_id: str,
    fact_type: str,
    field_name: str,
    raw_value: str,
    normalized_value: Optional[Decimal] = None,
    normalized_unit: Optional[str] = None,
    extraction_method: str = "MANUAL",
    metadata_json: Optional[Dict[str, Any]] = None
) -> ExtractedFact:
    # 1. Enforce Evidence existence and document hierarchy
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id, Evidence.document_id == document_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found for this document")

    # 2. Deterministic unit normalization if not manually overridden
    if normalized_value is None:
        norm_val, norm_unit = normalize_dimension(raw_value)
        if norm_val is not None:
            normalized_value = norm_val
            normalized_unit = norm_unit

    fact = ExtractedFact(
        evidence_id=evidence.id,
        fact_type=fact_type,
        field_name=field_name,
        raw_value=raw_value,
        normalized_value=normalized_value,
        normalized_unit=normalized_unit,
        extraction_method=extraction_method,
        extraction_version=EXTRACTION_VERSION,
        extraction_status="EXTRACTED",
        created_by=user_id,
        verification_status="UNVERIFIED",
        metadata_json=metadata_json
    )
    db.add(fact)
    db.flush()

    log_action(db, user_id, "FACT_CREATED", "ExtractedFact", fact.id, f"{field_name}={raw_value}")
    return fact

def verify_or_correct_fact(
    db: Session,
    project_id: str,
    document_id: str,
    fact_id: str,
    user_id: str,
    status: str,
    verification_note: Optional[str] = None,
    corrected_value: Optional[Decimal] = None,
    corrected_unit: Optional[str] = None,
    metadata_json: Optional[Dict[str, Any]] = None
) -> FactVerification:
    """
    Supervisor verification or correction of an extracted fact.
    IMMUTABILITY PRINCIPLE: The original ExtractedFact is NEVER overwritten.
    A distinct FactVerification record preserves the supervisor's decision,
    corrected value, and audit trail.
    """
    # 1. Traverse and verify hierarchy: Project -> Document -> Evidence -> Fact
    fact = db.query(ExtractedFact).join(Evidence).join(Document).filter(
        ExtractedFact.id == fact_id,
        Evidence.document_id == document_id,
        Document.project_id == project_id
    ).first()
    if not fact:
        raise HTTPException(status_code=404, detail="ExtractedFact not found in this document/project")

    # 2. Update status flags on fact without modifying raw or original values
    fact.verification_status = status
    if status == "VERIFIED":
        fact.extraction_status = "VERIFIED"
    elif status == "REJECTED":
        fact.extraction_status = "REJECTED"

    # 3. Create explicit verification record
    verification = FactVerification(
        fact_id=fact.id,
        verified_by=user_id,
        status=status,
        verification_note=verification_note,
        corrected_value=corrected_value,
        corrected_unit=corrected_unit,
        metadata_json=metadata_json
    )
    db.add(verification)
    db.flush()

    action = "FACT_CORRECTED" if corrected_value is not None else ("FACT_VERIFIED" if status == "VERIFIED" else "FACT_REJECTED")
    log_action(db, user_id, action, "FactVerification", verification.id, verification_note or f"Status set to {status}")
    return verification

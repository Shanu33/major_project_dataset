from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.db.models import (
    EngineeringElement,
    EngineeringElementRevision,
    ExtractedFact,
    Evidence,
    Document,
    Project,
    User
)
from app.services.audit import log_action
from app.schemas.schemas import (
    EngineeringElementTypeEnum,
    ElementVerificationStatusEnum,
    ElementProvenanceChainResponse,
    EngineeringElementResponse,
    EngineeringElementRevisionResponse
)

def create_element_record(
    db: Session,
    project_id: str,
    user_id: str,
    element_type: str,
    element_name: str,
    source_fact_id: Optional[str] = None,
    metadata_json: Optional[Dict[str, Any]] = None
) -> EngineeringElement:
    # 1. Enforce Project existence
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    # 2. Validate element_type
    try:
        EngineeringElementTypeEnum(element_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid element_type '{element_type}'. Supported types: {[e.value for e in EngineeringElementTypeEnum]}"
        )

    source_document_id = None
    source_page_id = None

    # 3. Verified Fact Requirement
    if source_fact_id:
        fact = db.query(ExtractedFact).join(Evidence).join(Document).filter(
            ExtractedFact.id == source_fact_id
        ).first()

        if not fact:
            raise HTTPException(status_code=404, detail="Referenced source_fact does not exist")

        # Project boundary check
        fact_doc = fact.evidence.document
        if fact_doc.project_id != project_id:
            raise HTTPException(status_code=400, detail="Cross-project source_fact reference is strictly rejected")

        # Verified status invariant
        if fact.verification_status != "VERIFIED":
            raise HTTPException(
                status_code=400,
                detail=f"Source fact must have verification_status VERIFIED. Current status is '{fact.verification_status}'"
            )

        source_document_id = fact_doc.id
        source_page_id = fact.evidence.page_id

    # 4. Create EngineeringElement identity
    element = EngineeringElement(
        project_id=project_id,
        element_type=element_type,
        element_name=element_name,
        source_document_id=source_document_id,
        source_page_id=source_page_id,
        source_fact_id=source_fact_id,
        status="ACTIVE",
        verification_status="PENDING",
        created_by=user_id,
        metadata_json=metadata_json
    )
    db.add(element)
    db.flush()

    # 5. Create initial immutable revision 0
    rev_0 = EngineeringElementRevision(
        element_id=element.id,
        revision_number=0,
        element_type=element_type,
        element_name=element_name,
        source_document_id=source_document_id,
        source_page_id=source_page_id,
        source_fact_id=source_fact_id,
        verification_status="PENDING",
        revision_note="Initial element creation",
        created_by=user_id,
        metadata_json=metadata_json
    )
    db.add(rev_0)
    db.flush()

    log_action(db, user_id, "ENGINEERING_ELEMENT_CREATED", "EngineeringElement", element.id, f"{element_type}: {element_name}")
    return element

def verify_or_revise_element_record(
    db: Session,
    project_id: str,
    element_id: str,
    user: User,
    verification_status: Optional[str] = None,
    revision_note: Optional[str] = None,
    new_name: Optional[str] = None,
    new_type: Optional[str] = None,
    new_source_fact_id: Optional[str] = None,
    metadata_json: Optional[Dict[str, Any]] = None
) -> EngineeringElement:
    # 1. Authorization: Only supervisor or admin can verify/revise
    if user.role not in ["supervisor", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only supervisors or admins are authorized to verify or revise engineering elements"
        )

    # 2. Element existence & project ownership
    element = db.query(EngineeringElement).filter(
        EngineeringElement.id == element_id,
        EngineeringElement.project_id == project_id
    ).first()
    if not element:
        raise HTTPException(status_code=404, detail="EngineeringElement not found in this project")

    # 3. Compute next revision number
    latest_rev = max([r.revision_number for r in element.revisions], default=0)
    next_rev_num = latest_rev + 1

    # 4. Resolve updated fields
    target_type = new_type or element.element_type
    target_name = new_name or element.element_name
    target_fact_id = new_source_fact_id if new_source_fact_id is not None else element.source_fact_id
    target_ver_status = verification_status or element.verification_status

    if new_type:
        try:
            EngineeringElementTypeEnum(target_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid element_type '{target_type}'")

    if verification_status:
        try:
            ElementVerificationStatusEnum(target_ver_status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid verification_status '{target_ver_status}'")

    source_doc_id = element.source_document_id
    source_page_id = element.source_page_id

    # If updating source_fact_id, validate verified fact
    if new_source_fact_id:
        fact = db.query(ExtractedFact).join(Evidence).join(Document).filter(
            ExtractedFact.id == new_source_fact_id
        ).first()
        if not fact:
            raise HTTPException(status_code=404, detail="Referenced source_fact does not exist")
        fact_doc = fact.evidence.document
        if fact_doc.project_id != project_id:
            raise HTTPException(status_code=400, detail="Cross-project source_fact reference is strictly rejected")
        if fact.verification_status != "VERIFIED":
            raise HTTPException(
                status_code=400,
                detail=f"Source fact must have verification_status VERIFIED. Current status is '{fact.verification_status}'"
            )
        source_doc_id = fact_doc.id
        source_page_id = fact.evidence.page_id

    # 5. Create new immutable revision record
    new_rev = EngineeringElementRevision(
        element_id=element.id,
        revision_number=next_rev_num,
        element_type=target_type,
        element_name=target_name,
        source_document_id=source_doc_id,
        source_page_id=source_page_id,
        source_fact_id=target_fact_id,
        verification_status=target_ver_status,
        revision_note=revision_note,
        created_by=user.id,
        metadata_json=metadata_json or element.metadata_json
    )
    db.add(new_rev)
    db.flush()

    # 6. Update current summary state on EngineeringElement
    element.element_type = target_type
    element.element_name = target_name
    element.source_document_id = source_doc_id
    element.source_page_id = source_page_id
    element.source_fact_id = target_fact_id
    element.verification_status = target_ver_status
    if metadata_json:
        element.metadata_json = metadata_json

    action = "ENGINEERING_ELEMENT_VERIFIED" if verification_status in ["VERIFIED", "REJECTED"] else "ENGINEERING_ELEMENT_REVISED"
    log_action(db, user.id, action, "EngineeringElement", element.id, revision_note or f"Status: {target_ver_status}")
    return element

def build_element_response(db: Session, element: EngineeringElement) -> EngineeringElementResponse:
    project = element.project
    prov = None

    if element.source_fact_id and element.source_fact:
        fact = element.source_fact
        ev = fact.evidence
        page = ev.page if ev else None
        doc = ev.document if ev else None

        prov = ElementProvenanceChainResponse(
            provenance_type="DOCUMENT_DERIVED",
            fact_id=fact.id,
            fact_type=fact.fact_type,
            field_name=fact.field_name,
            raw_value=fact.raw_value,
            normalized_value=fact.normalized_value,
            normalized_unit=fact.normalized_unit,
            fact_verification_status=fact.verification_status,
            evidence_id=ev.id if ev else None,
            evidence_type=ev.evidence_type if ev else None,
            source_reference=ev.source_reference if ev else None,
            locator=ev.locator if ev else None,
            page_id=page.id if page else None,
            page_number=page.page_number if page else None,
            document_id=doc.id if doc else None,
            original_filename=doc.original_filename if doc else None,
            project_id=project.id,
            project_name=project.name
        )
    else:
        prov = ElementProvenanceChainResponse(
            provenance_type="MANUALLY_SUPPLIED",
            project_id=project.id,
            project_name=project.name
        )

    revisions_resp = [
        EngineeringElementRevisionResponse(
            id=r.id,
            element_id=r.element_id,
            revision_number=r.revision_number,
            element_type=EngineeringElementTypeEnum(r.element_type),
            element_name=r.element_name,
            source_document_id=r.source_document_id,
            source_page_id=r.source_page_id,
            source_fact_id=r.source_fact_id,
            verification_status=ElementVerificationStatusEnum(r.verification_status),
            revision_note=r.revision_note,
            created_by=r.created_by,
            created_at=r.created_at,
            metadata_json=r.metadata_json
        ) for r in element.revisions
    ]

    return EngineeringElementResponse(
        id=element.id,
        project_id=element.project_id,
        element_type=EngineeringElementTypeEnum(element.element_type),
        element_name=element.element_name,
        source_document_id=element.source_document_id,
        source_page_id=element.source_page_id,
        source_fact_id=element.source_fact_id,
        status=element.status,
        verification_status=ElementVerificationStatusEnum(element.verification_status),
        created_by=element.created_by,
        created_at=element.created_at,
        metadata_json=element.metadata_json,
        revisions=revisions_resp,
        provenance=prov
    )

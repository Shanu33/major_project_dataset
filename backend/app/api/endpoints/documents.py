from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import hashlib
import uuid
import os
from app.db.database import get_db
from app.db.models import (
    Document, DocumentPage, DocumentProcessingHistory, Project, User,
    Evidence, ExtractedFact, FactVerification
)
from app.schemas.schemas import (
    DocumentResponse,
    DocumentTypeEnum,
    DocumentPageResponse,
    DocumentProcessingHistoryResponse,
    DocumentStatusResponse,
    EvidenceCreate,
    EvidenceResponse,
    FactCreate,
    FactResponse,
    FactVerify,
    FactVerificationResponse,
    FactProvenanceResponse
)
from app.api.dependencies import require_project_access
from app.services.audit import log_action
from app.services.document_processing import process_document
from app.services.extraction import create_evidence_record, create_fact_record, verify_or_correct_fact
from app.storage.service import storage
from app.core.config import settings

router = APIRouter()

@router.post("/", response_model=DocumentResponse)
def upload_document(
    project_id: str,
    file: UploadFile = File(...),
    document_type: DocumentTypeEnum = Form(DocumentTypeEnum.UNKNOWN),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access)
):
    if file.content_type not in settings.ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file format.")
        
    file_bytes = file.file.read()
    if len(file_bytes) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds limit.")
        
    if file.content_type == "application/pdf" and not file_bytes.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="Invalid PDF file signature.")

    file_hash = hashlib.sha256(file_bytes).hexdigest()
    
    # Preliminary duplicate check
    existing = db.query(Document).filter(
        Document.project_id == project_id,
        Document.sha256_hash == file_hash
    ).first()
    
    if existing:
        raise HTTPException(status_code=409, detail="Document with identical content already exists in this project.")
        
    # Generate storage key
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    storage_key = f"{uuid.uuid4()}{ext}"
    
    # Rewind and store
    import io
    file_obj = io.BytesIO(file_bytes)
    storage.save(storage_key, file_obj)
    
    try:
        doc = Document(
            project_id=project_id,
            original_filename=file.filename or "",
            storage_key=storage_key,
            document_type=document_type.value,
            mime_type=file.content_type,
            file_size_bytes=len(file_bytes),
            sha256_hash=file_hash,
            uploaded_by=current_user.id
        )
        db.add(doc)
        db.flush() # get id
        
        log_action(db, current_user.id, "DOCUMENT_UPLOADED", "Document", doc.id, file.filename or "")
        db.commit()
        db.refresh(doc)
        return doc
    except IntegrityError:
        db.rollback()
        storage.delete(storage_key) # Clean up orphaned file
        raise HTTPException(status_code=409, detail="Document with identical content already exists in this project.")
    except Exception:
        db.rollback()
        storage.delete(storage_key) # Clean up orphaned file
        raise HTTPException(status_code=500, detail="Database transaction failed")

@router.get("/", response_model=list[DocumentResponse], dependencies=[Depends(require_project_access)])
def list_documents(project_id: str, db: Session = Depends(get_db)):
    return db.query(Document).filter(Document.project_id == project_id).all()

@router.get("/{document_id}", response_model=DocumentResponse, dependencies=[Depends(require_project_access)])
def get_document(project_id: str, document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id, Document.project_id == project_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.post("/{document_id}/process", response_model=DocumentStatusResponse)
def trigger_document_processing(
    project_id: str,
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access)
):
    doc = process_document(db, project_id, document_id, current_user.id)
    page_count = db.query(DocumentPage).filter(DocumentPage.document_id == doc.id).count()
    return DocumentStatusResponse(
        id=doc.id,
        project_id=doc.project_id,
        original_filename=doc.original_filename,
        document_type=doc.document_type,
        classified_document_type=doc.classified_document_type,
        classification_score=doc.classification_score,
        classification_method=doc.classification_method,
        classified_at=doc.classified_at,
        processing_status=doc.processing_status,
        total_pages=page_count
    )

@router.get("/{document_id}/processing-status", response_model=DocumentStatusResponse, dependencies=[Depends(require_project_access)])
def get_document_processing_status(
    project_id: str,
    document_id: str,
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id, Document.project_id == project_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    page_count = db.query(DocumentPage).filter(DocumentPage.document_id == doc.id).count()
    return DocumentStatusResponse(
        id=doc.id,
        project_id=doc.project_id,
        original_filename=doc.original_filename,
        document_type=doc.document_type,
        classified_document_type=doc.classified_document_type,
        classification_score=doc.classification_score,
        classification_method=doc.classification_method,
        classified_at=doc.classified_at,
        processing_status=doc.processing_status,
        total_pages=page_count
    )

@router.get("/{document_id}/processing-history", response_model=list[DocumentProcessingHistoryResponse], dependencies=[Depends(require_project_access)])
def get_document_processing_history(
    project_id: str,
    document_id: str,
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id, Document.project_id == project_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    return db.query(DocumentProcessingHistory).filter(DocumentProcessingHistory.document_id == doc.id).order_by(DocumentProcessingHistory.started_at.desc()).all()

@router.get("/{document_id}/pages", response_model=list[DocumentPageResponse], dependencies=[Depends(require_project_access)])
def get_document_pages(
    project_id: str,
    document_id: str,
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id, Document.project_id == project_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    return db.query(DocumentPage).filter(DocumentPage.document_id == doc.id).order_by(DocumentPage.page_number.asc()).all()

# ==============================================================================
# PHASE 1C: EVIDENCE & PROVENANCE ENDPOINTS
# ==============================================================================

@router.post("/{document_id}/evidence", response_model=EvidenceResponse)
def create_evidence(
    project_id: str,
    document_id: str,
    evidence_in: EvidenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access)
):
    evidence = create_evidence_record(
        db=db,
        project_id=project_id,
        document_id=document_id,
        user_id=current_user.id,
        evidence_type=evidence_in.evidence_type.value,
        source_reference=evidence_in.source_reference,
        page_id=evidence_in.page_id,
        locator=evidence_in.locator,
        raw_content=evidence_in.raw_content,
        metadata_json=evidence_in.metadata_json
    )
    db.commit()
    db.refresh(evidence)
    return evidence

@router.get("/{document_id}/evidence", response_model=list[EvidenceResponse], dependencies=[Depends(require_project_access)])
def list_evidence(
    project_id: str,
    document_id: str,
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id, Document.project_id == project_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return db.query(Evidence).filter(Evidence.document_id == document_id).order_by(Evidence.created_at.asc()).all()

@router.post("/{document_id}/evidence/{evidence_id}/facts", response_model=FactResponse)
def create_fact(
    project_id: str,
    document_id: str,
    evidence_id: str,
    fact_in: FactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access)
):
    fact = create_fact_record(
        db=db,
        project_id=project_id,
        document_id=document_id,
        evidence_id=evidence_id,
        user_id=current_user.id,
        fact_type=fact_in.fact_type,
        field_name=fact_in.field_name,
        raw_value=fact_in.raw_value,
        normalized_value=fact_in.normalized_value,
        normalized_unit=fact_in.normalized_unit,
        extraction_method=fact_in.extraction_method.value,
        metadata_json=fact_in.metadata_json
    )
    db.commit()
    db.refresh(fact)
    return fact

@router.get("/{document_id}/evidence/{evidence_id}/facts", response_model=list[FactResponse], dependencies=[Depends(require_project_access)])
def list_facts_for_evidence(
    project_id: str,
    document_id: str,
    evidence_id: str,
    db: Session = Depends(get_db)
):
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id, Evidence.document_id == document_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return db.query(ExtractedFact).filter(ExtractedFact.evidence_id == evidence_id).order_by(ExtractedFact.created_at.asc()).all()

@router.get("/{document_id}/facts/{fact_id}", response_model=FactProvenanceResponse, dependencies=[Depends(require_project_access)])
def get_fact_provenance(
    project_id: str,
    document_id: str,
    fact_id: str,
    db: Session = Depends(get_db)
):
    fact = db.query(ExtractedFact).join(Evidence).join(Document).join(Project).filter(
        ExtractedFact.id == fact_id,
        Evidence.document_id == document_id,
        Document.project_id == project_id
    ).first()
    if not fact:
        raise HTTPException(status_code=404, detail="ExtractedFact not found")

    evidence = fact.evidence
    doc = evidence.document
    project = doc.project
    page = evidence.page

    return FactProvenanceResponse(
        fact_id=fact.id,
        fact_type=fact.fact_type,
        field_name=fact.field_name,
        raw_value=fact.raw_value,
        normalized_value=fact.normalized_value,
        normalized_unit=fact.normalized_unit,
        extraction_method=fact.extraction_method,
        extraction_version=fact.extraction_version,
        extraction_status=fact.extraction_status,
        verification_status=fact.verification_status,
        evidence_id=evidence.id,
        evidence_type=evidence.evidence_type,
        source_reference=evidence.source_reference,
        locator=evidence.locator,
        raw_content=evidence.raw_content,
        page_id=page.id if page else None,
        page_number=page.page_number if page else None,
        document_id=doc.id,
        original_filename=doc.original_filename,
        project_id=project.id,
        project_name=project.name,
        verifications=[
            FactVerificationResponse(
                id=v.id,
                fact_id=v.fact_id,
                verified_by=v.verified_by,
                status=v.status,
                verification_note=v.verification_note,
                corrected_value=v.corrected_value,
                corrected_unit=v.corrected_unit,
                verified_at=v.verified_at,
                metadata_json=v.metadata_json
            ) for v in fact.verifications
        ]
    )

@router.post("/{document_id}/facts/{fact_id}/verify", response_model=FactVerificationResponse)
def verify_fact(
    project_id: str,
    document_id: str,
    fact_id: str,
    verify_in: FactVerify,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_project_access)
):
    if current_user.role not in ["supervisor", "admin"]:
        raise HTTPException(status_code=403, detail="Only supervisors or admins are authorized to verify or correct facts")

    verification = verify_or_correct_fact(
        db=db,
        project_id=project_id,
        document_id=document_id,
        fact_id=fact_id,
        user_id=current_user.id,
        status=verify_in.status.value,
        verification_note=verify_in.verification_note,
        corrected_value=verify_in.corrected_value,
        corrected_unit=verify_in.corrected_unit,
        metadata_json=verify_in.metadata_json
    )
    db.commit()
    db.refresh(verification)
    return verification


import hashlib
import os
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from pypdf import PdfReader

from app.db.models import Document, DocumentPage, DocumentProcessingHistory
from app.services.audit import log_action
from app.services.classification import classify_document
from app.storage.service import storage

PROCESSOR_VERSION = "phase-1b-v1"

def process_document(db: Session, project_id: str, document_id: str, current_user_id: str) -> Document:
    """
    Executes the Phase 1B document processing lifecycle:
    1. Storage and Hash re-verification (Integrity Check)
    2. PDF Structure & Page Metadata Indexing (Traceability)
    3. Deterministic Rule-Based Classification (Provenance)
    4. Processing History and Audit Tracking
    
    Idempotent: Reprocessing reconciles page records without duplication.
    Original file and user-declared metadata remain permanently preserved.
    """
    doc = db.query(Document).filter(Document.id == document_id, Document.project_id == project_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    started_at = datetime.now(timezone.utc)
    history = DocumentProcessingHistory(
        document_id=doc.id,
        processing_type="FULL_PIPELINE",
        status="STARTED",
        started_at=started_at,
        processor_version=PROCESSOR_VERSION
    )
    db.add(history)
    log_action(db, current_user_id, "DOCUMENT_VALIDATION_STARTED", "Document", doc.id)
    db.flush()

    try:
        # Step 1: Storage Object & Integrity Re-verification
        if not storage.exists(doc.storage_key):
            history.status = "FAILED"
            history.completed_at = datetime.now(timezone.utc)
            history.error_code = "STORAGE_OBJECT_MISSING"
            history.error_message = "Stored file object not found in storage."
            doc.processing_status = "PROCESSING_FAILED"
            log_action(db, current_user_id, "DOCUMENT_PROCESSING_FAILED", "Document", doc.id, "Storage object missing")
            db.commit()
            db.refresh(doc)
            return doc

        file_path = storage.get(doc.storage_key)
        with open(file_path, "rb") as f:
            stored_bytes = f.read()

        computed_hash = hashlib.sha256(stored_bytes).hexdigest()
        if computed_hash != doc.sha256_hash:
            history.status = "FAILED"
            history.completed_at = datetime.now(timezone.utc)
            history.error_code = "HASH_MISMATCH"
            history.error_message = "Stored file integrity re-verification failed: SHA-256 mismatch."
            doc.processing_status = "PROCESSING_FAILED"
            log_action(db, current_user_id, "DOCUMENT_PROCESSING_FAILED", "Document", doc.id, "Hash mismatch")
            db.commit()
            db.refresh(doc)
            return doc

        doc.processing_status = "VALIDATED"
        log_action(db, current_user_id, "DOCUMENT_VALIDATED", "Document", doc.id)
        db.flush()

        # Step 2: PDF Page Structure & Metadata Indexing
        try:
            reader = PdfReader(file_path)
            page_count = len(reader.pages)
            if page_count < 1:
                raise ValueError("PDF contains 0 pages")
        except Exception as e:
            history.status = "FAILED"
            history.completed_at = datetime.now(timezone.utc)
            history.error_code = "INVALID_PDF"
            history.error_message = f"Failed to parse PDF document structure: {str(e)}"
            doc.processing_status = "PROCESSING_FAILED"
            log_action(db, current_user_id, "DOCUMENT_PROCESSING_FAILED", "Document", doc.id, "Invalid PDF structure")
            db.commit()
            db.refresh(doc)
            return doc

        # Idempotency: Reconcile existing pages cleanly before inserting new structure
        db.query(DocumentPage).filter(DocumentPage.document_id == doc.id).delete()
        db.flush()

        for idx, page in enumerate(reader.pages, start=1):
            width = float(page.mediabox.width) if hasattr(page, "mediabox") and page.mediabox else None
            height = float(page.mediabox.height) if hasattr(page, "mediabox") and page.mediabox else None
            rotation = int(page.get("/Rotate", 0)) if hasattr(page, "get") else 0
            
            page_meta = {
                "width": width,
                "height": height,
                "rotation": rotation
            }
            page_rec = DocumentPage(
                document_id=doc.id,
                page_number=idx,
                page_count=page_count,
                page_metadata=page_meta
            )
            db.add(page_rec)

        db.flush()

        # Step 3: Deterministic Rule-Based Classification
        classified_type, score, method = classify_document(doc.original_filename, doc.document_type)
        doc.classified_document_type = classified_type
        doc.classification_score = score
        doc.classification_method = method
        doc.classified_at = datetime.now(timezone.utc)
        doc.processing_status = "READY_FOR_EXTRACTION"

        log_action(db, current_user_id, "DOCUMENT_CLASSIFIED", "Document", doc.id, f"Classified as {classified_type}")

        # Complete Processing Record
        history.status = "COMPLETED"
        history.completed_at = datetime.now(timezone.utc)
        history.metadata_json = {
            "page_count": page_count,
            "classified_type": classified_type,
            "score": score,
            "method": method
        }

        db.commit()
        db.refresh(doc)
        return doc

    except Exception as e:
        db.rollback()
        # Record failure attempt in isolated commit
        fail_history = DocumentProcessingHistory(
            document_id=doc.id,
            processing_type="FULL_PIPELINE",
            status="FAILED",
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            error_code="PROCESSING_ERROR",
            error_message="Unexpected internal error during processing.",
            processor_version=PROCESSOR_VERSION
        )
        db.add(fail_history)
        doc.processing_status = "PROCESSING_FAILED"
        log_action(db, current_user_id, "DOCUMENT_PROCESSING_FAILED", "Document", doc.id, "Unexpected failure")
        db.commit()
        db.refresh(doc)
        return doc

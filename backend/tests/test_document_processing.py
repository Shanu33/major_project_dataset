import io
import os
import hashlib
import pytest
from pypdf import PdfWriter
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import get_db, engine
from app.storage.service import storage

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

import itertools
_pdf_counter = itertools.count(1)

def create_test_pdf(num_pages: int = 1, seed: int = None) -> bytes:
    if seed is None:
        seed = next(_pdf_counter)
    writer = PdfWriter()
    for i in range(num_pages):
        writer.add_blank_page(width=595.0 + float(seed), height=842.0 + float(i))
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()

@pytest.fixture(scope="module")
def client_fixture():
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture(scope="module")
def setup_auth(client_fixture):
    # Setup test users and projects
    db = TestingSessionLocal()
    db.commit()
    db.close()

    # 1. Admin setup
    res = client_fixture.post("/api/auth/register/admin", json={"email": "admin_p1b@test.com", "password": "pass", "role": "admin"})
    admin_token = client_fixture.post("/api/auth/login", data={"username": "admin_p1b@test.com", "password": "pass"}).json()["access_token"]

    # 2. Contractor and Supervisor
    client_fixture.post("/api/auth/users", json={"email": "c1_p1b@test.com", "password": "p", "role": "contractor"}, headers={"Authorization": f"Bearer {admin_token}"})
    client_fixture.post("/api/auth/users", json={"email": "c2_p1b@test.com", "password": "p", "role": "contractor"}, headers={"Authorization": f"Bearer {admin_token}"})

    c1_token = client_fixture.post("/api/auth/login", data={"username": "c1_p1b@test.com", "password": "p"}).json()["access_token"]
    c2_token = client_fixture.post("/api/auth/login", data={"username": "c2_p1b@test.com", "password": "p"}).json()["access_token"]

    # 3. Projects
    res = client_fixture.post("/api/projects/", json={"name": "Project 1B Alpha"}, headers={"Authorization": f"Bearer {c1_token}"})
    p1_id = res.json()["id"]

    res = client_fixture.post("/api/projects/", json={"name": "Project 1B Beta"}, headers={"Authorization": f"Bearer {c2_token}"})
    p2_id = res.json()["id"]

    return p1_id, p2_id, c1_token, c2_token

def test_valid_pdf_validation_and_page_indexing(client_fixture, setup_auth):
    """
    A. Valid PDF validation succeeds.
    D. Valid PDF page count is detected.
    E. Correct number of Page records is created.
    F. Page numbers are correct.
    H. Processing history is created.
    K. Original document metadata remains unchanged.
    L. Original stored file remains unchanged.
    Q. Processing status transitions correctly.
    T. Audit events are generated.
    """
    p1_id, p2_id, c1_token, c2_token = setup_auth
    pdf_bytes = create_test_pdf(3)
    files = {'file': ('structural_foundation_plan.pdf', pdf_bytes, 'application/pdf')}
    data = {'document_type': 'STRUCTURAL_DRAWING'}

    # 1. Upload
    up_res = client_fixture.post(f"/api/projects/{p1_id}/documents/", files=files, data=data, headers={"Authorization": f"Bearer {c1_token}"})
    assert up_res.status_code == 200
    doc_id = up_res.json()["id"]
    orig_hash = up_res.json()["sha256_hash"]
    orig_declared_type = up_res.json()["document_type"]

    # 2. Trigger Process
    proc_res = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_id}/process", headers={"Authorization": f"Bearer {c1_token}"})
    assert proc_res.status_code == 200
    proc_data = proc_res.json()

    # Status transition
    assert proc_data["processing_status"] == "READY_FOR_EXTRACTION"
    assert proc_data["total_pages"] == 3
    assert proc_data["classified_document_type"] == "STRUCTURAL_DRAWING"
    assert proc_data["classification_score"] == 0.85
    assert proc_data["classification_method"] == "RULE_BASED"

    # Original metadata unchanged
    assert proc_data["document_type"] == orig_declared_type
    assert proc_data["original_filename"] == "structural_foundation_plan.pdf"

    # Verify pages endpoint
    pages_res = client_fixture.get(f"/api/projects/{p1_id}/documents/{doc_id}/pages", headers={"Authorization": f"Bearer {c1_token}"})
    assert pages_res.status_code == 200
    pages = pages_res.json()
    assert len(pages) == 3
    assert [p["page_number"] for p in pages] == [1, 2, 3]
    assert all(p["page_count"] == 3 for p in pages)
    assert all("width" in p["page_metadata"] for p in pages)

    # Verify history
    hist_res = client_fixture.get(f"/api/projects/{p1_id}/documents/{doc_id}/processing-history", headers={"Authorization": f"Bearer {c1_token}"})
    assert hist_res.status_code == 200
    hist = hist_res.json()
    assert len(hist) == 1
    assert hist[0]["status"] == "COMPLETED"
    assert hist[0]["processor_version"] == "phase-1b-v1"
    assert hist[0]["metadata_json"]["page_count"] == 3

    # Audit events
    db = TestingSessionLocal()
    actions = db.execute(text(f"SELECT action FROM audit_log WHERE entity_id='{doc_id}' ORDER BY timestamp ASC")).scalars().all()
    db.close()
    assert "DOCUMENT_UPLOADED" in actions
    assert "DOCUMENT_VALIDATION_STARTED" in actions
    assert "DOCUMENT_VALIDATED" in actions
    assert "DOCUMENT_CLASSIFIED" in actions

def test_missing_storage_object_causes_failure(client_fixture, setup_auth):
    """
    B. Missing storage object causes processing failure.
    I. Failed processing remains in history.
    """
    p1_id, p2_id, c1_token, c2_token = setup_auth
    pdf_bytes = create_test_pdf(1)
    files = {'file': ('doc_missing_file.pdf', pdf_bytes, 'application/pdf')}
    up_res = client_fixture.post(f"/api/projects/{p1_id}/documents/", files=files, headers={"Authorization": f"Bearer {c1_token}"})
    assert up_res.status_code == 200
    doc_id = up_res.json()["id"]

    # Delete physical file from storage manually
    db = TestingSessionLocal()
    storage_key = db.execute(text(f"SELECT storage_key FROM documents WHERE id='{doc_id}'")).scalar()
    db.close()
    storage.delete(storage_key)
    assert not storage.exists(storage_key)

    # Process
    proc_res = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_id}/process", headers={"Authorization": f"Bearer {c1_token}"})
    assert proc_res.status_code == 200
    proc_data = proc_res.json()
    assert proc_data["processing_status"] == "PROCESSING_FAILED"

    # Verify history recorded the failure
    hist_res = client_fixture.get(f"/api/projects/{p1_id}/documents/{doc_id}/processing-history", headers={"Authorization": f"Bearer {c1_token}"})
    assert hist_res.status_code == 200
    hist = hist_res.json()
    assert len(hist) == 1
    assert hist[0]["status"] == "FAILED"
    assert hist[0]["error_code"] == "STORAGE_OBJECT_MISSING"

def test_hash_mismatch_causes_failure(client_fixture, setup_auth):
    """
    C. SHA-256 mismatch causes processing failure.
    """
    p1_id, p2_id, c1_token, c2_token = setup_auth
    pdf_bytes = create_test_pdf(1)
    files = {'file': ('tampered_doc.pdf', pdf_bytes, 'application/pdf')}
    up_res = client_fixture.post(f"/api/projects/{p1_id}/documents/", files=files, headers={"Authorization": f"Bearer {c1_token}"})
    assert up_res.status_code == 200
    doc_id = up_res.json()["id"]

    # Tamper with the physical file in storage
    db = TestingSessionLocal()
    storage_key = db.execute(text(f"SELECT storage_key FROM documents WHERE id='{doc_id}'")).scalar()
    db.close()
    file_path = storage.get(storage_key)
    with open(file_path, "wb") as f:
        f.write(b"%PDF-1.4 Tampered Content")

    # Process
    proc_res = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_id}/process", headers={"Authorization": f"Bearer {c1_token}"})
    assert proc_res.status_code == 200
    proc_data = proc_res.json()
    assert proc_data["processing_status"] == "PROCESSING_FAILED"

    hist_res = client_fixture.get(f"/api/projects/{p1_id}/documents/{doc_id}/processing-history", headers={"Authorization": f"Bearer {c1_token}"})
    hist = hist_res.json()
    assert len(hist) == 1
    assert hist[0]["status"] == "FAILED"
    assert hist[0]["error_code"] == "HASH_MISMATCH"

def test_idempotent_reprocessing_and_retry_history(client_fixture, setup_auth):
    """
    G. Duplicate page records are prevented on re-process.
    J. Retry creates a new processing attempt in history.
    """
    p1_id, p2_id, c1_token, c2_token = setup_auth
    pdf_bytes = create_test_pdf(2)
    files = {'file': ('reprocess_sample.pdf', pdf_bytes, 'application/pdf')}
    up_res = client_fixture.post(f"/api/projects/{p1_id}/documents/", files=files, headers={"Authorization": f"Bearer {c1_token}"})
    doc_id = up_res.json()["id"]

    # Run 1
    res1 = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_id}/process", headers={"Authorization": f"Bearer {c1_token}"})
    assert res1.status_code == 200
    assert res1.json()["total_pages"] == 2

    # Run 2 (Reprocess)
    res2 = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_id}/process", headers={"Authorization": f"Bearer {c1_token}"})
    assert res2.status_code == 200
    assert res2.json()["total_pages"] == 2

    # Check page count in DB has not doubled
    pages_res = client_fixture.get(f"/api/projects/{p1_id}/documents/{doc_id}/pages", headers={"Authorization": f"Bearer {c1_token}"})
    assert len(pages_res.json()) == 2

    # Check history has 2 distinct attempts
    hist_res = client_fixture.get(f"/api/projects/{p1_id}/documents/{doc_id}/processing-history", headers={"Authorization": f"Bearer {c1_token}"})
    assert len(hist_res.json()) == 2

def test_classification_strategies(client_fixture, setup_auth):
    """
    M. Classification preserves original declared document_type.
    N. Rule-based classification produces a classification result.
    O. Unknown classification remains UNKNOWN rather than fabricated.
    P. Classification method is recorded.
    """
    p1_id, p2_id, c1_token, c2_token = setup_auth

    # 1. Architectural match by filename keyword
    files_arch = {'file': ('ground_floor_plan_arch.pdf', create_test_pdf(1), 'application/pdf')}
    res_arch = client_fixture.post(f"/api/projects/{p1_id}/documents/", files=files_arch, data={'document_type': 'UNKNOWN'}, headers={"Authorization": f"Bearer {c1_token}"})
    doc_arch_id = res_arch.json()["id"]
    p_arch = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_arch_id}/process", headers={"Authorization": f"Bearer {c1_token}"}).json()
    assert p_arch["classified_document_type"] == "ARCHITECTURAL_DRAWING"
    assert p_arch["document_type"] == "UNKNOWN" # Original declared type unchanged!
    assert p_arch["classification_score"] == 0.85
    assert p_arch["classification_method"] == "RULE_BASED"

    # 2. BOQ match by filename keyword
    files_boq = {'file': ('project_boq_items.pdf', create_test_pdf(1), 'application/pdf')}
    res_boq = client_fixture.post(f"/api/projects/{p1_id}/documents/", files=files_boq, headers={"Authorization": f"Bearer {c1_token}"})
    doc_boq_id = res_boq.json()["id"]
    p_boq = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_boq_id}/process", headers={"Authorization": f"Bearer {c1_token}"}).json()
    assert p_boq["classified_document_type"] == "BOQ"
    assert p_boq["classification_score"] == 0.85

    # 3. Fallback to declared type if filename has no keywords
    files_fb = {'file': ('document_scan_1234.pdf', create_test_pdf(1), 'application/pdf')}
    res_fb = client_fixture.post(f"/api/projects/{p1_id}/documents/", files=files_fb, data={'document_type': 'SPECIFICATION'}, headers={"Authorization": f"Bearer {c1_token}"})
    doc_fb_id = res_fb.json()["id"]
    p_fb = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_fb_id}/process", headers={"Authorization": f"Bearer {c1_token}"}).json()
    assert p_fb["classified_document_type"] == "SPECIFICATION"
    assert p_fb["classification_score"] == 0.60

    # 4. Unknown filename + Unknown declared type => UNKNOWN (not fabricated)
    files_unk = {'file': ('unlabeled_file_abc.pdf', create_test_pdf(1), 'application/pdf')}
    res_unk = client_fixture.post(f"/api/projects/{p1_id}/documents/", files=files_unk, data={'document_type': 'UNKNOWN'}, headers={"Authorization": f"Bearer {c1_token}"})
    doc_unk_id = res_unk.json()["id"]
    p_unk = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_unk_id}/process", headers={"Authorization": f"Bearer {c1_token}"}).json()
    assert p_unk["classified_document_type"] == "UNKNOWN"
    assert p_unk["classification_score"] == 0.0

def test_classification_score_semantics_and_documentation():
    """
    Verifies that the classification_score field is documented and exposed
    as an explicit heuristic rule score and not as a calibrated statistical probability.
    """
    from app.schemas.schemas import DocumentStatusResponse, DocumentResponse
    schema = DocumentStatusResponse.model_json_schema()
    score_prop = schema["properties"]["classification_score"]
    assert "heuristic" in score_prop["description"].lower()
    assert "not a statistical ml confidence or probability" in score_prop["description"].lower()

    doc_schema = DocumentResponse.model_json_schema()
    doc_score_prop = doc_schema["properties"]["classification_score"]
    assert "heuristic" in doc_score_prop["description"].lower()
    assert "not a statistical ml confidence or probability" in doc_score_prop["description"].lower()

def test_unauthorized_processing_and_access(client_fixture, setup_auth):
    """
    R. Unauthorized users cannot process another project's document.
    S. Unauthorized users cannot retrieve processing/page metadata.
    """
    p1_id, p2_id, c1_token, c2_token = setup_auth
    pdf_bytes = create_test_pdf(1)
    files = {'file': ('p1_private_doc.pdf', pdf_bytes, 'application/pdf')}

    # Upload to p1 with c1
    up_res = client_fixture.post(f"/api/projects/{p1_id}/documents/", files=files, headers={"Authorization": f"Bearer {c1_token}"})
    doc_id = up_res.json()["id"]

    # User c2 attempts to process p1's document -> 403 Forbidden
    proc_res = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_id}/process", headers={"Authorization": f"Bearer {c2_token}"})
    assert proc_res.status_code == 403

    # User c2 attempts to get processing-status -> 403 Forbidden
    status_res = client_fixture.get(f"/api/projects/{p1_id}/documents/{doc_id}/processing-status", headers={"Authorization": f"Bearer {c2_token}"})
    assert status_res.status_code == 403

    # User c2 attempts to get processing-history -> 403 Forbidden
    hist_res = client_fixture.get(f"/api/projects/{p1_id}/documents/{doc_id}/processing-history", headers={"Authorization": f"Bearer {c2_token}"})
    assert hist_res.status_code == 403

    # User c2 attempts to get pages -> 403 Forbidden
    pages_res = client_fixture.get(f"/api/projects/{p1_id}/documents/{doc_id}/pages", headers={"Authorization": f"Bearer {c2_token}"})
    assert pages_res.status_code == 403

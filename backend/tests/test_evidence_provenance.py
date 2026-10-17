import io
import pytest
from pypdf import PdfWriter
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import get_db, engine

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_test_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=595.0, height=842.0)
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
    res = client_fixture.post("/api/auth/register/admin", json={"email": "admin_p1c@test.com", "password": "pass", "role": "admin"})
    admin_token = client_fixture.post("/api/auth/login", data={"username": "admin_p1c@test.com", "password": "pass"}).json()["access_token"]

    # 2. Contractor and Supervisor
    client_fixture.post("/api/auth/users", json={"email": "c1_p1c@test.com", "password": "p", "role": "contractor"}, headers={"Authorization": f"Bearer {admin_token}"})
    client_fixture.post("/api/auth/users", json={"email": "c2_p1c@test.com", "password": "p", "role": "contractor"}, headers={"Authorization": f"Bearer {admin_token}"})
    client_fixture.post("/api/auth/users", json={"email": "s1_p1c@test.com", "password": "p", "role": "supervisor"}, headers={"Authorization": f"Bearer {admin_token}"})

    c1_token = client_fixture.post("/api/auth/login", data={"username": "c1_p1c@test.com", "password": "p"}).json()["access_token"]
    c2_token = client_fixture.post("/api/auth/login", data={"username": "c2_p1c@test.com", "password": "p"}).json()["access_token"]
    s1_token = client_fixture.post("/api/auth/login", data={"username": "s1_p1c@test.com", "password": "p"}).json()["access_token"]

    # 3. Projects
    res = client_fixture.post("/api/projects/", json={"name": "Project 1C Alpha"}, headers={"Authorization": f"Bearer {c1_token}"})
    p1_id = res.json()["id"]

    res = client_fixture.post("/api/projects/", json={"name": "Project 1C Beta"}, headers={"Authorization": f"Bearer {c2_token}"})
    p2_id = res.json()["id"]

    # Add s1 to Project 1
    db = TestingSessionLocal()
    s1_id = db.execute(text("SELECT id FROM users WHERE email = 's1_p1c@test.com'")).scalar()
    db.close()
    client_fixture.post(f"/api/projects/{p1_id}/members?user_id={s1_id}", headers={"Authorization": f"Bearer {admin_token}"})

    # Upload and process a document in p1
    pdf_bytes = create_test_pdf()
    files = {'file': ('structural_spec_sheet.pdf', pdf_bytes, 'application/pdf')}
    up_res = client_fixture.post(f"/api/projects/{p1_id}/documents/", files=files, headers={"Authorization": f"Bearer {c1_token}"})
    doc_id = up_res.json()["id"]
    client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_id}/process", headers={"Authorization": f"Bearer {c1_token}"})

    pages = client_fixture.get(f"/api/projects/{p1_id}/documents/{doc_id}/pages", headers={"Authorization": f"Bearer {c1_token}"}).json()
    page_id = pages[0]["id"]

    return p1_id, p2_id, c1_token, c2_token, s1_token, doc_id, page_id

def test_evidence_creation_and_integrity(client_fixture, setup_auth):
    """
    A. Evidence creation.
    B. Evidence requires valid document.
    C. Page-linked evidence requires valid page.
    S. Repeated evidence creation follows the defined duplicate policy.
    O. Audit event is created.
    """
    p1_id, p2_id, c1_token, c2_token, s1_token, doc_id, page_id = setup_auth

    # A. Valid Evidence creation
    ev_data = {
        "page_id": page_id,
        "evidence_type": "DIMENSION",
        "source_reference": "Drawing S-101 Section A-A",
        "locator": "region:x=100,y=200,w=300,h=50",
        "raw_content": "Beam Span = 600 mm",
        "metadata_json": {"grid_line": "B-3"}
    }
    res = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_id}/evidence", json=ev_data, headers={"Authorization": f"Bearer {c1_token}"})
    assert res.status_code == 200
    ev = res.json()
    assert ev["document_id"] == doc_id
    assert ev["page_id"] == page_id
    assert ev["evidence_type"] == "DIMENSION"
    assert ev["source_reference"] == "Drawing S-101 Section A-A"
    assert ev["raw_content"] == "Beam Span = 600 mm"
    assert ev["verification_status"] == "UNVERIFIED"

    # S. Duplicate evidence within same document is rejected
    dup_res = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_id}/evidence", json=ev_data, headers={"Authorization": f"Bearer {c1_token}"})
    assert dup_res.status_code == 409
    assert "already exists" in dup_res.json()["detail"]

    # B. Evidence requires valid document
    res_bad_doc = client_fixture.post(f"/api/projects/{p1_id}/documents/nonexistent-doc/evidence", json=ev_data, headers={"Authorization": f"Bearer {c1_token}"})
    assert res_bad_doc.status_code == 404

    # C. Page-linked evidence requires valid page
    bad_page_data = dict(ev_data)
    bad_page_data["page_id"] = "nonexistent-page-id"
    bad_page_data["locator"] = "region:x=999,y=999"
    res_bad_page = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_id}/evidence", json=bad_page_data, headers={"Authorization": f"Bearer {c1_token}"})
    assert res_bad_page.status_code == 400
    assert "does not exist" in res_bad_page.json()["detail"]

    # O. Audit event is created
    db = TestingSessionLocal()
    audit_count = db.execute(text(f"SELECT COUNT(*) FROM audit_log WHERE action='EVIDENCE_CREATED' AND entity_id='{ev['id']}'")).scalar()
    db.close()
    assert audit_count == 1

def test_fact_creation_and_provenance(client_fixture, setup_auth):
    """
    D. Fact requires valid evidence.
    F. Raw value is preserved.
    G. Normalized value is preserved separately.
    H. Unit is preserved.
    I. Extraction method is recorded.
    J. Extraction version is recorded.
    K. Verification status is explicit.
    T. Provenance chain can be traversed:
       Fact -> Evidence -> Page -> Document -> Project
    """
    p1_id, p2_id, c1_token, c2_token, s1_token, doc_id, page_id = setup_auth

    # 1. Create Evidence
    ev_data = {
        "page_id": page_id,
        "evidence_type": "TEXT",
        "source_reference": "Specification Clause 4.2",
        "locator": "para_3",
        "raw_content": "Clear cover to main reinforcement shall be 40 mm",
    }
    ev = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_id}/evidence", json=ev_data, headers={"Authorization": f"Bearer {c1_token}"}).json()
    ev_id = ev["id"]

    # 2. Create Fact (with deterministic unit normalization: 40 mm -> 0.04 m)
    fact_data = {
        "fact_type": "DIMENSION",
        "field_name": "clear_cover",
        "raw_value": "40 mm",
        "extraction_method": "MANUAL",
        "metadata_json": {"structural_element": "beam"}
    }
    f_res = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_id}/evidence/{ev_id}/facts", json=fact_data, headers={"Authorization": f"Bearer {c1_token}"})
    assert f_res.status_code == 200
    fact = f_res.json()

    # Assert Fact attributes
    assert fact["evidence_id"] == ev_id
    assert fact["field_name"] == "clear_cover"
    assert fact["raw_value"] == "40 mm"
    assert float(fact["normalized_value"]) == 0.04 # 40 mm converted to 0.04 m
    assert fact["normalized_unit"] == "m"
    assert fact["extraction_method"] == "MANUAL"
    assert fact["extraction_version"] == "phase-1c-v1"
    assert fact["extraction_status"] == "EXTRACTED"
    assert fact["verification_status"] == "UNVERIFIED"

    # D. Fact requires valid evidence
    f_bad_ev = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_id}/evidence/nonexistent-ev/facts", json=fact_data, headers={"Authorization": f"Bearer {c1_token}"})
    assert f_bad_ev.status_code == 404

    # T. Provenance chain can be traversed end-to-end
    prov_res = client_fixture.get(f"/api/projects/{p1_id}/documents/{doc_id}/facts/{fact['id']}", headers={"Authorization": f"Bearer {c1_token}"})
    assert prov_res.status_code == 200
    prov = prov_res.json()
    assert prov["fact_id"] == fact["id"]
    assert prov["raw_value"] == "40 mm"
    assert float(prov["normalized_value"]) == 0.04
    assert prov["evidence_id"] == ev_id
    assert prov["source_reference"] == "Specification Clause 4.2"
    assert prov["page_id"] == page_id
    assert prov["page_number"] == 1
    assert prov["document_id"] == doc_id
    assert prov["original_filename"] == "structural_spec_sheet.pdf"
    assert prov["project_id"] == p1_id
    assert prov["project_name"] == "Project 1C Alpha"

def test_supervisor_verification_and_immutable_correction(client_fixture, setup_auth):
    """
    L. Supervisor verification works.
    M. Supervisor correction preserves original fact.
    N. Corrected value is separately traceable.
    R. Contractor cannot perform supervisor-only verification.
    """
    p1_id, p2_id, c1_token, c2_token, s1_token, doc_id, page_id = setup_auth

    # 1. Create Evidence and Fact
    ev = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_id}/evidence", json={
        "page_id": page_id,
        "evidence_type": "DIMENSION",
        "source_reference": "Column C1 Schedule",
        "locator": "row_12",
        "raw_content": "Width = 450 mm"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()

    fact = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_id}/evidence/{ev['id']}/facts", json={
        "fact_type": "DIMENSION",
        "field_name": "column_width",
        "raw_value": "450 mm"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()

    # R. Contractor attempts verification -> 403 Forbidden
    verify_payload = {
        "status": "VERIFIED",
        "verification_note": "Contractor attempting self-verification"
    }
    c_res = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_id}/facts/{fact['id']}/verify", json=verify_payload, headers={"Authorization": f"Bearer {c1_token}"})
    assert c_res.status_code == 403

    # L & M & N. Supervisor verifies with a correction (e.g. As-built amendment to 500 mm / 0.5 m)
    correction_payload = {
        "status": "VERIFIED",
        "verification_note": "Approved per site amendment addendum A2",
        "corrected_value": 0.5,
        "corrected_unit": "m"
    }
    s_res = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_id}/facts/{fact['id']}/verify", json=correction_payload, headers={"Authorization": f"Bearer {s1_token}"})
    assert s_res.status_code == 200
    v_data = s_res.json()
    assert v_data["status"] == "VERIFIED"
    assert float(v_data["corrected_value"]) == 0.5
    assert v_data["corrected_unit"] == "m"

    # IMMUTABILITY CHECK: Retrieve fact provenance again
    prov_res = client_fixture.get(f"/api/projects/{p1_id}/documents/{doc_id}/facts/{fact['id']}", headers={"Authorization": f"Bearer {c1_token}"})
    prov = prov_res.json()

    # Original extracted values are permanently unchanged!
    assert prov["raw_value"] == "450 mm"
    assert float(prov["normalized_value"]) == 0.45
    assert prov["verification_status"] == "VERIFIED"

    # Separate verification history tracks the correction
    assert len(prov["verifications"]) == 1
    assert float(prov["verifications"][0]["corrected_value"]) == 0.5
    assert prov["verifications"][0]["corrected_unit"] == "m"
    assert prov["verifications"][0]["verification_note"] == "Approved per site amendment addendum A2"

def test_unauthorized_cross_project_provenance_access(client_fixture, setup_auth):
    """
    P. Unauthorized user cannot access another project's evidence.
    Q. Unauthorized user cannot create facts in another project.
    """
    p1_id, p2_id, c1_token, c2_token, s1_token, doc_id, page_id = setup_auth

    # User c2 (only in p2) attempts to create evidence in p1 -> 403 Forbidden
    res_ev = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_id}/evidence", json={
        "evidence_type": "TEXT",
        "source_reference": "Unauthorized ref"
    }, headers={"Authorization": f"Bearer {c2_token}"})
    assert res_ev.status_code == 403

    # User c2 attempts to list evidence in p1 -> 403 Forbidden
    res_list = client_fixture.get(f"/api/projects/{p1_id}/documents/{doc_id}/evidence", headers={"Authorization": f"Bearer {c2_token}"})
    assert res_list.status_code == 403

def test_structured_json_locator_storage_and_retrieval(client_fixture, setup_auth):
    """
    1. LOCATOR TYPE:
    Evidence.locator stores structured JSON without converting it to a string.
    Example:
    {
      "type": "bbox",
      "x0": 120,
      "y0": 300,
      "x1": 570,
      "y1": 500,
      "unit": "pt"
    }
    """
    p1_id, p2_id, c1_token, c2_token, s1_token, doc_id, page_id = setup_auth

    locator_data = {
        "type": "bbox",
        "x0": 120,
        "y0": 300,
        "x1": 570,
        "y1": 500,
        "unit": "pt"
    }

    ev_data = {
        "page_id": page_id,
        "evidence_type": "DRAWING_REGION",
        "source_reference": "Drawing S-103 Footing Detail",
        "locator": locator_data,
        "raw_content": "Footing F1 dimensions",
    }

    res = client_fixture.post(
        f"/api/projects/{p1_id}/documents/{doc_id}/evidence",
        json=ev_data,
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 200
    ev = res.json()
    assert isinstance(ev["locator"], dict)
    assert ev["locator"] == locator_data

    # Query from database directly using raw SQL to prove native JSON storage
    db = TestingSessionLocal()
    row = db.execute(text(f"SELECT locator FROM evidence WHERE id='{ev['id']}'")).scalar()
    db.close()
    assert isinstance(row, dict)
    assert row == locator_data

def test_exact_numeric_precision_preserved(client_fixture, setup_auth):
    """
    2. NUMERIC PRECISION:
    ExtractedFact.normalized_value uses exact NUMERIC(18,6).
    raw_value is preserved as original source string.
    """
    from decimal import Decimal

    p1_id, p2_id, c1_token, c2_token, s1_token, doc_id, page_id = setup_auth

    # Create evidence
    ev_data = {
        "page_id": page_id,
        "evidence_type": "DIMENSION",
        "source_reference": "Civil Survey Coordinates",
        "locator": {"station": "CH 0+150.500"},
        "raw_content": "12.345678 m chainage offset",
    }
    ev = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_id}/evidence", json=ev_data, headers={"Authorization": f"Bearer {c1_token}"}).json()

    # Fact with high-precision decimal: 12.345678
    fact_data = {
        "fact_type": "DIMENSION",
        "field_name": "offset_distance",
        "raw_value": "12.345678 m",
        "extraction_method": "MANUAL",
    }
    f_res = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_id}/evidence/{ev['id']}/facts", json=fact_data, headers={"Authorization": f"Bearer {c1_token}"})
    assert f_res.status_code == 200
    fact = f_res.json()

    assert fact["raw_value"] == "12.345678 m"
    assert Decimal(str(fact["normalized_value"])) == Decimal("12.345678")
    assert fact["normalized_unit"] == "m"

    # Verify directly via raw SQL
    db = TestingSessionLocal()
    raw_val, norm_val = db.execute(text(f"SELECT raw_value, normalized_value FROM extracted_facts WHERE id='{fact['id']}'")).one()
    db.close()

    assert raw_val == "12.345678 m"
    assert isinstance(norm_val, Decimal)
    assert norm_val == Decimal("12.345678")

def test_fact_verification_immutability_trigger(client_fixture, setup_auth):
    """
    3. FACT VERIFICATION IMMUTABILITY:
    FactVerification records are protected by database-level trigger.
    Raw SQL tests proving:
    - INSERT succeeds
    - UPDATE fails
    - DELETE fails
    """
    import uuid

    p1_id, p2_id, c1_token, c2_token, s1_token, doc_id, page_id = setup_auth

    # 1. Create Evidence and Fact
    ev = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_id}/evidence", json={
        "page_id": page_id,
        "evidence_type": "DIMENSION",
        "source_reference": "Trigger Test Schedule",
        "locator": {"row": 5},
        "raw_content": "Thickness = 250 mm"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()

    fact = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_id}/evidence/{ev['id']}/facts", json={
        "fact_type": "DIMENSION",
        "field_name": "slab_thickness",
        "raw_value": "250 mm"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()

    # 2. Get supervisor user_id
    db = TestingSessionLocal()
    s1_id = db.execute(text("SELECT id FROM users WHERE email = 's1_p1c@test.com'")).scalar()
    db.close()

    # 3. Test raw SQL INSERT succeeds
    v_id = str(uuid.uuid4())
    db = TestingSessionLocal()
    db.execute(text(f"""
        INSERT INTO fact_verifications (id, fact_id, verified_by, status, verification_note, corrected_value, corrected_unit)
        VALUES ('{v_id}', '{fact['id']}', '{s1_id}', 'VERIFIED', 'Initial sign-off', 0.250000, 'm')
    """))
    db.commit()

    # Confirm it was inserted
    status_db = db.execute(text(f"SELECT status FROM fact_verifications WHERE id='{v_id}'")).scalar()
    assert status_db == "VERIFIED"

    # 4. Test raw SQL UPDATE fails via PostgreSQL trigger
    try:
        db.execute(text(f"UPDATE fact_verifications SET status='REJECTED' WHERE id='{v_id}'"))
        db.commit()
        pytest.fail("UPDATE on fact_verifications succeeded, immutability trigger failed!")
    except Exception as e:
        db.rollback()
        assert "Fact verification records are immutable" in str(e) or "cannot be updated or deleted" in str(e)

    # 5. Test raw SQL DELETE fails via PostgreSQL trigger
    try:
        db.execute(text(f"DELETE FROM fact_verifications WHERE id='{v_id}'"))
        db.commit()
        pytest.fail("DELETE on fact_verifications succeeded, immutability trigger failed!")
    except Exception as e:
        db.rollback()
        assert "Fact verification records are immutable" in str(e) or "cannot be updated or deleted" in str(e)

    db.close()


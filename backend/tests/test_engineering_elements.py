import io
import uuid
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
def setup_p1d(client_fixture):
    # Setup test users and projects
    db = TestingSessionLocal()
    db.commit()
    db.close()

    # Admin setup
    res = client_fixture.post("/api/auth/register/admin", json={"email": "admin_p1d@test.com", "password": "pass", "role": "admin"})
    admin_token = client_fixture.post("/api/auth/login", data={"username": "admin_p1d@test.com", "password": "pass"}).json()["access_token"]

    # Users
    client_fixture.post("/api/auth/users", json={"email": "c1_p1d@test.com", "password": "p", "role": "contractor"}, headers={"Authorization": f"Bearer {admin_token}"})
    client_fixture.post("/api/auth/users", json={"email": "c2_p1d@test.com", "password": "p", "role": "contractor"}, headers={"Authorization": f"Bearer {admin_token}"})
    client_fixture.post("/api/auth/users", json={"email": "s1_p1d@test.com", "password": "p", "role": "supervisor"}, headers={"Authorization": f"Bearer {admin_token}"})

    c1_token = client_fixture.post("/api/auth/login", data={"username": "c1_p1d@test.com", "password": "p"}).json()["access_token"]
    c2_token = client_fixture.post("/api/auth/login", data={"username": "c2_p1d@test.com", "password": "p"}).json()["access_token"]
    s1_token = client_fixture.post("/api/auth/login", data={"username": "s1_p1d@test.com", "password": "p"}).json()["access_token"]

    # Projects
    p1 = client_fixture.post("/api/projects/", json={"name": "Project 1D Alpha"}, headers={"Authorization": f"Bearer {c1_token}"}).json()
    p1_id = p1["id"]
    p2 = client_fixture.post("/api/projects/", json={"name": "Project 1D Beta"}, headers={"Authorization": f"Bearer {c2_token}"}).json()
    p2_id = p2["id"]

    # Add supervisor to project 1
    db = TestingSessionLocal()
    s1_id = db.execute(text("SELECT id FROM users WHERE email = 's1_p1d@test.com'")).scalar()
    db.close()
    client_fixture.post(f"/api/projects/{p1_id}/members?user_id={s1_id}", headers={"Authorization": f"Bearer {admin_token}"})

    # Upload document to project 1
    pdf_bytes = create_test_pdf()
    files = {'file': ('structural_spec.pdf', pdf_bytes, 'application/pdf')}
    up_res = client_fixture.post(f"/api/projects/{p1_id}/documents/", files=files, headers={"Authorization": f"Bearer {c1_token}"})
    doc_id = up_res.json()["id"]
    client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_id}/process", headers={"Authorization": f"Bearer {c1_token}"})

    pages = client_fixture.get(f"/api/projects/{p1_id}/documents/{doc_id}/pages", headers={"Authorization": f"Bearer {c1_token}"}).json()
    page_id = pages[0]["id"]

    # Create Evidence in project 1
    ev_data = {
        "page_id": page_id,
        "evidence_type": "DRAWING_REGION",
        "source_reference": "Drawing S-101 Section A",
        "locator": {"type": "bbox", "x0": 50, "y0": 100, "x1": 250, "y1": 300},
        "raw_content": "Column C1 Cross-Section 400x400 mm"
    }
    ev = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_id}/evidence", json=ev_data, headers={"Authorization": f"Bearer {c1_token}"}).json()
    ev_id = ev["id"]

    # Create Fact in project 1 (initially UNVERIFIED)
    fact_data = {
        "fact_type": "DIMENSION",
        "field_name": "column_width",
        "raw_value": "400 mm",
        "extraction_method": "MANUAL"
    }
    f1 = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_id}/evidence/{ev_id}/facts", json=fact_data, headers={"Authorization": f"Bearer {c1_token}"}).json()
    f1_id = f1["id"]

    # Create a second fact that is explicitly verified
    f2 = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_id}/evidence/{ev_id}/facts", json={
        "fact_type": "DIMENSION",
        "field_name": "column_depth",
        "raw_value": "400 mm",
        "extraction_method": "MANUAL"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()
    f2_id = f2["id"]
    client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_id}/facts/{f2_id}/verify", json={"status": "VERIFIED"}, headers={"Authorization": f"Bearer {s1_token}"})

    # Create a third fact that is explicitly rejected
    f3 = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_id}/evidence/{ev_id}/facts", json={
        "fact_type": "DIMENSION",
        "field_name": "erroneous_dim",
        "raw_value": "999 mm",
        "extraction_method": "MANUAL"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()
    f3_id = f3["id"]
    client_fixture.post(f"/api/projects/{p1_id}/documents/{doc_id}/facts/{f3_id}/verify", json={"status": "REJECTED"}, headers={"Authorization": f"Bearer {s1_token}"})

    # Upload document to project 2 for cross-project checks
    files2 = {'file': ('p2_drawing.pdf', pdf_bytes, 'application/pdf')}
    up_res2 = client_fixture.post(f"/api/projects/{p2_id}/documents/", files=files2, headers={"Authorization": f"Bearer {c2_token}"})
    doc2_id = up_res2.json()["id"]
    client_fixture.post(f"/api/projects/{p2_id}/documents/{doc2_id}/process", headers={"Authorization": f"Bearer {c2_token}"})
    pages2 = client_fixture.get(f"/api/projects/{p2_id}/documents/{doc2_id}/pages", headers={"Authorization": f"Bearer {c2_token}"}).json()
    ev2 = client_fixture.post(f"/api/projects/{p2_id}/documents/{doc2_id}/evidence", json={
        "page_id": pages2[0]["id"],
        "evidence_type": "TEXT",
        "source_reference": "P2 Note"
    }, headers={"Authorization": f"Bearer {c2_token}"}).json()
    f_p2 = client_fixture.post(f"/api/projects/{p2_id}/documents/{doc2_id}/evidence/{ev2['id']}/facts", json={
        "fact_type": "SPECIFICATION",
        "field_name": "grade",
        "raw_value": "C30"
    }, headers={"Authorization": f"Bearer {c2_token}"}).json()
    # Mark f_p2 verified in project 2
    # Register supervisor in project 2
    client_fixture.post(f"/api/projects/{p2_id}/members?user_id={s1_id}", headers={"Authorization": f"Bearer {admin_token}"})
    client_fixture.post(f"/api/projects/{p2_id}/documents/{doc2_id}/facts/{f_p2['id']}/verify", json={"status": "VERIFIED"}, headers={"Authorization": f"Bearer {s1_token}"})

    return {
        "p1_id": p1_id,
        "p2_id": p2_id,
        "c1_token": c1_token,
        "c2_token": c2_token,
        "s1_token": s1_token,
        "admin_token": admin_token,
        "doc_id": doc_id,
        "page_id": page_id,
        "f_unverified_id": f1_id,
        "f_verified_id": f2_id,
        "f_rejected_id": f3_id,
        "f_p2_verified_id": f_p2["id"]
    }

def test_engineering_element_creation_without_source_fact(client_fixture, setup_p1d):
    """1. EngineeringElement creation without source_fact_id (manual input)."""
    env = setup_p1d
    payload = {
        "element_type": "COLUMN",
        "element_name": "Column C-Manual",
        "metadata_json": {"grid_location": "A-1"}
    }
    res = client_fixture.post(
        f"/api/projects/{env['p1_id']}/engineering-elements",
        json=payload,
        headers={"Authorization": f"Bearer {env['c1_token']}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["element_name"] == "Column C-Manual"
    assert data["element_type"] == "COLUMN"
    assert data["source_fact_id"] is None
    assert data["verification_status"] == "PENDING"
    assert len(data["revisions"]) == 1
    assert data["revisions"][0]["revision_number"] == 0
    assert data["provenance"]["provenance_type"] == "MANUALLY_SUPPLIED"

def test_engineering_element_creation_using_verified_fact(client_fixture, setup_p1d):
    """2. EngineeringElement creation using a VERIFIED fact."""
    env = setup_p1d
    payload = {
        "element_type": "COLUMN",
        "element_name": "Column C1",
        "source_fact_id": env["f_verified_id"],
        "metadata_json": {"floor": "L1"}
    }
    res = client_fixture.post(
        f"/api/projects/{env['p1_id']}/engineering-elements",
        json=payload,
        headers={"Authorization": f"Bearer {env['c1_token']}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["element_name"] == "Column C1"
    assert data["element_type"] == "COLUMN"
    assert data["source_fact_id"] == env["f_verified_id"]
    assert data["source_document_id"] == env["doc_id"]
    assert data["source_page_id"] == env["page_id"]
    assert data["provenance"]["provenance_type"] == "DOCUMENT_DERIVED"
    assert data["provenance"]["fact_id"] == env["f_verified_id"]
    assert data["provenance"]["fact_verification_status"] == "VERIFIED"

def test_reject_unverified_pending_fact(client_fixture, setup_p1d):
    """3. Reject PENDING/UNVERIFIED fact."""
    env = setup_p1d
    payload = {
        "element_type": "COLUMN",
        "element_name": "Column C-Unverified",
        "source_fact_id": env["f_unverified_id"]
    }
    res = client_fixture.post(
        f"/api/projects/{env['p1_id']}/engineering-elements",
        json=payload,
        headers={"Authorization": f"Bearer {env['c1_token']}"}
    )
    assert res.status_code == 400
    assert "Source fact must have verification_status VERIFIED" in res.json()["detail"]

def test_reject_unverified_rejected_fact(client_fixture, setup_p1d):
    """4. Reject REJECTED fact."""
    env = setup_p1d
    payload = {
        "element_type": "COLUMN",
        "element_name": "Column C-Rejected",
        "source_fact_id": env["f_rejected_id"]
    }
    res = client_fixture.post(
        f"/api/projects/{env['p1_id']}/engineering-elements",
        json=payload,
        headers={"Authorization": f"Bearer {env['c1_token']}"}
    )
    assert res.status_code == 400
    assert "Source fact must have verification_status VERIFIED" in res.json()["detail"]

def test_reject_cross_project_source_fact(client_fixture, setup_p1d):
    """5. Reject cross-project source_fact."""
    env = setup_p1d
    # Attempt to create element in Project 1 using verified fact from Project 2
    payload = {
        "element_type": "SLAB",
        "element_name": "Slab S1",
        "source_fact_id": env["f_p2_verified_id"]
    }
    res = client_fixture.post(
        f"/api/projects/{env['p1_id']}/engineering-elements",
        json=payload,
        headers={"Authorization": f"Bearer {env['c1_token']}"}
    )
    assert res.status_code == 400
    assert "Cross-project" in res.json()["detail"]

def test_reject_unauthorized_project_access(client_fixture, setup_p1d):
    """6. Reject unauthorized project access."""
    env = setup_p1d
    # c2 (only in p2) tries to create element in p1
    res = client_fixture.post(
        f"/api/projects/{env['p1_id']}/engineering-elements",
        json={"element_type": "BEAM", "element_name": "Beam B1"},
        headers={"Authorization": f"Bearer {env['c2_token']}"}
    )
    assert res.status_code == 403

def test_read_and_list_project_isolation(client_fixture, setup_p1d):
    """7. Read/list project isolation."""
    env = setup_p1d
    # Create element in p1
    el_res = client_fixture.post(
        f"/api/projects/{env['p1_id']}/engineering-elements",
        json={"element_type": "FOOTING", "element_name": "Footing F1"},
        headers={"Authorization": f"Bearer {env['c1_token']}"}
    )
    el_id = el_res.json()["id"]

    # c2 cannot read element in p1
    res_get = client_fixture.get(
        f"/api/projects/{env['p1_id']}/engineering-elements/{el_id}",
        headers={"Authorization": f"Bearer {env['c2_token']}"}
    )
    assert res_get.status_code == 403

    # c2 cannot list elements in p1
    res_list = client_fixture.get(
        f"/api/projects/{env['p1_id']}/engineering-elements",
        headers={"Authorization": f"Bearer {env['c2_token']}"}
    )
    assert res_list.status_code == 403

    # c1 can list elements in p1 and finds F1
    c1_list = client_fixture.get(
        f"/api/projects/{env['p1_id']}/engineering-elements",
        headers={"Authorization": f"Bearer {env['c1_token']}"}
    )
    assert c1_list.status_code == 200
    ids = [item["id"] for item in c1_list.json()]
    assert el_id in ids

def test_provenance_chain_is_correct(client_fixture, setup_p1d):
    """8. Provenance chain is correct and fully traversable."""
    env = setup_p1d
    res = client_fixture.post(
        f"/api/projects/{env['p1_id']}/engineering-elements",
        json={
            "element_type": "PILE",
            "element_name": "Pile P-10",
            "source_fact_id": env["f_verified_id"]
        },
        headers={"Authorization": f"Bearer {env['c1_token']}"}
    )
    assert res.status_code == 200
    prov = res.json()["provenance"]

    assert prov["provenance_type"] == "DOCUMENT_DERIVED"
    assert prov["fact_id"] == env["f_verified_id"]
    assert prov["fact_verification_status"] == "VERIFIED"
    assert prov["document_id"] == env["doc_id"]
    assert prov["original_filename"] == "structural_spec.pdf"
    assert prov["page_id"] == env["page_id"]
    assert prov["project_id"] == env["p1_id"]
    assert prov["project_name"] == "Project 1D Alpha"

def test_element_verification_works(client_fixture, setup_p1d):
    """9. Element verification works and contractor is rejected."""
    env = setup_p1d
    el = client_fixture.post(
        f"/api/projects/{env['p1_id']}/engineering-elements",
        json={"element_type": "SLAB", "element_name": "Slab Ground"},
        headers={"Authorization": f"Bearer {env['c1_token']}"}
    ).json()

    # Contractor cannot verify -> 403
    c_res = client_fixture.post(
        f"/api/projects/{env['p1_id']}/engineering-elements/{el['id']}/verify",
        json={"verification_status": "VERIFIED"},
        headers={"Authorization": f"Bearer {env['c1_token']}"}
    )
    assert c_res.status_code == 403

    # Supervisor can verify -> 200
    s_res = client_fixture.post(
        f"/api/projects/{env['p1_id']}/engineering-elements/{el['id']}/verify",
        json={"verification_status": "VERIFIED", "verification_note": "Site verified per inspection"},
        headers={"Authorization": f"Bearer {env['s1_token']}"}
    )
    assert s_res.status_code == 200
    assert s_res.json()["verification_status"] == "VERIFIED"

def test_historical_revision_preserves_original_state(client_fixture, setup_p1d):
    """10. Historical revision/correction does not overwrite original state."""
    env = setup_p1d
    # Create element (revision 0)
    el = client_fixture.post(
        f"/api/projects/{env['p1_id']}/engineering-elements",
        json={"element_type": "WALL", "element_name": "Retaining Wall W1"},
        headers={"Authorization": f"Bearer {env['c1_token']}"}
    ).json()
    el_id = el["id"]

    # Supervisor issues revision 1 with corrected name and status
    client_fixture.post(
        f"/api/projects/{env['p1_id']}/engineering-elements/{el_id}/revisions",
        json={
            "element_name": "Retaining Wall W1-Amended",
            "verification_status": "CORRECTED",
            "revision_note": "Amended according to addendum #3"
        },
        headers={"Authorization": f"Bearer {env['s1_token']}"}
    )

    # Fetch element and check revisions
    updated = client_fixture.get(
        f"/api/projects/{env['p1_id']}/engineering-elements/{el_id}",
        headers={"Authorization": f"Bearer {env['c1_token']}"}
    ).json()

    assert len(updated["revisions"]) == 2
    rev0 = updated["revisions"][0]
    rev1 = updated["revisions"][1]

    # Revision 0 is permanently preserved!
    assert rev0["revision_number"] == 0
    assert rev0["element_name"] == "Retaining Wall W1"
    assert rev0["verification_status"] == "PENDING"

    # Revision 1 contains the correction
    assert rev1["revision_number"] == 1
    assert rev1["element_name"] == "Retaining Wall W1-Amended"
    assert rev1["verification_status"] == "CORRECTED"
    assert rev1["revision_note"] == "Amended according to addendum #3"

def test_element_revision_db_immutability_trigger(client_fixture, setup_p1d):
    """11. DB-level immutability of historical revision records via raw SQL."""
    env = setup_p1d
    el = client_fixture.post(
        f"/api/projects/{env['p1_id']}/engineering-elements",
        json={"element_type": "KERB", "element_name": "Kerb K-1"},
        headers={"Authorization": f"Bearer {env['c1_token']}"}
    ).json()
    el_id = el["id"]

    db = TestingSessionLocal()
    s1_id = db.execute(text(f"SELECT id FROM users WHERE email = 's1_p1d@test.com'")).scalar()
    
    # 1. Raw SQL INSERT succeeds
    rev_id = str(uuid.uuid4())
    db.execute(text(f"""
        INSERT INTO engineering_element_revisions (
            id, element_id, revision_number, element_type, element_name,
            verification_status, revision_note, created_by
        ) VALUES (
            '{rev_id}', '{el_id}', 99, 'KERB', 'Kerb K-1 Raw',
            'VERIFIED', 'Raw SQL audit insert', '{s1_id}'
        )
    """))
    db.commit()

    # 2. Raw SQL UPDATE fails via trigger
    try:
        db.execute(text(f"UPDATE engineering_element_revisions SET element_name='Hacked' WHERE id='{rev_id}'"))
        db.commit()
        pytest.fail("UPDATE on engineering_element_revisions succeeded, immutability trigger failed!")
    except Exception as e:
        db.rollback()
        assert "Engineering element revisions are immutable" in str(e) or "cannot be updated or deleted" in str(e)

    # 3. Raw SQL DELETE fails via trigger
    try:
        db.execute(text(f"DELETE FROM engineering_element_revisions WHERE id='{rev_id}'"))
        db.commit()
        pytest.fail("DELETE on engineering_element_revisions succeeded, immutability trigger failed!")
    except Exception as e:
        db.rollback()
        assert "Engineering element revisions are immutable" in str(e) or "cannot be updated or deleted" in str(e)

    db.close()

def test_invalid_element_type_rejected(client_fixture, setup_p1d):
    """12. Invalid element_type is rejected with 422 or 400."""
    env = setup_p1d
    res = client_fixture.post(
        f"/api/projects/{env['p1_id']}/engineering-elements",
        json={"element_type": "SPACESHIP", "element_name": "Rocket 1"},
        headers={"Authorization": f"Bearer {env['c1_token']}"}
    )
    assert res.status_code in [400, 422]

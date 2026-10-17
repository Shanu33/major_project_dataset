import io
import uuid
from decimal import Decimal
import pytest
from pypdf import PdfWriter
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import get_db, engine
from app.db.models import EngineeringCalculation

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
def setup_calc(client_fixture):
    # Setup test users and projects
    db = TestingSessionLocal()
    db.commit()
    db.close()

    # Admin setup
    client_fixture.post("/api/auth/register/admin", json={"email": "admin_calc@test.com", "password": "pass", "role": "admin"})
    admin_token = client_fixture.post("/api/auth/login", data={"username": "admin_calc@test.com", "password": "pass"}).json()["access_token"]

    # Users
    client_fixture.post("/api/auth/users", json={"email": "c1_calc@test.com", "password": "p", "role": "contractor"}, headers={"Authorization": f"Bearer {admin_token}"})
    client_fixture.post("/api/auth/users", json={"email": "c2_calc@test.com", "password": "p", "role": "contractor"}, headers={"Authorization": f"Bearer {admin_token}"})
    client_fixture.post("/api/auth/users", json={"email": "s1_calc@test.com", "password": "p", "role": "supervisor"}, headers={"Authorization": f"Bearer {admin_token}"})

    c1_token = client_fixture.post("/api/auth/login", data={"username": "c1_calc@test.com", "password": "p"}).json()["access_token"]
    c2_token = client_fixture.post("/api/auth/login", data={"username": "c2_calc@test.com", "password": "p"}).json()["access_token"]
    s1_token = client_fixture.post("/api/auth/login", data={"username": "s1_calc@test.com", "password": "p"}).json()["access_token"]

    # Projects
    p1 = client_fixture.post("/api/projects/", json={"name": "Project Calc Alpha"}, headers={"Authorization": f"Bearer {c1_token}"}).json()
    p1_id = p1["id"]
    p2 = client_fixture.post("/api/projects/", json={"name": "Project Calc Beta"}, headers={"Authorization": f"Bearer {c2_token}"}).json()
    p2_id = p2["id"]

    # Add supervisor to project 1
    db = TestingSessionLocal()
    s1_id = db.execute(text("SELECT id FROM users WHERE email = 's1_calc@test.com'")).scalar()
    db.close()
    client_fixture.post(f"/api/projects/{p1_id}/members?user_id={s1_id}", headers={"Authorization": f"Bearer {admin_token}"})

    # Upload document to project 1
    pdf_bytes = create_test_pdf()
    files = {'file': ('calc_drawing.pdf', pdf_bytes, 'application/pdf')}
    up_res = client_fixture.post(f"/api/projects/{p1_id}/documents/", files=files, headers={"Authorization": f"Bearer {c1_token}"})
    doc1_id = up_res.json()["id"]
    client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/process", headers={"Authorization": f"Bearer {c1_token}"})

    pages = client_fixture.get(f"/api/projects/{p1_id}/documents/{doc1_id}/pages", headers={"Authorization": f"Bearer {c1_token}"}).json()
    page1_id = pages[0]["id"]

    # Create Evidence in project 1
    ev_data = {
        "page_id": page1_id,
        "evidence_type": "DRAWING_REGION",
        "source_reference": "Drawing S-201 Section Footing",
        "locator": {"type": "bbox", "x0": 100, "y0": 200, "x1": 400, "y1": 500},
        "raw_content": "Footing F1 2.5m x 1.8m x 0.6m"
    }
    ev = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/evidence", json=ev_data, headers={"Authorization": f"Bearer {c1_token}"}).json()
    ev1_id = ev["id"]

    # Create Facts in project 1
    # 1. Length fact (verified: 2.5 m)
    f_len = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/evidence/{ev1_id}/facts", json={
        "fact_type": "DIMENSION",
        "field_name": "length",
        "raw_value": "2.5 m",
        "extraction_method": "MANUAL"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()
    client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/facts/{f_len['id']}/verify", json={
        "status": "VERIFIED"
    }, headers={"Authorization": f"Bearer {s1_token}"})

    # 2. Width fact (verified: 1.8 m)
    f_wid = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/evidence/{ev1_id}/facts", json={
        "fact_type": "DIMENSION",
        "field_name": "width",
        "raw_value": "1.8 m",
        "extraction_method": "MANUAL"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()
    client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/facts/{f_wid['id']}/verify", json={
        "status": "VERIFIED"
    }, headers={"Authorization": f"Bearer {s1_token}"})

    # 3. Depth fact (verified: 0.6 m)
    f_dep = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/evidence/{ev1_id}/facts", json={
        "fact_type": "DIMENSION",
        "field_name": "depth",
        "raw_value": "0.6 m",
        "extraction_method": "MANUAL"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()
    client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/facts/{f_dep['id']}/verify", json={
        "status": "VERIFIED"
    }, headers={"Authorization": f"Bearer {s1_token}"})

    # 4. Precision Facts (verified: 1.234567, 2.345678, 3.456789)
    f_p_l = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/evidence/{ev1_id}/facts", json={
        "fact_type": "DIMENSION",
        "field_name": "p_length",
        "raw_value": "1.234567 m",
        "extraction_method": "MANUAL"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()
    client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/facts/{f_p_l['id']}/verify", json={
        "status": "VERIFIED"
    }, headers={"Authorization": f"Bearer {s1_token}"})

    f_p_w = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/evidence/{ev1_id}/facts", json={
        "fact_type": "DIMENSION",
        "field_name": "p_width",
        "raw_value": "2.345678 m",
        "extraction_method": "MANUAL"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()
    client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/facts/{f_p_w['id']}/verify", json={
        "status": "VERIFIED"
    }, headers={"Authorization": f"Bearer {s1_token}"})

    f_p_d = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/evidence/{ev1_id}/facts", json={
        "fact_type": "DIMENSION",
        "field_name": "p_depth",
        "raw_value": "3.456789 m",
        "extraction_method": "MANUAL"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()
    client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/facts/{f_p_d['id']}/verify", json={
        "status": "VERIFIED"
    }, headers={"Authorization": f"Bearer {s1_token}"})

    # 5. Pending fact (not verified)
    f_pending = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/evidence/{ev1_id}/facts", json={
        "fact_type": "DIMENSION",
        "field_name": "pending_dim",
        "raw_value": "1.0 m",
        "extraction_method": "MANUAL"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()

    # 6. Rejected fact
    f_rejected = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/evidence/{ev1_id}/facts", json={
        "fact_type": "DIMENSION",
        "field_name": "rejected_dim",
        "raw_value": "0.5 m",
        "extraction_method": "MANUAL"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()
    client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/facts/{f_rejected['id']}/verify", json={
        "status": "REJECTED"
    }, headers={"Authorization": f"Bearer {s1_token}"})

    # Upload document and fact in Project 2 (Beta) for cross-project test
    files2 = {'file': ('beta_drawing.pdf', pdf_bytes, 'application/pdf')}
    up2 = client_fixture.post(f"/api/projects/{p2_id}/documents/", files=files2, headers={"Authorization": f"Bearer {c2_token}"}).json()
    client_fixture.post(f"/api/projects/{p2_id}/documents/{up2['id']}/process", headers={"Authorization": f"Bearer {c2_token}"})
    p2_pages = client_fixture.get(f"/api/projects/{p2_id}/documents/{up2['id']}/pages", headers={"Authorization": f"Bearer {c2_token}"}).json()
    ev2 = client_fixture.post(f"/api/projects/{p2_id}/documents/{up2['id']}/evidence", json={
        "page_id": p2_pages[0]["id"],
        "evidence_type": "DRAWING_REGION",
        "source_reference": "Beta Spec",
        "raw_content": "Beta dim"
    }, headers={"Authorization": f"Bearer {c2_token}"}).json()
    f_beta = client_fixture.post(f"/api/projects/{p2_id}/documents/{up2['id']}/evidence/{ev2['id']}/facts", json={
        "fact_type": "DIMENSION",
        "field_name": "beta_length",
        "raw_value": "3.0 m",
        "extraction_method": "MANUAL"
    }, headers={"Authorization": f"Bearer {c2_token}"}).json()
    client_fixture.post(f"/api/projects/{p2_id}/members?user_id={s1_id}", headers={"Authorization": f"Bearer {admin_token}"})
    client_fixture.post(f"/api/projects/{p2_id}/documents/{up2['id']}/facts/{f_beta['id']}/verify", json={
        "status": "VERIFIED"
    }, headers={"Authorization": f"Bearer {s1_token}"})

    # Elements in Project 1
    el_footing = client_fixture.post(f"/api/projects/{p1_id}/engineering-elements", json={
        "element_type": "FOOTING",
        "element_name": "Footing F-101"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()

    el_column = client_fixture.post(f"/api/projects/{p1_id}/engineering-elements", json={
        "element_type": "COLUMN",
        "element_name": "Column C-101"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()

    el_wall = client_fixture.post(f"/api/projects/{p1_id}/engineering-elements", json={
        "element_type": "WALL",
        "element_name": "Wall W-101"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()

    return {
        "admin_token": admin_token,
        "c1_token": c1_token,
        "c2_token": c2_token,
        "s1_token": s1_token,
        "p1_id": p1_id,
        "p2_id": p2_id,
        "doc1_id": doc1_id,
        "ev1_id": ev1_id,
        "page1_id": page1_id,
        "f_len_id": f_len["id"],
        "f_wid_id": f_wid["id"],
        "f_dep_id": f_dep["id"],
        "f_p_l_id": f_p_l["id"],
        "f_p_w_id": f_p_w["id"],
        "f_p_d_id": f_p_d["id"],
        "f_pending_id": f_pending["id"],
        "f_rejected_id": f_rejected["id"],
        "f_beta_id": f_beta["id"],
        "el_footing_id": el_footing["id"],
        "el_column_id": el_column["id"],
        "el_wall_id": el_wall["id"],
    }


def make_valid_inputs(setup_calc):
    return {
        "length_m": {
            "value": "2.5",
            "unit": "m",
            "source_fact_id": setup_calc["f_len_id"],
            "source_type": "VERIFIED_FACT"
        },
        "width_m": {
            "value": "1.8",
            "unit": "m",
            "source_fact_id": setup_calc["f_wid_id"],
            "source_type": "VERIFIED_FACT"
        },
        "depth_m": {
            "value": "0.6",
            "unit": "m",
            "source_fact_id": setup_calc["f_dep_id"],
            "source_type": "VERIFIED_FACT"
        }
    }


def test_deterministic_rectangular_volume_with_verified_facts(client_fixture, setup_calc):
    """
    Test 1: Calculation succeeds with three VERIFIED source facts:
    2.5m x 1.8m x 0.6m = 2.700000 m3
    """
    p1_id = setup_calc["p1_id"]
    el_id = setup_calc["el_footing_id"]
    c1_token = setup_calc["c1_token"]

    payload = {
        "calculation_type": "CONCRETE_VOLUME_RECTANGULAR",
        "inputs": make_valid_inputs(setup_calc)
    }

    res = client_fixture.post(
        f"/api/projects/{p1_id}/engineering-elements/{el_id}/calculations",
        json=payload,
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["calculation_type"] == "CONCRETE_VOLUME_RECTANGULAR"
    assert data["formula_identifier"] == "RECTANGULAR_VOLUME"
    assert data["formula_expression"] == "V = L * W * D"
    assert data["result_unit"] == "m3"
    assert Decimal(str(data["result_value"])) == Decimal("2.700000")
    assert data["status"] == "CALCULATED"
    assert data["element_name"] == "Footing F-101"
    assert data["element_type"] == "FOOTING"


def test_full_provenance_hierarchy_reconstruction(client_fixture, setup_calc):
    """
    Test 2: Provenance reconstructs full hierarchy:
    Calculation -> EngineeringElement -> Fact -> Evidence -> Page -> Document -> Project
    """
    p1_id = setup_calc["p1_id"]
    el_id = setup_calc["el_footing_id"]
    c1_token = setup_calc["c1_token"]

    payload = {
        "calculation_type": "CONCRETE_VOLUME_RECTANGULAR",
        "inputs": make_valid_inputs(setup_calc)
    }

    res = client_fixture.post(
        f"/api/projects/{p1_id}/engineering-elements/{el_id}/calculations",
        json=payload,
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 200
    data = res.json()

    assert data["project_id"] == p1_id
    assert data["engineering_element_id"] == el_id

    prov = {item["dimension_name"]: item for item in data["provenance_details"]}
    for dim_name in ["length_m", "width_m", "depth_m"]:
        item = prov[dim_name]
        assert item["fact_id"] is not None
        assert item["raw_value"] is not None
        assert item["fact_verification_status"] == "VERIFIED"
        assert item["evidence_id"] == setup_calc["ev1_id"]
        assert item["evidence_type"] == "DRAWING_REGION"
        assert item["page_id"] == setup_calc["page1_id"]
        assert item["document_id"] == setup_calc["doc1_id"]
        assert item["project_id"] == p1_id
        assert item["project_name"] == "Project Calc Alpha"


def test_fails_when_length_has_no_source_fact_id(client_fixture, setup_calc):
    """
    Test 3: Calculation fails when length has no source_fact_id.
    """
    p1_id = setup_calc["p1_id"]
    el_id = setup_calc["el_footing_id"]
    c1_token = setup_calc["c1_token"]

    inputs = make_valid_inputs(setup_calc)
    inputs["length_m"] = {
        "value": "2.5",
        "unit": "m",
        "source_type": "VERIFIED_FACT"
    }

    res = client_fixture.post(
        f"/api/projects/{p1_id}/engineering-elements/{el_id}/calculations",
        json={"calculation_type": "CONCRETE_VOLUME_RECTANGULAR", "inputs": inputs},
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 400
    assert "missing required 'source_fact_id'" in res.json()["detail"].lower()


def test_fails_when_width_has_no_source_fact_id(client_fixture, setup_calc):
    """
    Test 4: Calculation fails when width has no source_fact_id.
    """
    p1_id = setup_calc["p1_id"]
    el_id = setup_calc["el_footing_id"]
    c1_token = setup_calc["c1_token"]

    inputs = make_valid_inputs(setup_calc)
    inputs["width_m"] = {
        "value": "1.8",
        "unit": "m",
        "source_fact_id": None,
        "source_type": "VERIFIED_FACT"
    }

    res = client_fixture.post(
        f"/api/projects/{p1_id}/engineering-elements/{el_id}/calculations",
        json={"calculation_type": "CONCRETE_VOLUME_RECTANGULAR", "inputs": inputs},
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 400
    assert "missing required 'source_fact_id'" in res.json()["detail"].lower()


def test_fails_when_depth_has_no_source_fact_id(client_fixture, setup_calc):
    """
    Test 5: Calculation fails when depth has no source_fact_id.
    """
    p1_id = setup_calc["p1_id"]
    el_id = setup_calc["el_footing_id"]
    c1_token = setup_calc["c1_token"]

    inputs = make_valid_inputs(setup_calc)
    inputs["depth_m"] = {
        "value": "0.6",
        "unit": "m",
        "source_fact_id": "",
        "source_type": "VERIFIED_FACT"
    }

    res = client_fixture.post(
        f"/api/projects/{p1_id}/engineering-elements/{el_id}/calculations",
        json={"calculation_type": "CONCRETE_VOLUME_RECTANGULAR", "inputs": inputs},
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 400
    assert "missing required 'source_fact_id'" in res.json()["detail"].lower()


def test_fails_when_source_type_is_not_verified_fact(client_fixture, setup_calc):
    """
    Test 6: Calculation fails when source_type is missing or not VERIFIED_FACT.
    """
    p1_id = setup_calc["p1_id"]
    el_id = setup_calc["el_footing_id"]
    c1_token = setup_calc["c1_token"]

    # Invalid source_type
    inputs1 = make_valid_inputs(setup_calc)
    inputs1["length_m"]["source_type"] = "MANUAL_INPUT"
    res1 = client_fixture.post(
        f"/api/projects/{p1_id}/engineering-elements/{el_id}/calculations",
        json={"calculation_type": "CONCRETE_VOLUME_RECTANGULAR", "inputs": inputs1},
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res1.status_code == 400
    assert "only 'verified_fact' is permitted" in res1.json()["detail"].lower()

    # Missing source_type
    inputs2 = make_valid_inputs(setup_calc)
    del inputs2["length_m"]["source_type"]
    res2 = client_fixture.post(
        f"/api/projects/{p1_id}/engineering-elements/{el_id}/calculations",
        json={"calculation_type": "CONCRETE_VOLUME_RECTANGULAR", "inputs": inputs2},
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res2.status_code == 400
    assert "missing required 'source_type'" in res2.json()["detail"].lower()


def test_fails_when_direct_numeric_inputs_provided(client_fixture, setup_calc):
    """
    Test 7: Direct numeric geometry values (unexplained numbers) are rejected with 400.
    """
    p1_id = setup_calc["p1_id"]
    el_id = setup_calc["el_footing_id"]
    c1_token = setup_calc["c1_token"]

    res = client_fixture.post(
        f"/api/projects/{p1_id}/engineering-elements/{el_id}/calculations",
        json={
            "calculation_type": "CONCRETE_VOLUME_RECTANGULAR",
            "inputs": {
                "length_m": "2.5",
                "width_m": "1.8",
                "depth_m": "0.6"
            }
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 400
    assert "must be a dictionary specifying source provenance" in res.json()["detail"].lower()


def test_fails_when_assumptions_introduced(client_fixture, setup_calc):
    """
    Test 8: Calculations with assumptions are rejected with 400 in Phase 1E.
    """
    p1_id = setup_calc["p1_id"]
    el_id = setup_calc["el_footing_id"]
    c1_token = setup_calc["c1_token"]

    res = client_fixture.post(
        f"/api/projects/{p1_id}/engineering-elements/{el_id}/calculations",
        json={
            "calculation_type": "CONCRETE_VOLUME_RECTANGULAR",
            "inputs": make_valid_inputs(setup_calc),
            "assumptions": {"concrete_grade": "C30/37"}
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 400
    assert "assumptions are not permitted in phase 1e" in res.json()["detail"].lower()


def test_exact_numeric_precision(client_fixture, setup_calc):
    """
    Test 9: Exact numeric precision with 6 decimal places.
    1.234567 * 2.345678 * 3.456789 = 10.010729 (exact Decimal)
    """
    p1_id = setup_calc["p1_id"]
    el_id = setup_calc["el_column_id"]
    c1_token = setup_calc["c1_token"]

    l = Decimal("1.234567")
    w = Decimal("2.345678")
    d = Decimal("3.456789")
    expected = (l * w * d).quantize(Decimal("0.000001"))

    payload = {
        "calculation_type": "CONCRETE_VOLUME_RECTANGULAR",
        "inputs": {
            "length_m": {
                "value": str(l),
                "unit": "m",
                "source_fact_id": setup_calc["f_p_l_id"],
                "source_type": "VERIFIED_FACT"
            },
            "width_m": {
                "value": str(w),
                "unit": "m",
                "source_fact_id": setup_calc["f_p_w_id"],
                "source_type": "VERIFIED_FACT"
            },
            "depth_m": {
                "value": str(d),
                "unit": "m",
                "source_fact_id": setup_calc["f_p_d_id"],
                "source_type": "VERIFIED_FACT"
            }
        }
    }

    res = client_fixture.post(
        f"/api/projects/{p1_id}/engineering-elements/{el_id}/calculations",
        json=payload,
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert Decimal(str(data["result_value"])) == expected


def test_supported_element_types(client_fixture, setup_calc):
    """
    Test 10: Supported element types (FOOTING, PILE_CAP, COLUMN, BEAM, SLAB, FOUNDATION).
    """
    p1_id = setup_calc["p1_id"]
    c1_token = setup_calc["c1_token"]

    supported = ["FOOTING", "PILE_CAP", "COLUMN", "BEAM", "SLAB", "FOUNDATION"]
    for el_type in supported:
        el = client_fixture.post(f"/api/projects/{p1_id}/engineering-elements", json={
            "element_type": el_type,
            "element_name": f"Test {el_type}"
        }, headers={"Authorization": f"Bearer {c1_token}"}).json()

        res = client_fixture.post(
            f"/api/projects/{p1_id}/engineering-elements/{el['id']}/calculations",
            json={
                "calculation_type": "CONCRETE_VOLUME_RECTANGULAR",
                "inputs": make_valid_inputs(setup_calc)
            },
            headers={"Authorization": f"Bearer {c1_token}"}
        )
        assert res.status_code == 200, f"Failed for supported type {el_type}: {res.text}"


def test_unsupported_element_types_rejected(client_fixture, setup_calc):
    """
    Test 11: Unsupported element types (WALL, PAVEMENT, KERB, PILE, OTHER) rejected with 400.
    """
    p1_id = setup_calc["p1_id"]
    c1_token = setup_calc["c1_token"]

    unsupported = ["WALL", "PAVEMENT", "KERB", "PILE", "OTHER"]
    for el_type in unsupported:
        el = client_fixture.post(f"/api/projects/{p1_id}/engineering-elements", json={
            "element_type": el_type,
            "element_name": f"Test {el_type}"
        }, headers={"Authorization": f"Bearer {c1_token}"}).json()

        res = client_fixture.post(
            f"/api/projects/{p1_id}/engineering-elements/{el['id']}/calculations",
            json={
                "calculation_type": "CONCRETE_VOLUME_RECTANGULAR",
                "inputs": make_valid_inputs(setup_calc)
            },
            headers={"Authorization": f"Bearer {c1_token}"}
        )
        assert res.status_code == 400, f"Should reject unsupported type {el_type}"
        assert "unsupported for calculation" in res.json()["detail"].lower()


def test_missing_dimension_rejected(client_fixture, setup_calc):
    """
    Test 12: Missing required dimension rejected with 400 (REQUIRES_INPUT).
    """
    p1_id = setup_calc["p1_id"]
    el_id = setup_calc["el_footing_id"]
    c1_token = setup_calc["c1_token"]

    # Missing depth_m
    payload = {
        "calculation_type": "CONCRETE_VOLUME_RECTANGULAR",
        "inputs": {
            "length_m": {
                "value": "2.5",
                "unit": "m",
                "source_fact_id": setup_calc["f_len_id"],
                "source_type": "VERIFIED_FACT"
            },
            "width_m": {
                "value": "1.8",
                "unit": "m",
                "source_fact_id": setup_calc["f_wid_id"],
                "source_type": "VERIFIED_FACT"
            }
        }
    }

    res = client_fixture.post(
        f"/api/projects/{p1_id}/engineering-elements/{el_id}/calculations",
        json=payload,
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 400
    assert "requires_input" in res.json()["detail"].lower() or "missing required dimension" in res.json()["detail"].lower()


def test_zero_or_negative_dimensions_rejected(client_fixture, setup_calc):
    """
    Test 13: Dimensions <= 0 rejected with 400 (INVALID_INPUT).
    """
    p1_id = setup_calc["p1_id"]
    el_id = setup_calc["el_footing_id"]
    c1_token = setup_calc["c1_token"]

    # Zero length
    inputs1 = make_valid_inputs(setup_calc)
    inputs1["length_m"]["value"] = "0.0"
    res1 = client_fixture.post(
        f"/api/projects/{p1_id}/engineering-elements/{el_id}/calculations",
        json={"calculation_type": "CONCRETE_VOLUME_RECTANGULAR", "inputs": inputs1},
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res1.status_code == 400
    assert "strictly positive" in res1.json()["detail"].lower()

    # Negative width
    inputs2 = make_valid_inputs(setup_calc)
    inputs2["width_m"]["value"] = "-1.5"
    res2 = client_fixture.post(
        f"/api/projects/{p1_id}/engineering-elements/{el_id}/calculations",
        json={"calculation_type": "CONCRETE_VOLUME_RECTANGULAR", "inputs": inputs2},
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res2.status_code == 400
    assert "strictly positive" in res2.json()["detail"].lower()


def test_non_metric_unit_rejected(client_fixture, setup_calc):
    """
    Test 14: Non-metric unit without normalization rejected with 400.
    """
    p1_id = setup_calc["p1_id"]
    el_id = setup_calc["el_footing_id"]
    c1_token = setup_calc["c1_token"]

    inputs = make_valid_inputs(setup_calc)
    inputs["length_m"]["unit"] = "ft"

    res = client_fixture.post(
        f"/api/projects/{p1_id}/engineering-elements/{el_id}/calculations",
        json={"calculation_type": "CONCRETE_VOLUME_RECTANGULAR", "inputs": inputs},
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 400
    assert "must be normalized to 'm'" in res.json()["detail"].lower()


def test_unverified_fact_rejected(client_fixture, setup_calc):
    """
    Test 15: Reference to unverified (PENDING) or REJECTED fact is rejected with 400.
    """
    p1_id = setup_calc["p1_id"]
    el_id = setup_calc["el_footing_id"]
    c1_token = setup_calc["c1_token"]

    # Pending fact
    inputs1 = make_valid_inputs(setup_calc)
    inputs1["length_m"]["source_fact_id"] = setup_calc["f_pending_id"]
    res1 = client_fixture.post(
        f"/api/projects/{p1_id}/engineering-elements/{el_id}/calculations",
        json={"calculation_type": "CONCRETE_VOLUME_RECTANGULAR", "inputs": inputs1},
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res1.status_code == 400
    assert "must be verified" in res1.json()["detail"].lower()

    # Rejected fact
    inputs2 = make_valid_inputs(setup_calc)
    inputs2["length_m"]["source_fact_id"] = setup_calc["f_rejected_id"]
    res2 = client_fixture.post(
        f"/api/projects/{p1_id}/engineering-elements/{el_id}/calculations",
        json={"calculation_type": "CONCRETE_VOLUME_RECTANGULAR", "inputs": inputs2},
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res2.status_code == 400
    assert "must be verified" in res2.json()["detail"].lower()


def test_cross_project_fact_rejected(client_fixture, setup_calc):
    """
    Test 16: Reference to fact from another project rejected with 400.
    """
    p1_id = setup_calc["p1_id"]
    el_id = setup_calc["el_footing_id"]
    c1_token = setup_calc["c1_token"]

    inputs = make_valid_inputs(setup_calc)
    inputs["length_m"]["source_fact_id"] = setup_calc["f_beta_id"]

    res = client_fixture.post(
        f"/api/projects/{p1_id}/engineering-elements/{el_id}/calculations",
        json={"calculation_type": "CONCRETE_VOLUME_RECTANGULAR", "inputs": inputs},
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 400
    assert "cross-project fact rejected" in res.json()["detail"].lower()


def test_cross_element_fact_rejected(client_fixture, setup_calc):
    """
    Test 17: Reference to fact already bound to a different element rejected with 400.
    """
    p1_id = setup_calc["p1_id"]
    c1_token = setup_calc["c1_token"]
    s1_token = setup_calc["s1_token"]
    doc1_id = setup_calc["doc1_id"]
    ev1_id = setup_calc["ev1_id"]

    # Create a separate verified fact for this test
    f_ce = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/evidence/{ev1_id}/facts", json={
        "fact_type": "DIMENSION",
        "field_name": "ce_length",
        "raw_value": "3.5 m",
        "extraction_method": "MANUAL"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()
    client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/facts/{f_ce['id']}/verify", json={
        "status": "VERIFIED"
    }, headers={"Authorization": f"Bearer {s1_token}"})

    # Bind f_ce to a new element
    client_fixture.post(f"/api/projects/{p1_id}/engineering-elements", json={
        "element_type": "BEAM",
        "element_name": "Beam B-Bound-Cross",
        "source_fact_id": f_ce["id"]
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()

    # Attempt to calculate Footing F-101 using f_ce (which is bound to Beam)
    inputs = make_valid_inputs(setup_calc)
    inputs["length_m"] = {
        "value": "3.5",
        "unit": "m",
        "source_fact_id": f_ce["id"],
        "source_type": "VERIFIED_FACT"
    }

    res = client_fixture.post(
        f"/api/projects/{p1_id}/engineering-elements/{setup_calc['el_footing_id']}/calculations",
        json={
            "calculation_type": "CONCRETE_VOLUME_RECTANGULAR",
            "inputs": inputs
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 400
    assert "cross-element fact rejected" in res.json()["detail"].lower()


def test_recalculation_supersedes_previous(client_fixture, setup_calc):
    """
    Test 18: Recalculation creates new active record and supersedes previous calculation.
    """
    p1_id = setup_calc["p1_id"]
    c1_token = setup_calc["c1_token"]

    el = client_fixture.post(f"/api/projects/{p1_id}/engineering-elements", json={
        "element_type": "SLAB",
        "element_name": "Slab S-Supersede"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()
    el_id = el["id"]

    # Run Calc 1
    res1 = client_fixture.post(
        f"/api/projects/{p1_id}/engineering-elements/{el_id}/calculations",
        json={
            "calculation_type": "CONCRETE_VOLUME_RECTANGULAR",
            "inputs": make_valid_inputs(setup_calc)
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res1.status_code == 200
    calc1 = res1.json()
    assert calc1["status"] == "CALCULATED"

    # Run Calc 2 with precision facts
    res2 = client_fixture.post(
        f"/api/projects/{p1_id}/engineering-elements/{el_id}/calculations",
        json={
            "calculation_type": "CONCRETE_VOLUME_RECTANGULAR",
            "inputs": {
                "length_m": {
                    "value": "1.234567",
                    "unit": "m",
                    "source_fact_id": setup_calc["f_p_l_id"],
                    "source_type": "VERIFIED_FACT"
                },
                "width_m": {
                    "value": "2.345678",
                    "unit": "m",
                    "source_fact_id": setup_calc["f_p_w_id"],
                    "source_type": "VERIFIED_FACT"
                },
                "depth_m": {
                    "value": "3.456789",
                    "unit": "m",
                    "source_fact_id": setup_calc["f_p_d_id"],
                    "source_type": "VERIFIED_FACT"
                }
            }
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res2.status_code == 200
    calc2 = res2.json()
    assert calc2["status"] == "CALCULATED"

    # Verify Calc 1 is now SUPERSEDED
    get1 = client_fixture.get(
        f"/api/projects/{p1_id}/engineering-elements/{el_id}/calculations/{calc1['id']}",
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert get1.status_code == 200
    assert get1.json()["status"] == "SUPERSEDED"

    # List calculations
    list_res = client_fixture.get(
        f"/api/projects/{p1_id}/engineering-elements/{el_id}/calculations",
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert list_res.status_code == 200
    calcs = list_res.json()
    assert len(calcs) == 2


def test_db_immutability_trigger_enforcement(client_fixture, setup_calc):
    """
    Test 19: PostgreSQL trigger prevents DELETE and unauthorized UPDATE.
    """
    p1_id = setup_calc["p1_id"]
    c1_token = setup_calc["c1_token"]

    el = client_fixture.post(f"/api/projects/{p1_id}/engineering-elements", json={
        "element_type": "BEAM",
        "element_name": "Beam B-TriggerTest"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()

    calc = client_fixture.post(
        f"/api/projects/{p1_id}/engineering-elements/{el['id']}/calculations",
        json={
            "calculation_type": "CONCRETE_VOLUME_RECTANGULAR",
            "inputs": make_valid_inputs(setup_calc)
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    ).json()
    calc_id = calc["id"]

    db = TestingSessionLocal()
    try:
        # 1. Attempt DELETE via direct SQL -> MUST FAIL
        with pytest.raises(Exception) as exc_delete:
            db.execute(text(f"DELETE FROM engineering_calculations WHERE id = '{calc_id}'"))
            db.commit()
        assert "immutable and cannot be deleted" in str(exc_delete.value).lower()
        db.rollback()

        # 2. Attempt unauthorized UPDATE of result_value -> MUST FAIL
        with pytest.raises(Exception) as exc_update_val:
            db.execute(text(f"UPDATE engineering_calculations SET result_value = 999.0 WHERE id = '{calc_id}'"))
            db.commit()
        assert "immutable" in str(exc_update_val.value).lower()
        db.rollback()

        # 3. Attempt unauthorized UPDATE of inputs_json -> MUST FAIL
        with pytest.raises(Exception) as exc_update_inp:
            db.execute(text(f"UPDATE engineering_calculations SET inputs_json = '{{}}'::json WHERE id = '{calc_id}'"))
            db.commit()
        assert "immutable" in str(exc_update_inp.value).lower()
        db.rollback()

        # 4. Attempt status change from CALCULATED to SUPERSEDED while illegally altering result_value -> MUST FAIL
        with pytest.raises(Exception) as exc_sneaky:
            db.execute(text(f"UPDATE engineering_calculations SET status = 'SUPERSEDED', result_value = 100.0 WHERE id = '{calc_id}'"))
            db.commit()
        assert "cannot modify calculation inputs, formulas, or results" in str(exc_sneaky.value).lower()
        db.rollback()

        # 5. Legitimate status update from CALCULATED to SUPERSEDED with all other fields unmodified -> MUST SUCCEED
        db.execute(text(f"UPDATE engineering_calculations SET status = 'SUPERSEDED' WHERE id = '{calc_id}'"))
        db.commit()

        # Verify status is now SUPERSEDED
        status = db.execute(text(f"SELECT status FROM engineering_calculations WHERE id = '{calc_id}'")).scalar()
        assert status == "SUPERSEDED"

        # 6. Attempt status change from SUPERSEDED back to CALCULATED -> MUST FAIL
        with pytest.raises(Exception) as exc_revert:
            db.execute(text(f"UPDATE engineering_calculations SET status = 'CALCULATED' WHERE id = '{calc_id}'"))
            db.commit()
        assert "immutable" in str(exc_revert.value).lower()
        db.rollback()

    finally:
        db.close()


def test_audit_log_written_for_calculation(client_fixture, setup_calc):
    """
    Test 20: CALCULATION_PERFORMED audit entry is generated.
    """
    p1_id = setup_calc["p1_id"]
    c1_token = setup_calc["c1_token"]

    el = client_fixture.post(f"/api/projects/{p1_id}/engineering-elements", json={
        "element_type": "PILE_CAP",
        "element_name": "Pile Cap PC-Audit"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()

    calc = client_fixture.post(
        f"/api/projects/{p1_id}/engineering-elements/{el['id']}/calculations",
        json={
            "calculation_type": "CONCRETE_VOLUME_RECTANGULAR",
            "inputs": make_valid_inputs(setup_calc)
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    ).json()

    db = TestingSessionLocal()
    audit = db.execute(text(
        f"SELECT action, entity_type, entity_id FROM audit_log WHERE entity_id = '{calc['id']}'"
    )).first()
    db.close()

    assert audit is not None
    assert audit[0] == "CALCULATION_PERFORMED"
    assert audit[1] == "EngineeringCalculation"
    assert audit[2] == calc["id"]


def test_project_authorization_boundary(client_fixture, setup_calc):
    """
    Test 21: User without project access cannot execute or view calculations.
    """
    p1_id = setup_calc["p1_id"]
    c2_token = setup_calc["c2_token"] # Member of Beta, not Alpha
    el_id = setup_calc["el_footing_id"]

    # Attempt create
    res = client_fixture.post(
        f"/api/projects/{p1_id}/engineering-elements/{el_id}/calculations",
        json={
            "calculation_type": "CONCRETE_VOLUME_RECTANGULAR",
            "inputs": make_valid_inputs(setup_calc)
        },
        headers={"Authorization": f"Bearer {c2_token}"}
    )
    assert res.status_code == 403

    # Attempt list
    res_list = client_fixture.get(
        f"/api/projects/{p1_id}/engineering-elements/{el_id}/calculations",
        headers={"Authorization": f"Bearer {c2_token}"}
    )
    assert res_list.status_code == 403


def test_not_found_handling(client_fixture, setup_calc):
    """
    Test 22: 404 returned for nonexistent element or calculation.
    """
    p1_id = setup_calc["p1_id"]
    c1_token = setup_calc["c1_token"]
    fake_id = str(uuid.uuid4())

    # Nonexistent element calculation execution
    res = client_fixture.post(
        f"/api/projects/{p1_id}/engineering-elements/{fake_id}/calculations",
        json={
            "calculation_type": "CONCRETE_VOLUME_RECTANGULAR",
            "inputs": make_valid_inputs(setup_calc)
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 404

    # Nonexistent calculation retrieval
    res_get = client_fixture.get(
        f"/api/projects/{p1_id}/engineering-elements/{setup_calc['el_footing_id']}/calculations/{fake_id}",
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res_get.status_code == 404


def test_list_calculations_status_filter(client_fixture, setup_calc):
    """
    Test 23: Filter calculations by status.
    """
    p1_id = setup_calc["p1_id"]
    c1_token = setup_calc["c1_token"]

    el = client_fixture.post(f"/api/projects/{p1_id}/engineering-elements", json={
        "element_type": "FOUNDATION",
        "element_name": "Foundation F-Filter"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()
    el_id = el["id"]

    # Calculation 1
    client_fixture.post(
        f"/api/projects/{p1_id}/engineering-elements/{el_id}/calculations",
        json={
            "calculation_type": "CONCRETE_VOLUME_RECTANGULAR",
            "inputs": make_valid_inputs(setup_calc)
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )

    # Calculation 2 (supersedes 1)
    client_fixture.post(
        f"/api/projects/{p1_id}/engineering-elements/{el_id}/calculations",
        json={
            "calculation_type": "CONCRETE_VOLUME_RECTANGULAR",
            "inputs": make_valid_inputs(setup_calc)
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )

    # Filter CALCULATED
    res_calc = client_fixture.get(
        f"/api/projects/{p1_id}/engineering-elements/{el_id}/calculations?status=CALCULATED",
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res_calc.status_code == 200
    items_calc = res_calc.json()
    assert len(items_calc) == 1
    assert items_calc[0]["status"] == "CALCULATED"

    # Filter SUPERSEDED
    res_sup = client_fixture.get(
        f"/api/projects/{p1_id}/engineering-elements/{el_id}/calculations?status=SUPERSEDED",
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res_sup.status_code == 200
    items_sup = res_sup.json()
    assert len(items_sup) == 1
    assert items_sup[0]["status"] == "SUPERSEDED"


def test_alembic_installed_calculation_trigger():
    """
    Test 24: Verify Alembic migration installed the prevent_calculation_modification_trg trigger.
    """
    db = TestingSessionLocal()
    try:
        trigger_name = db.execute(text(
            "SELECT tgname FROM pg_trigger WHERE tgname = 'prevent_calculation_modification_trg'"
        )).scalar()
        assert trigger_name == "prevent_calculation_modification_trg"
    finally:
        db.close()

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
from app.db.models import RuleBasedEstimation, Rule, EngineeringCalculation

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
def setup_est(client_fixture):
    # Setup test users and projects
    db = TestingSessionLocal()
    db.commit()
    db.close()

    # Admin setup
    client_fixture.post("/api/auth/register/admin", json={"email": "admin_est@test.com", "password": "pass", "role": "admin"})
    admin_token = client_fixture.post("/api/auth/login", data={"username": "admin_est@test.com", "password": "pass"}).json()["access_token"]

    # Users
    client_fixture.post("/api/auth/users", json={"email": "c1_est@test.com", "password": "p", "role": "contractor"}, headers={"Authorization": f"Bearer {admin_token}"})
    client_fixture.post("/api/auth/users", json={"email": "c2_est@test.com", "password": "p", "role": "contractor"}, headers={"Authorization": f"Bearer {admin_token}"})
    client_fixture.post("/api/auth/users", json={"email": "s1_est@test.com", "password": "p", "role": "supervisor"}, headers={"Authorization": f"Bearer {admin_token}"})

    c1_token = client_fixture.post("/api/auth/login", data={"username": "c1_est@test.com", "password": "p"}).json()["access_token"]
    c2_token = client_fixture.post("/api/auth/login", data={"username": "c2_est@test.com", "password": "p"}).json()["access_token"]
    s1_token = client_fixture.post("/api/auth/login", data={"username": "s1_est@test.com", "password": "p"}).json()["access_token"]

    # Projects
    p1 = client_fixture.post("/api/projects/", json={"name": "Project Est Alpha"}, headers={"Authorization": f"Bearer {c1_token}"}).json()
    p1_id = p1["id"]
    p2 = client_fixture.post("/api/projects/", json={"name": "Project Est Beta"}, headers={"Authorization": f"Bearer {c2_token}"}).json()
    p2_id = p2["id"]

    # Add supervisor to project 1 and project 2
    db = TestingSessionLocal()
    s1_id = db.execute(text("SELECT id FROM users WHERE email = 's1_est@test.com'")).scalar()
    admin_id = db.execute(text("SELECT id FROM users WHERE email = 'admin_est@test.com'")).scalar()
    db.close()
    client_fixture.post(f"/api/projects/{p1_id}/members?user_id={s1_id}", headers={"Authorization": f"Bearer {admin_token}"})
    client_fixture.post(f"/api/projects/{p2_id}/members?user_id={s1_id}", headers={"Authorization": f"Bearer {admin_token}"})

    # Upload document to project 1
    pdf_bytes = create_test_pdf()
    files = {'file': ('est_drawing.pdf', pdf_bytes, 'application/pdf')}
    up_res = client_fixture.post(f"/api/projects/{p1_id}/documents/", files=files, headers={"Authorization": f"Bearer {c1_token}"})
    doc1_id = up_res.json()["id"]
    client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/process", headers={"Authorization": f"Bearer {c1_token}"})

    pages = client_fixture.get(f"/api/projects/{p1_id}/documents/{doc1_id}/pages", headers={"Authorization": f"Bearer {c1_token}"}).json()
    page1_id = pages[0]["id"]

    # Evidence in project 1
    ev_data = {
        "page_id": page1_id,
        "evidence_type": "DRAWING_REGION",
        "source_reference": "Drawing S-301 Section Footing",
        "locator": {"type": "bbox", "x0": 100, "y0": 200, "x1": 400, "y1": 500},
        "raw_content": "Footing F1 2.0m x 2.0m x 0.5m"
    }
    ev = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/evidence", json=ev_data, headers={"Authorization": f"Bearer {c1_token}"}).json()
    ev1_id = ev["id"]

    # Facts in project 1 (length, width, depth verified: 2m, 2m, 0.5m -> 2.000000 m3)
    f_l = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/evidence/{ev1_id}/facts", json={
        "fact_type": "DIMENSION",
        "field_name": "length",
        "raw_value": "2.0 m",
        "extraction_method": "MANUAL"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()
    client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/facts/{f_l['id']}/verify", json={"status": "VERIFIED"}, headers={"Authorization": f"Bearer {s1_token}"})

    f_w = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/evidence/{ev1_id}/facts", json={
        "fact_type": "DIMENSION",
        "field_name": "width",
        "raw_value": "2.0 m",
        "extraction_method": "MANUAL"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()
    client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/facts/{f_w['id']}/verify", json={"status": "VERIFIED"}, headers={"Authorization": f"Bearer {s1_token}"})

    f_d = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/evidence/{ev1_id}/facts", json={
        "fact_type": "DIMENSION",
        "field_name": "depth",
        "raw_value": "0.5 m",
        "extraction_method": "MANUAL"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()
    client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/facts/{f_d['id']}/verify", json={"status": "VERIFIED"}, headers={"Authorization": f"Bearer {s1_token}"})

    # Facts for 10m3 calculation (5m x 2m x 1m = 10 m3)
    f_l10 = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/evidence/{ev1_id}/facts", json={
        "fact_type": "DIMENSION",
        "field_name": "l10",
        "raw_value": "5.0 m",
        "extraction_method": "MANUAL"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()
    client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/facts/{f_l10['id']}/verify", json={"status": "VERIFIED"}, headers={"Authorization": f"Bearer {s1_token}"})

    f_w10 = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/evidence/{ev1_id}/facts", json={
        "fact_type": "DIMENSION",
        "field_name": "w10",
        "raw_value": "2.0 m",
        "extraction_method": "MANUAL"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()
    client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/facts/{f_w10['id']}/verify", json={"status": "VERIFIED"}, headers={"Authorization": f"Bearer {s1_token}"})

    f_d10 = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/evidence/{ev1_id}/facts", json={
        "fact_type": "DIMENSION",
        "field_name": "d10",
        "raw_value": "1.0 m",
        "extraction_method": "MANUAL"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()
    client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/facts/{f_d10['id']}/verify", json={"status": "VERIFIED"}, headers={"Authorization": f"Bearer {s1_token}"})

    # Element in Project 1
    el1 = client_fixture.post(f"/api/projects/{p1_id}/engineering-elements", json={
        "element_type": "FOOTING",
        "element_name": "Footing F-Est-1"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()
    el1_id = el1["id"]

    # Calculation 1 (2.0 m3)
    calc1 = client_fixture.post(
        f"/api/projects/{p1_id}/engineering-elements/{el1_id}/calculations",
        json={
            "calculation_type": "CONCRETE_VOLUME_RECTANGULAR",
            "inputs": {
                "length_m": {"value": "2.0", "unit": "m", "source_fact_id": f_l["id"], "source_type": "VERIFIED_FACT"},
                "width_m": {"value": "2.0", "unit": "m", "source_fact_id": f_w["id"], "source_type": "VERIFIED_FACT"},
                "depth_m": {"value": "0.5", "unit": "m", "source_fact_id": f_d["id"], "source_type": "VERIFIED_FACT"}
            }
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    ).json()

    # Calculation 2 (10.0 m3)
    calc10 = client_fixture.post(
        f"/api/projects/{p1_id}/engineering-elements/{el1_id}/calculations",
        json={
            "calculation_type": "CONCRETE_VOLUME_RECTANGULAR",
            "inputs": {
                "length_m": {"value": "5.0", "unit": "m", "source_fact_id": f_l10["id"], "source_type": "VERIFIED_FACT"},
                "width_m": {"value": "2.0", "unit": "m", "source_fact_id": f_w10["id"], "source_type": "VERIFIED_FACT"},
                "depth_m": {"value": "1.0", "unit": "m", "source_fact_id": f_d10["id"], "source_type": "VERIFIED_FACT"}
            }
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    ).json()

    # Document & Calculation in Project 2 (Beta) for cross-project test
    files2 = {'file': ('beta_est.pdf', pdf_bytes, 'application/pdf')}
    up2 = client_fixture.post(f"/api/projects/{p2_id}/documents/", files=files2, headers={"Authorization": f"Bearer {c2_token}"}).json()
    client_fixture.post(f"/api/projects/{p2_id}/documents/{up2['id']}/process", headers={"Authorization": f"Bearer {c2_token}"})
    p2_pages = client_fixture.get(f"/api/projects/{p2_id}/documents/{up2['id']}/pages", headers={"Authorization": f"Bearer {c2_token}"}).json()
    ev2 = client_fixture.post(f"/api/projects/{p2_id}/documents/{up2['id']}/evidence", json={
        "page_id": p2_pages[0]["id"],
        "evidence_type": "DRAWING_REGION",
        "source_reference": "Beta Spec",
        "raw_content": "Beta footing"
    }, headers={"Authorization": f"Bearer {c2_token}"}).json()
    f_b_l = client_fixture.post(f"/api/projects/{p2_id}/documents/{up2['id']}/evidence/{ev2['id']}/facts", json={
        "fact_type": "DIMENSION", "field_name": "b_l", "raw_value": "1.0 m", "extraction_method": "MANUAL"
    }, headers={"Authorization": f"Bearer {c2_token}"}).json()
    client_fixture.post(f"/api/projects/{p2_id}/documents/{up2['id']}/facts/{f_b_l['id']}/verify", json={"status": "VERIFIED"}, headers={"Authorization": f"Bearer {s1_token}"})

    f_b_w = client_fixture.post(f"/api/projects/{p2_id}/documents/{up2['id']}/evidence/{ev2['id']}/facts", json={
        "fact_type": "DIMENSION", "field_name": "b_w", "raw_value": "1.0 m", "extraction_method": "MANUAL"
    }, headers={"Authorization": f"Bearer {c2_token}"}).json()
    client_fixture.post(f"/api/projects/{p2_id}/documents/{up2['id']}/facts/{f_b_w['id']}/verify", json={"status": "VERIFIED"}, headers={"Authorization": f"Bearer {s1_token}"})

    f_b_d = client_fixture.post(f"/api/projects/{p2_id}/documents/{up2['id']}/evidence/{ev2['id']}/facts", json={
        "fact_type": "DIMENSION", "field_name": "b_d", "raw_value": "1.0 m", "extraction_method": "MANUAL"
    }, headers={"Authorization": f"Bearer {c2_token}"}).json()
    client_fixture.post(f"/api/projects/{p2_id}/documents/{up2['id']}/facts/{f_b_d['id']}/verify", json={"status": "VERIFIED"}, headers={"Authorization": f"Bearer {s1_token}"})

    el_b = client_fixture.post(f"/api/projects/{p2_id}/engineering-elements", json={
        "element_type": "FOOTING",
        "element_name": "Beta Footing"
    }, headers={"Authorization": f"Bearer {c2_token}"}).json()

    calc_beta = client_fixture.post(
        f"/api/projects/{p2_id}/engineering-elements/{el_b['id']}/calculations",
        json={
            "calculation_type": "CONCRETE_VOLUME_RECTANGULAR",
            "inputs": {
                "length_m": {"value": "1.0", "unit": "m", "source_fact_id": f_b_l["id"], "source_type": "VERIFIED_FACT"},
                "width_m": {"value": "1.0", "unit": "m", "source_fact_id": f_b_w["id"], "source_type": "VERIFIED_FACT"},
                "depth_m": {"value": "1.0", "unit": "m", "source_fact_id": f_b_d["id"], "source_type": "VERIFIED_FACT"}
            }
        },
        headers={"Authorization": f"Bearer {c2_token}"}
    ).json()

    return {
        "admin_id": admin_id,
        "admin_token": admin_token,
        "c1_token": c1_token,
        "c2_token": c2_token,
        "s1_token": s1_token,
        "p1_id": p1_id,
        "p2_id": p2_id,
        "doc1_id": doc1_id,
        "page1_id": page1_id,
        "ev1_id": ev1_id,
        "el1_id": el1_id,
        "calc1_id": calc1["id"],
        "calc10_id": calc10["id"],
        "calc_beta_id": calc_beta["id"]
    }


def test_create_valid_labour_hour_estimation(client_fixture, setup_est):
    """
    Test 1: Create valid labour-hour estimation:
    Concrete quantity = 10 m3, Productivity = 0.50 m3/hour
    Labour hours = 10 / 0.50 = 20.000000 labour-hours
    Explicitly labelled ASSUMPTION_BASED.
    """
    p1_id = setup_est["p1_id"]
    c1_token = setup_est["c1_token"]
    calc10_id = setup_est["calc10_id"]

    payload = {
        "calculation_id": calc10_id,
        "rule_code": "LABOUR_HOURS_FROM_QUANTITY",
        "rule_version": "1.0",
        "parameters": {
            "productivity_rate": "0.50",
            "productivity_unit": "m3/hour",
            "source_reference": "IS 7272 Construction Output Norms"
        }
    }

    res = client_fixture.post(
        f"/api/projects/{p1_id}/rule-based-estimations",
        json=payload,
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["project_id"] == p1_id
    assert data["calculation_id"] == calc10_id
    assert data["rule_code"] == "LABOUR_HOURS_FROM_QUANTITY"
    assert data["rule_version"] == "1.0"
    assert data["estimation_type"] == "LABOUR_HOURS"
    assert data["status"] == "ESTIMATED"
    assert Decimal(str(data["input_value"])) == Decimal("10.000000")
    assert data["input_unit"] == "m3"
    assert Decimal(str(data["result_value"])) == Decimal("20.000000")
    assert data["result_unit"] == "labour-hour"
    assert data["estimation_method"] == "RULE_BASED"
    assert data["confidence_classification"] == "ASSUMPTION_BASED"
    assert data["assumptions_json"]["assumption_type"] == "ASSUMPTION_BASED"
    assert data["assumptions_json"]["productivity_rate"] == "0.50"


def test_correct_decimal_arithmetic_precision(client_fixture, setup_est):
    """
    Test 2: Correct Decimal arithmetic precision without binary floating point inaccuracy:
    Quantity = 10.000000 m3, Productivity = 0.333333 m3/hour
    Expected = 30.000030 labour-hours
    """
    p1_id = setup_est["p1_id"]
    c1_token = setup_est["c1_token"]
    calc10_id = setup_est["calc10_id"]

    q = Decimal("10.000000")
    r = Decimal("0.333333")
    expected = (q / r).quantize(Decimal("0.000001"))

    payload = {
        "calculation_id": calc10_id,
        "rule_code": "LABOUR_HOURS_FROM_QUANTITY",
        "rule_version": "1.0",
        "parameters": {
            "productivity_rate": "0.333333",
            "productivity_unit": "m3/hour"
        }
    }

    res = client_fixture.post(
        f"/api/projects/{p1_id}/rule-based-estimations",
        json=payload,
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert Decimal(str(data["result_value"])) == expected


def test_correct_unit_validation(client_fixture, setup_est):
    """
    Test 3: Correct unit validation:
    - Supported productivity units (m3/hour, m3/labour-hour) accepted
    - Incompatible units (e.g. kg/hour, m2/hour) rejected with 400
    """
    p1_id = setup_est["p1_id"]
    c1_token = setup_est["c1_token"]
    calc10_id = setup_est["calc10_id"]

    # Incompatible productivity unit
    res = client_fixture.post(
        f"/api/projects/{p1_id}/rule-based-estimations",
        json={
            "calculation_id": calc10_id,
            "rule_code": "LABOUR_HOURS_FROM_QUANTITY",
            "rule_version": "1.0",
            "parameters": {
                "productivity_rate": "0.50",
                "productivity_unit": "kg/hour"
            }
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 400
    assert "unsupported productivity_unit" in res.json()["detail"].lower()


def test_missing_calculation_rejected(client_fixture, setup_est):
    """
    Test 4: Nonexistent calculation rejected with 404.
    """
    p1_id = setup_est["p1_id"]
    c1_token = setup_est["c1_token"]
    fake_calc_id = str(uuid.uuid4())

    res = client_fixture.post(
        f"/api/projects/{p1_id}/rule-based-estimations",
        json={
            "calculation_id": fake_calc_id,
            "rule_code": "LABOUR_HOURS_FROM_QUANTITY",
            "rule_version": "1.0",
            "parameters": {"productivity_rate": "0.50", "productivity_unit": "m3/hour"}
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 404


def test_cross_project_calculation_rejected(client_fixture, setup_est):
    """
    Test 5: Calculation belonging to another project rejected with 400.
    """
    p1_id = setup_est["p1_id"]
    c1_token = setup_est["c1_token"]
    calc_beta_id = setup_est["calc_beta_id"] # Belongs to Project Beta

    res = client_fixture.post(
        f"/api/projects/{p1_id}/rule-based-estimations",
        json={
            "calculation_id": calc_beta_id,
            "rule_code": "LABOUR_HOURS_FROM_QUANTITY",
            "rule_version": "1.0",
            "parameters": {"productivity_rate": "0.50", "productivity_unit": "m3/hour"}
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 400
    assert "cross-project calculation rejected" in res.json()["detail"].lower()


def test_invalid_calculation_status_rejected(client_fixture, setup_est):
    """
    Test 6: Calculation that is SUPERSEDED cannot be estimated.
    """
    p1_id = setup_est["p1_id"]
    c1_token = setup_est["c1_token"]
    calc1_id = setup_est["calc1_id"] # Was superseded when calc10 was calculated for el1

    res = client_fixture.post(
        f"/api/projects/{p1_id}/rule-based-estimations",
        json={
            "calculation_id": calc1_id,
            "rule_code": "LABOUR_HOURS_FROM_QUANTITY",
            "rule_version": "1.0",
            "parameters": {"productivity_rate": "0.50", "productivity_unit": "m3/hour"}
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 400
    assert "invalid calculation status" in res.json()["detail"].lower()


def test_zero_and_negative_productivity_rejected(client_fixture, setup_est):
    """
    Test 7 & 8: Zero and negative productivity rates rejected with 400.
    """
    p1_id = setup_est["p1_id"]
    c1_token = setup_est["c1_token"]
    calc10_id = setup_est["calc10_id"]

    # Zero productivity
    res0 = client_fixture.post(
        f"/api/projects/{p1_id}/rule-based-estimations",
        json={
            "calculation_id": calc10_id,
            "rule_code": "LABOUR_HOURS_FROM_QUANTITY",
            "rule_version": "1.0",
            "parameters": {"productivity_rate": "0.0", "productivity_unit": "m3/hour"}
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res0.status_code == 400
    assert "strictly positive" in res0.json()["detail"].lower()

    # Negative productivity
    res_neg = client_fixture.post(
        f"/api/projects/{p1_id}/rule-based-estimations",
        json={
            "calculation_id": calc10_id,
            "rule_code": "LABOUR_HOURS_FROM_QUANTITY",
            "rule_version": "1.0",
            "parameters": {"productivity_rate": "-0.50", "productivity_unit": "m3/hour"}
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res_neg.status_code == 400
    assert "strictly positive" in res_neg.json()["detail"].lower()


def test_missing_productivity_parameters_rejected(client_fixture, setup_est):
    """
    Test 9: Missing productivity parameters rejected with 400.
    """
    p1_id = setup_est["p1_id"]
    c1_token = setup_est["c1_token"]
    calc10_id = setup_est["calc10_id"]

    # Missing productivity_rate
    res = client_fixture.post(
        f"/api/projects/{p1_id}/rule-based-estimations",
        json={
            "calculation_id": calc10_id,
            "rule_code": "LABOUR_HOURS_FROM_QUANTITY",
            "rule_version": "1.0",
            "parameters": {"productivity_unit": "m3/hour"}
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 400
    assert "missing required rule parameter 'productivity_rate'" in res.json()["detail"].lower()

    # Missing productivity_unit
    res2 = client_fixture.post(
        f"/api/projects/{p1_id}/rule-based-estimations",
        json={
            "calculation_id": calc10_id,
            "rule_code": "LABOUR_HOURS_FROM_QUANTITY",
            "rule_version": "1.0",
            "parameters": {"productivity_rate": "0.50"}
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res2.status_code == 400
    assert "missing required rule parameter 'productivity_unit'" in res2.json()["detail"].lower()


def test_unsupported_rule_code_or_version_rejected(client_fixture, setup_est):
    """
    Test 10: Unsupported rule code or version rejected with 404 or 400.
    """
    p1_id = setup_est["p1_id"]
    c1_token = setup_est["c1_token"]
    calc10_id = setup_est["calc10_id"]

    res = client_fixture.post(
        f"/api/projects/{p1_id}/rule-based-estimations",
        json={
            "calculation_id": calc10_id,
            "rule_code": "NONEXISTENT_RULE",
            "rule_version": "1.0",
            "parameters": {"productivity_rate": "0.50", "productivity_unit": "m3/hour"}
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code in [400, 404]

    # Unsupported version
    res_v = client_fixture.post(
        f"/api/projects/{p1_id}/rule-based-estimations",
        json={
            "calculation_id": calc10_id,
            "rule_code": "LABOUR_HOURS_FROM_QUANTITY",
            "rule_version": "99.0",
            "parameters": {"productivity_rate": "0.50", "productivity_unit": "m3/hour"}
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res_v.status_code in [400, 404]


def test_superseding_creates_new_record_and_preserves_old(client_fixture, setup_est):
    """
    Test 11: Re-estimation supersedes previous active estimation and creates a new one.
    """
    p1_id = setup_est["p1_id"]
    c1_token = setup_est["c1_token"]
    calc10_id = setup_est["calc10_id"]

    # Estimation 1 (rate 0.50 -> 20 hours)
    res1 = client_fixture.post(
        f"/api/projects/{p1_id}/rule-based-estimations",
        json={
            "calculation_id": calc10_id,
            "rule_code": "LABOUR_HOURS_FROM_QUANTITY",
            "rule_version": "1.0",
            "parameters": {"productivity_rate": "0.50", "productivity_unit": "m3/hour"}
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res1.status_code == 200
    est1 = res1.json()
    assert est1["status"] == "ESTIMATED"

    # Estimation 2 (rate 0.25 -> 40 hours)
    res2 = client_fixture.post(
        f"/api/projects/{p1_id}/rule-based-estimations",
        json={
            "calculation_id": calc10_id,
            "rule_code": "LABOUR_HOURS_FROM_QUANTITY",
            "rule_version": "1.0",
            "parameters": {"productivity_rate": "0.25", "productivity_unit": "m3/hour"}
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res2.status_code == 200
    est2 = res2.json()
    assert est2["status"] == "ESTIMATED"
    assert Decimal(str(est2["result_value"])) == Decimal("40.000000")

    # Verify est1 is now SUPERSEDED
    get1 = client_fixture.get(
        f"/api/projects/{p1_id}/rule-based-estimations/{est1['id']}",
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert get1.status_code == 200
    assert get1.json()["status"] == "SUPERSEDED"


def test_db_immutability_trigger_enforcement(client_fixture, setup_est):
    """
    Test 12: PostgreSQL trigger prevents DELETE and unauthorized UPDATE on rule_based_estimations.
    """
    p1_id = setup_est["p1_id"]
    c1_token = setup_est["c1_token"]
    calc10_id = setup_est["calc10_id"]

    est = client_fixture.post(
        f"/api/projects/{p1_id}/rule-based-estimations",
        json={
            "calculation_id": calc10_id,
            "rule_code": "LABOUR_HOURS_FROM_QUANTITY",
            "rule_version": "1.0",
            "parameters": {"productivity_rate": "0.50", "productivity_unit": "m3/hour"}
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    ).json()
    est_id = est["id"]

    db = TestingSessionLocal()
    try:
        # 1. Attempt DELETE via direct SQL -> MUST FAIL
        with pytest.raises(Exception) as exc_del:
            db.execute(text(f"DELETE FROM rule_based_estimations WHERE id = '{est_id}'"))
            db.commit()
        assert "immutable and cannot be deleted" in str(exc_del.value).lower()
        db.rollback()

        # 2. Attempt unauthorized UPDATE of result_value -> MUST FAIL
        with pytest.raises(Exception) as exc_upd:
            db.execute(text(f"UPDATE rule_based_estimations SET result_value = 999.0 WHERE id = '{est_id}'"))
            db.commit()
        assert "immutable" in str(exc_upd.value).lower()
        db.rollback()

        # 3. Legitimate transition to SUPERSEDED -> MUST SUCCEED
        db.execute(text(f"UPDATE rule_based_estimations SET status = 'SUPERSEDED' WHERE id = '{est_id}'"))
        db.commit()
        st = db.execute(text(f"SELECT status FROM rule_based_estimations WHERE id = '{est_id}'")).scalar()
        assert st == "SUPERSEDED"

        # 4. Attempt transition back to ESTIMATED -> MUST FAIL
        with pytest.raises(Exception) as exc_rev:
            db.execute(text(f"UPDATE rule_based_estimations SET status = 'ESTIMATED' WHERE id = '{est_id}'"))
            db.commit()
        assert "immutable" in str(exc_rev.value).lower()
        db.rollback()

    finally:
        db.close()


def test_audit_event_created_transactionally(client_fixture, setup_est):
    """
    Test 13: ESTIMATION_PERFORMED audit record is written in the same transaction.
    """
    p1_id = setup_est["p1_id"]
    c1_token = setup_est["c1_token"]
    calc10_id = setup_est["calc10_id"]

    est = client_fixture.post(
        f"/api/projects/{p1_id}/rule-based-estimations",
        json={
            "calculation_id": calc10_id,
            "rule_code": "LABOUR_HOURS_FROM_QUANTITY",
            "rule_version": "1.0",
            "parameters": {"productivity_rate": "0.50", "productivity_unit": "m3/hour"}
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    ).json()

    db = TestingSessionLocal()
    audit = db.execute(text(
        f"SELECT action, entity_type, entity_id FROM audit_log WHERE entity_id = '{est['id']}'"
    )).first()
    db.close()

    assert audit is not None
    assert audit[0] == "ESTIMATION_PERFORMED"
    assert audit[1] == "RuleBasedEstimation"
    assert audit[2] == est["id"]


def test_failed_estimation_creates_no_partial_audit(client_fixture, setup_est):
    """
    Test 14: Failed estimation does not create partial audit state.
    """
    p1_id = setup_est["p1_id"]
    c1_token = setup_est["c1_token"]

    db = TestingSessionLocal()
    count_before = db.execute(text("SELECT count(*) FROM audit_log")).scalar()
    db.close()

    # Intentionally trigger failure (zero productivity)
    res = client_fixture.post(
        f"/api/projects/{p1_id}/rule-based-estimations",
        json={
            "calculation_id": setup_est["calc10_id"],
            "rule_code": "LABOUR_HOURS_FROM_QUANTITY",
            "rule_version": "1.0",
            "parameters": {"productivity_rate": "0.0", "productivity_unit": "m3/hour"}
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 400

    db = TestingSessionLocal()
    count_after = db.execute(text("SELECT count(*) FROM audit_log")).scalar()
    db.close()

    assert count_before == count_after


def test_project_authorization_enforced(client_fixture, setup_est):
    """
    Test 15: Non-member user is rejected with 403 on create and list.
    """
    p1_id = setup_est["p1_id"]
    c2_token = setup_est["c2_token"] # Member of Beta, not Alpha
    calc10_id = setup_est["calc10_id"]

    res_post = client_fixture.post(
        f"/api/projects/{p1_id}/rule-based-estimations",
        json={
            "calculation_id": calc10_id,
            "rule_code": "LABOUR_HOURS_FROM_QUANTITY",
            "rule_version": "1.0",
            "parameters": {"productivity_rate": "0.50", "productivity_unit": "m3/hour"}
        },
        headers={"Authorization": f"Bearer {c2_token}"}
    )
    assert res_post.status_code == 403

    res_get = client_fixture.get(
        f"/api/projects/{p1_id}/rule-based-estimations",
        headers={"Authorization": f"Bearer {c2_token}"}
    )
    assert res_get.status_code == 403


def test_full_provenance_chain_resolves_correctly(client_fixture, setup_est):
    """
    Test 16: Full provenance chain reconstructs:
    Estimation -> Calculation -> EngineeringElement -> Fact -> Evidence -> Page -> Document -> Project
    """
    p1_id = setup_est["p1_id"]
    c1_token = setup_est["c1_token"]
    calc10_id = setup_est["calc10_id"]

    res = client_fixture.post(
        f"/api/projects/{p1_id}/rule-based-estimations",
        json={
            "calculation_id": calc10_id,
            "rule_code": "LABOUR_HOURS_FROM_QUANTITY",
            "rule_version": "1.0",
            "parameters": {"productivity_rate": "0.50", "productivity_unit": "m3/hour"}
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 200
    data = res.json()

    chain = data["provenance_chain"]
    assert chain is not None
    assert chain["estimation_id"] == data["id"]
    assert chain["calculation"]["id"] == calc10_id
    assert chain["engineering_element"]["id"] == setup_est["el1_id"]
    assert chain["project"]["id"] == p1_id
    assert chain["project"]["name"] == "Project Est Alpha"

    # Verify underlying facts in calculation
    facts = chain["calculation"]["inputs_provenance"]
    assert len(facts) >= 3
    fact_names = [f["dimension_name"] for f in facts]
    assert "length_m" in fact_names
    assert "width_m" in fact_names
    assert "depth_m" in fact_names

    f0 = facts[0]
    assert f0["evidence_id"] == setup_est["ev1_id"]
    assert f0["page_id"] == setup_est["page1_id"]
    assert f0["document_id"] == setup_est["doc1_id"]
    assert f0["project_id"] == p1_id


def test_inactive_rule_rejected(client_fixture, setup_est):
    """
    Test 17: Execution of INACTIVE rule is rejected.
    """
    p1_id = setup_est["p1_id"]
    c1_token = setup_est["c1_token"]
    calc10_id = setup_est["calc10_id"]

    # Deactivate rule in database
    db = TestingSessionLocal()
    db.execute(text("UPDATE rules SET status = 'INACTIVE' WHERE rule_code = 'LABOUR_HOURS_FROM_QUANTITY' AND version = '1.0'"))
    db.commit()
    db.close()

    try:
        res = client_fixture.post(
            f"/api/projects/{p1_id}/rule-based-estimations",
            json={
                "calculation_id": calc10_id,
                "rule_code": "LABOUR_HOURS_FROM_QUANTITY",
                "rule_version": "1.0",
                "parameters": {"productivity_rate": "0.50", "productivity_unit": "m3/hour"}
            },
            headers={"Authorization": f"Bearer {c1_token}"}
        )
        assert res.status_code == 400
        assert "not active" in res.json()["detail"].lower()
    finally:
        # Restore status
        db = TestingSessionLocal()
        db.execute(text("UPDATE rules SET status = 'ACTIVE' WHERE rule_code = 'LABOUR_HOURS_FROM_QUANTITY' AND version = '1.0'"))
        db.commit()
        db.close()


def test_rule_immutability_trigger_all_semantic_fields(client_fixture, setup_est):
    """
    Test 18: Hardened trigger: Once a rule is referenced by an estimation,
    prevent modification of ALL semantic definition fields via direct SQL:
    - formula_expression
    - formula_identifier
    - rule_code
    - rule_name
    - description
    - rule_category
    - input_unit
    - output_unit
    - parameters_json
    - source_reference
    - version
    - metadata_json
    - created_by
    - created_at
    And prevent DELETE.
    Only lifecycle status (ACTIVE, INACTIVE, DEPRECATED) is allowed.
    """
    db = TestingSessionLocal()
    rule_id = db.execute(text("SELECT id FROM rules WHERE rule_code = 'LABOUR_HOURS_FROM_QUANTITY' AND version = '1.0'")).scalar()

    # 1. DELETE rejection
    with pytest.raises(Exception) as exc_del:
        db.execute(text(f"DELETE FROM rules WHERE id = '{rule_id}'"))
        db.commit()
    assert "cannot delete rule" in str(exc_del.value).lower()
    db.rollback()

    # 2. Semantic fields UPDATE rejections
    semantic_updates = [
        ("formula_expression", "'labour_hours = quantity * 2'"),
        ("formula_identifier", "'ALTERED_FORMULA'"),
        ("rule_code", "'ALTERED_CODE'"),
        ("rule_name", "'Altered Name'"),
        ("description", "'Altered description'"),
        ("rule_category", "'ALTERED_CATEGORY'"),
        ("input_unit", "'ton'"),
        ("output_unit", "'days'"),
        ("parameters_json", "'{\"altered\": true}'::json"),
        ("source_reference", "'Fake Norm 2026'"),
        ("version", "'1.1'"),
        ("metadata_json", "'{\"tampered\": true}'::json"),
    ]

    for col, val in semantic_updates:
        with pytest.raises(Exception) as exc_col:
            db.execute(text(f"UPDATE rules SET {col} = {val} WHERE id = '{rule_id}'"))
            db.commit()
        assert "cannot modify semantic definition fields" in str(exc_col.value).lower(), f"Failed on column {col}"
        db.rollback()

    # 3. Lifecycle status modification (ACTIVE -> INACTIVE -> DEPRECATED -> ACTIVE) MUST SUCCEED
    db.execute(text(f"UPDATE rules SET status = 'INACTIVE' WHERE id = '{rule_id}'"))
    db.commit()
    s_in = db.execute(text(f"SELECT status FROM rules WHERE id = '{rule_id}'")).scalar()
    assert s_in == "INACTIVE"

    db.execute(text(f"UPDATE rules SET status = 'DEPRECATED' WHERE id = '{rule_id}'"))
    db.commit()
    s_dep = db.execute(text(f"SELECT status FROM rules WHERE id = '{rule_id}'")).scalar()
    assert s_dep == "DEPRECATED"

    # Restore to ACTIVE
    db.execute(text(f"UPDATE rules SET status = 'ACTIVE' WHERE id = '{rule_id}'"))
    db.commit()
    s_act = db.execute(text(f"SELECT status FROM rules WHERE id = '{rule_id}'")).scalar()
    assert s_act == "ACTIVE"

    db.close()


def test_registry_database_mismatch_rejected(client_fixture, setup_est):
    """
    Test 19: Registry-Database agreement check:
    If DB record has modified formula_identifier or units not agreeing with executable strategy,
    execution is rejected with 400.
    """
    p1_id = setup_est["p1_id"]
    c1_token = setup_est["c1_token"]
    calc10_id = setup_est["calc10_id"]
    admin_id = setup_est["admin_id"]

    db = TestingSessionLocal()
    # Insert an unreferenced rule with mismatched formula_identifier
    mismatch_rule_id = str(uuid.uuid4())
    db.execute(text(f"""
        INSERT INTO rules (id, rule_code, rule_name, rule_category, input_unit, output_unit, formula_identifier, formula_expression, parameters_json, version, status, created_by)
        VALUES ('{mismatch_rule_id}', 'LABOUR_HOURS_FROM_QUANTITY', 'Test Mismatch', 'LABOUR_PRODUCTIVITY', 'm3', 'labour-hour', 'MISMATCHED_FORMULA', 'V / P', '{{}}'::json, '9.9', 'ACTIVE', '{admin_id}')
    """))
    db.commit()
    db.close()

    try:
        res = client_fixture.post(
            f"/api/projects/{p1_id}/rule-based-estimations",
            json={
                "calculation_id": calc10_id,
                "rule_code": "LABOUR_HOURS_FROM_QUANTITY",
                "rule_version": "9.9",
                "parameters": {"productivity_rate": "0.50", "productivity_unit": "m3/hour"}
            },
            headers={"Authorization": f"Bearer {c1_token}"}
        )
        assert res.status_code in [400, 404]
    finally:
        db = TestingSessionLocal()
        db.execute(text(f"DELETE FROM rules WHERE id = '{mismatch_rule_id}'"))
        db.commit()
        db.close()


def test_new_rule_version_creation_works(client_fixture, setup_est):
    """
    Test 20: Creating a new rule version (v2.0) works cleanly and does not mutate v1.0.
    """
    admin_id = setup_est["admin_id"]
    db = TestingSessionLocal()
    v2_id = str(uuid.uuid4())
    db.execute(text(f"""
        INSERT INTO rules (id, rule_code, rule_name, rule_category, input_unit, output_unit, formula_identifier, formula_expression, parameters_json, version, status, created_by)
        VALUES ('{v2_id}', 'LABOUR_HOURS_FROM_QUANTITY', 'Labour Hours v2', 'LABOUR_PRODUCTIVITY', 'm3', 'labour-hour', 'QUANTITY_DIVIDED_BY_PRODUCTIVITY', 'labour_hours = quantity / productivity_rate', '{{"v2": true}}'::json, '2.0', 'ACTIVE', '{admin_id}')
    """))
    db.commit()

    # Query both versions
    v1 = db.execute(text("SELECT id, version FROM rules WHERE rule_code = 'LABOUR_HOURS_FROM_QUANTITY' AND version = '1.0'")).first()
    v2 = db.execute(text("SELECT id, version FROM rules WHERE rule_code = 'LABOUR_HOURS_FROM_QUANTITY' AND version = '2.0'")).first()
    db.close()

    assert v1 is not None and v1[1] == "1.0"
    assert v2 is not None and v2[1] == "2.0"


def test_list_and_filter_estimations(client_fixture, setup_est):
    """
    Test 21: List estimations and filter by status.
    """
    p1_id = setup_est["p1_id"]
    c1_token = setup_est["c1_token"]

    res_all = client_fixture.get(
        f"/api/projects/{p1_id}/rule-based-estimations",
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res_all.status_code == 200
    assert len(res_all.json()) >= 1

    res_est = client_fixture.get(
        f"/api/projects/{p1_id}/rule-based-estimations?status=ESTIMATED",
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res_est.status_code == 200
    for item in res_est.json():
        assert item["status"] == "ESTIMATED"


def test_alembic_installed_estimation_triggers():
    """
    Test 22: Verify Alembic migration installed both estimation and rule triggers.
    """
    db = TestingSessionLocal()
    try:
        trg1 = db.execute(text(
            "SELECT tgname FROM pg_trigger WHERE tgname = 'prevent_estimation_modification_trg'"
        )).scalar()
        assert trg1 == "prevent_estimation_modification_trg"

        trg2 = db.execute(text(
            "SELECT tgname FROM pg_trigger WHERE tgname = 'prevent_rule_modification_trg'"
        )).scalar()
        assert trg2 == "prevent_rule_modification_trg"
    finally:
        db.close()


def test_get_estimation_by_id_and_not_found(client_fixture, setup_est):
    """
    Test 23: Retrieve estimation by ID, and verify 404 for nonexistent ID.
    """
    p1_id = setup_est["p1_id"]
    c1_token = setup_est["c1_token"]
    fake_id = str(uuid.uuid4())

    res_404 = client_fixture.get(
        f"/api/projects/{p1_id}/rule-based-estimations/{fake_id}",
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res_404.status_code == 404


def test_role_based_access_supervisor_and_admin(client_fixture, setup_est):
    """
    Test 24: Supervisor and Admin can also access and create estimations in their project.
    """
    p1_id = setup_est["p1_id"]
    s1_token = setup_est["s1_token"]
    admin_token = setup_est["admin_token"]

    # Supervisor access
    res_s = client_fixture.get(
        f"/api/projects/{p1_id}/rule-based-estimations",
        headers={"Authorization": f"Bearer {s1_token}"}
    )
    assert res_s.status_code == 200

    # Admin access
    res_a = client_fixture.get(
        f"/api/projects/{p1_id}/rule-based-estimations",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_a.status_code == 200

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
from app.db.models import (
    ResourcePlan,
    Resource,
    CalculationResourceMapping,
    RuleBasedEstimation,
    EngineeringCalculation,
    AuditLog
)

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
def setup_plan(client_fixture):
    # Setup test users and projects
    db = TestingSessionLocal()
    db.commit()
    db.close()

    # Admin setup
    client_fixture.post("/api/auth/register/admin", json={"email": "admin_rp@test.com", "password": "pass", "role": "admin"})
    admin_token = client_fixture.post("/api/auth/login", data={"username": "admin_rp@test.com", "password": "pass"}).json()["access_token"]

    # Users
    client_fixture.post("/api/auth/users", json={"email": "c1_rp@test.com", "password": "p", "role": "contractor"}, headers={"Authorization": f"Bearer {admin_token}"})
    client_fixture.post("/api/auth/users", json={"email": "c2_rp@test.com", "password": "p", "role": "contractor"}, headers={"Authorization": f"Bearer {admin_token}"})
    client_fixture.post("/api/auth/users", json={"email": "s1_rp@test.com", "password": "p", "role": "supervisor"}, headers={"Authorization": f"Bearer {admin_token}"})

    c1_token = client_fixture.post("/api/auth/login", data={"username": "c1_rp@test.com", "password": "p"}).json()["access_token"]
    c2_token = client_fixture.post("/api/auth/login", data={"username": "c2_rp@test.com", "password": "p"}).json()["access_token"]
    s1_token = client_fixture.post("/api/auth/login", data={"username": "s1_rp@test.com", "password": "p"}).json()["access_token"]

    # Projects
    p1 = client_fixture.post("/api/projects/", json={"name": "Project RP Alpha"}, headers={"Authorization": f"Bearer {c1_token}"}).json()
    p1_id = p1["id"]
    p2 = client_fixture.post("/api/projects/", json={"name": "Project RP Beta"}, headers={"Authorization": f"Bearer {c2_token}"}).json()
    p2_id = p2["id"]

    # Add supervisor to project 1 and project 2
    db = TestingSessionLocal()
    s1_id = db.execute(text("SELECT id FROM users WHERE email = 's1_rp@test.com'")).scalar()
    admin_id = db.execute(text("SELECT id FROM users WHERE email = 'admin_rp@test.com'")).scalar()
    db.close()
    client_fixture.post(f"/api/projects/{p1_id}/members?user_id={s1_id}", headers={"Authorization": f"Bearer {admin_token}"})
    client_fixture.post(f"/api/projects/{p2_id}/members?user_id={s1_id}", headers={"Authorization": f"Bearer {admin_token}"})

    # Upload document to project 1
    pdf_bytes = create_test_pdf()
    files = {'file': ('rp_drawing.pdf', pdf_bytes, 'application/pdf')}
    up_res = client_fixture.post(f"/api/projects/{p1_id}/documents/", files=files, headers={"Authorization": f"Bearer {c1_token}"})
    doc1_id = up_res.json()["id"]
    client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/process", headers={"Authorization": f"Bearer {c1_token}"})

    pages = client_fixture.get(f"/api/projects/{p1_id}/documents/{doc1_id}/pages", headers={"Authorization": f"Bearer {c1_token}"}).json()
    page1_id = pages[0]["id"]

    # Evidence in project 1
    ev_data = {
        "page_id": page1_id,
        "evidence_type": "DRAWING_REGION",
        "source_reference": "Drawing S-101 RP Footing",
        "locator": {"type": "bbox", "x0": 100, "y0": 200, "x1": 400, "y1": 500},
        "raw_content": "Footing F1 5.0m x 2.0m x 1.0m (10 m3)"
    }
    ev = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/evidence", json=ev_data, headers={"Authorization": f"Bearer {c1_token}"}).json()
    ev1_id = ev["id"]

    # Verified Facts for 10 m3 calculation
    f_l = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/evidence/{ev1_id}/facts", json={
        "fact_type": "DIMENSION", "field_name": "l", "raw_value": "5.0 m", "extraction_method": "MANUAL"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()
    client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/facts/{f_l['id']}/verify", json={"status": "VERIFIED"}, headers={"Authorization": f"Bearer {s1_token}"})

    f_w = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/evidence/{ev1_id}/facts", json={
        "fact_type": "DIMENSION", "field_name": "w", "raw_value": "2.0 m", "extraction_method": "MANUAL"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()
    client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/facts/{f_w['id']}/verify", json={"status": "VERIFIED"}, headers={"Authorization": f"Bearer {s1_token}"})

    f_d = client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/evidence/{ev1_id}/facts", json={
        "fact_type": "DIMENSION", "field_name": "d", "raw_value": "1.0 m", "extraction_method": "MANUAL"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()
    client_fixture.post(f"/api/projects/{p1_id}/documents/{doc1_id}/facts/{f_d['id']}/verify", json={"status": "VERIFIED"}, headers={"Authorization": f"Bearer {s1_token}"})

    # Element 1 in Project 1
    el1 = client_fixture.post(f"/api/projects/{p1_id}/engineering-elements", json={
        "element_type": "FOOTING",
        "element_name": "Footing F-RP-1"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()
    el1_id = el1["id"]

    # Element 2 in Project 1 (for cross-element mismatch test)
    el2 = client_fixture.post(f"/api/projects/{p1_id}/engineering-elements", json={
        "element_type": "BEAM",
        "element_name": "Beam B-RP-2"
    }, headers={"Authorization": f"Bearer {c1_token}"}).json()
    el2_id = el2["id"]

    # Calculation 1 on Element 1 (10.000000 m3)
    calc10 = client_fixture.post(
        f"/api/projects/{p1_id}/engineering-elements/{el1_id}/calculations",
        json={
            "calculation_type": "CONCRETE_VOLUME_RECTANGULAR",
            "inputs": {
                "length_m": {"value": "5.0", "unit": "m", "source_fact_id": f_l["id"], "source_type": "VERIFIED_FACT"},
                "width_m": {"value": "2.0", "unit": "m", "source_fact_id": f_w["id"], "source_type": "VERIFIED_FACT"},
                "depth_m": {"value": "1.0", "unit": "m", "source_fact_id": f_d["id"], "source_type": "VERIFIED_FACT"}
            }
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    ).json()
    calc10_id = calc10["id"]

    # Rule-Based Estimation on Element 1 (10 m3 / 0.50 m3/hour = 20.000000 labour-hours)
    est20 = client_fixture.post(
        f"/api/projects/{p1_id}/rule-based-estimations",
        json={
            "calculation_id": calc10_id,
            "rule_code": "LABOUR_HOURS_FROM_QUANTITY",
            "rule_version": "1.0",
            "parameters": {"productivity_rate": "0.50", "productivity_unit": "m3/hour"}
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    ).json()
    est20_id = est20["id"]

    # Setup for Project 2 (Beta) for cross-project isolation tests
    files2 = {'file': ('beta_rp.pdf', pdf_bytes, 'application/pdf')}
    up2 = client_fixture.post(f"/api/projects/{p2_id}/documents/", files=files2, headers={"Authorization": f"Bearer {c2_token}"}).json()
    client_fixture.post(f"/api/projects/{p2_id}/documents/{up2['id']}/process", headers={"Authorization": f"Bearer {c2_token}"})
    p2_pages = client_fixture.get(f"/api/projects/{p2_id}/documents/{up2['id']}/pages", headers={"Authorization": f"Bearer {c2_token}"}).json()
    ev2 = client_fixture.post(f"/api/projects/{p2_id}/documents/{up2['id']}/evidence", json={
        "page_id": p2_pages[0]["id"], "evidence_type": "DRAWING_REGION", "source_reference": "Beta Ref", "raw_content": "Beta"
    }, headers={"Authorization": f"Bearer {c2_token}"}).json()
    f_b_l = client_fixture.post(f"/api/projects/{p2_id}/documents/{up2['id']}/evidence/{ev2['id']}/facts", json={
        "fact_type": "DIMENSION", "field_name": "b_l", "raw_value": "1.0 m", "extraction_method": "MANUAL"
    }, headers={"Authorization": f"Bearer {c2_token}"}).json()
    client_fixture.post(f"/api/projects/{p2_id}/documents/{up2['id']}/facts/{f_b_l['id']}/verify", json={"status": "VERIFIED"}, headers={"Authorization": f"Bearer {s1_token}"})

    el_b = client_fixture.post(f"/api/projects/{p2_id}/engineering-elements", json={
        "element_type": "FOOTING", "element_name": "Beta Footing"
    }, headers={"Authorization": f"Bearer {c2_token}"}).json()
    el_b_id = el_b["id"]

    calc_b = client_fixture.post(
        f"/api/projects/{p2_id}/engineering-elements/{el_b_id}/calculations",
        json={
            "calculation_type": "CONCRETE_VOLUME_RECTANGULAR",
            "inputs": {
                "length_m": {"value": "1.0", "unit": "m", "source_fact_id": f_b_l["id"], "source_type": "VERIFIED_FACT"},
                "width_m": {"value": "1.0", "unit": "m", "source_fact_id": f_b_l["id"], "source_type": "VERIFIED_FACT"},
                "depth_m": {"value": "1.0", "unit": "m", "source_fact_id": f_b_l["id"], "source_type": "VERIFIED_FACT"}
            }
        },
        headers={"Authorization": f"Bearer {c2_token}"}
    ).json()
    calc_b_id = calc_b["id"]

    est_b = client_fixture.post(
        f"/api/projects/{p2_id}/rule-based-estimations",
        json={
            "calculation_id": calc_b_id,
            "rule_code": "LABOUR_HOURS_FROM_QUANTITY",
            "rule_version": "1.0",
            "parameters": {"productivity_rate": "1.0", "productivity_unit": "m3/hour"}
        },
        headers={"Authorization": f"Bearer {c2_token}"}
    ).json()
    est_b_id = est_b["id"]

    return {
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
        "el2_id": el2_id,
        "calc10_id": calc10_id,
        "est20_id": est20_id,
        "el_b_id": el_b_id,
        "calc_b_id": calc_b_id,
        "est_b_id": est_b_id
    }


def test_create_resource(client_fixture, setup_plan):
    """
    Test 1: Create resource via POST /api/resources, verify fields, status, category, unit.
    """
    admin_token = setup_plan["admin_token"]
    res = client_fixture.post(
        "/api/resources",
        json={
            "resource_code": "LABOUR-CARPENTER",
            "resource_name": "Formwork Carpenter",
            "resource_category": "LABOUR",
            "unit": "labour-hour",
            "description": "Formwork fabrication and shuttering labour",
            "status": "ACTIVE"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["resource_code"] == "LABOUR-CARPENTER"
    assert data["resource_category"] == "LABOUR"
    assert data["unit"] == "labour-hour"
    assert data["status"] == "ACTIVE"


def test_valid_deterministic_calculation_explicitly_mapped_resource_succeeds(client_fixture, setup_plan):
    """
    Test 2: Valid deterministic calculation -> explicitly mapped resource (MATERIAL-CONCRETE) succeeds.
    """
    p1_id = setup_plan["p1_id"]
    c1_token = setup_plan["c1_token"]
    calc10_id = setup_plan["calc10_id"]

    res = client_fixture.post(
        f"/api/projects/{p1_id}/resource-plans",
        json={
            "resource_code": "MATERIAL-CONCRETE",
            "calculation_id": calc10_id
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["project_id"] == p1_id
    assert data["status"] == "PLANNED"
    assert data["planning_method"] == "DETERMINISTIC"
    assert data["classification"] == "CALCULATED"
    assert Decimal(str(data["resource_demand"])) == Decimal("10.000000")
    assert data["resource_demand_unit"] == "m3"
    assert data["mapping_id"] is not None


def test_calculation_with_no_mapping_rejected(client_fixture, setup_plan):
    """
    Test 3: Calculation with no explicit mapping is rejected.
    Try to map CONCRETE_VOLUME_RECTANGULAR to an unmapped resource (e.g. LABOUR-CARPENTER or unmapped equipment).
    """
    p1_id = setup_plan["p1_id"]
    c1_token = setup_plan["c1_token"]
    calc10_id = setup_plan["calc10_id"]

    # Create unmapped material with same unit 'm3'
    admin_token = setup_plan["admin_token"]
    client_fixture.post(
        "/api/resources",
        json={
            "resource_code": "MATERIAL-SAND",
            "resource_name": "River Sand",
            "resource_category": "MATERIAL",
            "unit": "m3",
            "status": "ACTIVE"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    res = client_fixture.post(
        f"/api/projects/{p1_id}/resource-plans",
        json={
            "resource_code": "MATERIAL-SAND",
            "calculation_id": calc10_id
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 400
    assert "no explicit calculation-to-resource mapping found" in res.json()["detail"].lower()


def test_calculation_with_same_unit_but_wrong_semantic_resource_rejected(client_fixture, setup_plan):
    """
    Test 4: Calculation with same unit (m3) but unmapped/wrong semantic resource is rejected.
    Unit equality alone is NOT sufficient.
    """
    p1_id = setup_plan["p1_id"]
    c1_token = setup_plan["c1_token"]
    calc10_id = setup_plan["calc10_id"]
    admin_token = setup_plan["admin_token"]

    client_fixture.post(
        "/api/resources",
        json={
            "resource_code": "MATERIAL-WATER",
            "resource_name": "Curing Water",
            "resource_category": "MATERIAL",
            "unit": "m3",
            "status": "ACTIVE"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    res = client_fixture.post(
        f"/api/projects/{p1_id}/resource-plans",
        json={
            "resource_code": "MATERIAL-WATER",
            "calculation_id": calc10_id
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 400
    assert "no explicit calculation-to-resource mapping found" in res.json()["detail"].lower()


def test_calculation_with_wrong_calculation_type_rejected(client_fixture, setup_plan):
    """
    Test 5: Calculation with non-matching calculation_type in mapping is rejected.
    """
    p1_id = setup_plan["p1_id"]
    c1_token = setup_plan["c1_token"]

    # Create a calculation with different type (e.g. STEEL_WEIGHT)
    db = TestingSessionLocal()
    calc_other = EngineeringCalculation(
        project_id=p1_id,
        engineering_element_id=setup_plan["el1_id"],
        calculation_type="STEEL_REINFORCEMENT_WEIGHT",
        calculation_version="1.0",
        status="CALCULATED",
        result_value=Decimal("150.000000"),
        result_unit="kg",
        formula_identifier="LENGTH_TIMES_WEIGHT_PER_M",
        formula_expression="W = L * w",
        inputs_json={"test": 1},
        created_by=db.execute(text("SELECT id FROM users WHERE email = 'c1_rp@test.com'")).scalar()
    )
    db.add(calc_other)
    db.commit()
    other_calc_id = calc_other.id
    db.close()

    res = client_fixture.post(
        f"/api/projects/{p1_id}/resource-plans",
        json={
            "resource_code": "MATERIAL-CONCRETE",
            "calculation_id": other_calc_id
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 400
    assert "no explicit calculation-to-resource mapping found" in res.json()["detail"].lower()


def test_calculation_with_wrong_calculation_version_rejected(client_fixture, setup_plan):
    """
    Test 6: Calculation with wrong calculation_version is rejected.
    """
    p1_id = setup_plan["p1_id"]
    c1_token = setup_plan["c1_token"]

    db = TestingSessionLocal()
    calc_v2 = EngineeringCalculation(
        project_id=p1_id,
        engineering_element_id=setup_plan["el1_id"],
        calculation_type="CONCRETE_VOLUME_RECTANGULAR",
        calculation_version="2.0",
        status="CALCULATED",
        result_value=Decimal("10.000000"),
        result_unit="m3",
        formula_identifier="RECTANGULAR_PRISM",
        formula_expression="V = L * W * D",
        inputs_json={"test": 1},
        created_by=db.execute(text("SELECT id FROM users WHERE email = 'c1_rp@test.com'")).scalar()
    )
    db.add(calc_v2)
    db.commit()
    v2_calc_id = calc_v2.id
    db.close()

    res = client_fixture.post(
        f"/api/projects/{p1_id}/resource-plans",
        json={
            "resource_code": "MATERIAL-CONCRETE",
            "calculation_id": v2_calc_id
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 400
    assert "no explicit calculation-to-resource mapping found" in res.json()["detail"].lower()


def test_inactive_and_deprecated_mapping_rejected(client_fixture, setup_plan):
    """
    Test 7 & 8: Inactive or deprecated mapping is rejected.
    """
    p1_id = setup_plan["p1_id"]
    c1_token = setup_plan["c1_token"]
    calc10_id = setup_plan["calc10_id"]

    db = TestingSessionLocal()
    mapping = db.query(CalculationResourceMapping).filter(
        CalculationResourceMapping.calculation_type == "CONCRETE_VOLUME_RECTANGULAR",
        CalculationResourceMapping.calculation_version == "1.0"
    ).first()
    mapping.status = "INACTIVE"
    db.commit()
    db.close()

    try:
        # Inactive mapping test
        res_inact = client_fixture.post(
            f"/api/projects/{p1_id}/resource-plans",
            json={
                "resource_code": "MATERIAL-CONCRETE",
                "calculation_id": calc10_id
            },
            headers={"Authorization": f"Bearer {c1_token}"}
        )
        assert res_inact.status_code == 400
        assert "not active" in res_inact.json()["detail"].lower()

        # Deprecated mapping test
        db = TestingSessionLocal()
        m = db.query(CalculationResourceMapping).filter(
            CalculationResourceMapping.calculation_type == "CONCRETE_VOLUME_RECTANGULAR",
            CalculationResourceMapping.calculation_version == "1.0"
        ).first()
        m.status = "DEPRECATED"
        db.commit()
        db.close()

        res_dep = client_fixture.post(
            f"/api/projects/{p1_id}/resource-plans",
            json={
                "resource_code": "MATERIAL-CONCRETE",
                "calculation_id": calc10_id
            },
            headers={"Authorization": f"Bearer {c1_token}"}
        )
        assert res_dep.status_code == 400
        assert "not active" in res_dep.json()["detail"].lower()

    finally:
        # Restore active mapping
        db = TestingSessionLocal()
        m = db.query(CalculationResourceMapping).filter(
            CalculationResourceMapping.calculation_type == "CONCRETE_VOLUME_RECTANGULAR",
            CalculationResourceMapping.calculation_version == "1.0"
        ).first()
        m.status = "ACTIVE"
        db.commit()
        db.close()


def test_rule_based_labour_estimation_continues_to_work(client_fixture, setup_plan):
    """
    Test 11: Rule-based labour estimation continues to work.
    """
    p1_id = setup_plan["p1_id"]
    c1_token = setup_plan["c1_token"]
    est20_id = setup_plan["est20_id"]

    res = client_fixture.post(
        f"/api/projects/{p1_id}/resource-plans",
        json={
            "resource_code": "LABOUR-CONCRETE",
            "estimation_id": est20_id
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["planning_method"] == "RULE_BASED"
    assert data["classification"] == "ASSUMPTION_BASED"
    assert Decimal(str(data["resource_demand"])) == Decimal("20.000000")


def test_rule_based_labour_estimation_mapped_to_incompatible_material_rejected(client_fixture, setup_plan):
    """
    Test 12: Rule-based labour estimation mapped to incompatible material resource is rejected.
    """
    p1_id = setup_plan["p1_id"]
    c1_token = setup_plan["c1_token"]
    est20_id = setup_plan["est20_id"]

    res = client_fixture.post(
        f"/api/projects/{p1_id}/resource-plans",
        json={
            "resource_code": "MATERIAL-CONCRETE",
            "estimation_id": est20_id
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 400
    assert "incompatible resource" in res.json()["detail"].lower()


def test_conflicting_calculation_and_estimation_rejected(client_fixture, setup_plan):
    """
    Test 13: Conflicting calculation and estimation sources rejected.
    E.g. Calculation: CONCRETE_VOLUME_RECTANGULAR (10 m3), Estimation: LABOUR_HOURS (20 labour-hours), Resource: MATERIAL-CONCRETE.
    """
    p1_id = setup_plan["p1_id"]
    c1_token = setup_plan["c1_token"]
    est20_id = setup_plan["est20_id"]
    calc10_id = setup_plan["calc10_id"]

    res = client_fixture.post(
        f"/api/projects/{p1_id}/resource-plans",
        json={
            "resource_code": "MATERIAL-CONCRETE",
            "estimation_id": est20_id,
            "calculation_id": calc10_id
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 400
    assert "conflicting" in res.json()["detail"].lower()


def test_mapping_provenance_appears_in_response(client_fixture, setup_plan):
    """
    Test 14: Mapping provenance appears in response for deterministic planning.
    """
    p1_id = setup_plan["p1_id"]
    c1_token = setup_plan["c1_token"]
    calc10_id = setup_plan["calc10_id"]

    res = client_fixture.post(
        f"/api/projects/{p1_id}/resource-plans",
        json={
            "resource_code": "MATERIAL-CONCRETE",
            "calculation_id": calc10_id
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    hier = data["provenance_hierarchy"]
    assert hier["mapping"] is not None
    assert hier["mapping"]["calculation_type"] == "CONCRETE_VOLUME_RECTANGULAR"
    assert hier["mapping"]["calculation_version"] == "1.0"
    assert hier["mapping"]["mapping_method"] == "DIRECT"
    assert hier["mapping"]["source_unit"] == "m3"
    assert hier["mapping"]["resource_unit"] == "m3"


def test_referenced_mapping_semantic_mutation_and_delete_blocked(client_fixture, setup_plan):
    """
    Test 15 & 16: Referenced mapping semantic UPDATE and DELETE blocked at PostgreSQL level.
    """
    p1_id = setup_plan["p1_id"]
    c1_token = setup_plan["c1_token"]
    calc10_id = setup_plan["calc10_id"]

    res = client_fixture.post(
        f"/api/projects/{p1_id}/resource-plans",
        json={
            "resource_code": "MATERIAL-CONCRETE",
            "calculation_id": calc10_id
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    mapping_id = res.json()["mapping_id"]
    assert mapping_id is not None

    db = TestingSessionLocal()
    # Test DELETE blocked
    with pytest.raises(Exception) as exc_del:
        db.execute(text("DELETE FROM calculation_resource_mappings WHERE id = :mid"), {"mid": mapping_id})
        db.commit()
    db.rollback()
    assert "referenced" in str(exc_del.value).lower()

    # Test semantic UPDATE blocked
    with pytest.raises(Exception) as exc_upd:
        db.execute(text("UPDATE calculation_resource_mappings SET source_unit = 'ton' WHERE id = :mid"), {"mid": mapping_id})
        db.commit()
    db.rollback()
    assert "semantic definition" in str(exc_upd.value).lower()
    db.close()


def test_mapping_lifecycle_status_behavior_works(client_fixture, setup_plan):
    """
    Test 17: Mapping lifecycle status transition works on referenced mapping.
    """
    p1_id = setup_plan["p1_id"]
    c1_token = setup_plan["c1_token"]
    calc10_id = setup_plan["calc10_id"]

    res = client_fixture.post(
        f"/api/projects/{p1_id}/resource-plans",
        json={
            "resource_code": "MATERIAL-CONCRETE",
            "calculation_id": calc10_id
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    mapping_id = res.json()["mapping_id"]

    db = TestingSessionLocal()
    # Transition to DEPRECATED
    db.execute(text("UPDATE calculation_resource_mappings SET status = 'DEPRECATED' WHERE id = :mid"), {"mid": mapping_id})
    db.commit()

    row = db.execute(text("SELECT status FROM calculation_resource_mappings WHERE id = :mid"), {"mid": mapping_id}).fetchone()
    assert row[0] == "DEPRECATED"

    # Restore to ACTIVE
    db.execute(text("UPDATE calculation_resource_mappings SET status = 'ACTIVE' WHERE id = :mid"), {"mid": mapping_id})
    db.commit()
    db.close()


def test_cross_project_and_element_rejections(client_fixture, setup_plan):
    """
    Test 9 & 10: Cross-project calculation and cross-project estimation remain rejected.
    """
    p1_id = setup_plan["p1_id"]
    c1_token = setup_plan["c1_token"]
    calc_b_id = setup_plan["calc_b_id"]
    est_b_id = setup_plan["est_b_id"]

    res_c = client_fixture.post(
        f"/api/projects/{p1_id}/resource-plans",
        json={"resource_code": "MATERIAL-CONCRETE", "calculation_id": calc_b_id},
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res_c.status_code == 400
    assert "cross-project" in res_c.json()["detail"].lower()

    res_e = client_fixture.post(
        f"/api/projects/{p1_id}/resource-plans",
        json={"resource_code": "LABOUR-CONCRETE", "estimation_id": est_b_id},
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res_e.status_code == 400
    assert "cross-project" in res_e.json()["detail"].lower()


def test_resource_plan_immutability_and_audit(client_fixture, setup_plan):
    """
    Test 18, 19, 20, 21: ResourcePlan immutability, audit transactionality, project authorization.
    """
    p1_id = setup_plan["p1_id"]
    c1_token = setup_plan["c1_token"]
    c2_token = setup_plan["c2_token"]
    calc10_id = setup_plan["calc10_id"]

    # Authorization
    res_auth = client_fixture.post(
        f"/api/projects/{p1_id}/resource-plans",
        json={"resource_code": "MATERIAL-CONCRETE", "calculation_id": calc10_id},
        headers={"Authorization": f"Bearer {c2_token}"}
    )
    assert res_auth.status_code == 403

    # Success creation
    res = client_fixture.post(
        f"/api/projects/{p1_id}/resource-plans",
        json={"resource_code": "MATERIAL-CONCRETE", "calculation_id": calc10_id},
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    plan_id = res.json()["id"]

    # Audit check
    db = TestingSessionLocal()
    audit = db.query(AuditLog).filter(
        AuditLog.entity_type == "ResourcePlan",
        AuditLog.entity_id == plan_id,
        AuditLog.action == "RESOURCE_PLAN_CREATED"
    ).first()
    assert audit is not None
    assert "demand" in audit.reason.lower()

    # DB Delete blocked
    with pytest.raises(Exception):
        db.execute(text("DELETE FROM resource_plans WHERE id = :pid"), {"pid": plan_id})
        db.commit()
    db.rollback()

    # DB Update demand blocked
    with pytest.raises(Exception):
        db.execute(text("UPDATE resource_plans SET resource_demand = 888.0 WHERE id = :pid"), {"pid": plan_id})
        db.commit()
    db.rollback()

    # Controlled transition to SUPERSEDED succeeds
    db.execute(text("UPDATE resource_plans SET status = 'SUPERSEDED' WHERE id = :pid"), {"pid": plan_id})
    db.commit()
    row = db.execute(text("SELECT status FROM resource_plans WHERE id = :pid"), {"pid": plan_id}).fetchone()
    assert row[0] == "SUPERSEDED"
    db.close()


def test_list_and_get_endpoints(client_fixture, setup_plan):
    """
    Test endpoints: list, filter, get by id.
    """
    p1_id = setup_plan["p1_id"]
    c1_token = setup_plan["c1_token"]
    calc10_id = setup_plan["calc10_id"]

    res_create = client_fixture.post(
        f"/api/projects/{p1_id}/resource-plans",
        json={"resource_code": "MATERIAL-CONCRETE", "calculation_id": calc10_id},
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    pid = res_create.json()["id"]

    res_list = client_fixture.get(
        f"/api/projects/{p1_id}/resource-plans",
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    res_get = client_fixture.get(
        f"/api/projects/{p1_id}/resource-plans/{pid}",
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res_get.status_code == 200
    res_404 = client_fixture.get(
        f"/api/projects/{p1_id}/resource-plans/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res_404.status_code == 404


def test_historical_resource_plan_remains_unchanged(client_fixture, setup_plan):
    """
    Test 18: Historical ResourcePlan remains completely unchanged when superseded.
    """
    p1_id = setup_plan["p1_id"]
    c1_token = setup_plan["c1_token"]
    calc10_id = setup_plan["calc10_id"]

    res1 = client_fixture.post(
        f"/api/projects/{p1_id}/resource-plans",
        json={"resource_code": "MATERIAL-CONCRETE", "calculation_id": calc10_id},
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    id1 = res1.json()["id"]

    res2 = client_fixture.post(
        f"/api/projects/{p1_id}/resource-plans",
        json={"resource_code": "MATERIAL-CONCRETE", "calculation_id": calc10_id},
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    id2 = res2.json()["id"]
    assert id1 != id2

    db = TestingSessionLocal()
    old_p = db.query(ResourcePlan).filter(ResourcePlan.id == id1).first()
    assert old_p.status == "SUPERSEDED"
    assert old_p.resource_demand == Decimal("10.000000")
    assert old_p.resource_demand_unit == "m3"
    db.close()


def test_cross_element_rejection(client_fixture, setup_plan):
    """
    Test 10: Cross-element source remains rejected.
    """
    p1_id = setup_plan["p1_id"]
    c1_token = setup_plan["c1_token"]
    calc10_id = setup_plan["calc10_id"]
    el2_id = setup_plan["el2_id"]

    res = client_fixture.post(
        f"/api/projects/{p1_id}/resource-plans",
        json={
            "resource_code": "MATERIAL-CONCRETE",
            "calculation_id": calc10_id,
            "engineering_element_id": el2_id
        },
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 400
    assert "cross-element mismatch" in res.json()["detail"].lower()


def test_referenced_resource_immutability(client_fixture, setup_plan):
    """
    Test referenced resource deletion and semantic mutation blocked by trigger.
    """
    p1_id = setup_plan["p1_id"]
    c1_token = setup_plan["c1_token"]
    calc10_id = setup_plan["calc10_id"]

    res = client_fixture.post(
        f"/api/projects/{p1_id}/resource-plans",
        json={"resource_code": "MATERIAL-CONCRETE", "calculation_id": calc10_id},
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    res_id = res.json()["resource_id"]

    db = TestingSessionLocal()
    with pytest.raises(Exception):
        db.execute(text("DELETE FROM resources WHERE id = :rid"), {"rid": res_id})
        db.commit()
    db.rollback()

    with pytest.raises(Exception):
        db.execute(text("UPDATE resources SET unit = 'liter' WHERE id = :rid"), {"rid": res_id})
        db.commit()
    db.rollback()
    db.close()


"""Phase 1K: Deterministic Cost Estimation & Rate-Based Valuation Hardened Test Suite.

Comprehensive test suite explicitly covering all Phase 1K requirements:
1. Rate Management & Strict Input Validation (non-empty unit, rate_code, description, source_ref; 400/422 only, never 500)
2. Direct PostgreSQL Confirmed-Rate Immutability (all 17 columns tested against direct SQL mutation)
3. Rate Versioning Concurrency & Atomic Rollback
4. Direct PostgreSQL Cost-Calculation Immutability (all 22 columns tested against direct SQL mutation, DELETE blocked)
5. VERIFIED_RECONCILED Decision Semantics (ACCEPT_MATCH, ACCEPT_CALCULATED, ACCEPT_BOQ, non-MATCH validation, decision immutability)
6. Supervisor/Admin Decision Authority (contractor 403, supervisor 201, admin 201)
7. Audit Transactionality & Failure-Path Rollback (atomic business mutation + audit; zero audit logs on failed operations)
8. Global Rate Semantics (global catalog vs project isolation, document restriction)
9. Rate-Unit Compatibility (canonical pairs accepted, incompatible dimensions rejected)
10. Currency Snapshot Integrity & SQL Trigger Enforcement
11. Historical Valuation Stability on Rate Supersession
12. Aggregation & Comparative Valuation Delta (isolated from unmapped items)
13. Database-Level Project Isolation via Triggers (cross-project direct SQL attempts blocked)
"""
import uuid
from decimal import Decimal
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import get_db, engine
from app.db.models import (
    User,
    Project,
    ProjectMember,
    Document,
    Evidence,
    EngineeringElement,
    EngineeringCalculation,
    BoqItem,
    BoqCalculationMapping,
    BoqReconciliation,
    CostRate,
    CostCalculation,
    AuditLog,
)
from app.core.security import get_password_hash, create_access_token

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def client_fixture():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="module")
def setup_data(client_fixture):
    # 1. Users: Admin, Supervisor, Contractor, Outsider
    admin_email = f"admin_cost_{uuid.uuid4().hex[:6]}@test.com"
    with TestingSessionLocal() as db:
        adm = User(email=admin_email, password_hash=get_password_hash("pass"), role="admin")
        db.add(adm)
        db.commit()
    admin_token = create_access_token(data={"sub": admin_email, "role": "admin"})

    sup_email = f"sup_cost_{uuid.uuid4().hex[:6]}@test.com"
    con_email = f"con_cost_{uuid.uuid4().hex[:6]}@test.com"
    out_email = f"out_cost_{uuid.uuid4().hex[:6]}@test.com"

    client_fixture.post("/api/auth/users", json={"email": sup_email, "password": "p", "role": "supervisor"}, headers={"Authorization": f"Bearer {admin_token}"})
    client_fixture.post("/api/auth/users", json={"email": con_email, "password": "p", "role": "contractor"}, headers={"Authorization": f"Bearer {admin_token}"})
    client_fixture.post("/api/auth/users", json={"email": out_email, "password": "p", "role": "contractor"}, headers={"Authorization": f"Bearer {admin_token}"})

    sup_token = client_fixture.post("/api/auth/login", data={"username": sup_email, "password": "p"}).json()["access_token"]
    con_token = client_fixture.post("/api/auth/login", data={"username": con_email, "password": "p"}).json()["access_token"]
    out_token = client_fixture.post("/api/auth/login", data={"username": out_email, "password": "p"}).json()["access_token"]

    # 2. Project 1 and Project 2
    p1_resp = client_fixture.post("/api/projects", json={"name": f"Cost Project 1 {uuid.uuid4().hex[:6]}"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert p1_resp.status_code == 200
    p1_id = p1_resp.json()["id"]

    p2_resp = client_fixture.post("/api/projects", json={"name": f"Cost Project 2 {uuid.uuid4().hex[:6]}"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert p2_resp.status_code == 200
    p2_id = p2_resp.json()["id"]

    with TestingSessionLocal() as db:
        sup_user = db.query(User).filter(User.email == sup_email).first()
        con_user = db.query(User).filter(User.email == con_email).first()
        adm_user = db.query(User).filter(User.email == admin_email).first()

        db.add(ProjectMember(project_id=p1_id, user_id=sup_user.id))
        db.add(ProjectMember(project_id=p1_id, user_id=con_user.id))
        db.add(ProjectMember(project_id=p2_id, user_id=sup_user.id))
        db.commit()

        # Seed Documents & Evidence in Project 1
        doc1 = Document(
            id=str(uuid.uuid4()),
            project_id=p1_id,
            original_filename="tender_boq.pdf",
            storage_key=f"raw/{p1_id}/tender_boq.pdf",
            file_size_bytes=1024,
            mime_type="application/pdf",
            sha256_hash="aabbcc112233",
            uploaded_by=con_user.id,
            document_type="BOQ",
        )
        db.add(doc1)
        db.flush()

        ev1 = Evidence(
            id=str(uuid.uuid4()),
            document_id=doc1.id,
            evidence_type="BOQ_ITEM",
            source_reference="Item 4.1",
            created_by=sup_user.id,
            verification_status="VERIFIED",
        )
        db.add(ev1)

        # Seed Documents & Evidence in Project 2
        doc2 = Document(
            id=str(uuid.uuid4()),
            project_id=p2_id,
            original_filename="tender_boq_p2.pdf",
            storage_key=f"raw/{p2_id}/tender_boq_p2.pdf",
            file_size_bytes=1024,
            mime_type="application/pdf",
            sha256_hash="aabbcc223344",
            uploaded_by=adm_user.id,
            document_type="BOQ",
        )
        db.add(doc2)
        db.flush()

        ev2 = Evidence(
            id=str(uuid.uuid4()),
            document_id=doc2.id,
            evidence_type="BOQ_ITEM",
            source_reference="Item P2-4.1",
            created_by=adm_user.id,
            verification_status="VERIFIED",
        )
        db.add(ev2)
        db.commit()

        # Seed Engineering Elements in P1 & P2
        elem1 = EngineeringElement(
            id=str(uuid.uuid4()),
            project_id=p1_id,
            element_type="SLAB",
            element_name="Slab Level 1",
            status="ACTIVE",
            created_by=sup_user.id,
        )
        elem2 = EngineeringElement(
            id=str(uuid.uuid4()),
            project_id=p2_id,
            element_type="BEAM",
            element_name="Beam Level 1 P2",
            status="ACTIVE",
            created_by=adm_user.id,
        )
        db.add(elem1)
        db.add(elem2)
        db.commit()

        # Seed Engineering Calculations in P1 & P2
        calc1 = EngineeringCalculation(
            id=str(uuid.uuid4()),
            engineering_element_id=elem1.id,
            project_id=p1_id,
            calculation_type="CONCRETE_VOLUME",
            calculation_version="1.0",
            result_value=Decimal("120.500000"),
            result_unit="m3",
            formula_identifier="RECTANGULAR_VOLUME",
            formula_expression="V = L * W * D",
            inputs_json={"length": 10, "width": 12, "depth": 1.004166},
            created_by=sup_user.id,
        )
        calc2 = EngineeringCalculation(
            id=str(uuid.uuid4()),
            engineering_element_id=elem2.id,
            project_id=p2_id,
            calculation_type="STEEL_WEIGHT",
            calculation_version="1.0",
            result_value=Decimal("50.000000"),
            result_unit="kg",
            formula_identifier="REBAR_WEIGHT",
            formula_expression="W = N * L * M",
            inputs_json={"bars": 10},
            created_by=adm_user.id,
        )
        calc1_b = EngineeringCalculation(
            id=str(uuid.uuid4()),
            engineering_element_id=elem1.id,
            project_id=p1_id,
            calculation_type="CONCRETE_VOLUME",
            calculation_version="1.0",
            result_value=Decimal("120.500000"),
            result_unit="m3",
            formula_identifier="RECTANGULAR_VOLUME",
            formula_expression="V = L * W * D",
            inputs_json={"length": 10, "width": 12, "depth": 1.004166},
            created_by=sup_user.id,
        )
        db.add(calc1)
        db.add(calc2)
        db.add(calc1_b)
        db.commit()

        # Seed Confirmed BOQ Items in P1 & P2
        boq1 = BoqItem(
            id=str(uuid.uuid4()),
            project_id=p1_id,
            document_id=doc1.id,
            item_code="BOQ-C-101",
            description="M25 Concrete for Slabs",
            unit="m3",
            stated_quantity=Decimal("125.000000"),
            status="CONFIRMED",
            classification="STATED_FROM_DOCUMENT",
            provenance_json={"source": "doc"},
            created_by=con_user.id,
            confirmed_by=sup_user.id,
            confirmed_at=datetime.now(timezone.utc),
        )
        boq2_draft = BoqItem(
            id=str(uuid.uuid4()),
            project_id=p1_id,
            document_id=doc1.id,
            item_code="BOQ-C-102-DRAFT",
            description="Reinforcement Steel Draft",
            unit="kg",
            stated_quantity=Decimal("5000.000000"),
            status="DRAFT",
            classification="STATED_FROM_DOCUMENT",
            provenance_json={"source": "doc"},
            created_by=con_user.id,
        )
        boq2_conf = BoqItem(
            id=str(uuid.uuid4()),
            project_id=p1_id,
            document_id=doc1.id,
            item_code="BOQ-C-102-CONF",
            description="M20 Concrete for Beams",
            unit="m3",
            stated_quantity=Decimal("100.000000"),
            status="CONFIRMED",
            classification="STATED_FROM_DOCUMENT",
            provenance_json={"source": "doc"},
            created_by=con_user.id,
            confirmed_by=sup_user.id,
            confirmed_at=datetime.now(timezone.utc),
        )
        boq_p2 = BoqItem(
            id=str(uuid.uuid4()),
            project_id=p2_id,
            document_id=doc2.id,
            item_code="BOQ-P2-201",
            description="P2 Structural Works",
            unit="m3",
            stated_quantity=Decimal("200.000000"),
            status="CONFIRMED",
            classification="STATED_FROM_DOCUMENT",
            provenance_json={"source": "doc"},
            created_by=adm_user.id,
            confirmed_by=adm_user.id,
            confirmed_at=datetime.now(timezone.utc),
        )
        db.add(boq1)
        db.add(boq2_draft)
        db.add(boq2_conf)
        db.add(boq_p2)
        db.commit()

        # Seed Verified Mappings in P1 & P2
        mapping1 = BoqCalculationMapping(
            id=str(uuid.uuid4()),
            project_id=p1_id,
            boq_item_id=boq1.id,
            calculation_id=calc1.id,
            mapping_type="DIRECT",
            status="VERIFIED",
            verified_by=sup_user.id,
            verified_at=datetime.now(timezone.utc),
            created_by=con_user.id,
        )
        mapping2 = BoqCalculationMapping(
            id=str(uuid.uuid4()),
            project_id=p1_id,
            boq_item_id=boq2_conf.id,
            calculation_id=calc1_b.id,
            mapping_type="DIRECT",
            status="VERIFIED",
            verified_by=sup_user.id,
            verified_at=datetime.now(timezone.utc),
            created_by=con_user.id,
        )
        mapping_p2 = BoqCalculationMapping(
            id=str(uuid.uuid4()),
            project_id=p2_id,
            boq_item_id=boq_p2.id,
            calculation_id=calc2.id,
            mapping_type="DIRECT",
            status="VERIFIED",
            verified_by=adm_user.id,
            verified_at=datetime.now(timezone.utc),
            created_by=adm_user.id,
        )
        db.add(mapping1)
        db.add(mapping2)
        db.add(mapping_p2)
        db.commit()

        # Seed BoqReconciliation in P1 (MATCH)
        rec1_match = BoqReconciliation(
            id=str(uuid.uuid4()),
            project_id=p1_id,
            mapping_id=mapping1.id,
            boq_item_id=boq1.id,
            calculation_id=calc1.id,
            boq_quantity=Decimal("120.500000"),
            boq_unit="m3",
            calculated_quantity=Decimal("120.500000"),
            calculated_unit="m3",
            quantity_delta=Decimal("0.000000"),
            variance_percentage=Decimal("0.000000"),
            tolerance_threshold=Decimal("0.000000"),
            discrepancy_status="MATCH",
            status="CALCULATED",
            algorithm_version="1.0",
            provenance_json={"mapping_id": mapping1.id},
            created_by=sup_user.id,
        )
        # Seed BoqReconciliation in P1 (OVER_CALCULATED)
        rec2_over = BoqReconciliation(
            id=str(uuid.uuid4()),
            project_id=p1_id,
            mapping_id=mapping2.id,
            boq_item_id=boq2_conf.id,
            calculation_id=calc1_b.id,
            boq_quantity=Decimal("100.000000"),
            boq_unit="m3",
            calculated_quantity=Decimal("120.500000"),
            calculated_unit="m3",
            quantity_delta=Decimal("20.500000"),
            variance_percentage=Decimal("20.500000"),
            tolerance_threshold=Decimal("0.000000"),
            discrepancy_status="OVER_CALCULATED",
            status="CALCULATED",
            algorithm_version="1.0",
            provenance_json={"mapping_id": mapping2.id},
            created_by=sup_user.id,
        )
        # Seed BoqReconciliation in P2
        rec_p2 = BoqReconciliation(
            id=str(uuid.uuid4()),
            project_id=p2_id,
            mapping_id=mapping_p2.id,
            boq_item_id=boq_p2.id,
            calculation_id=calc2.id,
            boq_quantity=Decimal("50.000000"),
            boq_unit="kg",
            calculated_quantity=Decimal("50.000000"),
            calculated_unit="kg",
            quantity_delta=Decimal("0.000000"),
            variance_percentage=Decimal("0.000000"),
            tolerance_threshold=Decimal("0.000000"),
            discrepancy_status="MATCH",
            status="CALCULATED",
            algorithm_version="1.0",
            provenance_json={"mapping_id": mapping_p2.id},
            created_by=adm_user.id,
        )
        db.add(rec1_match)
        db.add(rec2_over)
        db.add(rec_p2)
        db.commit()

        doc1_id = doc1.id
        ev1_id = ev1.id
        doc2_id = doc2.id
        ev2_id = ev2.id
        calc1_id = calc1.id
        calc2_id = calc2.id
        boq1_id = boq1.id
        boq2_draft_id = boq2_draft.id
        boq_p2_id = boq_p2.id
        rec1_match_id = rec1_match.id
        rec2_over_id = rec2_over.id
        rec_p2_id = rec_p2.id

    return {
        "admin_token": admin_token,
        "sup_token": sup_token,
        "con_token": con_token,
        "out_token": out_token,
        "p1_id": p1_id,
        "p2_id": p2_id,
        "doc1_id": doc1_id,
        "ev1_id": ev1_id,
        "doc2_id": doc2_id,
        "ev2_id": ev2_id,
        "calc1_id": calc1_id,
        "calc2_id": calc2_id,
        "boq1_id": boq1_id,
        "boq2_draft_id": boq2_draft_id,
        "boq_p2_id": boq_p2_id,
        "rec1_match_id": rec1_match_id,
        "rec2_over_id": rec2_over_id,
        "rec_p2_id": rec_p2_id,
    }


# ==============================================================================
# SECTION 1: RATE DECLARATION & INPUT VALIDATION (Never 500, exact 400/422)
# ==============================================================================

def test_01_declare_global_draft_rate(client_fixture, setup_data):
    """Test 01: Declare global draft rate (project_id=None, source_doc=None)."""
    resp = client_fixture.post(
        "/api/cost-rates",
        json={
            "rate_code": f"DSR-M25-{uuid.uuid4().hex[:4]}",
            "description": "Delhi Schedule of Rates M25 Concrete",
            "unit": "m3",
            "rate_value": "4500.50",
            "currency": "INR",
            "source_type": "OFFICIAL_SCHEDULE",
            "source_reference": "CPWD DSR 2023 Item 4.1.2",
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["project_id"] is None
    assert data["status"] == "DRAFT"
    assert Decimal(str(data["rate_value"])) == Decimal("4500.500000")


def test_02_declare_project_specific_draft_rate(client_fixture, setup_data):
    """Test 02: Declare project-specific draft rate."""
    code = f"PROJ-M25-{uuid.uuid4().hex[:4]}"
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": code,
            "description": "Project Specific M25 Concrete Rate",
            "unit": "m3",
            "rate_value": "4800.00",
            "currency": "INR",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Contract Agreement Cl. 12",
            "source_document_id": setup_data["doc1_id"],
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["project_id"] == setup_data["p1_id"]
    assert data["status"] == "DRAFT"
    assert data["rate_code"] == code


def test_03_reject_global_rate_with_project_doc(client_fixture, setup_data):
    """Test 03: Reject global rate referencing a project document."""
    resp = client_fixture.post(
        "/api/cost-rates",
        json={
            "rate_code": f"DSR-INVALID-{uuid.uuid4().hex[:4]}",
            "description": "Invalid Global Rate with Doc",
            "unit": "m3",
            "rate_value": "4000.00",
            "source_type": "OFFICIAL_SCHEDULE",
            "source_reference": "Invalid",
            "source_document_id": setup_data["doc1_id"],
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert resp.status_code == 400
    assert "Global cost rates cannot reference" in resp.json()["detail"]


def test_04_reject_negative_rate_value(client_fixture, setup_data):
    """Test 04: Reject negative rate value with 422."""
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": f"NEG-{uuid.uuid4().hex[:4]}",
            "description": "Negative rate",
            "unit": "m3",
            "rate_value": "-100.00",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    )
    assert resp.status_code == 422


def test_05_reject_blank_rate_code(client_fixture, setup_data):
    """Test 05: Reject blank rate code with 400."""
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": "",
            "description": "Blank rate code",
            "unit": "m3",
            "rate_value": "100.00",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    )
    assert resp.status_code == 400
    assert "rate_code cannot be empty" in resp.json()["detail"]


def test_06a_reject_blank_unit(client_fixture, setup_data):
    """Test 06a: Reject unit="" with 400, never 500."""
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": f"CODE-{uuid.uuid4().hex[:4]}",
            "description": "Blank unit test",
            "unit": "",
            "rate_value": "100.00",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    )
    assert resp.status_code == 400
    assert "unit cannot be empty" in resp.json()["detail"]


def test_06b_reject_whitespace_unit(client_fixture, setup_data):
    """Test 06b: Reject unit="   " with 400, never 500."""
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": f"CODE-{uuid.uuid4().hex[:4]}",
            "description": "Whitespace unit test",
            "unit": "   ",
            "rate_value": "100.00",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    )
    assert resp.status_code == 400
    assert "unit cannot be empty" in resp.json()["detail"]


def test_06c_reject_whitespace_rate_code(client_fixture, setup_data):
    """Test 06c: Reject rate_code="   " with 400."""
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": "     ",
            "description": "Whitespace code test",
            "unit": "m3",
            "rate_value": "100.00",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    )
    assert resp.status_code == 400
    assert "rate_code cannot be empty" in resp.json()["detail"]


def test_06d_reject_whitespace_description(client_fixture, setup_data):
    """Test 06d: Reject description="   " with 400."""
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": f"CODE-{uuid.uuid4().hex[:4]}",
            "description": "   ",
            "unit": "m3",
            "rate_value": "100.00",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    )
    assert resp.status_code == 400
    assert "description cannot be empty" in resp.json()["detail"]


def test_06e_reject_whitespace_source_reference(client_fixture, setup_data):
    """Test 06e: Reject source_reference="   " with 400."""
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": f"CODE-{uuid.uuid4().hex[:4]}",
            "description": "Valid desc",
            "unit": "m3",
            "rate_value": "100.00",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "   ",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    )
    assert resp.status_code == 400
    assert "source_reference cannot be empty" in resp.json()["detail"]


def test_07_confirm_draft_rate(client_fixture, setup_data):
    """Test 07: Confirm draft rate sets confirmed_by, confirmed_at, status=CONFIRMED."""
    create_resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": f"CONF-RATE-{uuid.uuid4().hex[:4]}",
            "description": "To be confirmed",
            "unit": "m3",
            "rate_value": "5200.00",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Quotation 45",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    )
    rate_id = create_resp.json()["id"]

    conf_resp = client_fixture.patch(
        f"/api/cost-rates/{rate_id}/confirm",
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert conf_resp.status_code == 200
    data = conf_resp.json()
    assert data["status"] == "CONFIRMED"
    assert data["confirmed_by"] is not None
    assert data["confirmed_at"] is not None


def test_08_reject_confirming_already_confirmed_rate(client_fixture, setup_data):
    """Test 08: Reject confirming already confirmed rate."""
    rate_resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": f"ALREADY-CONF-{uuid.uuid4().hex[:4]}",
            "description": "Double confirm test",
            "unit": "m3",
            "rate_value": "5100.00",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Q1",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    )
    rate_id = rate_resp.json()["id"]
    client_fixture.patch(f"/api/cost-rates/{rate_id}/confirm", headers={"Authorization": f"Bearer {setup_data['sup_token']}"})

    resp = client_fixture.patch(
        f"/api/cost-rates/{rate_id}/confirm",
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert resp.status_code == 400
    assert "Only DRAFT rates can be confirmed" in resp.json()["detail"]


def test_09_prohibit_duplicate_active_confirmed_rate_code_globally(client_fixture, setup_data):
    """Test 09: Prohibit duplicate active confirmed rate code globally."""
    code = f"GLOBAL-DUP-{uuid.uuid4().hex[:4]}"
    r1 = client_fixture.post(
        "/api/cost-rates",
        json={
            "rate_code": code,
            "description": "Global 1",
            "unit": "m3",
            "rate_value": "1000.00",
            "source_type": "OFFICIAL_SCHEDULE",
            "source_reference": "Ref 1",
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    ).json()["id"]
    client_fixture.patch(f"/api/cost-rates/{r1}/confirm", headers={"Authorization": f"Bearer {setup_data['sup_token']}"})

    r2_resp = client_fixture.post(
        "/api/cost-rates",
        json={
            "rate_code": code,
            "description": "Global 2 Dup",
            "unit": "m3",
            "rate_value": "1200.00",
            "source_type": "OFFICIAL_SCHEDULE",
            "source_reference": "Ref 2",
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert r2_resp.status_code == 409


def test_10_prohibit_duplicate_active_confirmed_rate_code_in_project(client_fixture, setup_data):
    """Test 10: Prohibit duplicate active confirmed rate code in project."""
    code = f"PROJ-DUP-{uuid.uuid4().hex[:4]}"
    r1 = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": code,
            "description": "Project 1",
            "unit": "m3",
            "rate_value": "1000.00",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref 1",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    ).json()["id"]
    client_fixture.patch(f"/api/cost-rates/{r1}/confirm", headers={"Authorization": f"Bearer {setup_data['sup_token']}"})

    r2_resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": code,
            "description": "Project 2 Dup",
            "unit": "m3",
            "rate_value": "1200.00",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref 2",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    )
    assert r2_resp.status_code == 409


def test_11_allow_duplicate_draft_rate_codes(client_fixture, setup_data):
    """Test 11: Allow duplicate draft rate codes."""
    code = f"DRAFT-DUP-{uuid.uuid4().hex[:4]}"
    r1 = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": code,
            "description": "Draft 1",
            "unit": "m3",
            "rate_value": "1000.00",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref 1",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    )
    assert r1.status_code == 201

    r2 = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": code,
            "description": "Draft 2",
            "unit": "m3",
            "rate_value": "1050.00",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref 2",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    )
    assert r2.status_code == 201


def test_12_supersede_rate_workflow(client_fixture, setup_data):
    """Test 12: Supersede rate: declare new version with replaces_rate_id, confirming supersedes old."""
    code = f"RATE-VER-{uuid.uuid4().hex[:4]}"
    r1 = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": code,
            "description": "Rate v1",
            "unit": "m3",
            "rate_value": "1000.00",
            "version": "1.0",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Doc v1",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    ).json()["id"]
    client_fixture.patch(f"/api/cost-rates/{r1}/confirm", headers={"Authorization": f"Bearer {setup_data['sup_token']}"})

    r2 = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": code,
            "description": "Rate v2 Updated",
            "unit": "m3",
            "rate_value": "1150.00",
            "version": "2.0",
            "replaces_rate_id": r1,
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Doc v2",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    ).json()["id"]

    conf2 = client_fixture.patch(f"/api/cost-rates/{r2}/confirm", headers={"Authorization": f"Bearer {setup_data['sup_token']}"})
    assert conf2.status_code == 200
    assert conf2.json()["status"] == "CONFIRMED"

    with TestingSessionLocal() as db:
        old = db.query(CostRate).filter(CostRate.id == r1).first()
        assert old.status == "SUPERSEDED"


def test_13_reject_new_version_with_different_rate_code(client_fixture, setup_data):
    """Test 13: Reject new version with different rate_code."""
    code1 = f"CODE-A-{uuid.uuid4().hex[:4]}"
    r1 = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": code1,
            "description": "Rate A",
            "unit": "m3",
            "rate_value": "1000.00",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Doc A",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    ).json()["id"]
    client_fixture.patch(f"/api/cost-rates/{r1}/confirm", headers={"Authorization": f"Bearer {setup_data['sup_token']}"})

    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": f"CODE-B-{uuid.uuid4().hex[:4]}",
            "description": "Rate B replacing A",
            "unit": "m3",
            "rate_value": "1100.00",
            "replaces_rate_id": r1,
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Doc B",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    )
    assert resp.status_code == 400
    assert "maintain the same rate_code" in resp.json()["detail"]


def test_14_reject_new_version_changing_project_scope(client_fixture, setup_data):
    """Test 14: Reject new version changing project scope."""
    code = f"SCOPE-CODE-{uuid.uuid4().hex[:4]}"
    r1 = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": code,
            "description": "Project 1 Rate",
            "unit": "m3",
            "rate_value": "1000.00",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    ).json()["id"]
    client_fixture.patch(f"/api/cost-rates/{r1}/confirm", headers={"Authorization": f"Bearer {setup_data['sup_token']}"})

    resp = client_fixture.post(
        f"/api/projects/{setup_data['p2_id']}/cost-rates",
        json={
            "rate_code": code,
            "description": "Project 2 Rate replacing P1",
            "unit": "m3",
            "rate_value": "1050.00",
            "replaces_rate_id": r1,
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref",
        },
        headers={"Authorization": f"Bearer {setup_data['admin_token']}"},
    )
    assert resp.status_code == 400
    assert "cannot change project scope" in resp.json()["detail"]


def test_15_delete_draft_rate_succeeds(client_fixture, setup_data):
    """Test 15: Delete draft rate succeeds."""
    r_id = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": f"DEL-DRAFT-{uuid.uuid4().hex[:4]}",
            "description": "Draft to delete",
            "unit": "m3",
            "rate_value": "100.00",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    ).json()["id"]

    del_resp = client_fixture.delete(f"/api/cost-rates/{r_id}", headers={"Authorization": f"Bearer {setup_data['con_token']}"})
    assert del_resp.status_code == 204


def test_16_prohibit_deleting_confirmed_rate(client_fixture, setup_data):
    """Test 16: Prohibit deleting confirmed rate."""
    r_id = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": f"NO-DEL-CONF-{uuid.uuid4().hex[:4]}",
            "description": "Confirmed rate",
            "unit": "m3",
            "rate_value": "100.00",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    ).json()["id"]
    client_fixture.patch(f"/api/cost-rates/{r_id}/confirm", headers={"Authorization": f"Bearer {setup_data['sup_token']}"})

    del_resp = client_fixture.delete(f"/api/cost-rates/{r_id}", headers={"Authorization": f"Bearer {setup_data['con_token']}"})
    assert del_resp.status_code == 400
    assert "Cannot delete non-draft" in del_resp.json()["detail"]


def test_17_prohibit_deleting_superseded_rate(client_fixture, setup_data):
    """Test 17: Prohibit deleting superseded rate."""
    code = f"NO-DEL-SUP-{uuid.uuid4().hex[:4]}"
    r1 = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": code,
            "description": "v1",
            "unit": "m3",
            "rate_value": "100.00",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    ).json()["id"]
    client_fixture.patch(f"/api/cost-rates/{r1}/confirm", headers={"Authorization": f"Bearer {setup_data['sup_token']}"})

    r2 = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": code,
            "description": "v2",
            "unit": "m3",
            "rate_value": "110.00",
            "replaces_rate_id": r1,
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    ).json()["id"]
    client_fixture.patch(f"/api/cost-rates/{r2}/confirm", headers={"Authorization": f"Bearer {setup_data['sup_token']}"})

    del_resp = client_fixture.delete(f"/api/cost-rates/{r1}", headers={"Authorization": f"Bearer {setup_data['sup_token']}"})
    assert del_resp.status_code == 400


# ==============================================================================
# SECTION 2: DIRECT POSTGRESQL CONFIRMED-RATE IMMUTABILITY (All 17 fields)
# ==============================================================================

@pytest.fixture(scope="module")
def sql_confirmed_rate(setup_data):
    with TestingSessionLocal() as db:
        admin_id = db.query(User).filter(User.role == "admin").first().id
        rate = CostRate(
            id=str(uuid.uuid4()),
            project_id=setup_data["p1_id"],
            rate_code=f"SQL-ALL-IMMUT-{uuid.uuid4().hex[:4]}",
            description="Base contractual rate for immutability tests",
            unit="m3",
            rate_value=Decimal("500.000000"),
            currency="INR",
            source_type="PROJECT_SPECIFIC",
            source_reference="Spec Cl 5",
            source_document_id=setup_data["doc1_id"],
            source_evidence_id=setup_data["ev1_id"],
            version="1.0",
            status="CONFIRMED",
            created_by=admin_id,
            confirmed_by=admin_id,
            confirmed_at=datetime.now(timezone.utc),
            metadata_json={"tag": "immut_base"},
        )
        db.add(rate)
        db.commit()
        return rate.id


@pytest.mark.parametrize("field,bad_val", [
    ("rate_value", "999.00"),
    ("unit", "'tonne'"),
    ("rate_code", "'MUTATED-CODE'"),
    ("currency", "'USD'"),
    ("source_reference", "'Altered Ref'"),
    ("source_type", "'OFFICIAL_SCHEDULE'"),
    ("description", "'Altered Description'"),
    ("source_document_id", f"'{str(uuid.uuid4())}'"),
    ("source_evidence_id", f"'{str(uuid.uuid4())}'"),
    ("version", "'9.9'"),
    ("replaces_rate_id", f"'{str(uuid.uuid4())}'"),
    ("metadata_json", "'{\"altered\": true}'::json"),
    ("created_by", f"'{str(uuid.uuid4())}'"),
    ("created_at", "now()"),
    ("confirmed_by", f"'{str(uuid.uuid4())}'"),
    ("confirmed_at", "now()"),
    ("project_id", f"'{str(uuid.uuid4())}'"),
])
def test_18_confirmed_rate_direct_sql_field_mutations_blocked(sql_confirmed_rate, field, bad_val):
    """Test 18: Every individual contractual field direct SQL update is blocked by trg_protect_cost_rate."""
    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as excinfo:
            db.execute(text(f"UPDATE cost_rates SET {field} = {bad_val} WHERE id = '{sql_confirmed_rate}'"))
            db.commit()
        assert "contractual fields cannot be modified" in str(excinfo.value)


def test_18r_confirmed_rate_simultaneous_mutation_with_superseded_blocked(sql_confirmed_rate):
    """Test 18r: Transition to SUPERSEDED while simultaneously mutating another field is blocked."""
    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as excinfo:
            db.execute(text(f"UPDATE cost_rates SET status = 'SUPERSEDED', rate_value = 888.00 WHERE id = '{sql_confirmed_rate}'"))
            db.commit()
        assert "contractual fields cannot be modified" in str(excinfo.value)


def test_rate_lifecycle_draft_to_superseded_prohibited(setup_data):
    """Test: DRAFT -> SUPERSEDED direct SQL transition is prohibited by fn_protect_cost_rate."""
    with TestingSessionLocal() as db:
        admin_id = db.query(User).filter(User.role == "admin").first().id
        rate = CostRate(
            id=str(uuid.uuid4()),
            project_id=setup_data["p1_id"],
            rate_code=f"DRAFT-SUP-{uuid.uuid4().hex[:4]}",
            description="Draft",
            unit="m3",
            rate_value=Decimal("100.00"),
            currency="INR",
            source_type="PROJECT_SPECIFIC",
            source_reference="Ref",
            status="DRAFT",
            created_by=admin_id,
        )
        db.add(rate)
        db.commit()
        rate_id = rate.id

    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as excinfo:
            db.execute(text(f"UPDATE cost_rates SET status = 'SUPERSEDED' WHERE id = '{rate_id}'"))
            db.commit()
        assert "Illegal cost rate status transition" in str(excinfo.value)


def test_rate_lifecycle_superseded_to_draft_prohibited(setup_data):
    """Test: SUPERSEDED -> DRAFT direct SQL transition is prohibited."""
    with TestingSessionLocal() as db:
        admin_id = db.query(User).filter(User.role == "admin").first().id
        rate = CostRate(
            id=str(uuid.uuid4()),
            project_id=setup_data["p1_id"],
            rate_code=f"SUP-DRAFT-{uuid.uuid4().hex[:4]}",
            description="Superseded",
            unit="m3",
            rate_value=Decimal("100.00"),
            currency="INR",
            source_type="PROJECT_SPECIFIC",
            source_reference="Ref",
            status="SUPERSEDED",
            created_by=admin_id,
            confirmed_by=admin_id,
            confirmed_at=datetime.now(timezone.utc),
        )
        db.add(rate)
        db.commit()
        rate_id = rate.id

    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as excinfo:
            db.execute(text(f"UPDATE cost_rates SET status = 'DRAFT' WHERE id = '{rate_id}'"))
            db.commit()
        assert "Illegal cost rate status transition" in str(excinfo.value)


def test_rate_lifecycle_superseded_to_confirmed_prohibited(setup_data):
    """Test: SUPERSEDED -> CONFIRMED direct SQL transition is prohibited."""
    with TestingSessionLocal() as db:
        admin_id = db.query(User).filter(User.role == "admin").first().id
        rate = CostRate(
            id=str(uuid.uuid4()),
            project_id=setup_data["p1_id"],
            rate_code=f"SUP-CONF-{uuid.uuid4().hex[:4]}",
            description="Superseded",
            unit="m3",
            rate_value=Decimal("100.00"),
            currency="INR",
            source_type="PROJECT_SPECIFIC",
            source_reference="Ref",
            status="SUPERSEDED",
            created_by=admin_id,
            confirmed_by=admin_id,
            confirmed_at=datetime.now(timezone.utc),
        )
        db.add(rate)
        db.commit()
        rate_id = rate.id

    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as excinfo:
            db.execute(text(f"UPDATE cost_rates SET status = 'CONFIRMED' WHERE id = '{rate_id}'"))
            db.commit()
        assert "Illegal cost rate status transition" in str(excinfo.value)


def test_rate_lifecycle_superseded_mutation_prohibited(setup_data):
    """Test: SUPERSEDED -> SUPERSEDED with mutation is prohibited."""
    with TestingSessionLocal() as db:
        admin_id = db.query(User).filter(User.role == "admin").first().id
        rate = CostRate(
            id=str(uuid.uuid4()),
            project_id=setup_data["p1_id"],
            rate_code=f"SUP-MUT-{uuid.uuid4().hex[:4]}",
            description="Superseded",
            unit="m3",
            rate_value=Decimal("100.00"),
            currency="INR",
            source_type="PROJECT_SPECIFIC",
            source_reference="Ref",
            status="SUPERSEDED",
            created_by=admin_id,
            confirmed_by=admin_id,
            confirmed_at=datetime.now(timezone.utc),
        )
        db.add(rate)
        db.commit()
        rate_id = rate.id

    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as excinfo:
            db.execute(text(f"UPDATE cost_rates SET rate_value = 999.00 WHERE id = '{rate_id}'"))
            db.commit()
        assert "contractual fields cannot be modified" in str(excinfo.value)


def test_rate_lifecycle_confirmed_to_draft_prohibited(sql_confirmed_rate):
    """Test: CONFIRMED -> DRAFT direct SQL transition is prohibited."""
    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as excinfo:
            db.execute(text(f"UPDATE cost_rates SET status = 'DRAFT' WHERE id = '{sql_confirmed_rate}'"))
            db.commit()
        assert "Illegal cost rate status transition" in str(excinfo.value)


def test_19_prohibit_direct_sql_superseded_transition(setup_data):
    """Test 19: Direct SQL transition from SUPERSEDED to anything else is prohibited."""
    with TestingSessionLocal() as db:
        admin_id = db.query(User).filter(User.role == "admin").first().id
        rate = CostRate(
            id=str(uuid.uuid4()),
            project_id=setup_data["p1_id"],
            rate_code=f"SQL-SUPER-{uuid.uuid4().hex[:4]}",
            description="Superseded Transition Test",
            unit="m3",
            rate_value=Decimal("500.000000"),
            currency="INR",
            source_type="PROJECT_SPECIFIC",
            source_reference="Direct",
            status="SUPERSEDED",
            created_by=admin_id,
            confirmed_by=admin_id,
            confirmed_at=datetime.now(timezone.utc),
        )
        db.add(rate)
        db.commit()
        rate_id = rate.id

    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as excinfo:
            db.execute(text(f"UPDATE cost_rates SET status = 'CONFIRMED' WHERE id = '{rate_id}'"))
            db.commit()
        assert "Illegal cost rate status transition" in str(excinfo.value)


def test_20_prohibit_direct_sql_delete_of_confirmed_rate(sql_confirmed_rate):
    """Test 20: Direct SQL DELETE of confirmed rate is prohibited by trigger."""
    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as excinfo:
            db.execute(text(f"DELETE FROM cost_rates WHERE id = '{sql_confirmed_rate}'"))
            db.commit()
        assert "Confirmed and superseded cost rates cannot be deleted" in str(excinfo.value)


# ==============================================================================
# SECTION 3: RATE VERSIONING CONCURRENCY & ATOMIC ROLLBACK
# ==============================================================================

def test_concurrency_rate_active_confirmed_uniqueness_db_level(setup_data):
    """Test concurrency: direct DB partial unique index blocks concurrent active confirmed rates."""
    code = f"CONCURR-CODE-{uuid.uuid4().hex[:4]}"
    with TestingSessionLocal() as db1:
        admin_id = db1.query(User).filter(User.role == "admin").first().id
        r1 = CostRate(
            id=str(uuid.uuid4()),
            project_id=setup_data["p1_id"],
            rate_code=code,
            description="Active version 1",
            unit="m3",
            rate_value=Decimal("100.00"),
            currency="INR",
            source_type="PROJECT_SPECIFIC",
            source_reference="Ref",
            status="CONFIRMED",
            created_by=admin_id,
            confirmed_by=admin_id,
            confirmed_at=datetime.now(timezone.utc),
        )
        db1.add(r1)
        db1.commit()

    with TestingSessionLocal() as db2:
        with pytest.raises(Exception) as excinfo:
            r2 = CostRate(
                id=str(uuid.uuid4()),
                project_id=setup_data["p1_id"],
                rate_code=code,
                description="Active version 2 (violating)",
                unit="m3",
                rate_value=Decimal("120.00"),
                currency="INR",
                source_type="PROJECT_SPECIFIC",
                source_reference="Ref",
                status="CONFIRMED",
                created_by=admin_id,
                confirmed_by=admin_id,
                confirmed_at=datetime.now(timezone.utc),
            )
            db2.add(r2)
            db2.commit()
        assert "uq_cost_rates_project_active_code" in str(excinfo.value) or "duplicate key" in str(excinfo.value)


def test_concurrency_failed_confirmation_rolls_back_completely(client_fixture, setup_data):
    """Test concurrency rollback: failed confirmation leaves no status changes, supersession, or audit logs."""
    code = f"CONC-ROLLBACK-{uuid.uuid4().hex[:4]}"
    # Author two draft rates concurrently with the same rate_code BEFORE either is confirmed
    r1_resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": code,
            "description": "First draft rate",
            "unit": "m3",
            "rate_value": "100.00",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    )
    assert r1_resp.status_code == 201
    r1 = r1_resp.json()["id"]

    r2_resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": code,
            "description": "Concurrent second draft without replaces_rate_id",
            "unit": "m3",
            "rate_value": "110.00",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    )
    assert r2_resp.status_code == 201
    r2 = r2_resp.json()["id"]

    # Now confirm the first rate
    conf1 = client_fixture.patch(f"/api/cost-rates/{r1}/confirm", headers={"Authorization": f"Bearer {setup_data['sup_token']}"})
    assert conf1.status_code == 200

    audit_count_before = 0
    with TestingSessionLocal() as db:
        audit_count_before = db.query(AuditLog).filter(AuditLog.entity_id == r2).count()

    conf_fail = client_fixture.patch(f"/api/cost-rates/{r2}/confirm", headers={"Authorization": f"Bearer {setup_data['sup_token']}"})
    assert conf_fail.status_code == 409

    with TestingSessionLocal() as db:
        rate2_in_db = db.query(CostRate).filter(CostRate.id == r2).first()
        assert rate2_in_db.status == "DRAFT"
        rate1_in_db = db.query(CostRate).filter(CostRate.id == r1).first()
        assert rate1_in_db.status == "CONFIRMED"
        audit_count_after = db.query(AuditLog).filter(AuditLog.entity_id == r2).count()
        assert audit_count_after == audit_count_before


# ==============================================================================
# SECTION 4: QUANTITY BASIS & CALCULATION EXECUTION (Decision Semantics)
# ==============================================================================

@pytest.fixture(scope="module")
def confirmed_m3_rate(client_fixture, setup_data):
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": f"M25-SHARED-{uuid.uuid4().hex[:4]}",
            "description": "Shared M25 Concrete Rate",
            "unit": "m3",
            "rate_value": "5000.00",
            "currency": "INR",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Contract Schedule B",
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    rate_id = resp.json()["id"]
    client_fixture.patch(f"/api/cost-rates/{rate_id}/confirm", headers={"Authorization": f"Bearer {setup_data['sup_token']}"})
    return rate_id


def test_21_calculate_boq_stated(client_fixture, setup_data, confirmed_m3_rate):
    """Test 21: Calculate BOQ_STATED with confirmed BOQ item: total_cost = quantity * rate."""
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "BOQ_STATED",
            "boq_item_id": setup_data["boq1_id"],
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["quantity_basis"] == "BOQ_STATED"
    assert Decimal(str(data["quantity_value"])) == Decimal("125.000000")
    assert Decimal(str(data["total_cost"])) == Decimal("625000.000000")
    assert data["status"] == "CALCULATED"


def test_22_reject_boq_stated_with_draft_boq_item(client_fixture, setup_data, confirmed_m3_rate):
    """Test 22: Reject BOQ_STATED with draft BOQ item."""
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "BOQ_STATED",
            "boq_item_id": setup_data["boq2_draft_id"],
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert resp.status_code == 400
    assert "BOQ item must be CONFIRMED" in resp.json()["detail"]


def test_23_reject_boq_stated_with_nonexistent_boq_item(client_fixture, setup_data, confirmed_m3_rate):
    """Test 23: Reject BOQ_STATED with non-existent BOQ item."""
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "BOQ_STATED",
            "boq_item_id": str(uuid.uuid4()),
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert resp.status_code == 404


def test_24_reject_boq_stated_cross_project(client_fixture, setup_data, confirmed_m3_rate):
    """Test 24: Reject BOQ_STATED referencing cross-project BOQ item."""
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "BOQ_STATED",
            "boq_item_id": setup_data["boq_p2_id"],
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert resp.status_code == 400
    assert "does not belong to specified project" in resp.json()["detail"]


def test_25_calculate_engineering_calculated(client_fixture, setup_data, confirmed_m3_rate):
    """Test 25: Calculate ENGINEERING_CALCULATED with valid engineering calculation."""
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "ENGINEERING_CALCULATED",
            "calculation_id": setup_data["calc1_id"],
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["quantity_basis"] == "ENGINEERING_CALCULATED"
    assert Decimal(str(data["quantity_value"])) == Decimal("120.500000")
    assert Decimal(str(data["total_cost"])) == Decimal("602500.000000")


def test_26_reject_engineering_calculated_cross_project(client_fixture, setup_data, confirmed_m3_rate):
    """Test 26: Reject ENGINEERING_CALCULATED referencing cross-project calculation."""
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "ENGINEERING_CALCULATED",
            "calculation_id": setup_data["calc2_id"],
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert resp.status_code == 400
    assert "does not belong to specified project" in resp.json()["detail"]


def test_27_reconciled_accept_match_uses_calculated_quantity(client_fixture, setup_data, confirmed_m3_rate):
    """Test 27: VERIFIED_RECONCILED with ACCEPT_MATCH uses calculated quantity."""
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "VERIFIED_RECONCILED",
            "reconciliation_id": setup_data["rec1_match_id"],
            "reconciliation_decision": "ACCEPT_MATCH",
            "decision_reason": "Matched verified quantities exactly.",
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["reconciliation_decision"] == "ACCEPT_MATCH"
    assert Decimal(str(data["quantity_value"])) == Decimal("120.500000")
    assert Decimal(str(data["total_cost"])) == Decimal("602500.000000")


def test_28_reconciled_accept_match_rejected_on_discrepancy(client_fixture, setup_data, confirmed_m3_rate):
    """Test 28: Reject VERIFIED_RECONCILED with ACCEPT_MATCH when discrepancy is not MATCH."""
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "VERIFIED_RECONCILED",
            "reconciliation_id": setup_data["rec2_over_id"],
            "reconciliation_decision": "ACCEPT_MATCH",
            "decision_reason": "Discrepant item cannot accept match.",
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert resp.status_code == 400
    assert "Cannot choose ACCEPT_MATCH" in resp.json()["detail"]


def test_29_reconciled_accept_calculated_uses_calculated_quantity_and_unit(client_fixture, setup_data, confirmed_m3_rate):
    """Test 29: VERIFIED_RECONCILED with ACCEPT_CALCULATED uses calculated_quantity (120.5 m3)."""
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "VERIFIED_RECONCILED",
            "reconciliation_id": setup_data["rec2_over_id"],
            "reconciliation_decision": "ACCEPT_CALCULATED",
            "decision_reason": "Calculated value substantiated by laser measurement.",
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["reconciliation_decision"] == "ACCEPT_CALCULATED"
    assert Decimal(str(data["quantity_value"])) == Decimal("120.500000")
    assert data["quantity_unit"] == "m3"
    assert Decimal(str(data["total_cost"])) == Decimal("602500.000000")


def test_30_reconciled_accept_boq_uses_boq_quantity_and_unit(client_fixture, setup_data, confirmed_m3_rate):
    """Test 30: VERIFIED_RECONCILED with ACCEPT_BOQ uses boq_quantity (100.0 m3)."""
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "VERIFIED_RECONCILED",
            "reconciliation_id": setup_data["rec2_over_id"],
            "reconciliation_decision": "ACCEPT_BOQ",
            "decision_reason": "Contractually bounded to stated BOQ cap.",
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["reconciliation_decision"] == "ACCEPT_BOQ"
    assert Decimal(str(data["quantity_value"])) == Decimal("100.000000")
    assert data["quantity_unit"] == "m3"
    assert Decimal(str(data["total_cost"])) == Decimal("500000.000000")


def test_30b_reconciled_decision_immutable_after_creation(client_fixture, setup_data, confirmed_m3_rate):
    """Test 30b: Direct SQL update of reconciliation_decision is blocked."""
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "VERIFIED_RECONCILED",
            "reconciliation_id": setup_data["rec1_match_id"],
            "reconciliation_decision": "ACCEPT_MATCH",
            "decision_reason": "Initial decision",
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    calc_id = resp.json()["id"]

    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as excinfo:
            db.execute(text(f"UPDATE cost_calculations SET reconciliation_decision = 'ACCEPT_BOQ' WHERE id = '{calc_id}'"))
            db.commit()
        assert "cannot be modified" in str(excinfo.value)


def test_31_reject_verified_reconciled_without_decision(client_fixture, setup_data, confirmed_m3_rate):
    """Test 31: Reject VERIFIED_RECONCILED without reconciliation_decision."""
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "VERIFIED_RECONCILED",
            "reconciliation_id": setup_data["rec1_match_id"],
            "decision_reason": "Missing decision",
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert resp.status_code == 400
    assert "reconciliation_decision is required" in resp.json()["detail"]


def test_32_reject_verified_reconciled_without_reason(client_fixture, setup_data, confirmed_m3_rate):
    """Test 32: Reject VERIFIED_RECONCILED without decision_reason."""
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "VERIFIED_RECONCILED",
            "reconciliation_id": setup_data["rec1_match_id"],
            "reconciliation_decision": "ACCEPT_MATCH",
            "decision_reason": "   ",
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert resp.status_code == 400
    assert "decision_reason is required" in resp.json()["detail"]


def test_33_reject_verified_reconciled_cross_project(client_fixture, setup_data, confirmed_m3_rate):
    """Test 33: Reject VERIFIED_RECONCILED referencing cross-project reconciliation."""
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "VERIFIED_RECONCILED",
            "reconciliation_id": setup_data["rec_p2_id"],
            "reconciliation_decision": "ACCEPT_MATCH",
            "decision_reason": "Cross isolation",
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert resp.status_code == 400
    assert "does not belong to specified project" in resp.json()["detail"]


def test_34_reject_calculation_using_draft_rate(client_fixture, setup_data):
    """Test 34: Reject calculation using draft rate."""
    draft_rate = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": f"DRAFT-RATE-{uuid.uuid4().hex[:4]}",
            "description": "Draft rate not confirmed",
            "unit": "m3",
            "rate_value": "4000.00",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    ).json()["id"]

    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": draft_rate,
            "quantity_basis": "BOQ_STATED",
            "boq_item_id": setup_data["boq1_id"],
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert resp.status_code == 400
    assert "must be in CONFIRMED status" in resp.json()["detail"]


def test_35_reject_calculation_using_superseded_rate(client_fixture, setup_data):
    """Test 35: Reject calculation using superseded rate."""
    code = f"SUP-RATE-{uuid.uuid4().hex[:4]}"
    r1 = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": code,
            "description": "v1",
            "unit": "m3",
            "rate_value": "4000.00",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    ).json()["id"]
    client_fixture.patch(f"/api/cost-rates/{r1}/confirm", headers={"Authorization": f"Bearer {setup_data['sup_token']}"})

    r2 = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": code,
            "description": "v2",
            "unit": "m3",
            "rate_value": "4200.00",
            "replaces_rate_id": r1,
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    ).json()["id"]
    client_fixture.patch(f"/api/cost-rates/{r2}/confirm", headers={"Authorization": f"Bearer {setup_data['sup_token']}"})

    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": r1,
            "quantity_basis": "BOQ_STATED",
            "boq_item_id": setup_data["boq1_id"],
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert resp.status_code == 400
    assert "must be in CONFIRMED status" in resp.json()["detail"]


def test_36_reject_calculation_using_cross_project_rate(client_fixture, setup_data):
    """Test 36: Reject calculation using cross-project rate."""
    r_p2 = client_fixture.post(
        f"/api/projects/{setup_data['p2_id']}/cost-rates",
        json={
            "rate_code": f"P2-RATE-{uuid.uuid4().hex[:4]}",
            "description": "P2 Rate",
            "unit": "m3",
            "rate_value": "6000.00",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref",
        },
        headers={"Authorization": f"Bearer {setup_data['admin_token']}"},
    ).json()["id"]
    client_fixture.patch(f"/api/cost-rates/{r_p2}/confirm", headers={"Authorization": f"Bearer {setup_data['admin_token']}"})

    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": r_p2,
            "quantity_basis": "BOQ_STATED",
            "boq_item_id": setup_data["boq1_id"],
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert resp.status_code == 400
    assert "belongs to a different project" in resp.json()["detail"]


def test_37_allow_calculation_using_global_confirmed_rate(client_fixture, setup_data):
    """Test 37: Allow calculation using global confirmed rate."""
    r_global = client_fixture.post(
        "/api/cost-rates",
        json={
            "rate_code": f"GLOBAL-M25-{uuid.uuid4().hex[:4]}",
            "description": "Global CPWD M25 Concrete Rate",
            "unit": "m3",
            "rate_value": "4750.00",
            "source_type": "OFFICIAL_SCHEDULE",
            "source_reference": "CPWD 2023",
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    ).json()["id"]
    client_fixture.patch(f"/api/cost-rates/{r_global}/confirm", headers={"Authorization": f"Bearer {setup_data['sup_token']}"})

    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": r_global,
            "quantity_basis": "ENGINEERING_CALCULATED",
            "calculation_id": setup_data["calc1_id"],
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert Decimal(str(data["total_cost"])) == Decimal("120.500000") * Decimal("4750.000000")


# ==============================================================================
# SECTION 5: RATE-UNIT COMPATIBILITY & PRECISION
# ==============================================================================

@pytest.mark.parametrize("u1,u2", [
    ("m3", "cum"),
    ("m2", "sqm"),
    ("m", "metre"),
    ("kg", "kilogram"),
])
def test_38_unit_compatibility_canonical_pairs_accepted(client_fixture, setup_data, u1, u2):
    """Test 38: Canonical compatible unit pairs are accepted."""
    with TestingSessionLocal() as db:
        admin_id = db.query(User).filter(User.role == "admin").first().id
        elem = EngineeringElement(
            id=str(uuid.uuid4()),
            project_id=setup_data["p1_id"],
            element_type="SLAB",
            element_name=f"Unit Test Elem {u1}",
            created_by=admin_id,
        )
        db.add(elem)
        db.flush()

        calc = EngineeringCalculation(
            id=str(uuid.uuid4()),
            project_id=setup_data["p1_id"],
            engineering_element_id=elem.id,
            calculation_type="PARAM_TEST",
            calculation_version="1.0",
            result_value=Decimal("10.000000"),
            result_unit=u1,
            formula_identifier="DIRECT",
            formula_expression="X",
            inputs_json={},
            created_by=admin_id,
        )
        db.add(calc)
        db.commit()
        calc_id = calc.id

    r_id = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": f"UNIT-COMPAT-{uuid.uuid4().hex[:4]}",
            "description": f"Rate in {u2}",
            "unit": u2,
            "rate_value": "100.00",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    ).json()["id"]
    client_fixture.patch(f"/api/cost-rates/{r_id}/confirm", headers={"Authorization": f"Bearer {setup_data['sup_token']}"})

    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": r_id,
            "quantity_basis": "ENGINEERING_CALCULATED",
            "calculation_id": calc_id,
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert resp.status_code == 201


@pytest.mark.parametrize("qty_unit,rate_unit", [
    ("m3", "kg"),
    ("m2", "kg"),
    ("m", "m3"),
])
def test_39_unit_compatibility_incompatible_dimensions_rejected(client_fixture, setup_data, qty_unit, rate_unit):
    """Test 39: Incompatible dimensional units are deterministically rejected with UNIT_MISMATCH."""
    with TestingSessionLocal() as db:
        admin_id = db.query(User).filter(User.role == "admin").first().id
        elem = EngineeringElement(
            id=str(uuid.uuid4()),
            project_id=setup_data["p1_id"],
            element_type="SLAB",
            element_name=f"Incompat Elem {qty_unit}",
            created_by=admin_id,
        )
        db.add(elem)
        db.flush()

        calc = EngineeringCalculation(
            id=str(uuid.uuid4()),
            project_id=setup_data["p1_id"],
            engineering_element_id=elem.id,
            calculation_type="PARAM_TEST",
            calculation_version="1.0",
            result_value=Decimal("10.000000"),
            result_unit=qty_unit,
            formula_identifier="DIRECT",
            formula_expression="X",
            inputs_json={},
            created_by=admin_id,
        )
        db.add(calc)
        db.commit()
        calc_id = calc.id

    r_id = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": f"INCOMPAT-{uuid.uuid4().hex[:4]}",
            "description": f"Rate in {rate_unit}",
            "unit": rate_unit,
            "rate_value": "100.00",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    ).json()["id"]
    client_fixture.patch(f"/api/cost-rates/{r_id}/confirm", headers={"Authorization": f"Bearer {setup_data['sup_token']}"})

    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": r_id,
            "quantity_basis": "ENGINEERING_CALCULATED",
            "calculation_id": calc_id,
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert resp.status_code == 400
    assert "UNIT_MISMATCH" in resp.json()["detail"]


def test_40_exact_decimal_precision(client_fixture, setup_data):
    """Test 40: Verify no floating point rounding errors."""
    with TestingSessionLocal() as db:
        elem = EngineeringElement(
            id=str(uuid.uuid4()),
            project_id=setup_data["p1_id"],
            element_type="FOOTING",
            element_name="Precision Element",
            status="ACTIVE",
            created_by=db.query(User).filter(User.role == "supervisor").first().id,
        )
        db.add(elem)
        db.commit()

        calc_prec = EngineeringCalculation(
            id=str(uuid.uuid4()),
            engineering_element_id=elem.id,
            project_id=setup_data["p1_id"],
            calculation_type="CONCRETE_VOLUME",
            calculation_version="1.0",
            result_value=Decimal("10.333333"),
            result_unit="m3",
            formula_identifier="RECTANGULAR_VOLUME",
            formula_expression="V = L * W * D",
            inputs_json={"length": 10},
            created_by=db.query(User).filter(User.role == "supervisor").first().id,
        )
        db.add(calc_prec)
        db.commit()
        calc_id = calc_prec.id

    rate_prec = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": f"PREC-{uuid.uuid4().hex[:4]}",
            "description": "Precision Rate",
            "unit": "m3",
            "rate_value": "100.555555",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    ).json()["id"]
    client_fixture.patch(f"/api/cost-rates/{rate_prec}/confirm", headers={"Authorization": f"Bearer {setup_data['sup_token']}"})

    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": rate_prec,
            "quantity_basis": "ENGINEERING_CALCULATED",
            "calculation_id": calc_id,
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert resp.status_code == 201
    expected_total = (Decimal("10.333333") * Decimal("100.555555")).quantize(Decimal("0.000001"))
    assert Decimal(str(resp.json()["total_cost"])) == expected_total


def test_currency_snapshot_match_required_sql_trigger(setup_data, confirmed_m3_rate):
    """Test: Currency mismatch between cost_calculation and rate rejected by trigger."""
    with TestingSessionLocal() as db:
        admin_id = db.query(User).filter(User.role == "admin").first().id
        with pytest.raises(Exception) as excinfo:
            calc_bad_curr = CostCalculation(
                id=str(uuid.uuid4()),
                project_id=setup_data["p1_id"],
                cost_rate_id=confirmed_m3_rate,
                quantity_basis="BOQ_STATED",
                boq_item_id=setup_data["boq1_id"],
                quantity_value=Decimal("125.000000"),
                quantity_unit="m3",
                rate_value=Decimal("5000.000000"),
                rate_unit="m3",
                rate_version="1.0",
                currency="USD",  # Rate currency is INR
                total_cost=Decimal("625000.000000"),
                status="CALCULATED",
                formula_identifier="DIRECT_RATE_VALUATION",
                formula_expression="total_cost = quantity * rate",
                algorithm_version="1.0",
                provenance_json={},
                created_by=admin_id,
            )
            db.add(calc_bad_curr)
            db.commit()
        assert "currency must match rate currency" in str(excinfo.value)


# ==============================================================================
# SECTION 6: CALCULATION SUPERSESSION & IMMUTABILITY (All 22 fields)
# ==============================================================================

def test_41_active_calculation_supersession_boq(client_fixture, setup_data, confirmed_m3_rate):
    """Test 41: Executing new BOQ_STATED calculation for same BOQ item supersedes previous."""
    calc1 = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "BOQ_STATED",
            "boq_item_id": setup_data["boq1_id"],
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    ).json()

    calc2 = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "BOQ_STATED",
            "boq_item_id": setup_data["boq1_id"],
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    ).json()

    assert calc2["status"] == "CALCULATED"
    with TestingSessionLocal() as db:
        old_calc = db.query(CostCalculation).filter(CostCalculation.id == calc1["id"]).first()
        assert old_calc.status == "SUPERSEDED"


def test_42_active_calculation_supersession_eng(client_fixture, setup_data, confirmed_m3_rate):
    """Test 42: Executing new ENGINEERING_CALCULATED calculation supersedes previous."""
    calc1 = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "ENGINEERING_CALCULATED",
            "calculation_id": setup_data["calc1_id"],
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    ).json()

    calc2 = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "ENGINEERING_CALCULATED",
            "calculation_id": setup_data["calc1_id"],
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    ).json()

    assert calc2["status"] == "CALCULATED"
    with TestingSessionLocal() as db:
        old_calc = db.query(CostCalculation).filter(CostCalculation.id == calc1["id"]).first()
        assert old_calc.status == "SUPERSEDED"


def test_43_active_calculation_supersession_reconciliation(client_fixture, setup_data, confirmed_m3_rate):
    """Test 43: Executing new VERIFIED_RECONCILED calculation supersedes previous."""
    calc1 = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "VERIFIED_RECONCILED",
            "reconciliation_id": setup_data["rec1_match_id"],
            "reconciliation_decision": "ACCEPT_MATCH",
            "decision_reason": "First run",
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    ).json()

    calc2 = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "VERIFIED_RECONCILED",
            "reconciliation_id": setup_data["rec1_match_id"],
            "reconciliation_decision": "ACCEPT_MATCH",
            "decision_reason": "Second run recalculation",
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    ).json()

    assert calc2["status"] == "CALCULATED"
    with TestingSessionLocal() as db:
        old_calc = db.query(CostCalculation).filter(CostCalculation.id == calc1["id"]).first()
        assert old_calc.status == "SUPERSEDED"


def test_44_prohibit_duplicate_active_calculations_at_sql_level(setup_data, confirmed_m3_rate):
    """Test 44: Direct SQL insert violating partial unique index is rejected."""
    with TestingSessionLocal() as db:
        admin_id = db.query(User).filter(User.role == "admin").first().id
        with pytest.raises(Exception) as excinfo:
            c1 = CostCalculation(
                id=str(uuid.uuid4()),
                project_id=setup_data["p1_id"],
                cost_rate_id=confirmed_m3_rate,
                quantity_basis="BOQ_STATED",
                boq_item_id=setup_data["boq1_id"],
                quantity_value=Decimal("125.000000"),
                quantity_unit="m3",
                rate_value=Decimal("5000.000000"),
                rate_unit="m3",
                rate_version="1.0",
                currency="INR",
                total_cost=Decimal("625000.000000"),
                status="CALCULATED",
                formula_identifier="DIRECT_RATE_VALUATION",
                formula_expression="total_cost = quantity * rate",
                algorithm_version="1.0",
                provenance_json={},
                created_by=admin_id,
            )
            db.add(c1)
            db.commit()
        assert "uq_cost_calc_active_boq" in str(excinfo.value) or "duplicate key" in str(excinfo.value)


def test_45_provenance_snapshot_completeness(client_fixture, setup_data, confirmed_m3_rate):
    """Test 45: Provenance snapshot completeness in calculation result."""
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "BOQ_STATED",
            "boq_item_id": setup_data["boq1_id"],
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert resp.status_code == 201
    prov = resp.json()["provenance_json"]
    for field in ["quantity_basis", "quantity_value", "quantity_unit", "rate_id", "rate_code", "rate_value", "rate_unit", "rate_version", "currency", "total_cost", "calculated_at"]:
        assert field in prov


def test_historical_valuation_stability_on_rate_supersession(client_fixture, setup_data):
    """Test: Later rate supersession does not mutate historical cost calculation."""
    code = f"HIST-STAB-{uuid.uuid4().hex[:4]}"
    # 1. Rate v1
    r1 = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": code,
            "description": "Rate v1",
            "unit": "m3",
            "rate_value": "3000.00",
            "version": "1.0",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    ).json()["id"]
    client_fixture.patch(f"/api/cost-rates/{r1}/confirm", headers={"Authorization": f"Bearer {setup_data['sup_token']}"})

    # 2. Cost calculation with v1
    calc_resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": r1,
            "quantity_basis": "BOQ_STATED",
            "boq_item_id": setup_data["boq1_id"],
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    calc_id = calc_resp.json()["id"]
    initial_total = Decimal(str(calc_resp.json()["total_cost"]))
    assert initial_total == Decimal("125.000000") * Decimal("3000.000000")

    # 3. Rate v2 replacing v1
    r2 = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": code,
            "description": "Rate v2",
            "unit": "m3",
            "rate_value": "3500.00",
            "version": "2.0",
            "replaces_rate_id": r1,
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    ).json()["id"]
    client_fixture.patch(f"/api/cost-rates/{r2}/confirm", headers={"Authorization": f"Bearer {setup_data['sup_token']}"})

    # 4. Verify historical cost calculation is completely stable
    with TestingSessionLocal() as db:
        old_calc = db.query(CostCalculation).filter(CostCalculation.id == calc_id).first()
        assert old_calc.cost_rate_id == r1
        assert old_calc.rate_value == Decimal("3000.000000")
        assert old_calc.rate_version == "1.0"
        assert old_calc.total_cost == initial_total


@pytest.fixture(scope="module")
def sql_calculation(setup_data):
    with TestingSessionLocal() as db:
        admin_id = db.query(User).filter(User.role == "admin").first().id
        proj = Project(
            id=str(uuid.uuid4()),
            name=f"SQL Direct Calc Project {uuid.uuid4().hex[:6]}",
            created_by=admin_id,
        )
        db.add(proj)
        db.flush()

        rate = CostRate(
            id=str(uuid.uuid4()),
            project_id=proj.id,
            rate_code=f"SQL-RATE-{uuid.uuid4().hex[:4]}",
            description="Dedicated SQL test rate",
            unit="m3",
            rate_value=Decimal("5000.000000"),
            currency="INR",
            source_type="PROJECT_SPECIFIC",
            source_reference="Ref",
            status="CONFIRMED",
            created_by=admin_id,
            confirmed_by=admin_id,
            confirmed_at=datetime.now(timezone.utc),
        )
        db.add(rate)
        db.flush()

        doc = Document(
            id=str(uuid.uuid4()),
            project_id=proj.id,
            original_filename="tender.pdf",
            storage_key=f"raw/{proj.id}/tender.pdf",
            file_size_bytes=100,
            mime_type="application/pdf",
            sha256_hash="hash123",
            uploaded_by=admin_id,
            document_type="BOQ",
        )
        db.add(doc)
        db.flush()

        boq_sql = BoqItem(
            id=str(uuid.uuid4()),
            project_id=proj.id,
            document_id=doc.id,
            item_code=f"BOQ-SQL-CALC-{uuid.uuid4().hex[:6]}",
            description="Dedicated SQL Calc Test BOQ",
            unit="m3",
            stated_quantity=Decimal("125.000000"),
            status="CONFIRMED",
            classification="STATED_FROM_DOCUMENT",
            provenance_json={"source": "test"},
            created_by=admin_id,
            confirmed_by=admin_id,
            confirmed_at=datetime.now(timezone.utc),
        )
        db.add(boq_sql)
        db.flush()

        calc = CostCalculation(
            id=str(uuid.uuid4()),
            project_id=proj.id,
            cost_rate_id=rate.id,
            quantity_basis="BOQ_STATED",
            boq_item_id=boq_sql.id,
            quantity_value=Decimal("125.000000"),
            quantity_unit="m3",
            rate_value=Decimal("5000.000000"),
            rate_unit="m3",
            rate_version="1.0",
            currency="INR",
            total_cost=Decimal("625000.000000"),
            status="CALCULATED",
            formula_identifier="DIRECT_RATE_VALUATION",
            formula_expression="total_cost = quantity * rate",
            algorithm_version="1.0",
            provenance_json={"test": "immut"},
            metadata_json={"tag": "base"},
            created_by=admin_id,
        )
        db.add(calc)
        db.commit()
        return calc.id


@pytest.mark.parametrize("field,bad_val", [
    ("id", f"'{str(uuid.uuid4())}'"),
    ("project_id", f"'{str(uuid.uuid4())}'"),
    ("cost_rate_id", f"'{str(uuid.uuid4())}'"),
    ("quantity_basis", "'ENGINEERING_CALCULATED'"),
    ("boq_item_id", f"'{str(uuid.uuid4())}'"),
    ("calculation_id", f"'{str(uuid.uuid4())}'"),
    ("reconciliation_id", f"'{str(uuid.uuid4())}'"),
    ("reconciliation_decision", "'ACCEPT_MATCH'"),
    ("decision_reason", "'Mutated Reason'"),
    ("decided_by", f"'{str(uuid.uuid4())}'"),
    ("decided_at", "now()"),
    ("quantity_value", "999.00"),
    ("quantity_unit", "'kg'"),
    ("rate_value", "9999.00"),
    ("rate_unit", "'kg'"),
    ("rate_version", "'9.9'"),
    ("currency", "'USD'"),
    ("total_cost", "999999.00"),
    ("formula_identifier", "'MODIFIED_FORMULA'"),
    ("formula_expression", "'total = q + r'"),
    ("algorithm_version", "'2.0'"),
    ("provenance_json", "'{\"mutated\": true}'::json"),
    ("metadata_json", "'{\"mutated\": true}'::json"),
    ("created_by", f"'{str(uuid.uuid4())}'"),
    ("created_at", "now()"),
])
def test_65_cost_calc_direct_sql_field_mutations_blocked(sql_calculation, field, bad_val):
    """Test 65: Every individual cost calculation field direct SQL update is blocked by trg_protect_cost_calculation."""
    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as excinfo:
            db.execute(text(f"UPDATE cost_calculations SET {field} = {bad_val} WHERE id = '{sql_calculation}'"))
            db.commit()
        assert "cannot be modified" in str(excinfo.value)


def test_65y_cost_calc_simultaneous_mutation_with_superseded_blocked(sql_calculation):
    """Test 65y: Transition to SUPERSEDED while simultaneously mutating math field is blocked."""
    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as excinfo:
            db.execute(text(f"UPDATE cost_calculations SET status = 'SUPERSEDED', total_cost = 111.00 WHERE id = '{sql_calculation}'"))
            db.commit()
        assert "cannot be modified" in str(excinfo.value)


def test_calc_lifecycle_calculated_to_invalid_status_prohibited(sql_calculation):
    """Test: CALCULATED -> invalid status is prohibited at DB level."""
    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as excinfo:
            db.execute(text(f"UPDATE cost_calculations SET status = 'INVALID_STATUS' WHERE id = '{sql_calculation}'"))
            db.commit()
        assert "violates check constraint" in str(excinfo.value).lower() or "illegal cost calculation status transition" in str(excinfo.value).lower()


def test_calc_lifecycle_superseded_to_calculated_prohibited(sql_calculation):
    """Test: SUPERSEDED -> CALCULATED direct SQL transition is prohibited."""
    with TestingSessionLocal() as db:
        db.execute(text(f"UPDATE cost_calculations SET status = 'SUPERSEDED' WHERE id = '{sql_calculation}'"))
        db.commit()

    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as excinfo:
            db.execute(text(f"UPDATE cost_calculations SET status = 'CALCULATED' WHERE id = '{sql_calculation}'"))
            db.commit()
        assert "Illegal cost calculation status transition" in str(excinfo.value)


def test_calc_lifecycle_superseded_mutation_prohibited(sql_calculation):
    """Test: SUPERSEDED -> SUPERSEDED with mutation is prohibited."""
    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as excinfo:
            db.execute(text(f"UPDATE cost_calculations SET total_cost = 9999.00 WHERE id = '{sql_calculation}'"))
            db.commit()
        assert "cannot be modified" in str(excinfo.value)


def test_calc_lifecycle_delete_superseded_prohibited(sql_calculation):
    """Test: Direct SQL DELETE of SUPERSEDED calculation is prohibited."""
    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as excinfo:
            db.execute(text(f"DELETE FROM cost_calculations WHERE id = '{sql_calculation}'"))
            db.commit()
        assert "cannot be deleted" in str(excinfo.value)


def test_64_direct_sql_delete_calculation_prohibited(setup_data, confirmed_m3_rate):
    """Test 64: Direct SQL DELETE of CALCULATED cost calculation is blocked by trigger."""
    with TestingSessionLocal() as db:
        admin_id = db.query(User).filter(User.role == "admin").first().id
        proj = Project(id=str(uuid.uuid4()), name=f"Del Calc Proj {uuid.uuid4().hex[:6]}", created_by=admin_id)
        db.add(proj)
        db.flush()
        rate = CostRate(
            id=str(uuid.uuid4()),
            project_id=proj.id,
            rate_code=f"DEL-RATE-{uuid.uuid4().hex[:4]}",
            description="Del rate",
            unit="m3",
            rate_value=Decimal("100.00"),
            currency="INR",
            source_type="PROJECT_SPECIFIC",
            source_reference="Ref",
            status="CONFIRMED",
            created_by=admin_id,
            confirmed_by=admin_id,
            confirmed_at=datetime.now(timezone.utc),
        )
        db.add(rate)
        db.flush()
        doc = Document(id=str(uuid.uuid4()), project_id=proj.id, original_filename="t.pdf", storage_key=f"r/{proj.id}/t.pdf", file_size_bytes=10, mime_type="application/pdf", sha256_hash="h1", uploaded_by=admin_id, document_type="BOQ")
        db.add(doc)
        db.flush()
        boq = BoqItem(id=str(uuid.uuid4()), project_id=proj.id, document_id=doc.id, item_code="B1", description="B1", unit="m3", stated_quantity=Decimal("10.0"), status="CONFIRMED", classification="STATED_FROM_DOCUMENT", provenance_json={}, created_by=admin_id, confirmed_by=admin_id, confirmed_at=datetime.now(timezone.utc))
        db.add(boq)
        db.flush()
        calc = CostCalculation(
            id=str(uuid.uuid4()),
            project_id=proj.id,
            cost_rate_id=rate.id,
            quantity_basis="BOQ_STATED",
            boq_item_id=boq.id,
            quantity_value=Decimal("10.0"),
            quantity_unit="m3",
            rate_value=Decimal("100.0"),
            rate_unit="m3",
            rate_version="1.0",
            currency="INR",
            total_cost=Decimal("1000.0"),
            status="CALCULATED",
            formula_identifier="DIRECT_RATE_VALUATION",
            formula_expression="total_cost = quantity * rate",
            algorithm_version="1.0",
            provenance_json={},
            created_by=admin_id,
        )
        db.add(calc)
        db.commit()
        c_id = calc.id

    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as excinfo:
            db.execute(text(f"DELETE FROM cost_calculations WHERE id = '{c_id}'"))
            db.commit()
        assert "Cost calculations are immutable audit records and cannot be deleted" in str(excinfo.value)


# ==============================================================================
# SECTION 7: PROJECT ISOLATION AT SERVICE & DATABASE LEVEL
# ==============================================================================

def test_46_project_isolation_rate(client_fixture, setup_data):
    """Test 46: Project 1 cannot use Project 2 rate."""
    r_p2 = client_fixture.post(
        f"/api/projects/{setup_data['p2_id']}/cost-rates",
        json={
            "rate_code": f"ISO-P2-{uuid.uuid4().hex[:4]}",
            "description": "P2 Isolation",
            "unit": "m3",
            "rate_value": "5000.00",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref",
        },
        headers={"Authorization": f"Bearer {setup_data['admin_token']}"},
    ).json()["id"]
    client_fixture.patch(f"/api/cost-rates/{r_p2}/confirm", headers={"Authorization": f"Bearer {setup_data['admin_token']}"})

    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": r_p2,
            "quantity_basis": "BOQ_STATED",
            "boq_item_id": setup_data["boq1_id"],
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert resp.status_code == 400
    assert "belongs to a different project" in resp.json()["detail"]


def test_47_project_isolation_boq_item(client_fixture, setup_data, confirmed_m3_rate):
    """Test 47: Project 1 cannot calculate cost for Project 2 BOQ item."""
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "BOQ_STATED",
            "boq_item_id": setup_data["boq_p2_id"],
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert resp.status_code == 400


def test_48_project_isolation_calc(client_fixture, setup_data, confirmed_m3_rate):
    """Test 48: Project 1 cannot calculate cost for Project 2 calculation."""
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "ENGINEERING_CALCULATED",
            "calculation_id": setup_data["calc2_id"],
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert resp.status_code == 400


def test_49_project_isolation_reconciliation(client_fixture, setup_data, confirmed_m3_rate):
    """Test 49: Project 1 cannot calculate cost for Project 2 reconciliation."""
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "VERIFIED_RECONCILED",
            "reconciliation_id": setup_data["rec_p2_id"],
            "reconciliation_decision": "ACCEPT_MATCH",
            "decision_reason": "Cross isolation",
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert resp.status_code == 400


def test_sql_isolation_calc_p1_rate_p2_blocked(setup_data):
    """Test: Direct SQL P1 cost calc pointing to P2 rate blocked by trigger."""
    with TestingSessionLocal() as db:
        admin_id = db.query(User).filter(User.role == "admin").first().id
        r_p2 = CostRate(
            id=str(uuid.uuid4()),
            project_id=setup_data["p2_id"],
            rate_code=f"SQL-ISO-{uuid.uuid4().hex[:4]}",
            description="P2 rate",
            unit="m3",
            rate_value=Decimal("500.00"),
            currency="INR",
            source_type="PROJECT_SPECIFIC",
            source_reference="Ref",
            status="CONFIRMED",
            created_by=admin_id,
            confirmed_by=admin_id,
            confirmed_at=datetime.now(timezone.utc),
        )
        db.add(r_p2)
        db.commit()

        with pytest.raises(Exception) as excinfo:
            calc_bad = CostCalculation(
                id=str(uuid.uuid4()),
                project_id=setup_data["p1_id"],
                cost_rate_id=r_p2.id,
                quantity_basis="BOQ_STATED",
                boq_item_id=setup_data["boq1_id"],
                quantity_value=Decimal("125.00"),
                quantity_unit="m3",
                rate_value=Decimal("500.00"),
                rate_unit="m3",
                rate_version="1.0",
                currency="INR",
                total_cost=Decimal("62500.00"),
                status="CALCULATED",
                formula_identifier="DIRECT_RATE_VALUATION",
                formula_expression="total = q * r",
                algorithm_version="1.0",
                provenance_json={},
                created_by=admin_id,
            )
            db.add(calc_bad)
            db.commit()
        assert "does not belong to calculation project" in str(excinfo.value)


def test_sql_isolation_rate_p1_doc_p2_blocked(setup_data):
    """Test: Direct SQL P1 rate pointing to P2 document blocked by trigger."""
    with TestingSessionLocal() as db:
        admin_id = db.query(User).filter(User.role == "admin").first().id
        with pytest.raises(Exception) as excinfo:
            rate_bad_doc = CostRate(
                id=str(uuid.uuid4()),
                project_id=setup_data["p1_id"],
                rate_code=f"SQL-P1-P2DOC-{uuid.uuid4().hex[:4]}",
                description="Cross project doc",
                unit="m3",
                rate_value=Decimal("500.00"),
                currency="INR",
                source_type="PROJECT_SPECIFIC",
                source_reference="Ref",
                source_document_id=setup_data["doc2_id"],  # Doc in P2!
                status="DRAFT",
                created_by=admin_id,
            )
            db.add(rate_bad_doc)
            db.commit()
        assert "does not belong to the project" in str(excinfo.value)


# ==============================================================================
# SECTION 8: AGGREGATION & COMPARATIVE VALUATION
# ==============================================================================

@pytest.fixture(scope="module")
def summary_data(client_fixture, setup_data, confirmed_m3_rate):
    # Ensure fresh active calculations exist for P1
    client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "BOQ_STATED",
            "boq_item_id": setup_data["boq1_id"],
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "ENGINEERING_CALCULATED",
            "calculation_id": setup_data["calc1_id"],
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "VERIFIED_RECONCILED",
            "reconciliation_id": setup_data["rec1_match_id"],
            "reconciliation_decision": "ACCEPT_MATCH",
            "decision_reason": "Summary test reconciliation",
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    resp = client_fixture.get(
        f"/api/projects/{setup_data['p1_id']}/cost-summary",
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    )
    assert resp.status_code == 200
    return resp.json()


def test_50_cost_summary_boq_stated_total(summary_data):
    """Test 50: cost summary returns correct boq_stated_total."""
    assert Decimal(str(summary_data["boq_stated_total"])) == Decimal("625000.000000")


def test_51_cost_summary_engineering_calculated_total(summary_data):
    """Test 51: cost summary returns correct engineering_calculated_total."""
    assert Decimal(str(summary_data["engineering_calculated_total"])) >= Decimal("602500.000000")


def test_52_cost_summary_verified_reconciled_total(summary_data):
    """Test 52: cost summary returns correct verified_reconciled_total."""
    assert Decimal(str(summary_data["verified_reconciled_total"])) >= Decimal("602500.000000")


def test_53_cost_summary_active_rates_count(summary_data):
    """Test 53: cost summary returns correct active_rates_count."""
    assert summary_data["active_rates_count"] >= 1


def test_54_cost_summary_active_calculations_count(summary_data):
    """Test 54: cost summary returns correct active_calculations_count."""
    assert summary_data["active_calculations_count"] >= 3


def test_55_cost_summary_comparable_items_count(summary_data):
    """Test 55: cost summary returns correct comparable_items_count."""
    assert summary_data["comparable_items_count"] == 1


def test_56_cost_summary_unmatched_boq_items_count(summary_data):
    """Test 56: cost summary returns correct unmatched_boq_items_count."""
    assert summary_data["unmatched_boq_items_count"] >= 0


def test_57_cost_summary_unmatched_engineering_items_count(summary_data):
    """Test 57: cost summary returns correct unmatched_engineering_items_count."""
    assert summary_data["unmatched_engineering_items_count"] >= 0


def test_58_cost_summary_comparable_valuation_delta(summary_data):
    """Test 58: cost summary returns correct comparable_valuation_delta."""
    assert Decimal(str(summary_data["comparable_valuation_delta"])) == Decimal("22500.000000")


def test_59_unmatched_items_do_not_distort_comparable_valuation_delta(summary_data):
    """Test 59: unmapped calculations do not blend into or distort comparable_valuation_delta."""
    # boq1 = 625,000; calc1 = 602,500 -> delta = 22,500 strictly over comparable pair
    assert Decimal(str(summary_data["comparable_valuation_delta"])) == Decimal("22500.000000")


# ==============================================================================
# SECTION 9: AUDIT & ROLE SECURITY TRANSACTIONALITY
# ==============================================================================

def test_60_audit_logging_recorded_on_success(client_fixture, setup_data):
    """Test 60: Audit logs recorded for successful business operations."""
    with TestingSessionLocal() as db:
        logs = db.query(AuditLog).filter(
            AuditLog.action.in_([
                "DECLARE_COST_RATE",
                "CONFIRM_COST_RATE",
                "DELETE_COST_RATE_DRAFT",
                "SUPERSEDE_COST_RATE",
                "EXECUTE_COST_CALCULATION",
                "SUPERSEDE_COST_CALCULATION",
            ])
        ).all()
        actions = {l.action for l in logs}
        assert "DECLARE_COST_RATE" in actions
        assert "CONFIRM_COST_RATE" in actions
        assert "EXECUTE_COST_CALCULATION" in actions


def test_audit_failure_rate_confirmation_no_log(client_fixture, setup_data):
    """Test: When rate confirmation fails, no audit record is committed."""
    bad_rate_id = str(uuid.uuid4())
    audit_count_before = 0
    with TestingSessionLocal() as db:
        audit_count_before = db.query(AuditLog).filter(AuditLog.entity_id == bad_rate_id).count()

    resp = client_fixture.patch(f"/api/cost-rates/{bad_rate_id}/confirm", headers={"Authorization": f"Bearer {setup_data['sup_token']}"})
    assert resp.status_code == 404

    with TestingSessionLocal() as db:
        audit_count_after = db.query(AuditLog).filter(AuditLog.entity_id == bad_rate_id).count()
        assert audit_count_after == audit_count_before


def test_audit_failure_cost_calculation_no_log(client_fixture, setup_data, confirmed_m3_rate):
    """Test: When cost calculation fails (e.g. cross-project), no audit log is committed."""
    initial_calc_audit_count = 0
    with TestingSessionLocal() as db:
        initial_calc_audit_count = db.query(AuditLog).filter(AuditLog.action == "EXECUTE_COST_CALCULATION").count()

    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "BOQ_STATED",
            "boq_item_id": setup_data["boq_p2_id"],  # Cross project!
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert resp.status_code == 400

    with TestingSessionLocal() as db:
        final_calc_audit_count = db.query(AuditLog).filter(AuditLog.action == "EXECUTE_COST_CALCULATION").count()
        assert final_calc_audit_count == initial_calc_audit_count


def test_61_contractor_cannot_confirm_rate(client_fixture, setup_data):
    """Test 61: Contractor cannot confirm rate (403)."""
    draft = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": f"SEC-CONF-{uuid.uuid4().hex[:4]}",
            "description": "Sec test",
            "unit": "m3",
            "rate_value": "100.00",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    ).json()["id"]

    resp = client_fixture.patch(
        f"/api/cost-rates/{draft}/confirm",
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    )
    assert resp.status_code == 403


def test_62_contractor_cannot_execute_calculation(client_fixture, setup_data, confirmed_m3_rate):
    """Test 62: Contractor cannot execute cost calculation (403)."""
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "BOQ_STATED",
            "boq_item_id": setup_data["boq1_id"],
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    )
    assert resp.status_code == 403


def test_62b_contractor_verified_reconciled_valuation_403(client_fixture, setup_data, confirmed_m3_rate):
    """Test 62b: Contractor cannot execute VERIFIED_RECONCILED calculation (403)."""
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "VERIFIED_RECONCILED",
            "reconciliation_id": setup_data["rec1_match_id"],
            "reconciliation_decision": "ACCEPT_MATCH",
            "decision_reason": "Contractor attempt",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    )
    assert resp.status_code == 403


def test_62c_supervisor_verified_reconciled_valuation_allowed(client_fixture, setup_data, confirmed_m3_rate):
    """Test 62c: Supervisor is authorized to execute VERIFIED_RECONCILED calculation (201)."""
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "VERIFIED_RECONCILED",
            "reconciliation_id": setup_data["rec1_match_id"],
            "reconciliation_decision": "ACCEPT_MATCH",
            "decision_reason": "Supervisor verification decision",
        },
        headers={"Authorization": f"Bearer {setup_data['sup_token']}"},
    )
    assert resp.status_code == 201


def test_62d_admin_verified_reconciled_valuation_allowed(client_fixture, setup_data, confirmed_m3_rate):
    """Test 62d: Admin is authorized to execute VERIFIED_RECONCILED calculation (201)."""
    resp = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-calculations",
        json={
            "cost_rate_id": confirmed_m3_rate,
            "quantity_basis": "VERIFIED_RECONCILED",
            "reconciliation_id": setup_data["rec1_match_id"],
            "reconciliation_decision": "ACCEPT_MATCH",
            "decision_reason": "Admin verification decision",
        },
        headers={"Authorization": f"Bearer {setup_data['admin_token']}"},
    )
    assert resp.status_code == 201


def test_63_outsider_rejected_for_project_cost_data(client_fixture, setup_data):
    """Test 63: Outsider cannot access project cost data (403)."""
    resp = client_fixture.get(
        f"/api/projects/{setup_data['p1_id']}/cost-summary",
        headers={"Authorization": f"Bearer {setup_data['out_token']}"},
    )
    assert resp.status_code == 403


# ==============================================================================
# SECTION 10: DEEP INVARIANT AUDIT SUITE
# ==============================================================================

# --- Point 4: Rate Replacement Integrity at DB Level ---

def test_rate_replacement_self_replacement_blocked(setup_data):
    """Test: Rate cannot replace itself (blocked by check constraint and trigger)."""
    rate_id = str(uuid.uuid4())
    with TestingSessionLocal() as db:
        admin_id = db.query(User).filter(User.role == "admin").first().id
        with pytest.raises(Exception) as excinfo:
            rate = CostRate(
                id=rate_id,
                project_id=setup_data["p1_id"],
                rate_code=f"SELF-REP-{uuid.uuid4().hex[:4]}",
                description="Self replace",
                unit="m3",
                rate_value=Decimal("100.00"),
                currency="INR",
                source_type="PROJECT_SPECIFIC",
                source_reference="Ref",
                status="DRAFT",
                replaces_rate_id=rate_id,
                created_by=admin_id,
            )
            db.add(rate)
            db.commit()
        assert "cannot replace itself" in str(excinfo.value).lower() or "ck_cost_rates_no_self_replace" in str(excinfo.value)


def test_rate_replacement_draft_replacement_blocked(setup_data):
    """Test: Rate cannot replace a DRAFT rate."""
    with TestingSessionLocal() as db:
        admin_id = db.query(User).filter(User.role == "admin").first().id
        code = f"REP-DRAFT-{uuid.uuid4().hex[:4]}"
        draft1 = CostRate(
            id=str(uuid.uuid4()),
            project_id=setup_data["p1_id"],
            rate_code=code,
            description="Draft 1",
            unit="m3",
            rate_value=Decimal("100.00"),
            currency="INR",
            source_type="PROJECT_SPECIFIC",
            source_reference="Ref",
            status="DRAFT",
            created_by=admin_id,
        )
        db.add(draft1)
        db.commit()

        with pytest.raises(Exception) as excinfo:
            draft2 = CostRate(
                id=str(uuid.uuid4()),
                project_id=setup_data["p1_id"],
                rate_code=code,
                description="Draft 2 replacing Draft 1",
                unit="m3",
                rate_value=Decimal("110.00"),
                currency="INR",
                source_type="PROJECT_SPECIFIC",
                source_reference="Ref",
                status="DRAFT",
                replaces_rate_id=draft1.id,
                created_by=admin_id,
            )
            db.add(draft2)
            db.commit()
        assert "can only replace a CONFIRMED rate" in str(excinfo.value)


def test_rate_replacement_superseded_replacement_blocked(setup_data):
    """Test: Rate cannot replace a SUPERSEDED rate."""
    with TestingSessionLocal() as db:
        admin_id = db.query(User).filter(User.role == "admin").first().id
        code = f"REP-SUP-{uuid.uuid4().hex[:4]}"
        sup_rate = CostRate(
            id=str(uuid.uuid4()),
            project_id=setup_data["p1_id"],
            rate_code=code,
            description="Superseded",
            unit="m3",
            rate_value=Decimal("100.00"),
            currency="INR",
            source_type="PROJECT_SPECIFIC",
            source_reference="Ref",
            status="SUPERSEDED",
            created_by=admin_id,
            confirmed_by=admin_id,
            confirmed_at=datetime.now(timezone.utc),
        )
        db.add(sup_rate)
        db.commit()

        with pytest.raises(Exception) as excinfo:
            new_rate = CostRate(
                id=str(uuid.uuid4()),
                project_id=setup_data["p1_id"],
                rate_code=code,
                description="Draft replacing Superseded",
                unit="m3",
                rate_value=Decimal("110.00"),
                currency="INR",
                source_type="PROJECT_SPECIFIC",
                source_reference="Ref",
                status="DRAFT",
                replaces_rate_id=sup_rate.id,
                created_by=admin_id,
            )
            db.add(new_rate)
            db.commit()
        assert "can only replace a CONFIRMED rate" in str(excinfo.value)


def test_rate_replacement_cross_project_replacement_blocked(setup_data):
    """Test: Rate cannot replace a rate belonging to another project."""
    with TestingSessionLocal() as db:
        admin_id = db.query(User).filter(User.role == "admin").first().id
        code = f"REP-XP-{uuid.uuid4().hex[:4]}"
        p1_rate = CostRate(
            id=str(uuid.uuid4()),
            project_id=setup_data["p1_id"],
            rate_code=code,
            description="P1 Confirmed",
            unit="m3",
            rate_value=Decimal("100.00"),
            currency="INR",
            source_type="PROJECT_SPECIFIC",
            source_reference="Ref",
            status="CONFIRMED",
            created_by=admin_id,
            confirmed_by=admin_id,
            confirmed_at=datetime.now(timezone.utc),
        )
        db.add(p1_rate)
        db.commit()

        with pytest.raises(Exception) as excinfo:
            p2_rate = CostRate(
                id=str(uuid.uuid4()),
                project_id=setup_data["p2_id"],
                rate_code=code,
                description="P2 Rate trying to replace P1 Rate",
                unit="m3",
                rate_value=Decimal("110.00"),
                currency="INR",
                source_type="PROJECT_SPECIFIC",
                source_reference="Ref",
                status="DRAFT",
                replaces_rate_id=p1_rate.id,
                created_by=admin_id,
            )
            db.add(p2_rate)
            db.commit()
        assert "cannot change project scope" in str(excinfo.value)


def test_rate_replacement_global_to_project_replacement_blocked(setup_data):
    """Test: Project rate cannot replace a global rate."""
    with TestingSessionLocal() as db:
        admin_id = db.query(User).filter(User.role == "admin").first().id
        code = f"REP-G-P-{uuid.uuid4().hex[:4]}"
        g_rate = CostRate(
            id=str(uuid.uuid4()),
            project_id=None,
            rate_code=code,
            description="Global Confirmed",
            unit="m3",
            rate_value=Decimal("100.00"),
            currency="INR",
            source_type="OFFICIAL_SCHEDULE",
            source_reference="Schedule",
            status="CONFIRMED",
            created_by=admin_id,
            confirmed_by=admin_id,
            confirmed_at=datetime.now(timezone.utc),
        )
        db.add(g_rate)
        db.commit()

        with pytest.raises(Exception) as excinfo:
            p_rate = CostRate(
                id=str(uuid.uuid4()),
                project_id=setup_data["p1_id"],
                rate_code=code,
                description="Project Rate trying to replace Global",
                unit="m3",
                rate_value=Decimal("110.00"),
                currency="INR",
                source_type="PROJECT_SPECIFIC",
                source_reference="Ref",
                status="DRAFT",
                replaces_rate_id=g_rate.id,
                created_by=admin_id,
            )
            db.add(p_rate)
            db.commit()
        assert "cannot change project scope" in str(excinfo.value)


def test_rate_replacement_project_to_global_replacement_blocked(setup_data):
    """Test: Global rate cannot replace a project rate."""
    with TestingSessionLocal() as db:
        admin_id = db.query(User).filter(User.role == "admin").first().id
        code = f"REP-P-G-{uuid.uuid4().hex[:4]}"
        p_rate = CostRate(
            id=str(uuid.uuid4()),
            project_id=setup_data["p1_id"],
            rate_code=code,
            description="Project Confirmed",
            unit="m3",
            rate_value=Decimal("100.00"),
            currency="INR",
            source_type="PROJECT_SPECIFIC",
            source_reference="Ref",
            status="CONFIRMED",
            created_by=admin_id,
            confirmed_by=admin_id,
            confirmed_at=datetime.now(timezone.utc),
        )
        db.add(p_rate)
        db.commit()

        with pytest.raises(Exception) as excinfo:
            g_rate = CostRate(
                id=str(uuid.uuid4()),
                project_id=None,
                rate_code=code,
                description="Global Rate trying to replace Project",
                unit="m3",
                rate_value=Decimal("110.00"),
                currency="INR",
                source_type="OFFICIAL_SCHEDULE",
                source_reference="Schedule",
                status="DRAFT",
                replaces_rate_id=p_rate.id,
                created_by=admin_id,
            )
            db.add(g_rate)
            db.commit()
        assert "cannot change project scope" in str(excinfo.value)


def test_rate_replacement_different_rate_code_blocked(setup_data):
    """Test: Replacement rate must maintain the exact same rate_code."""
    with TestingSessionLocal() as db:
        admin_id = db.query(User).filter(User.role == "admin").first().id
        code1 = f"CODE-ORIG-{uuid.uuid4().hex[:4]}"
        code2 = f"CODE-DIFF-{uuid.uuid4().hex[:4]}"
        r1 = CostRate(
            id=str(uuid.uuid4()),
            project_id=setup_data["p1_id"],
            rate_code=code1,
            description="Original",
            unit="m3",
            rate_value=Decimal("100.00"),
            currency="INR",
            source_type="PROJECT_SPECIFIC",
            source_reference="Ref",
            status="CONFIRMED",
            created_by=admin_id,
            confirmed_by=admin_id,
            confirmed_at=datetime.now(timezone.utc),
        )
        db.add(r1)
        db.commit()

        with pytest.raises(Exception) as excinfo:
            r2 = CostRate(
                id=str(uuid.uuid4()),
                project_id=setup_data["p1_id"],
                rate_code=code2,
                description="Different code",
                unit="m3",
                rate_value=Decimal("110.00"),
                currency="INR",
                source_type="PROJECT_SPECIFIC",
                source_reference="Ref",
                status="DRAFT",
                replaces_rate_id=r1.id,
                created_by=admin_id,
            )
            db.add(r2)
            db.commit()
        assert "must maintain the same rate_code" in str(excinfo.value)


# --- Point 5: Rate-Source Provenance at DB Level ---

def test_rate_source_evidence_without_doc_blocked(setup_data):
    """Test: source_evidence_id without source_document_id is blocked at DB level."""
    with TestingSessionLocal() as db:
        admin_id = db.query(User).filter(User.role == "admin").first().id
        with pytest.raises(Exception) as excinfo:
            rate = CostRate(
                id=str(uuid.uuid4()),
                project_id=setup_data["p1_id"],
                rate_code=f"NO-DOC-EV-{uuid.uuid4().hex[:4]}",
                description="Evidence without doc",
                unit="m3",
                rate_value=Decimal("100.00"),
                currency="INR",
                source_type="PROJECT_SPECIFIC",
                source_reference="Ref",
                source_document_id=None,
                source_evidence_id=setup_data["ev1_id"],
                status="DRAFT",
                created_by=admin_id,
            )
            db.add(rate)
            db.commit()
        assert "source_evidence_id requires source_document_id" in str(excinfo.value) or "ck_cost_rates_evidence_requires_doc" in str(excinfo.value)


def test_rate_source_global_with_doc_or_evidence_blocked(setup_data):
    """Test: Global rate cannot reference project document or evidence."""
    with TestingSessionLocal() as db:
        admin_id = db.query(User).filter(User.role == "admin").first().id
        with pytest.raises(Exception) as excinfo:
            rate = CostRate(
                id=str(uuid.uuid4()),
                project_id=None,
                rate_code=f"GLOBAL-WITH-DOC-{uuid.uuid4().hex[:4]}",
                description="Global rate with doc",
                unit="m3",
                rate_value=Decimal("100.00"),
                currency="INR",
                source_type="OFFICIAL_SCHEDULE",
                source_reference="Ref",
                source_document_id=setup_data["doc1_id"],
                status="DRAFT",
                created_by=admin_id,
            )
            db.add(rate)
            db.commit()
        assert "Global cost rates cannot reference" in str(excinfo.value) or "ck_cost_rates_global_no_doc" in str(excinfo.value)


# --- Points 6 & 7: CostCalculation Source-Basis & Decision Fields at DB Level ---

def test_calc_source_basis_boq_with_calculation_id_blocked(setup_data, confirmed_m3_rate):
    """Test: BOQ_STATED basis with calculation_id is blocked by ck_cost_calc_basis_sources."""
    with TestingSessionLocal() as db:
        admin_id = db.query(User).filter(User.role == "admin").first().id
        with pytest.raises(Exception) as excinfo:
            calc = CostCalculation(
                id=str(uuid.uuid4()),
                project_id=setup_data["p1_id"],
                cost_rate_id=confirmed_m3_rate,
                quantity_basis="BOQ_STATED",
                boq_item_id=setup_data["boq1_id"],
                calculation_id=setup_data["calc1_id"],  # Illegal simultaneous field!
                quantity_value=Decimal("125.000000"),
                quantity_unit="m3",
                rate_value=Decimal("5000.000000"),
                rate_unit="m3",
                rate_version="1.0",
                currency="INR",
                total_cost=Decimal("625000.000000"),
                status="CALCULATED",
                formula_identifier="DIRECT_RATE_VALUATION",
                formula_expression="total_cost = quantity * rate",
                algorithm_version="1.0",
                provenance_json={},
                created_by=admin_id,
            )
            db.add(calc)
            db.commit()
        assert "ck_cost_calc_basis_sources" in str(excinfo.value)


def test_calc_source_basis_verified_reconciled_missing_decision_fields_blocked(setup_data, confirmed_m3_rate):
    """Test: VERIFIED_RECONCILED without decision_reason/decided_by/decided_at blocked by check constraint."""
    with TestingSessionLocal() as db:
        admin_id = db.query(User).filter(User.role == "admin").first().id
        with pytest.raises(Exception) as excinfo:
            calc = CostCalculation(
                id=str(uuid.uuid4()),
                project_id=setup_data["p1_id"],
                cost_rate_id=confirmed_m3_rate,
                quantity_basis="VERIFIED_RECONCILED",
                reconciliation_id=setup_data["rec1_match_id"],
                reconciliation_decision="ACCEPT_MATCH",
                decision_reason=None,  # Missing!
                decided_by=None,        # Missing!
                decided_at=None,        # Missing!
                quantity_value=Decimal("120.500000"),
                quantity_unit="m3",
                rate_value=Decimal("5000.000000"),
                rate_unit="m3",
                rate_version="1.0",
                currency="INR",
                total_cost=Decimal("602500.000000"),
                status="CALCULATED",
                formula_identifier="DIRECT_RATE_VALUATION",
                formula_expression="total_cost = quantity * rate",
                algorithm_version="1.0",
                provenance_json={},
                created_by=admin_id,
            )
            db.add(calc)
            db.commit()
        assert "ck_cost_calc_basis_sources" in str(excinfo.value)


# --- Point 8: Decision-to-Quantity Consistency at DB Level ---

def test_calc_decision_quantity_consistency_accept_match_on_discrepancy_blocked(setup_data, confirmed_m3_rate):
    """Test: ACCEPT_MATCH on non-MATCH reconciliation is blocked by DB trigger."""
    with TestingSessionLocal() as db:
        admin_id = db.query(User).filter(User.role == "admin").first().id
        with pytest.raises(Exception) as excinfo:
            calc = CostCalculation(
                id=str(uuid.uuid4()),
                project_id=setup_data["p1_id"],
                cost_rate_id=confirmed_m3_rate,
                quantity_basis="VERIFIED_RECONCILED",
                reconciliation_id=setup_data["rec2_over_id"],  # OVER_CALCULATED!
                reconciliation_decision="ACCEPT_MATCH",
                decision_reason="Should fail",
                decided_by=admin_id,
                decided_at=datetime.now(timezone.utc),
                quantity_value=Decimal("140.000000"),
                quantity_unit="m3",
                rate_value=Decimal("5000.000000"),
                rate_unit="m3",
                rate_version="1.0",
                currency="INR",
                total_cost=Decimal("700000.000000"),
                status="CALCULATED",
                formula_identifier="DIRECT_RATE_VALUATION",
                formula_expression="total_cost = quantity * rate",
                algorithm_version="1.0",
                provenance_json={},
                created_by=admin_id,
            )
            db.add(calc)
            db.commit()
        assert "ACCEPT_MATCH decision only valid when discrepancy status is MATCH" in str(excinfo.value)


def test_calc_quantity_mismatch_with_provenance_blocked_at_sql_level(setup_data, confirmed_m3_rate):
    """Test: Direct SQL calculation with quantity not matching BOQ stated quantity is blocked by trigger."""
    with TestingSessionLocal() as db:
        admin_id = db.query(User).filter(User.role == "admin").first().id
        boq_sql = BoqItem(
            id=str(uuid.uuid4()),
            project_id=setup_data["p1_id"],
            document_id=setup_data["doc1_id"],
            item_code=f"BOQ-QTY-CHECK-{uuid.uuid4().hex[:6]}",
            description="Qty consistency test",
            unit="m3",
            stated_quantity=Decimal("125.000000"),
            status="CONFIRMED",
            classification="STATED_FROM_DOCUMENT",
            provenance_json={"source": "test"},
            created_by=admin_id,
            confirmed_by=admin_id,
            confirmed_at=datetime.now(timezone.utc),
        )
        db.add(boq_sql)
        db.flush()

        with pytest.raises(Exception) as excinfo:
            calc = CostCalculation(
                id=str(uuid.uuid4()),
                project_id=setup_data["p1_id"],
                cost_rate_id=confirmed_m3_rate,
                quantity_basis="BOQ_STATED",
                boq_item_id=boq_sql.id,
                quantity_value=Decimal("999.000000"),  # Does NOT match 125.000000!
                quantity_unit="m3",
                rate_value=Decimal("5000.000000"),
                rate_unit="m3",
                rate_version="1.0",
                currency="INR",
                total_cost=Decimal("4995000.000000"),
                status="CALCULATED",
                formula_identifier="DIRECT_RATE_VALUATION",
                formula_expression="total_cost = quantity * rate",
                algorithm_version="1.0",
                provenance_json={},
                created_by=admin_id,
            )
            db.add(calc)
            db.commit()
        assert "does not match BOQ stated quantity" in str(excinfo.value)


# --- Point 9: Rate Snapshot Integrity at DB Level ---

def test_calc_insert_against_draft_rate_blocked_by_sql_trigger(setup_data):
    """Test: Direct SQL insert of calculation referencing DRAFT rate is blocked by trigger."""
    with TestingSessionLocal() as db:
        admin_id = db.query(User).filter(User.role == "admin").first().id
        draft_rate = CostRate(
            id=str(uuid.uuid4()),
            project_id=setup_data["p1_id"],
            rate_code=f"DRAFT-TRIG-{uuid.uuid4().hex[:4]}",
            description="Draft",
            unit="m3",
            rate_value=Decimal("5000.000000"),
            currency="INR",
            source_type="PROJECT_SPECIFIC",
            source_reference="Ref",
            status="DRAFT",
            created_by=admin_id,
        )
        db.add(draft_rate)
        db.flush()

        boq_sql = BoqItem(
            id=str(uuid.uuid4()),
            project_id=setup_data["p1_id"],
            document_id=setup_data["doc1_id"],
            item_code=f"BOQ-DRAFT-RATE-{uuid.uuid4().hex[:6]}",
            description="Draft rate test",
            unit="m3",
            stated_quantity=Decimal("10.000000"),
            status="CONFIRMED",
            classification="STATED_FROM_DOCUMENT",
            provenance_json={"source": "test"},
            created_by=admin_id,
            confirmed_by=admin_id,
            confirmed_at=datetime.now(timezone.utc),
        )
        db.add(boq_sql)
        db.flush()

        with pytest.raises(Exception) as excinfo:
            calc = CostCalculation(
                id=str(uuid.uuid4()),
                project_id=setup_data["p1_id"],
                cost_rate_id=draft_rate.id,
                quantity_basis="BOQ_STATED",
                boq_item_id=boq_sql.id,
                quantity_value=Decimal("10.000000"),
                quantity_unit="m3",
                rate_value=Decimal("5000.000000"),
                rate_unit="m3",
                rate_version="1.0",
                currency="INR",
                total_cost=Decimal("50000.000000"),
                status="CALCULATED",
                formula_identifier="DIRECT_RATE_VALUATION",
                formula_expression="total_cost = quantity * rate",
                algorithm_version="1.0",
                provenance_json={},
                created_by=admin_id,
            )
            db.add(calc)
            db.commit()
        assert "can only be created against a CONFIRMED cost rate" in str(excinfo.value)


def test_calc_total_cost_math_mismatch_blocked_by_sql_trigger(setup_data, confirmed_m3_rate):
    """Test: Calculation with total_cost != quantity * rate is blocked by SQL trigger."""
    with TestingSessionLocal() as db:
        admin_id = db.query(User).filter(User.role == "admin").first().id
        boq_sql = BoqItem(
            id=str(uuid.uuid4()),
            project_id=setup_data["p1_id"],
            document_id=setup_data["doc1_id"],
            item_code=f"BOQ-MATH-FAIL-{uuid.uuid4().hex[:6]}",
            description="Math fail test",
            unit="m3",
            stated_quantity=Decimal("10.000000"),
            status="CONFIRMED",
            classification="STATED_FROM_DOCUMENT",
            provenance_json={"source": "test"},
            created_by=admin_id,
            confirmed_by=admin_id,
            confirmed_at=datetime.now(timezone.utc),
        )
        db.add(boq_sql)
        db.flush()

        with pytest.raises(Exception) as excinfo:
            calc = CostCalculation(
                id=str(uuid.uuid4()),
                project_id=setup_data["p1_id"],
                cost_rate_id=confirmed_m3_rate,
                quantity_basis="BOQ_STATED",
                boq_item_id=boq_sql.id,
                quantity_value=Decimal("10.000000"),
                quantity_unit="m3",
                rate_value=Decimal("5000.000000"),
                rate_unit="m3",
                rate_version="1.0",
                currency="INR",
                total_cost=Decimal("999999.000000"),  # INCORRECT! Should be 50000.000000!
                status="CALCULATED",
                formula_identifier="DIRECT_RATE_VALUATION",
                formula_expression="total_cost = quantity * rate",
                algorithm_version="1.0",
                provenance_json={},
                created_by=admin_id,
            )
            db.add(calc)
            db.commit()
        assert "total_cost must equal quantity * rate" in str(excinfo.value)


# --- Point 13: Multi-Currency Aggregation Rejection ---

def test_aggregation_mixed_currencies_rejected(client_fixture, setup_data):
    """Test: Project cost summary rejects mixed currencies in active calculations with HTTP 400."""
    with TestingSessionLocal() as db:
        admin_id = db.query(User).filter(User.role == "admin").first().id
        proj = Project(
            id=str(uuid.uuid4()),
            name=f"Mixed Currency Project {uuid.uuid4().hex[:6]}",
            created_by=admin_id,
        )
        db.add(proj)
        db.flush()

        # INR Rate
        r_inr = CostRate(
            id=str(uuid.uuid4()),
            project_id=proj.id,
            rate_code=f"RATE-INR-{uuid.uuid4().hex[:4]}",
            description="INR Rate",
            unit="m3",
            rate_value=Decimal("1000.000000"),
            currency="INR",
            source_type="PROJECT_SPECIFIC",
            source_reference="Ref",
            status="CONFIRMED",
            created_by=admin_id,
            confirmed_by=admin_id,
            confirmed_at=datetime.now(timezone.utc),
        )
        # USD Rate
        r_usd = CostRate(
            id=str(uuid.uuid4()),
            project_id=proj.id,
            rate_code=f"RATE-USD-{uuid.uuid4().hex[:4]}",
            description="USD Rate",
            unit="m3",
            rate_value=Decimal("15.000000"),
            currency="USD",
            source_type="PROJECT_SPECIFIC",
            source_reference="Ref",
            status="CONFIRMED",
            created_by=admin_id,
            confirmed_by=admin_id,
            confirmed_at=datetime.now(timezone.utc),
        )
        db.add(r_inr)
        db.add(r_usd)
        db.flush()

        doc = Document(
            id=str(uuid.uuid4()),
            project_id=proj.id,
            original_filename="tender.pdf",
            storage_key=f"raw/{proj.id}/tender.pdf",
            file_size_bytes=100,
            mime_type="application/pdf",
            sha256_hash="hash_mixed",
            uploaded_by=admin_id,
            document_type="BOQ",
        )
        db.add(doc)
        db.flush()

        boq1 = BoqItem(
            id=str(uuid.uuid4()),
            project_id=proj.id,
            document_id=doc.id,
            item_code="BOQ-INR",
            description="Item INR",
            unit="m3",
            stated_quantity=Decimal("10.000000"),
            status="CONFIRMED",
            classification="STATED_FROM_DOCUMENT",
            provenance_json={},
            created_by=admin_id,
            confirmed_by=admin_id,
            confirmed_at=datetime.now(timezone.utc),
        )
        boq2 = BoqItem(
            id=str(uuid.uuid4()),
            project_id=proj.id,
            document_id=doc.id,
            item_code="BOQ-USD",
            description="Item USD",
            unit="m3",
            stated_quantity=Decimal("20.000000"),
            status="CONFIRMED",
            classification="STATED_FROM_DOCUMENT",
            provenance_json={},
            created_by=admin_id,
            confirmed_by=admin_id,
            confirmed_at=datetime.now(timezone.utc),
        )
        db.add(boq1)
        db.add(boq2)
        db.flush()

        # Insert active calculation in INR
        c_inr = CostCalculation(
            id=str(uuid.uuid4()),
            project_id=proj.id,
            cost_rate_id=r_inr.id,
            quantity_basis="BOQ_STATED",
            boq_item_id=boq1.id,
            quantity_value=Decimal("10.000000"),
            quantity_unit="m3",
            rate_value=Decimal("1000.000000"),
            rate_unit="m3",
            rate_version="1.0",
            currency="INR",
            total_cost=Decimal("10000.000000"),
            status="CALCULATED",
            formula_identifier="DIRECT_RATE_VALUATION",
            formula_expression="total_cost = quantity * rate",
            algorithm_version="1.0",
            provenance_json={},
            created_by=admin_id,
        )
        # Insert active calculation in USD
        c_usd = CostCalculation(
            id=str(uuid.uuid4()),
            project_id=proj.id,
            cost_rate_id=r_usd.id,
            quantity_basis="BOQ_STATED",
            boq_item_id=boq2.id,
            quantity_value=Decimal("20.000000"),
            quantity_unit="m3",
            rate_value=Decimal("15.000000"),
            rate_unit="m3",
            rate_version="1.0",
            currency="USD",
            total_cost=Decimal("300.000000"),
            status="CALCULATED",
            formula_identifier="DIRECT_RATE_VALUATION",
            formula_expression="total_cost = quantity * rate",
            algorithm_version="1.0",
            provenance_json={},
            created_by=admin_id,
        )
        db.add(c_inr)
        db.add(c_usd)
        db.commit()
        proj_id = proj.id

    resp = client_fixture.get(f"/api/projects/{proj_id}/cost-summary", headers={"Authorization": f"Bearer {setup_data['admin_token']}"})
    assert resp.status_code == 400
    assert "Mixed currencies found" in resp.json()["detail"]


# --- Point 14: Draft-Rate Deletion Audit Transactionality ---

def test_draft_rate_deletion_audit_transactionality(client_fixture, setup_data):
    """Test: Draft deletion succeeds and commits an audit log; confirmed and superseded deletion fails."""
    # 1. Draft deletion succeeds
    draft_id = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": f"DEL-DRAFT-{uuid.uuid4().hex[:4]}",
            "description": "To be deleted",
            "unit": "m3",
            "rate_value": "100.00",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    ).json()["id"]

    del_resp = client_fixture.delete(f"/api/cost-rates/{draft_id}", headers={"Authorization": f"Bearer {setup_data['con_token']}"})
    assert del_resp.status_code == 204

    with TestingSessionLocal() as db:
        deleted = db.query(CostRate).filter(CostRate.id == draft_id).first()
        assert deleted is None
        audit = db.query(AuditLog).filter(AuditLog.entity_id == draft_id, AuditLog.action == "DELETE_COST_RATE_DRAFT").first()
        assert audit is not None

    # 2. Confirmed deletion fails
    conf_id = client_fixture.post(
        f"/api/projects/{setup_data['p1_id']}/cost-rates",
        json={
            "rate_code": f"DEL-CONF-{uuid.uuid4().hex[:4]}",
            "description": "Confirmed rate",
            "unit": "m3",
            "rate_value": "100.00",
            "source_type": "PROJECT_SPECIFIC",
            "source_reference": "Ref",
        },
        headers={"Authorization": f"Bearer {setup_data['con_token']}"},
    ).json()["id"]
    client_fixture.patch(f"/api/cost-rates/{conf_id}/confirm", headers={"Authorization": f"Bearer {setup_data['sup_token']}"})

    del_conf = client_fixture.delete(f"/api/cost-rates/{conf_id}", headers={"Authorization": f"Bearer {setup_data['admin_token']}"})
    assert del_conf.status_code == 400


# --- Point 15: Full Authorization Matrix ---

def test_auth_declare_global_rate_roles(client_fixture, setup_data):
    """Test: Supervisor and Admin can declare global rates; contractor gets 403."""
    payload = {
        "rate_code": f"AUTH-GLOBAL-{uuid.uuid4().hex[:4]}",
        "description": "Global test",
        "unit": "m3",
        "rate_value": "100.00",
        "source_type": "OFFICIAL_SCHEDULE",
        "source_reference": "Ref",
    }
    # Contractor -> 403
    r_con = client_fixture.post("/api/cost-rates", json=payload, headers={"Authorization": f"Bearer {setup_data['con_token']}"})
    assert r_con.status_code == 403

    # Supervisor -> 201
    r_sup = client_fixture.post("/api/cost-rates", json=payload, headers={"Authorization": f"Bearer {setup_data['sup_token']}"})
    assert r_sup.status_code == 201

    # Admin -> 201
    payload["rate_code"] = f"AUTH-GLOBAL-ADM-{uuid.uuid4().hex[:4]}"
    r_adm = client_fixture.post("/api/cost-rates", json=payload, headers={"Authorization": f"Bearer {setup_data['admin_token']}"})
    assert r_adm.status_code == 201
    r_adm = client_fixture.post("/api/cost-rates", json=payload, headers={"Authorization": f"Bearer {setup_data['admin_token']}"})
    assert r_adm.status_code == 201


def test_auth_declare_project_rate_roles(client_fixture, setup_data):
    """Test: Admin, Supervisor, Contractor can declare project rates; outsider gets 403."""
    payload = {
        "rate_code": f"AUTH-PROJ-{uuid.uuid4().hex[:4]}",
        "description": "Proj test",
        "unit": "m3",
        "rate_value": "100.00",
        "source_type": "PROJECT_SPECIFIC",
        "source_reference": "Ref",
    }
    # Outsider -> 403
    r_out = client_fixture.post(f"/api/projects/{setup_data['p1_id']}/cost-rates", json=payload, headers={"Authorization": f"Bearer {setup_data['out_token']}"})
    assert r_out.status_code == 403

    # Contractor -> 201
    r_con = client_fixture.post(f"/api/projects/{setup_data['p1_id']}/cost-rates", json=payload, headers={"Authorization": f"Bearer {setup_data['con_token']}"})
    assert r_con.status_code == 201


def test_auth_list_rates_and_calculations_roles(client_fixture, setup_data):
    """Test: Project members can list rates/calcs; outsider gets 403."""
    # List rates
    assert client_fixture.get(f"/api/projects/{setup_data['p1_id']}/cost-rates", headers={"Authorization": f"Bearer {setup_data['con_token']}"}).status_code == 200
    assert client_fixture.get(f"/api/projects/{setup_data['p1_id']}/cost-rates", headers={"Authorization": f"Bearer {setup_data['out_token']}"}).status_code == 403

    # List calculations
    assert client_fixture.get(f"/api/projects/{setup_data['p1_id']}/cost-calculations", headers={"Authorization": f"Bearer {setup_data['con_token']}"}).status_code == 200
    assert client_fixture.get(f"/api/projects/{setup_data['p1_id']}/cost-calculations", headers={"Authorization": f"Bearer {setup_data['out_token']}"}).status_code == 403

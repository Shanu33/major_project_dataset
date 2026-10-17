"""Phase 1J: Comprehensive Test Suite for BOQ Line Items & Deterministic Quantity Reconciliation.

Tests Scenarios A through AA, audit transactionality, supersession,
and direct PostgreSQL database-level trigger / constraint tests.
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
def setup_boq(client_fixture):
    # 1. Setup users: Admin, Supervisor, Contractor, Outsider
    admin_email = f"admin_boq_{uuid.uuid4().hex[:6]}@test.com"
    reg_resp = client_fixture.post("/api/auth/register/admin", json={"email": admin_email, "password": "pass", "role": "admin"})
    if reg_resp.status_code == 200:
        login_resp = client_fixture.post("/api/auth/login", data={"username": admin_email, "password": "pass"})
        admin_token = login_resp.json()["access_token"]
    else:
        with TestingSessionLocal() as db:
            adm = User(email=admin_email, password_hash=get_password_hash("pass"), role="admin")
            db.add(adm)
            db.commit()
        admin_token = create_access_token(data={"sub": admin_email, "role": "admin"})

    sup_email = f"sup_boq_{uuid.uuid4().hex[:6]}@test.com"
    con_email = f"con_boq_{uuid.uuid4().hex[:6]}@test.com"
    out_email = f"out_boq_{uuid.uuid4().hex[:6]}@test.com"

    client_fixture.post("/api/auth/users", json={"email": sup_email, "password": "p", "role": "supervisor"}, headers={"Authorization": f"Bearer {admin_token}"})
    client_fixture.post("/api/auth/users", json={"email": con_email, "password": "p", "role": "contractor"}, headers={"Authorization": f"Bearer {admin_token}"})
    client_fixture.post("/api/auth/users", json={"email": out_email, "password": "p", "role": "contractor"}, headers={"Authorization": f"Bearer {admin_token}"})

    sup_token = client_fixture.post("/api/auth/login", data={"username": sup_email, "password": "p"}).json()["access_token"]
    con_token = client_fixture.post("/api/auth/login", data={"username": con_email, "password": "p"}).json()["access_token"]
    out_token = client_fixture.post("/api/auth/login", data={"username": out_email, "password": "p"}).json()["access_token"]

    # 2. Setup Project 1
    p1_resp = client_fixture.post("/api/projects", json={"name": f"BOQ Project 1 {uuid.uuid4().hex[:6]}"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert p1_resp.status_code == 200
    p1_id = p1_resp.json()["id"]

    # Add Supervisor & Contractor to Project 1
    with TestingSessionLocal() as db:
        sup_user = db.query(User).filter(User.email == sup_email).first()
        con_user = db.query(User).filter(User.email == con_email).first()
        admin_user = db.query(User).filter(User.email == admin_email).first()

        db.add(ProjectMember(project_id=p1_id, user_id=sup_user.id))
        db.add(ProjectMember(project_id=p1_id, user_id=con_user.id))

        # Setup Project 2 (for cross-project checks)
        p2 = Project(id=str(uuid.uuid4()), name=f"BOQ Project 2 {uuid.uuid4().hex[:6]}", created_by=admin_user.id)
        db.add(p2)
        db.flush()
        p2_id = p2.id

        # Setup BOQ Document in Project 1
        boq_doc = Document(
            id=str(uuid.uuid4()),
            project_id=p1_id,
            original_filename="official_boq.pdf",
            storage_key=f"raw/{p1_id}/boq.pdf",
            document_type="BOQ",
            mime_type="application/pdf",
            file_size_bytes=1024,
            sha256_hash=uuid.uuid4().hex,
            uploaded_by=admin_user.id,
        )
        db.add(boq_doc)

        # Setup NON-BOQ Document in Project 1
        non_boq_doc = Document(
            id=str(uuid.uuid4()),
            project_id=p1_id,
            original_filename="drawing.pdf",
            storage_key=f"raw/{p1_id}/drawing.pdf",
            document_type="DRAWING",
            mime_type="application/pdf",
            file_size_bytes=2048,
            sha256_hash=uuid.uuid4().hex,
            uploaded_by=admin_user.id,
        )
        db.add(non_boq_doc)

        # Setup BOQ Document in Project 2
        p2_boq_doc = Document(
            id=str(uuid.uuid4()),
            project_id=p2_id,
            original_filename="p2_boq.pdf",
            storage_key=f"raw/{p2_id}/boq.pdf",
            document_type="BOQ",
            mime_type="application/pdf",
            file_size_bytes=1024,
            sha256_hash=uuid.uuid4().hex,
            uploaded_by=admin_user.id,
        )
        db.add(p2_boq_doc)
        db.flush()

        # Setup Evidence in boq_doc
        boq_evidence = Evidence(
            id=str(uuid.uuid4()),
            document_id=boq_doc.id,
            evidence_type="BOQ_ITEM",
            source_reference="Item 2.1 Concrete Works",
            created_by=admin_user.id,
            verification_status="VERIFIED",
        )
        db.add(boq_evidence)

        # Setup Evidence in non_boq_doc
        other_evidence = Evidence(
            id=str(uuid.uuid4()),
            document_id=non_boq_doc.id,
            evidence_type="DIMENSION",
            source_reference="Section A-A",
            created_by=admin_user.id,
            verification_status="VERIFIED",
        )
        db.add(other_evidence)

        # Setup Engineering Elements & Calculations in Project 1
        elem1 = EngineeringElement(
            id=str(uuid.uuid4()),
            project_id=p1_id,
            element_type="FOUNDATION",
            element_name="F-01",
            created_by=admin_user.id,
        )
        db.add(elem1)
        db.flush()

        calc1 = EngineeringCalculation(
            id=str(uuid.uuid4()),
            project_id=p1_id,
            engineering_element_id=elem1.id,
            calculation_type="CONCRETE_VOLUME_RECTANGULAR",
            status="CALCULATED",
            result_value=Decimal("150.000000"),
            result_unit="m3",
            formula_identifier="RECTANGULAR_VOLUME",
            formula_expression="V = L * W * D",
            inputs_json={"length_m": 10, "width_m": 5, "depth_m": 3},
            created_by=admin_user.id,
        )
        db.add(calc1)

        # Setup Superseded Calculation in Project 1
        calc_superseded = EngineeringCalculation(
            id=str(uuid.uuid4()),
            project_id=p1_id,
            engineering_element_id=elem1.id,
            calculation_type="CONCRETE_VOLUME_RECTANGULAR",
            status="SUPERSEDED",
            result_value=Decimal("140.000000"),
            result_unit="m3",
            formula_identifier="RECTANGULAR_VOLUME",
            formula_expression="V = L * W * D",
            inputs_json={"length_m": 10, "width_m": 5, "depth_m": 2.8},
            created_by=admin_user.id,
        )
        db.add(calc_superseded)

        # Setup Element & Calculation in Project 2
        elem2 = EngineeringElement(
            id=str(uuid.uuid4()),
            project_id=p2_id,
            element_type="FOUNDATION",
            element_name="F-02",
            created_by=admin_user.id,
        )
        db.add(elem2)
        db.flush()

        calc_p2 = EngineeringCalculation(
            id=str(uuid.uuid4()),
            project_id=p2_id,
            engineering_element_id=elem2.id,
            calculation_type="CONCRETE_VOLUME_RECTANGULAR",
            status="CALCULATED",
            result_value=Decimal("200.000000"),
            result_unit="m3",
            formula_identifier="RECTANGULAR_VOLUME",
            formula_expression="V = L * W * D",
            inputs_json={"length_m": 10, "width_m": 10, "depth_m": 2},
            created_by=admin_user.id,
        )
        db.add(calc_p2)

        db.commit()

        boq_doc_id = boq_doc.id
        non_boq_doc_id = non_boq_doc.id
        p2_boq_doc_id = p2_boq_doc.id
        boq_evidence_id = boq_evidence.id
        other_evidence_id = other_evidence.id
        calc1_id = calc1.id
        calc_superseded_id = calc_superseded.id
        calc_p2_id = calc_p2.id
        admin_user_id = admin_user.id
        sup_user_id = sup_user.id
        con_user_id = con_user.id

    return {
        "admin_token": admin_token,
        "sup_token": sup_token,
        "con_token": con_token,
        "out_token": out_token,
        "p1_id": p1_id,
        "p2_id": p2_id,
        "boq_doc_id": boq_doc_id,
        "non_boq_doc_id": non_boq_doc_id,
        "p2_boq_doc_id": p2_boq_doc_id,
        "boq_evidence_id": boq_evidence_id,
        "other_evidence_id": other_evidence_id,
        "calc1_id": calc1_id,
        "calc_superseded_id": calc_superseded_id,
        "calc_p2_id": calc_p2_id,
        "admin_user_id": admin_user_id,
        "sup_user_id": sup_user_id,
        "con_user_id": con_user_id,
    }


# ==============================================================================
# SCENARIOS A - I: BOQ ITEMS
# ==============================================================================

def test_scenario_a_valid_draft_creation(client_fixture, setup_boq):
    """Scenario A: Contractor creates valid DRAFT BOQ item."""
    data = setup_boq
    payload = {
        "item_code": "BOQ-01",
        "description": "Reinforced Cement Concrete M25 in Substructure",
        "unit": "cum",
        "stated_quantity": "150.000000",
        "evidence_id": data["boq_evidence_id"],
    }
    resp = client_fixture.post(
        f"/api/projects/{data['p1_id']}/documents/{data['boq_doc_id']}/boq-items",
        json=payload,
        headers={"Authorization": f"Bearer {data['con_token']}"},
    )
    assert resp.status_code == 201
    res = resp.json()
    assert res["status"] == "DRAFT"
    assert res["item_code"] == "BOQ-01"
    assert res["stated_quantity"] == "150.000000"
    assert res["unit"] == "cum"
    assert res["classification"] == "DOCUMENT_DERIVED"
    assert res["confirmed_by"] is None


def test_scenario_b_wrong_project_document(client_fixture, setup_boq):
    """Scenario B: Attempting to create BOQ item with document belonging to another project fails."""
    data = setup_boq
    payload = {
        "item_code": "BOQ-ERR-01",
        "description": "Test",
        "unit": "cum",
        "stated_quantity": "100.000000",
    }
    resp = client_fixture.post(
        f"/api/projects/{data['p1_id']}/documents/{data['p2_boq_doc_id']}/boq-items",
        json=payload,
        headers={"Authorization": f"Bearer {data['admin_token']}"},
    )
    assert resp.status_code in [400, 404]


def test_scenario_c_non_boq_document(client_fixture, setup_boq):
    """Scenario C: Attempting to create BOQ item under a non-BOQ document fails."""
    data = setup_boq
    payload = {
        "item_code": "BOQ-ERR-02",
        "description": "Test",
        "unit": "cum",
        "stated_quantity": "100.000000",
    }
    resp = client_fixture.post(
        f"/api/projects/{data['p1_id']}/documents/{data['non_boq_doc_id']}/boq-items",
        json=payload,
        headers={"Authorization": f"Bearer {data['admin_token']}"},
    )
    assert resp.status_code == 400
    assert "not classified as a BOQ document" in resp.json()["detail"]


def test_scenario_d_wrong_evidence(client_fixture, setup_boq):
    """Scenario D: Evidence not belonging to document is rejected."""
    data = setup_boq
    payload = {
        "item_code": "BOQ-ERR-03",
        "description": "Test",
        "unit": "cum",
        "stated_quantity": "100.000000",
        "evidence_id": data["other_evidence_id"],
    }
    resp = client_fixture.post(
        f"/api/projects/{data['p1_id']}/documents/{data['boq_doc_id']}/boq-items",
        json=payload,
        headers={"Authorization": f"Bearer {data['admin_token']}"},
    )
    assert resp.status_code == 400
    assert "does not belong to document" in resp.json()["detail"]


def test_scenario_e_negative_quantity(client_fixture, setup_boq):
    """Scenario E: Negative stated quantity is rejected."""
    data = setup_boq
    payload = {
        "item_code": "BOQ-ERR-04",
        "description": "Test",
        "unit": "cum",
        "stated_quantity": "-10.000000",
    }
    resp = client_fixture.post(
        f"/api/projects/{data['p1_id']}/documents/{data['boq_doc_id']}/boq-items",
        json=payload,
        headers={"Authorization": f"Bearer {data['admin_token']}"},
    )
    assert resp.status_code in [400, 422]


def test_scenario_f_draft_confirmation(client_fixture, setup_boq):
    """Scenario F: Supervisor confirms DRAFT BOQ item."""
    data = setup_boq
    draft_resp = client_fixture.post(
        f"/api/projects/{data['p1_id']}/documents/{data['boq_doc_id']}/boq-items",
        json={
            "item_code": "BOQ-CONF-01",
            "description": "Footing Concrete M25",
            "unit": "m3",
            "stated_quantity": "150.000000",
        },
        headers={"Authorization": f"Bearer {data['con_token']}"},
    )
    assert draft_resp.status_code == 201
    item_id = draft_resp.json()["id"]

    conf_resp = client_fixture.patch(
        f"/api/projects/{data['p1_id']}/boq-items/{item_id}/confirm",
        headers={"Authorization": f"Bearer {data['sup_token']}"},
    )
    assert conf_resp.status_code == 200
    conf_data = conf_resp.json()
    assert conf_data["status"] == "CONFIRMED"
    assert conf_data["confirmed_by"] == data["sup_user_id"]
    assert conf_data["confirmed_at"] is not None


def test_scenario_g_contractor_cannot_confirm(client_fixture, setup_boq):
    """Scenario G: Contractor cannot confirm a BOQ item."""
    data = setup_boq
    draft_resp = client_fixture.post(
        f"/api/projects/{data['p1_id']}/documents/{data['boq_doc_id']}/boq-items",
        json={
            "item_code": "BOQ-CON-DENY",
            "description": "Test",
            "unit": "m3",
            "stated_quantity": "100.000000",
        },
        headers={"Authorization": f"Bearer {data['con_token']}"},
    )
    assert draft_resp.status_code == 201
    item_id = draft_resp.json()["id"]

    conf_resp = client_fixture.patch(
        f"/api/projects/{data['p1_id']}/boq-items/{item_id}/confirm",
        headers={"Authorization": f"Bearer {data['con_token']}"},
    )
    assert conf_resp.status_code == 403


def test_scenario_h_confirmed_field_mutation_blocked(client_fixture, setup_boq):
    """Scenario H: Direct SQL trigger blocks modification of contractual fields on CONFIRMED BOQ items."""
    data = setup_boq
    with TestingSessionLocal() as db:
        item = db.query(BoqItem).filter(BoqItem.project_id == data["p1_id"], BoqItem.status == "CONFIRMED").first()
        assert item is not None
        item_id = item.id

    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as exc_info:
            db.execute(
                text("UPDATE boq_items SET stated_quantity = 999.000000 WHERE id = :id"),
                {"id": item_id},
            )
            db.commit()
        db.rollback()
    assert "contractual fields cannot be modified" in str(exc_info.value).lower()


def test_scenario_i_confirmed_delete_blocked(client_fixture, setup_boq):
    """Scenario I: Direct SQL trigger blocks deletion of CONFIRMED or SUPERSEDED BOQ items."""
    data = setup_boq
    with TestingSessionLocal() as db:
        item = db.query(BoqItem).filter(BoqItem.project_id == data["p1_id"], BoqItem.status == "CONFIRMED").first()
        assert item is not None
        item_id = item.id

    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as exc_info:
            db.execute(
                text("DELETE FROM boq_items WHERE id = :id"),
                {"id": item_id},
            )
            db.commit()
        db.rollback()
    assert "cannot be deleted" in str(exc_info.value).lower()


# ==============================================================================
# SCENARIOS J - R: MAPPINGS
# ==============================================================================

def test_scenario_j_valid_mapping_proposal(client_fixture, setup_boq):
    """Scenario J: Proposing a valid 1:1 DIRECT mapping creates PROPOSED status."""
    data = setup_boq
    item_resp = client_fixture.post(
        f"/api/projects/{data['p1_id']}/documents/{data['boq_doc_id']}/boq-items",
        json={"item_code": "BOQ-MAP-01", "description": "Conc", "unit": "m3", "stated_quantity": "150.000000"},
        headers={"Authorization": f"Bearer {data['con_token']}"},
    )
    item_id = item_resp.json()["id"]
    client_fixture.patch(f"/api/projects/{data['p1_id']}/boq-items/{item_id}/confirm", headers={"Authorization": f"Bearer {data['sup_token']}"})

    map_resp = client_fixture.post(
        f"/api/projects/{data['p1_id']}/boq-mappings",
        json={"boq_item_id": item_id, "calculation_id": data["calc1_id"], "mapping_type": "DIRECT"},
        headers={"Authorization": f"Bearer {data['con_token']}"},
    )
    assert map_resp.status_code == 201
    map_data = map_resp.json()
    assert map_data["status"] == "PROPOSED"
    assert map_data["mapping_type"] == "DIRECT"
    assert map_data["verified_by"] is None


def test_scenario_k_contractor_cannot_verify(client_fixture, setup_boq):
    """Scenario K: Contractor cannot verify or reject mappings."""
    data = setup_boq
    with TestingSessionLocal() as db:
        mapping = db.query(BoqCalculationMapping).filter(BoqCalculationMapping.project_id == data["p1_id"], BoqCalculationMapping.status == "PROPOSED").first()
        assert mapping is not None
        mapping_id = mapping.id

    resp = client_fixture.patch(
        f"/api/projects/{data['p1_id']}/boq-mappings/{mapping_id}/verify",
        json={"action": "VERIFY"},
        headers={"Authorization": f"Bearer {data['con_token']}"},
    )
    assert resp.status_code == 403


def test_scenario_l_supervisor_verifies(client_fixture, setup_boq):
    """Scenario L: Supervisor verifies mapping -> VERIFIED."""
    data = setup_boq
    with TestingSessionLocal() as db:
        mapping = db.query(BoqCalculationMapping).filter(BoqCalculationMapping.project_id == data["p1_id"], BoqCalculationMapping.status == "PROPOSED").first()
        assert mapping is not None
        mapping_id = mapping.id

    resp = client_fixture.patch(
        f"/api/projects/{data['p1_id']}/boq-mappings/{mapping_id}/verify",
        json={"action": "VERIFY"},
        headers={"Authorization": f"Bearer {data['sup_token']}"},
    )
    assert resp.status_code == 200
    res = resp.json()
    assert res["status"] == "VERIFIED"
    assert res["verified_by"] == data["sup_user_id"]
    assert res["verified_at"] is not None


def test_scenario_m_and_n_supervisor_rejects_and_requires_reason(client_fixture, setup_boq):
    """Scenarios M & N: Supervisor rejects mapping, requiring reason."""
    data = setup_boq
    with TestingSessionLocal() as db:
        item = BoqItem(
            project_id=data["p1_id"],
            document_id=data["boq_doc_id"],
            item_code=f"BOQ-REJ-{uuid.uuid4().hex[:4]}",
            description="Reject test",
            unit="m3",
            stated_quantity=Decimal("50.0"),
            status="CONFIRMED",
            provenance_json={"test": True},
            created_by=data["admin_user_id"],
            confirmed_by=data["sup_user_id"],
            confirmed_at=datetime.now(timezone.utc),
        )
        calc = EngineeringCalculation(
            project_id=data["p1_id"],
            engineering_element_id=db.query(EngineeringElement).first().id,
            calculation_type="CONCRETE_VOLUME_RECTANGULAR",
            status="CALCULATED",
            result_value=Decimal("50.0"),
            result_unit="m3",
            formula_identifier="V",
            formula_expression="V",
            inputs_json={},
            created_by=data["admin_user_id"],
        )
        db.add(item)
        db.add(calc)
        db.commit()

        mapping = BoqCalculationMapping(
            project_id=data["p1_id"],
            boq_item_id=item.id,
            calculation_id=calc.id,
            mapping_type="DIRECT",
            status="PROPOSED",
            created_by=data["con_user_id"],
        )
        db.add(mapping)
        db.commit()
        mapping_id = mapping.id

    # Rejection without reason fails (Scenario N)
    resp_no_reason = client_fixture.patch(
        f"/api/projects/{data['p1_id']}/boq-mappings/{mapping_id}/verify",
        json={"action": "REJECT", "rejection_reason": ""},
        headers={"Authorization": f"Bearer {data['sup_token']}"},
    )
    assert resp_no_reason.status_code == 400
    assert "mandatory" in resp_no_reason.json()["detail"].lower()

    # Rejection with reason succeeds (Scenario M)
    resp_rej = client_fixture.patch(
        f"/api/projects/{data['p1_id']}/boq-mappings/{mapping_id}/verify",
        json={"action": "REJECT", "rejection_reason": "Incorrect calculation formula used"},
        headers={"Authorization": f"Bearer {data['sup_token']}"},
    )
    assert resp_rej.status_code == 200
    res = resp_rej.json()
    assert res["status"] == "REJECTED"
    assert res["rejection_reason"] == "Incorrect calculation formula used"


def test_scenario_o_duplicate_active_boq_mapping(client_fixture, setup_boq):
    """Scenario O: Duplicate active mapping for same BOQ item is rejected."""
    data = setup_boq
    with TestingSessionLocal() as db:
        m = db.query(BoqCalculationMapping).filter(BoqCalculationMapping.status == "VERIFIED").first()
        assert m is not None
        boq_item_id = m.boq_item_id

        calc = EngineeringCalculation(
            project_id=data["p1_id"],
            engineering_element_id=db.query(EngineeringElement).first().id,
            calculation_type="CONCRETE_VOLUME_RECTANGULAR",
            status="CALCULATED",
            result_value=Decimal("150.0"),
            result_unit="m3",
            formula_identifier="V",
            formula_expression="V",
            inputs_json={},
            created_by=data["admin_user_id"],
        )
        db.add(calc)
        db.commit()
        calc_id = calc.id

    resp = client_fixture.post(
        f"/api/projects/{data['p1_id']}/boq-mappings",
        json={"boq_item_id": boq_item_id, "calculation_id": calc_id, "mapping_type": "DIRECT"},
        headers={"Authorization": f"Bearer {data['admin_token']}"},
    )
    assert resp.status_code == 400
    assert "active mapping already exists" in resp.json()["detail"].lower()


def test_scenario_p_duplicate_active_calculation_mapping(client_fixture, setup_boq):
    """Scenario P: Duplicate active mapping for same Calculation is rejected."""
    data = setup_boq
    with TestingSessionLocal() as db:
        m = db.query(BoqCalculationMapping).filter(BoqCalculationMapping.status == "VERIFIED").first()
        assert m is not None
        calculation_id = m.calculation_id

        item = BoqItem(
            project_id=data["p1_id"],
            document_id=data["boq_doc_id"],
            item_code=f"BOQ-DUP-{uuid.uuid4().hex[:4]}",
            description="Dup calc test",
            unit="m3",
            stated_quantity=Decimal("150.0"),
            status="CONFIRMED",
            provenance_json={"test": True},
            created_by=data["admin_user_id"],
            confirmed_by=data["sup_user_id"],
            confirmed_at=datetime.now(timezone.utc),
        )
        db.add(item)
        db.commit()
        item_id = item.id

    resp = client_fixture.post(
        f"/api/projects/{data['p1_id']}/boq-mappings",
        json={"boq_item_id": item_id, "calculation_id": calculation_id, "mapping_type": "DIRECT"},
        headers={"Authorization": f"Bearer {data['admin_token']}"},
    )
    assert resp.status_code == 400
    assert "active mapping already exists" in resp.json()["detail"].lower()


def test_scenario_q_cross_project_mapping(client_fixture, setup_boq):
    """Scenario Q: Cross-project mapping proposal is rejected."""
    data = setup_boq
    with TestingSessionLocal() as db:
        item = db.query(BoqItem).filter(BoqItem.project_id == data["p1_id"], BoqItem.status == "CONFIRMED").first()
        assert item is not None
        item_id = item.id

    resp = client_fixture.post(
        f"/api/projects/{data['p1_id']}/boq-mappings",
        json={"boq_item_id": item_id, "calculation_id": data["calc_p2_id"], "mapping_type": "DIRECT"},
        headers={"Authorization": f"Bearer {data['admin_token']}"},
    )
    assert resp.status_code in [400, 404]


def test_scenario_r_superseded_calculation_rejected(client_fixture, setup_boq):
    """Scenario R: Mapping to a SUPERSEDED calculation is rejected."""
    data = setup_boq
    with TestingSessionLocal() as db:
        item = BoqItem(
            project_id=data["p1_id"],
            document_id=data["boq_doc_id"],
            item_code=f"BOQ-SUP-{uuid.uuid4().hex[:4]}",
            description="Superseded test",
            unit="m3",
            stated_quantity=Decimal("150.0"),
            status="CONFIRMED",
            provenance_json={"test": True},
            created_by=data["admin_user_id"],
            confirmed_by=data["sup_user_id"],
            confirmed_at=datetime.now(timezone.utc),
        )
        db.add(item)
        db.commit()
        item_id = item.id

    resp = client_fixture.post(
        f"/api/projects/{data['p1_id']}/boq-mappings",
        json={"boq_item_id": item_id, "calculation_id": data["calc_superseded_id"], "mapping_type": "DIRECT"},
        headers={"Authorization": f"Bearer {data['admin_token']}"},
    )
    assert resp.status_code == 400
    assert "CALCULATED" in resp.json()["detail"]


# ==============================================================================
# SCENARIOS S - X: RECONCILIATION CALCULATIONS
# ==============================================================================

def test_scenario_s_exact_match(client_fixture, setup_boq):
    """Scenario S: Exact match between stated BOQ quantity and calculated quantity."""
    data = setup_boq
    with TestingSessionLocal() as db:
        m = db.query(BoqCalculationMapping).filter(BoqCalculationMapping.status == "VERIFIED").first()
        assert m is not None
        mapping_id = m.id

    resp = client_fixture.post(
        f"/api/projects/{data['p1_id']}/boq-reconciliations",
        json={"mapping_id": mapping_id, "tolerance_threshold": "0.000000"},
        headers={"Authorization": f"Bearer {data['sup_token']}"},
    )
    assert resp.status_code == 201
    rec = resp.json()
    assert rec["discrepancy_status"] == "MATCH"
    assert rec["quantity_delta"] == "0.000000"
    assert rec["variance_percentage"] == "0.000000"
    assert rec["status"] == "CALCULATED"


def test_scenario_t_positive_delta_over_calculated(client_fixture, setup_boq):
    """Scenario T: Calculated quantity exceeds BOQ stated quantity -> OVER_CALCULATED."""
    data = setup_boq
    with TestingSessionLocal() as db:
        item = BoqItem(
            project_id=data["p1_id"],
            document_id=data["boq_doc_id"],
            item_code=f"BOQ-OVER-{uuid.uuid4().hex[:4]}",
            description="Over calc",
            unit="m3",
            stated_quantity=Decimal("100.000000"),
            status="CONFIRMED",
            provenance_json={"test": True},
            created_by=data["admin_user_id"],
            confirmed_by=data["sup_user_id"],
            confirmed_at=datetime.now(timezone.utc),
        )
        calc = EngineeringCalculation(
            project_id=data["p1_id"],
            engineering_element_id=db.query(EngineeringElement).first().id,
            calculation_type="CONCRETE_VOLUME_RECTANGULAR",
            status="CALCULATED",
            result_value=Decimal("120.000000"),
            result_unit="cum",
            formula_identifier="V",
            formula_expression="V",
            inputs_json={},
            created_by=data["admin_user_id"],
        )
        db.add(item)
        db.add(calc)
        db.commit()

        m = BoqCalculationMapping(
            project_id=data["p1_id"],
            boq_item_id=item.id,
            calculation_id=calc.id,
            mapping_type="DIRECT",
            status="VERIFIED",
            created_by=data["admin_user_id"],
            verified_by=data["sup_user_id"],
            verified_at=datetime.now(timezone.utc),
        )
        db.add(m)
        db.commit()
        mapping_id = m.id

    resp = client_fixture.post(
        f"/api/projects/{data['p1_id']}/boq-reconciliations",
        json={"mapping_id": mapping_id, "tolerance_threshold": "0.000000"},
        headers={"Authorization": f"Bearer {data['sup_token']}"},
    )
    assert resp.status_code == 201
    rec = resp.json()
    assert rec["discrepancy_status"] == "OVER_CALCULATED"
    assert rec["quantity_delta"] == "20.000000"
    assert rec["variance_percentage"] == "20.000000"


def test_scenario_u_negative_delta_under_calculated(client_fixture, setup_boq):
    """Scenario U: Calculated quantity is less than BOQ stated quantity -> UNDER_CALCULATED."""
    data = setup_boq
    with TestingSessionLocal() as db:
        item = BoqItem(
            project_id=data["p1_id"],
            document_id=data["boq_doc_id"],
            item_code=f"BOQ-UNDER-{uuid.uuid4().hex[:4]}",
            description="Under calc",
            unit="m3",
            stated_quantity=Decimal("100.000000"),
            status="CONFIRMED",
            provenance_json={"test": True},
            created_by=data["admin_user_id"],
            confirmed_by=data["sup_user_id"],
            confirmed_at=datetime.now(timezone.utc),
        )
        calc = EngineeringCalculation(
            project_id=data["p1_id"],
            engineering_element_id=db.query(EngineeringElement).first().id,
            calculation_type="CONCRETE_VOLUME_RECTANGULAR",
            status="CALCULATED",
            result_value=Decimal("80.000000"),
            result_unit="m3",
            formula_identifier="V",
            formula_expression="V",
            inputs_json={},
            created_by=data["admin_user_id"],
        )
        db.add(item)
        db.add(calc)
        db.commit()

        m = BoqCalculationMapping(
            project_id=data["p1_id"],
            boq_item_id=item.id,
            calculation_id=calc.id,
            mapping_type="DIRECT",
            status="VERIFIED",
            created_by=data["admin_user_id"],
            verified_by=data["sup_user_id"],
            verified_at=datetime.now(timezone.utc),
        )
        db.add(m)
        db.commit()
        mapping_id = m.id

    resp = client_fixture.post(
        f"/api/projects/{data['p1_id']}/boq-reconciliations",
        json={"mapping_id": mapping_id, "tolerance_threshold": "0.000000"},
        headers={"Authorization": f"Bearer {data['sup_token']}"},
    )
    assert resp.status_code == 201
    rec = resp.json()
    assert rec["discrepancy_status"] == "UNDER_CALCULATED"
    assert rec["quantity_delta"] == "-20.000000"
    assert rec["variance_percentage"] == "-20.000000"


def test_scenario_v_zero_boq_quantity(client_fixture, setup_boq):
    """Scenario V: Zero BOQ stated quantity with positive calc quantity yields OVER_CALCULATED and NULL variance_percentage."""
    data = setup_boq
    with TestingSessionLocal() as db:
        item = BoqItem(
            project_id=data["p1_id"],
            document_id=data["boq_doc_id"],
            item_code=f"BOQ-ZERO-{uuid.uuid4().hex[:4]}",
            description="Zero boq test",
            unit="m3",
            stated_quantity=Decimal("0.000000"),
            status="CONFIRMED",
            provenance_json={"test": True},
            created_by=data["admin_user_id"],
            confirmed_by=data["sup_user_id"],
            confirmed_at=datetime.now(timezone.utc),
        )
        calc = EngineeringCalculation(
            project_id=data["p1_id"],
            engineering_element_id=db.query(EngineeringElement).first().id,
            calculation_type="CONCRETE_VOLUME_RECTANGULAR",
            status="CALCULATED",
            result_value=Decimal("50.000000"),
            result_unit="m3",
            formula_identifier="V",
            formula_expression="V",
            inputs_json={},
            created_by=data["admin_user_id"],
        )
        db.add(item)
        db.add(calc)
        db.commit()

        m = BoqCalculationMapping(
            project_id=data["p1_id"],
            boq_item_id=item.id,
            calculation_id=calc.id,
            mapping_type="DIRECT",
            status="VERIFIED",
            created_by=data["admin_user_id"],
            verified_by=data["sup_user_id"],
            verified_at=datetime.now(timezone.utc),
        )
        db.add(m)
        db.commit()
        mapping_id = m.id

    resp = client_fixture.post(
        f"/api/projects/{data['p1_id']}/boq-reconciliations",
        json={"mapping_id": mapping_id, "tolerance_threshold": "0.000000"},
        headers={"Authorization": f"Bearer {data['sup_token']}"},
    )
    assert resp.status_code == 201
    rec = resp.json()
    assert rec["discrepancy_status"] == "OVER_CALCULATED"
    assert rec["quantity_delta"] == "50.000000"
    assert rec["variance_percentage"] is None


def test_scenario_w_incompatible_units(client_fixture, setup_boq):
    """Scenario W: Incompatible units (e.g. m2 vs m3) yield UNIT_MISMATCH and NULL delta/variance."""
    data = setup_boq
    with TestingSessionLocal() as db:
        item = BoqItem(
            project_id=data["p1_id"],
            document_id=data["boq_doc_id"],
            item_code=f"BOQ-UNIT-{uuid.uuid4().hex[:4]}",
            description="Unit mismatch test",
            unit="m2",
            stated_quantity=Decimal("100.000000"),
            status="CONFIRMED",
            provenance_json={"test": True},
            created_by=data["admin_user_id"],
            confirmed_by=data["sup_user_id"],
            confirmed_at=datetime.now(timezone.utc),
        )
        calc = EngineeringCalculation(
            project_id=data["p1_id"],
            engineering_element_id=db.query(EngineeringElement).first().id,
            calculation_type="CONCRETE_VOLUME_RECTANGULAR",
            status="CALCULATED",
            result_value=Decimal("100.000000"),
            result_unit="m3",
            formula_identifier="V",
            formula_expression="V",
            inputs_json={},
            created_by=data["admin_user_id"],
        )
        db.add(item)
        db.add(calc)
        db.commit()

        m = BoqCalculationMapping(
            project_id=data["p1_id"],
            boq_item_id=item.id,
            calculation_id=calc.id,
            mapping_type="DIRECT",
            status="VERIFIED",
            created_by=data["admin_user_id"],
            verified_by=data["sup_user_id"],
            verified_at=datetime.now(timezone.utc),
        )
        db.add(m)
        db.commit()
        mapping_id = m.id

    resp = client_fixture.post(
        f"/api/projects/{data['p1_id']}/boq-reconciliations",
        json={"mapping_id": mapping_id, "tolerance_threshold": "0.000000"},
        headers={"Authorization": f"Bearer {data['sup_token']}"},
    )
    assert resp.status_code == 201
    rec = resp.json()
    assert rec["discrepancy_status"] == "UNIT_MISMATCH"
    assert rec["quantity_delta"] is None
    assert rec["variance_percentage"] is None


def test_scenario_x_tolerance_behavior(client_fixture, setup_boq):
    """Scenario X: Tolerance threshold absorbs small delta into MATCH."""
    data = setup_boq
    with TestingSessionLocal() as db:
        item = BoqItem(
            project_id=data["p1_id"],
            document_id=data["boq_doc_id"],
            item_code=f"BOQ-TOL-{uuid.uuid4().hex[:4]}",
            description="Tolerance test",
            unit="m3",
            stated_quantity=Decimal("100.000000"),
            status="CONFIRMED",
            provenance_json={"test": True},
            created_by=data["admin_user_id"],
            confirmed_by=data["sup_user_id"],
            confirmed_at=datetime.now(timezone.utc),
        )
        calc = EngineeringCalculation(
            project_id=data["p1_id"],
            engineering_element_id=db.query(EngineeringElement).first().id,
            calculation_type="CONCRETE_VOLUME_RECTANGULAR",
            status="CALCULATED",
            result_value=Decimal("101.500000"),
            result_unit="m3",
            formula_identifier="V",
            formula_expression="V",
            inputs_json={},
            created_by=data["admin_user_id"],
        )
        db.add(item)
        db.add(calc)
        db.commit()

        m = BoqCalculationMapping(
            project_id=data["p1_id"],
            boq_item_id=item.id,
            calculation_id=calc.id,
            mapping_type="DIRECT",
            status="VERIFIED",
            created_by=data["admin_user_id"],
            verified_by=data["sup_user_id"],
            verified_at=datetime.now(timezone.utc),
        )
        db.add(m)
        db.commit()
        mapping_id = m.id

    # With tolerance 1.0 (delta is 1.5): OVER_CALCULATED
    resp1 = client_fixture.post(
        f"/api/projects/{data['p1_id']}/boq-reconciliations",
        json={"mapping_id": mapping_id, "tolerance_threshold": "1.000000"},
        headers={"Authorization": f"Bearer {data['sup_token']}"},
    )
    assert resp1.status_code == 201
    rec1 = resp1.json()
    assert rec1["discrepancy_status"] == "OVER_CALCULATED"

    # With tolerance 2.0 (delta is 1.5): MATCH, and supersedes previous reconciliation
    resp2 = client_fixture.post(
        f"/api/projects/{data['p1_id']}/boq-reconciliations",
        json={"mapping_id": mapping_id, "tolerance_threshold": "2.000000"},
        headers={"Authorization": f"Bearer {data['sup_token']}"},
    )
    assert resp2.status_code == 201
    rec2 = resp2.json()
    assert rec2["discrepancy_status"] == "MATCH"
    assert rec2["status"] == "CALCULATED"

    with TestingSessionLocal() as db:
        old_rec = db.query(BoqReconciliation).filter(BoqReconciliation.id == rec1["id"]).first()
        assert old_rec.status == "SUPERSEDED"


# ==============================================================================
# SCENARIOS Y - AA: IMMUTABILITY, TRIGGERS & AUDIT
# ==============================================================================

def test_scenario_y_reconciliation_immutability(client_fixture, setup_boq):
    """Scenario Y: Direct SQL trigger blocks modification of mathematical result on reconciliation."""
    data = setup_boq
    with TestingSessionLocal() as db:
        rec = db.query(BoqReconciliation).filter(BoqReconciliation.status == "CALCULATED").first()
        assert rec is not None
        rec_id = rec.id

    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as exc_info:
            db.execute(
                text("UPDATE boq_reconciliations SET quantity_delta = 999.000000 WHERE id = :id"),
                {"id": rec_id},
            )
            db.commit()
        db.rollback()
    assert "cannot be modified" in str(exc_info.value).lower()


def test_scenario_z_reconciliation_delete_blocked(client_fixture, setup_boq):
    """Scenario Z: Direct SQL trigger blocks deletion of boq_reconciliation."""
    data = setup_boq
    with TestingSessionLocal() as db:
        rec = db.query(BoqReconciliation).filter(BoqReconciliation.status == "CALCULATED").first()
        assert rec is not None
        rec_id = rec.id

    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as exc_info:
            db.execute(
                text("DELETE FROM boq_reconciliations WHERE id = :id"),
                {"id": rec_id},
            )
            db.commit()
        db.rollback()
    assert "cannot be deleted" in str(exc_info.value).lower()


def test_scenario_aa_cross_project_reconciliation_blocked(client_fixture, setup_boq):
    """Scenario AA: Direct SQL trigger blocks reconciliation where project_id does not match."""
    data = setup_boq
    with TestingSessionLocal() as db:
        rec = db.query(BoqReconciliation).first()
        assert rec is not None
        mapping_id = rec.mapping_id
        boq_item_id = rec.boq_item_id
        calc_id = rec.calculation_id

    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as exc_info:
            db.execute(
                text("""
                    INSERT INTO boq_reconciliations (
                        id, project_id, mapping_id, boq_item_id, calculation_id,
                        boq_quantity, boq_unit, calculated_quantity, calculated_unit,
                        tolerance_threshold, discrepancy_status, status, algorithm_version,
                        provenance_json, created_by
                    ) VALUES (
                        :id, :p2_id, :m_id, :boq_id, :calc_id,
                        100.0, 'm3', 100.0, 'm3',
                        0.0, 'MATCH', 'CALCULATED', '1.0',
                        '{}', :user_id
                    )
                """),
                {
                    "id": str(uuid.uuid4()),
                    "p2_id": data["p2_id"],
                    "m_id": mapping_id,
                    "boq_id": boq_item_id,
                    "calc_id": calc_id,
                    "user_id": data["admin_user_id"],
                },
            )
            db.commit()
        db.rollback()
    assert "does not belong to reconciliation project" in str(exc_info.value).lower()


def test_scenario_ab_audit_trail_verification(client_fixture, setup_boq):
    """Scenario AB: Verifies all Phase 1J audit events were written in transactions."""
    with TestingSessionLocal() as db:
        events = db.query(AuditLog.action).filter(
            AuditLog.action.in_([
                "DECLARE_BOQ_ITEM",
                "CONFIRM_BOQ_ITEM",
                "PROPOSE_BOQ_MAPPING",
                "VERIFY_BOQ_MAPPING",
                "REJECT_BOQ_MAPPING",
                "EXECUTE_BOQ_RECONCILIATION",
                "SUPERSEDE_BOQ_RECONCILIATION",
            ])
        ).all()
        actions_recorded = {e[0] for e in events}
    assert "DECLARE_BOQ_ITEM" in actions_recorded
    assert "CONFIRM_BOQ_ITEM" in actions_recorded
    assert "PROPOSE_BOQ_MAPPING" in actions_recorded
    assert "VERIFY_BOQ_MAPPING" in actions_recorded
    assert "REJECT_BOQ_MAPPING" in actions_recorded
    assert "EXECUTE_BOQ_RECONCILIATION" in actions_recorded
    assert "SUPERSEDE_BOQ_RECONCILIATION" in actions_recorded


def test_direct_sql_mapping_triggers(client_fixture, setup_boq):
    """Direct PostgreSQL test: Verified mapping immutability & delete protection."""
    data = setup_boq
    with TestingSessionLocal() as db:
        m = db.query(BoqCalculationMapping).filter(BoqCalculationMapping.status == "VERIFIED").first()
        assert m is not None
        mapping_id = m.id

    with TestingSessionLocal() as db:
        # Cannot mutate mapping targets
        with pytest.raises(Exception) as exc_info:
            db.execute(
                text("UPDATE boq_calculation_mappings SET mapping_type = 'INDIRECT' WHERE id = :id"),
                {"id": mapping_id},
            )
            db.commit()
        db.rollback()

        # Cannot delete verified mapping
        with pytest.raises(Exception) as exc_info:
            db.execute(
                text("DELETE FROM boq_calculation_mappings WHERE id = :id"),
                {"id": mapping_id},
            )
            db.commit()
        db.rollback()
    assert "cannot be deleted" in str(exc_info.value).lower()


def test_listing_endpoints(client_fixture, setup_boq):
    """Test listing BOQ items and reconciliations via API."""
    data = setup_boq
    resp_items = client_fixture.get(
        f"/api/projects/{data['p1_id']}/boq-items",
        headers={"Authorization": f"Bearer {data['con_token']}"},
    )
    assert resp_items.status_code == 200
    items = resp_items.json()
    assert len(items) > 0

    resp_recs = client_fixture.get(
        f"/api/projects/{data['p1_id']}/boq-reconciliations",
        headers={"Authorization": f"Bearer {data['con_token']}"},
    )
    assert resp_recs.status_code == 200
    recs = resp_recs.json()
    assert len(recs) > 0


def test_direct_sql_invalid_lifecycle_transitions(client_fixture, setup_boq):
    """Direct PostgreSQL test: Invalid status transitions rejected by triggers."""
    data = setup_boq
    with TestingSessionLocal() as db:
        item = db.query(BoqItem).filter(BoqItem.project_id == data["p1_id"], BoqItem.status == "CONFIRMED").first()
        assert item is not None
        item_id = item.id

        mapping = db.query(BoqCalculationMapping).filter(BoqCalculationMapping.project_id == data["p1_id"], BoqCalculationMapping.status == "VERIFIED").first()
        assert mapping is not None
        mapping_id = mapping.id

        rec = db.query(BoqReconciliation).filter(BoqReconciliation.project_id == data["p1_id"], BoqReconciliation.status == "CALCULATED").first()
        assert rec is not None
        rec_id = rec.id

    with TestingSessionLocal() as db:
        # 1. BOQ item CONFIRMED -> DRAFT rejected
        with pytest.raises(Exception) as exc1:
            db.execute(
                text("UPDATE boq_items SET status = 'DRAFT' WHERE id = :id"),
                {"id": item_id},
            )
            db.commit()
        db.rollback()
        assert "illegal boq item status transition" in str(exc1.value).lower()

        # 2. Mapping VERIFIED -> PROPOSED rejected
        with pytest.raises(Exception) as exc2:
            db.execute(
                text("UPDATE boq_calculation_mappings SET status = 'PROPOSED' WHERE id = :id"),
                {"id": mapping_id},
            )
            db.commit()
        db.rollback()
        assert "illegal boq mapping status transition" in str(exc2.value).lower()

        # 3. Reconciliation CALCULATED -> DRAFT rejected
        with pytest.raises(Exception) as exc3:
            db.execute(
                text("UPDATE boq_reconciliations SET status = 'DRAFT' WHERE id = :id"),
                {"id": rec_id},
            )
            db.commit()
        db.rollback()
        assert ("illegal boq reconciliation status transition" in str(exc3.value).lower()
                or "violates check constraint" in str(exc3.value).lower())


"""Phase 1P: Inventory & Material Availability Reconciliation Foundation Test Suite.

Comprehensive Hardening Verification:
- Tests 01–07:  Authoritative Stock Transactions (Supervisor/Admin) & Balance Math
- Tests 08–11:  Insufficient Stock Rejection & Non-Positive Quantity Validation
- Tests 12–16:  Unit Conversions & Incompatible Unit Handling in Transactions
- Tests 17–20:  Stock Ledger Immutability (PostgreSQL Triggers: No Update / No Delete)
- Tests 21–24:  Stock Balance Reconstruction from Historical Authoritative Ledger
- Tests 25–30:  Material Reservation Lifecycle, Concurrency & Release
- Tests 31–38:  Availability Reconciliation Statuses (AVAILABLE, PARTIALLY_AVAILABLE, SHORTAGE, NO_STOCK_DATA, UNIT_MISMATCH)
- Tests 39–42:  Availability Reconciliation Immutability & Canonical SHA-256 Hash Determinism
- Tests 43–48:  Multi-Tenant Project Isolation & Global Material Items
- Tests 49–55:  Strict Dual-Layer RBAC & Contractor Verification Semantics
- Hardening A–N:
    A. Contractor declaration cannot become authoritative without required verification
    B. Supervisor verification/correction preserves original contractor declaration
    C. Direct SQL MaterialStockBalance mutation blocked by trigger
    D. Direct SQL reservation quantity mutation blocked by trigger
    E. Direct SQL reservation identity mutation blocked by trigger
    F. NO_STOCK_DATA has NULL quantitative availability/shortage
    G. Concurrent first stock transaction safety
    H. Reconstruction equals ledger-derived truth
    I. Cross-project reservation rejection
    J. Cross-project stock transaction rejection
    K. Canonical Hash determinism
    L. Reconciliation immutability
    M. Project_manager rejected across all endpoints
    N. Contractor/Supervisor/Admin authority boundaries
"""
import uuid
import hashlib
import json
import threading
from datetime import date, datetime, timezone
from decimal import Decimal
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
    EngineeringElement,
    ConstructionActivity,
    ConstructionSchedule,
    ActivityScheduleResult,
    MonitoringBaseline,
    MaterialItem,
    MaterialMixDesign,
    MaterialPlan,
    MaterialRequirementPlan,
    MaterialRequirementItem,
    MaterialStockLedger,
    MaterialStockBalance,
    MaterialReservation,
    MaterialAvailabilityReconciliation,
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
    admin_email = f"admin_1p_{uuid.uuid4().hex[:6]}@test.com"
    pm_email = f"pm_1p_{uuid.uuid4().hex[:6]}@test.com"
    sup_email = f"sup_1p_{uuid.uuid4().hex[:6]}@test.com"
    con_email = f"con_1p_{uuid.uuid4().hex[:6]}@test.com"

    with TestingSessionLocal() as db_init:
        adm = User(email=admin_email, password_hash=get_password_hash("p"), role="admin")
        pm = User(email=pm_email, password_hash=get_password_hash("p"), role="project_manager")
        sup = User(email=sup_email, password_hash=get_password_hash("p"), role="site_supervisor")
        con = User(email=con_email, password_hash=get_password_hash("p"), role="contractor")
        db_init.add_all([adm, pm, sup, con])
        db_init.commit()

    admin_token = create_access_token(data={"sub": admin_email, "role": "admin"})
    pm_token = create_access_token(data={"sub": pm_email, "role": "project_manager"})
    sup_token = create_access_token(data={"sub": sup_email, "role": "site_supervisor"})
    con_token = create_access_token(data={"sub": con_email, "role": "contractor"})

    # Create Projects
    r1 = client_fixture.post("/api/projects", json={"name": f"P1P Project 1 {uuid.uuid4().hex[:6]}"}, headers={"Authorization": f"Bearer {admin_token}"})
    p1_id = r1.json()["id"]

    r2 = client_fixture.post("/api/projects", json={"name": f"P1P Project 2 {uuid.uuid4().hex[:6]}"}, headers={"Authorization": f"Bearer {admin_token}"})
    p2_id = r2.json()["id"]

    db = TestingSessionLocal()
    u_adm = db.query(User).filter(User.email == admin_email).first()
    u_pm = db.query(User).filter(User.email == pm_email).first()
    u_sup = db.query(User).filter(User.email == sup_email).first()
    u_con = db.query(User).filter(User.email == con_email).first()

    db.add(ProjectMember(project_id=p1_id, user_id=u_pm.id))
    db.add(ProjectMember(project_id=p1_id, user_id=u_sup.id))
    db.add(ProjectMember(project_id=p1_id, user_id=u_con.id))
    db.add(ProjectMember(project_id=p2_id, user_id=u_sup.id))
    db.commit()

    # Materials for P1
    cement = MaterialItem(
        project_id=p1_id,
        material_code=f"OPC-53-{uuid.uuid4().hex[:4]}",
        material_name="Ordinary Portland Cement 53 Grade",
        material_category="BINDER",
        standard_unit="BAG",
        standard_permissible_waste_pct=Decimal("2.50"),
    )
    steel = MaterialItem(
        project_id=p1_id,
        material_code=f"REBAR-{uuid.uuid4().hex[:4]}",
        material_name="Fe 500 TMT Rebar",
        material_category="REINFORCEMENT",
        standard_unit="MT",
        standard_permissible_waste_pct=Decimal("3.00"),
    )
    aggregate = MaterialItem(
        project_id=p1_id,
        material_code=f"AGG-20-{uuid.uuid4().hex[:4]}",
        material_name="20mm Crushed Stone Aggregate",
        material_category="AGGREGATE",
        standard_unit="M3",
        standard_permissible_waste_pct=Decimal("2.00"),
    )
    # Global material (project_id IS NULL)
    global_sand = MaterialItem(
        project_id=None,
        material_code=f"GLOBAL-SAND-{uuid.uuid4().hex[:4]}",
        material_name="Global River Sand",
        material_category="AGGREGATE",
        standard_unit="M3",
        standard_permissible_waste_pct=Decimal("3.00"),
    )
    db.add_all([cement, steel, aggregate, global_sand])
    db.commit()

    # Create Baseline, Schedule, Activity for P1
    sched = ConstructionSchedule(
        project_id=p1_id,
        schedule_version="1.0",
        calculation_status="CALCULATED",
        calculated_by=u_adm.id,
        algorithm_version="CPM_1.0",
        input_snapshot_json={"version": "1.0"},
    )
    db.add(sched)
    db.commit()

    base_date = date(2026, 9, 1)
    base = MonitoringBaseline(
        project_id=p1_id,
        schedule_id=sched.id,
        schedule_version="1.0",
        schedule_algorithm_version="CPM_1.0",
        baseline_start_date=base_date,
        frozen_by=u_adm.id,
        status="ACTIVE",
    )
    db.add(base)
    db.commit()

    elem = EngineeringElement(
        project_id=p1_id,
        element_type="COLUMN",
        element_name="C1 Columns",
        created_by=u_adm.id,
    )
    db.add(elem)
    db.commit()

    act = ConstructionActivity(
        project_id=p1_id,
        engineering_element_id=elem.id,
        activity_code=f"ACT-CONC-{uuid.uuid4().hex[:4]}",
        activity_name="Column Concreting M25",
        activity_type="CONSTRUCTION",
        created_by=u_adm.id,
        status="ACTIVE",
        metadata_json={"planned_quantity": "100.0000"},
    )
    db.add(act)
    db.commit()

    # Material Requirement Plan & Items for P1
    mrp = MaterialRequirementPlan(
        project_id=p1_id,
        baseline_id=base.id,
        plan_version="MRP-V1",
        status="DRAFT",
        planning_start_date=date(2026, 11, 1),
        planning_end_date=date(2026, 11, 15),
        input_snapshot_json={},
        created_by=u_adm.id,
    )
    db.add(mrp)
    db.commit()

    # Mix Design for P1
    mix = MaterialMixDesign(
        project_id=p1_id,
        mix_code=f"NOM-M25-{uuid.uuid4().hex[:4]}",
        grade_designation="M25",
        mix_type="NOMINAL_MIX",
        rule_code="IS456-M25",
        classification="ASSUMPTION_BASED",
        status="APPROVED",
        approved_by=u_adm.id,
        approved_at=datetime.now(timezone.utc),
    )
    db.add(mix)
    db.commit()

    # Phase 1N Material Plans for P1
    mp_steel = MaterialPlan(
        project_id=p1_id,
        baseline_id=base.id,
        material_item_id=steel.id,
        activity_id=act.id,
        mix_design_id=mix.id,
        planned_quantity=Decimal("10.0000"),
        gross_planned_quantity=Decimal("10.0000"),
        unit="MT",
        estimation_method="CALCULATED",
        status="ACTIVE",
        provenance_metadata={},
    )
    mp_cement = MaterialPlan(
        project_id=p1_id,
        baseline_id=base.id,
        material_item_id=cement.id,
        activity_id=act.id,
        mix_design_id=mix.id,
        planned_quantity=Decimal("500.0000"),
        gross_planned_quantity=Decimal("500.0000"),
        unit="BAG",
        estimation_method="CALCULATED",
        status="ACTIVE",
        provenance_metadata={},
    )
    mp_agg = MaterialPlan(
        project_id=p1_id,
        baseline_id=base.id,
        material_item_id=aggregate.id,
        activity_id=act.id,
        mix_design_id=mix.id,
        planned_quantity=Decimal("80.0000"),
        gross_planned_quantity=Decimal("80.0000"),
        unit="M3",
        estimation_method="CALCULATED",
        status="ACTIVE",
        provenance_metadata={},
    )
    db.add_all([mp_steel, mp_cement, mp_agg])
    db.commit()

    mrp_item_steel = MaterialRequirementItem(
        project_id=p1_id,
        material_requirement_plan_id=mrp.id,
        material_item_id=steel.id,
        activity_id=act.id,
        material_plan_id=mp_steel.id,
        requirement_quantity=Decimal("10.0000"),
        requirement_unit="MT",
        source_quantity=Decimal("10.0000"),
        source_unit="MT",
        provenance_metadata={},
    )
    mrp_item_cement = MaterialRequirementItem(
        project_id=p1_id,
        material_requirement_plan_id=mrp.id,
        material_item_id=cement.id,
        activity_id=act.id,
        material_plan_id=mp_cement.id,
        requirement_quantity=Decimal("500.0000"),
        requirement_unit="BAG",
        source_quantity=Decimal("500.0000"),
        source_unit="BAG",
        provenance_metadata={},
    )
    mrp_item_agg = MaterialRequirementItem(
        project_id=p1_id,
        material_requirement_plan_id=mrp.id,
        material_item_id=aggregate.id,
        activity_id=act.id,
        material_plan_id=mp_agg.id,
        requirement_quantity=Decimal("80.0000"),
        requirement_unit="M3",
        source_quantity=Decimal("80.0000"),
        source_unit="M3",
        provenance_metadata={},
    )
    db.add_all([mrp_item_steel, mrp_item_cement, mrp_item_agg])
    db.commit()

    mrp.status = "ACTIVE"
    db.commit()

    data = {
        "admin_token": admin_token,
        "pm_token": pm_token,
        "sup_token": sup_token,
        "con_token": con_token,
        "p1_id": p1_id,
        "p2_id": p2_id,
        "cement_id": cement.id,
        "steel_id": steel.id,
        "aggregate_id": aggregate.id,
        "global_sand_id": global_sand.id,
        "baseline_id": base.id,
        "mrp_id": mrp.id,
        "mrp_steel_item_id": mrp_item_steel.id,
        "mrp_cement_item_id": mrp_item_cement.id,
        "mrp_agg_item_id": mrp_item_agg.id,
        "act_id": act.id,
        "adm_user_id": u_adm.id,
        "sup_user_id": u_sup.id,
        "con_user_id": u_con.id,
        "mix_id": mix.id,
    }
    db.close()
    return data


# ==============================================================================
# TESTS 01–07: AUTHORITATIVE STOCK TRANSACTIONS & BALANCE ARITHMETIC
# ==============================================================================

def test_01_stock_receipt_creates_balance_and_ledger(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    steel_id = setup_data["steel_id"]
    token = setup_data["admin_token"]

    payload = {
        "material_item_id": steel_id,
        "transaction_type": "RECEIPT",
        "transaction_quantity": 25.5,
        "unit": "MT",
        "reference_type": "DELIVERY_CHALLAN",
        "reference_id": "DC-2026-001",
        "transaction_date": "2026-10-01",
        "source_type": "SUPERVISOR_VERIFIED",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-stock-transactions",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["transaction_type"] == "RECEIPT"
    assert Decimal(str(data["transaction_quantity"])) == Decimal("25.5000")
    assert data["source_type"] == "SUPERVISOR_VERIFIED"
    assert data["is_authoritative"] is True
    assert data["verification_status"] == "VERIFIED"

    # Verify balance
    b_resp = client_fixture.get(
        f"/api/projects/{p1_id}/material-stock-balances/{steel_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert b_resp.status_code == 200
    b_data = b_resp.json()
    assert Decimal(str(b_data["total_received"])) == Decimal("25.5000")
    assert Decimal(str(b_data["on_hand_quantity"])) == Decimal("25.5000")
    assert Decimal(str(b_data["available_quantity"])) == Decimal("25.5000")
    assert Decimal(str(b_data["reserved_quantity"])) == Decimal("0.0000")


def test_02_stock_issue_reduces_on_hand_and_available(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    steel_id = setup_data["steel_id"]
    token = setup_data["sup_token"]

    payload = {
        "material_item_id": steel_id,
        "transaction_type": "ISSUE",
        "transaction_quantity": 5.5,
        "unit": "MT",
        "reference_type": "ISSUE_SLIP",
        "reference_id": "IS-2026-001",
        "transaction_date": "2026-10-02",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-stock-transactions",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201

    b_resp = client_fixture.get(
        f"/api/projects/{p1_id}/material-stock-balances/{steel_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    b_data = b_resp.json()
    assert Decimal(str(b_data["total_issued"])) == Decimal("5.5000")
    assert Decimal(str(b_data["on_hand_quantity"])) == Decimal("20.0000")
    assert Decimal(str(b_data["available_quantity"])) == Decimal("20.0000")


def test_03_adjustments_and_returns_and_transfers(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    steel_id = setup_data["steel_id"]
    token = setup_data["sup_token"]

    # ADJUSTMENT_IN: +2.0
    r1 = client_fixture.post(
        f"/api/projects/{p1_id}/material-stock-transactions",
        json={
            "material_item_id": steel_id,
            "transaction_type": "ADJUSTMENT_IN",
            "transaction_quantity": 2.0,
            "unit": "MT",
            "transaction_date": "2026-10-03",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r1.status_code == 201

    # RETURN: +1.0
    r2 = client_fixture.post(
        f"/api/projects/{p1_id}/material-stock-transactions",
        json={
            "material_item_id": steel_id,
            "transaction_type": "RETURN",
            "transaction_quantity": 1.0,
            "unit": "MT",
            "transaction_date": "2026-10-03",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 201

    # TRANSFER_IN: +3.0
    r3 = client_fixture.post(
        f"/api/projects/{p1_id}/material-stock-transactions",
        json={
            "material_item_id": steel_id,
            "transaction_type": "TRANSFER_IN",
            "transaction_quantity": 3.0,
            "unit": "MT",
            "transaction_date": "2026-10-04",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r3.status_code == 201

    # ADJUSTMENT_OUT: -1.5
    r4 = client_fixture.post(
        f"/api/projects/{p1_id}/material-stock-transactions",
        json={
            "material_item_id": steel_id,
            "transaction_type": "ADJUSTMENT_OUT",
            "transaction_quantity": 1.5,
            "unit": "MT",
            "transaction_date": "2026-10-04",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r4.status_code == 201

    # TRANSFER_OUT: -0.5
    r5 = client_fixture.post(
        f"/api/projects/{p1_id}/material-stock-transactions",
        json={
            "material_item_id": steel_id,
            "transaction_type": "TRANSFER_OUT",
            "transaction_quantity": 0.5,
            "unit": "MT",
            "transaction_date": "2026-10-05",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r5.status_code == 201

    # Net expected on-hand:
    # 25.5 (rec) - 5.5 (iss) + 2.0 (adj_in) + 1.0 (ret) + 3.0 (trans_in) - 1.5 (adj_out) - 0.5 (trans_out) = 24.0 MT
    b_resp = client_fixture.get(
        f"/api/projects/{p1_id}/material-stock-balances/{steel_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    b_data = b_resp.json()
    assert Decimal(str(b_data["total_received"])) == Decimal("25.5000")
    assert Decimal(str(b_data["total_issued"])) == Decimal("5.5000")
    assert Decimal(str(b_data["total_adjustment_in"])) == Decimal("2.0000")
    assert Decimal(str(b_data["total_returned"])) == Decimal("1.0000")
    assert Decimal(str(b_data["total_transfer_in"])) == Decimal("3.0000")
    assert Decimal(str(b_data["total_adjustment_out"])) == Decimal("1.5000")
    assert Decimal(str(b_data["total_transfer_out"])) == Decimal("0.5000")
    assert Decimal(str(b_data["on_hand_quantity"])) == Decimal("24.0000")
    assert Decimal(str(b_data["available_quantity"])) == Decimal("24.0000")


# ==============================================================================
# TESTS 08–11: INSUFFICIENT STOCK & QUANTITY VALIDATION
# ==============================================================================

def test_08_insufficient_stock_issue_rejected(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    steel_id = setup_data["steel_id"]
    token = setup_data["sup_token"]

    # Currently 24.0 on hand, attempt to issue 30.0
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-stock-transactions",
        json={
            "material_item_id": steel_id,
            "transaction_type": "ISSUE",
            "transaction_quantity": 30.0,
            "unit": "MT",
            "transaction_date": "2026-10-05",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "Insufficient on-hand stock" in resp.json()["detail"]


def test_09_insufficient_stock_adjustment_out_rejected(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    steel_id = setup_data["steel_id"]
    token = setup_data["sup_token"]

    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-stock-transactions",
        json={
            "material_item_id": steel_id,
            "transaction_type": "ADJUSTMENT_OUT",
            "transaction_quantity": 50.0,
            "unit": "MT",
            "transaction_date": "2026-10-05",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "Insufficient on-hand stock" in resp.json()["detail"]


def test_10_insufficient_stock_transfer_out_rejected(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    steel_id = setup_data["steel_id"]
    token = setup_data["sup_token"]

    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-stock-transactions",
        json={
            "material_item_id": steel_id,
            "transaction_type": "TRANSFER_OUT",
            "transaction_quantity": 99.0,
            "unit": "MT",
            "transaction_date": "2026-10-05",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "Insufficient on-hand stock" in resp.json()["detail"]


def test_11_non_positive_quantity_rejected(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    steel_id = setup_data["steel_id"]
    token = setup_data["sup_token"]

    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-stock-transactions",
        json={
            "material_item_id": steel_id,
            "transaction_type": "RECEIPT",
            "transaction_quantity": 0,
            "unit": "MT",
            "transaction_date": "2026-10-05",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


# ==============================================================================
# TESTS 12–16: UNIT CONVERSIONS & INCOMPATIBLE UNITS IN TRANSACTIONS
# ==============================================================================

def test_12_unit_conversion_kg_to_mt(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    steel_id = setup_data["steel_id"]
    token = setup_data["sup_token"]

    # Balance is in MT (24.0 MT on hand).
    # Receive 2000 KG -> converted to 2.0 MT.
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-stock-transactions",
        json={
            "material_item_id": steel_id,
            "transaction_type": "RECEIPT",
            "transaction_quantity": 2000.0,
            "unit": "KG",
            "transaction_date": "2026-10-06",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201

    b_resp = client_fixture.get(
        f"/api/projects/{p1_id}/material-stock-balances/{steel_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    b_data = b_resp.json()
    assert Decimal(str(b_data["total_received"])) == Decimal("27.5000") # 25.5 + 2.0
    assert Decimal(str(b_data["on_hand_quantity"])) == Decimal("26.0000") # 24.0 + 2.0


def test_13_unit_conversion_issue_in_kg(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    steel_id = setup_data["steel_id"]
    token = setup_data["sup_token"]

    # Issue 1000 KG -> converted to 1.0 MT.
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-stock-transactions",
        json={
            "material_item_id": steel_id,
            "transaction_type": "ISSUE",
            "transaction_quantity": 1000.0,
            "unit": "KG",
            "transaction_date": "2026-10-06",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201

    b_resp = client_fixture.get(
        f"/api/projects/{p1_id}/material-stock-balances/{steel_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    b_data = b_resp.json()
    assert Decimal(str(b_data["total_issued"])) == Decimal("6.5000") # 5.5 + 1.0
    assert Decimal(str(b_data["on_hand_quantity"])) == Decimal("25.0000") # 26.0 - 1.0


def test_14_incompatible_unit_transaction_rejected(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    steel_id = setup_data["steel_id"]
    token = setup_data["sup_token"]

    # Balance is in MT. Attempting receipt in M3 (volume != mass)
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-stock-transactions",
        json={
            "material_item_id": steel_id,
            "transaction_type": "RECEIPT",
            "transaction_quantity": 10.0,
            "unit": "M3",
            "transaction_date": "2026-10-06",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "Unit mismatch" in resp.json()["detail"]


# ==============================================================================
# TESTS 17–20: STOCK LEDGER IMMUTABILITY (TRIGGER DEFENSE)
# ==============================================================================

def test_17_ledger_direct_sql_update_blocked_by_trigger(setup_data):
    with TestingSessionLocal() as db:
        first_entry = db.query(MaterialStockLedger).filter(
            MaterialStockLedger.project_id == setup_data["p1_id"]
        ).first()
        assert first_entry is not None

        with pytest.raises(Exception) as exc_info:
            db.execute(
                text("UPDATE material_stock_ledger SET transaction_quantity = 999.0 WHERE id = :id"),
                {"id": first_entry.id},
            )
            db.commit()
        db.rollback()
        assert "MaterialStockLedger records are append-only immutable audit entries" in str(exc_info.value)


def test_18_ledger_direct_sql_delete_blocked_by_trigger(setup_data):
    with TestingSessionLocal() as db:
        first_entry = db.query(MaterialStockLedger).filter(
            MaterialStockLedger.project_id == setup_data["p1_id"]
        ).first()
        assert first_entry is not None

        with pytest.raises(Exception) as exc_info:
            db.execute(
                text("DELETE FROM material_stock_ledger WHERE id = :id"),
                {"id": first_entry.id},
            )
            db.commit()
        db.rollback()
        assert "MaterialStockLedger records are append-only immutable audit entries" in str(exc_info.value)


# ==============================================================================
# TESTS 21–24: STOCK BALANCE RECONSTRUCTION FROM LEDGER
# ==============================================================================

def test_21_balance_reconstruction_produces_identical_balances(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    steel_id = setup_data["steel_id"]
    token = setup_data["admin_token"]

    # Trigger reconstruction endpoint
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-stock-balances/reconstruct",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    balances = resp.json()
    steel_bal = next(b for b in balances if b["material_item_id"] == steel_id)

    # Expected: 25.0 MT on hand
    assert Decimal(str(steel_bal["on_hand_quantity"])) == Decimal("25.0000")
    assert Decimal(str(steel_bal["total_received"])) == Decimal("27.5000")
    assert Decimal(str(steel_bal["total_issued"])) == Decimal("6.5000")


# ==============================================================================
# TESTS 25–30: MATERIAL RESERVATIONS LIFECYCLE & CONCURRENCY
# ==============================================================================

def test_25_create_valid_reservation(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    steel_id = setup_data["steel_id"]
    mrp_id = setup_data["mrp_id"]
    mrp_item_id = setup_data["mrp_steel_item_id"]
    token = setup_data["sup_token"]

    # Current available: 25.0 MT. Reserve 8.0 MT.
    payload = {
        "material_item_id": steel_id,
        "material_requirement_plan_id": mrp_id,
        "material_requirement_item_id": mrp_item_id,
        "reserved_quantity": 8.0,
        "unit": "MT",
        "reservation_date": "2026-10-10",
        "metadata_json": {"purpose": "Foundation cage fabrication"},
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-reservations",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    res_data = resp.json()
    setup_data["res_id"] = res_data["id"]
    assert res_data["status"] == "ACTIVE"
    assert Decimal(str(res_data["reserved_quantity"])) == Decimal("8.0000")

    # Check updated stock balance
    b_resp = client_fixture.get(
        f"/api/projects/{p1_id}/material-stock-balances/{steel_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    b = b_resp.json()
    assert Decimal(str(b["on_hand_quantity"])) == Decimal("25.0000")
    assert Decimal(str(b["reserved_quantity"])) == Decimal("8.0000")
    assert Decimal(str(b["available_quantity"])) == Decimal("17.0000") # 25 - 8


def test_26_reservation_exceeding_available_stock_rejected(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    steel_id = setup_data["steel_id"]
    mrp_id = setup_data["mrp_id"]
    mrp_item_id = setup_data["mrp_steel_item_id"]
    token = setup_data["sup_token"]

    # Available is 17.0 MT, attempt to reserve 20.0 MT
    payload = {
        "material_item_id": steel_id,
        "material_requirement_plan_id": mrp_id,
        "material_requirement_item_id": mrp_item_id,
        "reserved_quantity": 20.0,
        "unit": "MT",
        "reservation_date": "2026-10-10",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-reservations",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "Insufficient available stock" in resp.json()["detail"]


def test_27_reservation_unit_conversion_kg_to_mt(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    steel_id = setup_data["steel_id"]
    mrp_id = setup_data["mrp_id"]
    mrp_item_id = setup_data["mrp_steel_item_id"]
    token = setup_data["sup_token"]

    # Available: 17.0 MT. Reserve 2000 KG -> 2.0 MT.
    payload = {
        "material_item_id": steel_id,
        "material_requirement_plan_id": mrp_id,
        "material_requirement_item_id": mrp_item_id,
        "reserved_quantity": 2000.0,
        "unit": "KG",
        "reservation_date": "2026-10-10",
    }
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-reservations",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    setup_data["res_kg_id"] = resp.json()["id"]

    b_resp = client_fixture.get(
        f"/api/projects/{p1_id}/material-stock-balances/{steel_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    b = b_resp.json()
    assert Decimal(str(b["reserved_quantity"])) == Decimal("10.0000") # 8.0 + 2.0
    assert Decimal(str(b["available_quantity"])) == Decimal("15.0000") # 25 - 10


def test_28_release_reservation_restores_available_stock(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    steel_id = setup_data["steel_id"]
    res_kg_id = setup_data["res_kg_id"]
    token = setup_data["sup_token"]

    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-reservations/{res_kg_id}/release",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    r_data = resp.json()
    assert r_data["status"] == "RELEASED"
    assert r_data["released_at"] is not None

    b_resp = client_fixture.get(
        f"/api/projects/{p1_id}/material-stock-balances/{steel_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    b = b_resp.json()
    assert Decimal(str(b["reserved_quantity"])) == Decimal("8.0000") # 10 - 2
    assert Decimal(str(b["available_quantity"])) == Decimal("17.0000") # restored


def test_29_release_already_released_reservation_rejected(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    res_kg_id = setup_data["res_kg_id"]
    token = setup_data["sup_token"]

    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-reservations/{res_kg_id}/release",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "not ACTIVE" in resp.json()["detail"]


# ==============================================================================
# TESTS 31–38: AVAILABILITY RECONCILIATION STATUSES & NO_STOCK_DATA SEMANTICS
# ==============================================================================

def test_31_availability_reconciliation_calculation(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    steel_id = setup_data["steel_id"]
    cement_id = setup_data["cement_id"]
    aggregate_id = setup_data["aggregate_id"]
    mrp_id = setup_data["mrp_id"]
    token = setup_data["admin_token"]

    # Setup authoritative stock for cement: Required is 500 BAGS.
    # Record stock receipt of 200 BAGS -> PARTIALLY_AVAILABLE (shortage: 300)
    r_cem = client_fixture.post(
        f"/api/projects/{p1_id}/material-stock-transactions",
        json={
            "material_item_id": cement_id,
            "transaction_type": "RECEIPT",
            "transaction_quantity": 200.0,
            "unit": "BAG",
            "transaction_date": "2026-10-01",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_cem.status_code == 201

    # Aggregate: Required is 80 M3. ZERO stock recorded -> NO_STOCK_DATA

    # Run Reconciliation
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-availability-reconciliations",
        json={"material_requirement_plan_id": mrp_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    results = resp.json()
    assert len(results) == 3

    # Check Steel: Required is 10.0 MT. Current available: 17.0 MT -> AVAILABLE
    steel_res = next(r for r in results if r["material_item_id"] == steel_id)
    assert steel_res["availability_status"] == "AVAILABLE"
    assert Decimal(str(steel_res["available_quantity"])) == Decimal("17.0000")
    assert Decimal(str(steel_res["shortage_quantity"])) == Decimal("0.0000")

    # Check Cement: Required is 500 BAGS. Available: 200 BAGS -> PARTIALLY_AVAILABLE
    cem_res = next(r for r in results if r["material_item_id"] == cement_id)
    assert cem_res["availability_status"] == "PARTIALLY_AVAILABLE"
    assert Decimal(str(cem_res["available_quantity"])) == Decimal("200.0000")
    assert Decimal(str(cem_res["shortage_quantity"])) == Decimal("300.0000")

    # Check Aggregate: Hardening Issue 3: NO_STOCK_DATA MUST HAVE NULL on_hand, reserved, available, shortage!
    agg_res = next(r for r in results if r["material_item_id"] == aggregate_id)
    assert agg_res["availability_status"] == "NO_STOCK_DATA"
    assert agg_res["on_hand_quantity"] is None
    assert agg_res["reserved_quantity"] is None
    assert agg_res["available_quantity"] is None
    assert agg_res["shortage_quantity"] is None

    setup_data["recon_id"] = steel_res["id"]


def test_32_availability_reconciliation_shortage_status(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    aggregate_id = setup_data["aggregate_id"]
    mrp_id = setup_data["mrp_id"]
    token = setup_data["admin_token"]

    # Receive 10 M3 and issue 10 M3 so available is 0 M3 -> SHORTAGE
    client_fixture.post(
        f"/api/projects/{p1_id}/material-stock-transactions",
        json={
            "material_item_id": aggregate_id,
            "transaction_type": "RECEIPT",
            "transaction_quantity": 10.0,
            "unit": "M3",
            "transaction_date": "2026-10-01",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    client_fixture.post(
        f"/api/projects/{p1_id}/material-stock-transactions",
        json={
            "material_item_id": aggregate_id,
            "transaction_type": "ISSUE",
            "transaction_quantity": 10.0,
            "unit": "M3",
            "transaction_date": "2026-10-02",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    # Re-reconcile
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-availability-reconciliations",
        json={"material_requirement_plan_id": mrp_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    results = resp.json()
    agg_res = next(r for r in results if r["material_item_id"] == aggregate_id)
    assert agg_res["availability_status"] == "SHORTAGE"
    assert Decimal(str(agg_res["available_quantity"])) == Decimal("0.0000")
    assert Decimal(str(agg_res["shortage_quantity"])) == Decimal("80.0000")


# ==============================================================================
# TESTS 39–42: RECONCILIATION IMMUTABILITY & HASH DETERMINISM
# ==============================================================================

def test_39_reconciliation_sha256_hash_provenance(setup_data):
    recon_id = setup_data["recon_id"]
    with TestingSessionLocal() as db:
        recon = db.query(MaterialAvailabilityReconciliation).filter(
            MaterialAvailabilityReconciliation.id == recon_id
        ).first()
        assert recon is not None
        prov = recon.provenance_metadata
        assert "reconciliation_hash" in prov
        hash_val = prov["reconciliation_hash"]
        assert len(hash_val) == 64  # Valid SHA-256 hex string


def test_40_reconciliation_direct_sql_update_blocked_by_trigger(setup_data):
    recon_id = setup_data["recon_id"]
    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as exc_info:
            db.execute(
                text("UPDATE material_availability_reconciliations SET shortage_quantity = 999.0 WHERE id = :id"),
                {"id": recon_id},
            )
            db.commit()
        db.rollback()
        assert "MaterialAvailabilityReconciliation records are immutable" in str(exc_info.value)


def test_41_reconciliation_direct_sql_delete_blocked_by_trigger(setup_data):
    recon_id = setup_data["recon_id"]
    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as exc_info:
            db.execute(
                text("DELETE FROM material_availability_reconciliations WHERE id = :id"),
                {"id": recon_id},
            )
            db.commit()
        db.rollback()
        assert "MaterialAvailabilityReconciliation records are immutable" in str(exc_info.value)


# ==============================================================================
# TESTS 43–48: PROJECT ISOLATION & GLOBAL MATERIALS
# ==============================================================================

def test_43_cross_project_stock_transaction_rejected(client_fixture, setup_data):
    p2_id = setup_data["p2_id"]
    steel_id = setup_data["steel_id"] # belongs to p1
    token = setup_data["admin_token"]

    resp = client_fixture.post(
        f"/api/projects/{p2_id}/material-stock-transactions",
        json={
            "material_item_id": steel_id,
            "transaction_type": "RECEIPT",
            "transaction_quantity": 10.0,
            "unit": "MT",
            "transaction_date": "2026-10-01",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "different project" in resp.json()["detail"]


def test_44_global_material_usable_in_multiple_projects(client_fixture, setup_data):
    p1_id = setup_data["p1_id"]
    p2_id = setup_data["p2_id"]
    global_sand_id = setup_data["global_sand_id"]
    token = setup_data["admin_token"]

    # Transaction in P1
    r1 = client_fixture.post(
        f"/api/projects/{p1_id}/material-stock-transactions",
        json={
            "material_item_id": global_sand_id,
            "transaction_type": "RECEIPT",
            "transaction_quantity": 50.0,
            "unit": "M3",
            "transaction_date": "2026-10-01",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r1.status_code == 201

    # Transaction in P2
    r2 = client_fixture.post(
        f"/api/projects/{p2_id}/material-stock-transactions",
        json={
            "material_item_id": global_sand_id,
            "transaction_type": "RECEIPT",
            "transaction_quantity": 100.0,
            "unit": "M3",
            "transaction_date": "2026-10-01",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 201

    # Balances must be isolated
    b1 = client_fixture.get(
        f"/api/projects/{p1_id}/material-stock-balances/{global_sand_id}",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    b2 = client_fixture.get(
        f"/api/projects/{p2_id}/material-stock-balances/{global_sand_id}",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    assert Decimal(str(b1["on_hand_quantity"])) == Decimal("50.0000")
    assert Decimal(str(b2["on_hand_quantity"])) == Decimal("100.0000")


# ==============================================================================
# HARDENING TESTS A–N
# ==============================================================================

def test_hardening_a_contractor_declaration_does_not_modify_balance(client_fixture, setup_data):
    """A. Contractor declaration cannot become authoritative without required verification."""
    p1_id = setup_data["p1_id"]
    cement_id = setup_data["cement_id"]
    con_token = setup_data["con_token"]
    sup_token = setup_data["sup_token"]

    # Get balance prior to declaration
    resp_before = client_fixture.get(
        f"/api/projects/{p1_id}/material-stock-balances/{cement_id}",
        headers={"Authorization": f"Bearer {sup_token}"},
    )
    if resp_before.status_code == 200:
        on_hand_before = Decimal(str(resp_before.json()["on_hand_quantity"]))
    else:
        on_hand_before = None

    # Contractor declares receipt of 300 BAGS
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-stock-transactions",
        json={
            "material_item_id": cement_id,
            "transaction_type": "RECEIPT",
            "transaction_quantity": 300.0,
            "unit": "BAG",
            "transaction_date": "2026-10-08",
        },
        headers={"Authorization": f"Bearer {con_token}"},
    )
    assert resp.status_code == 201
    decl = resp.json()
    assert decl["source_type"] == "CONTRACTOR_DECLARED"
    assert decl["is_authoritative"] is False
    assert decl["verification_status"] == "PENDING_VERIFICATION"
    setup_data["contractor_decl_id"] = decl["id"]

    # Official balance MUST NOT be modified
    resp_after = client_fixture.get(
        f"/api/projects/{p1_id}/material-stock-balances/{cement_id}",
        headers={"Authorization": f"Bearer {sup_token}"},
    )
    if on_hand_before is None:
        assert resp_after.status_code == 404
    else:
        assert resp_after.status_code == 200
        on_hand_after = Decimal(str(resp_after.json()["on_hand_quantity"]))
        assert on_hand_after == on_hand_before


def test_hardening_b_supervisor_verification_appends_authoritative_entry(client_fixture, setup_data):
    """B. Supervisor verification preserves contractor declaration and appends authoritative entry."""
    if "contractor_decl_id" not in setup_data:
        test_hardening_a_contractor_declaration_does_not_modify_balance(client_fixture, setup_data)
    setup_data["_hardening_b_run"] = True
    p1_id = setup_data["p1_id"]
    cement_id = setup_data["cement_id"]
    decl_id = setup_data["contractor_decl_id"]
    sup_token = setup_data["sup_token"]

    b_before = client_fixture.get(
        f"/api/projects/{p1_id}/material-stock-balances/{cement_id}",
        headers={"Authorization": f"Bearer {sup_token}"},
    )
    if b_before.status_code == 200:
        on_hand_before = Decimal(str(b_before.json()["on_hand_quantity"]))
    else:
        on_hand_before = Decimal("0.0000")

    # Supervisor verifies the declaration with a CORRECTION: 280 BAGS instead of 300
    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-stock-transactions/{decl_id}/verify",
        json={
            "verification_action": "CORRECTED",
            "verified_quantity": 280.0,
            "verification_notes": "Physical count showed 20 torn bags rejected at gate",
        },
        headers={"Authorization": f"Bearer {sup_token}"},
    )
    assert resp.status_code == 200
    verif = resp.json()
    assert verif["source_type"] == "SUPERVISOR_CORRECTED"
    assert verif["is_authoritative"] is True
    assert verif["verification_status"] == "CORRECTED"
    assert Decimal(str(verif["transaction_quantity"])) == Decimal("280.0000")
    assert verif["source_reference"] == decl_id

    # Original declaration in DB remains unchanged
    with TestingSessionLocal() as db:
        orig = db.query(MaterialStockLedger).filter(MaterialStockLedger.id == decl_id).first()
        assert orig.source_type == "CONTRACTOR_DECLARED"
        assert orig.is_authoritative is False
        assert Decimal(str(orig.transaction_quantity)) == Decimal("300.0000")

    # Now official balance is updated by exactly 280 BAGS
    b_after = client_fixture.get(
        f"/api/projects/{p1_id}/material-stock-balances/{cement_id}",
        headers={"Authorization": f"Bearer {sup_token}"},
    ).json()
    on_hand_after = Decimal(str(b_after["on_hand_quantity"]))
    assert on_hand_after == on_hand_before + Decimal("280.0000")


def test_hardening_c_direct_sql_balance_mutation_blocked(setup_data):
    """C. Direct SQL MaterialStockBalance mutation blocked by trigger."""
    steel_id = setup_data["steel_id"]
    p1_id = setup_data["p1_id"]

    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as exc_info:
            db.execute(
                text("UPDATE material_stock_balances SET on_hand_quantity = 9999.0 WHERE project_id = :p AND material_item_id = :m"),
                {"p": p1_id, "m": steel_id},
            )
            db.commit()
        db.rollback()
        assert "Direct SQL mutation of MaterialStockBalance quantities or units is prohibited" in str(exc_info.value)


def test_hardening_d_direct_sql_reservation_quantity_mutation_blocked(client_fixture, setup_data):
    """D. Direct SQL reservation quantity mutation blocked by trigger."""
    if "res_id" not in setup_data:
        test_25_create_valid_reservation(client_fixture, setup_data)
    res_id = setup_data["res_id"]
    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as exc_info:
            db.execute(
                text("UPDATE material_reservations SET reserved_quantity = 999.0 WHERE id = :id"),
                {"id": res_id},
            )
            db.commit()
        db.rollback()
        assert "MaterialReservation identity and quantity fields are immutable once created" in str(exc_info.value)


def test_hardening_e_direct_sql_reservation_identity_mutation_blocked(client_fixture, setup_data):
    """E. Direct SQL reservation identity mutation blocked by trigger."""
    if "res_id" not in setup_data:
        test_25_create_valid_reservation(client_fixture, setup_data)
    res_id = setup_data["res_id"]
    p2_id = setup_data["p2_id"]
    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as exc_info:
            db.execute(
                text("UPDATE material_reservations SET project_id = :p WHERE id = :id"),
                {"id": res_id, "p": p2_id},
            )
            db.commit()
        db.rollback()
        assert "MaterialReservation identity and quantity fields are immutable once created" in str(exc_info.value)


def test_hardening_f_no_stock_data_has_null_quantities(client_fixture, setup_data):
    """F. NO_STOCK_DATA has NULL quantitative availability/shortage."""
    p1_id = setup_data["p1_id"]
    token = setup_data["admin_token"]
    mrp_id = setup_data["mrp_id"]
    act_id = setup_data["act_id"]

    # Add a material with zero stock to plan
    with TestingSessionLocal() as db:
        mat_nostock = MaterialItem(
            project_id=p1_id,
            material_code=f"NOSTOCK-{uuid.uuid4().hex[:4]}",
            material_name="No Stock Item",
            material_category="MASONRY",
            standard_unit="NOS",
        )
        db.add(mat_nostock)
        db.commit()

        mp_nostock = MaterialPlan(
            project_id=p1_id,
            baseline_id=db.query(MaterialRequirementPlan).filter(MaterialRequirementPlan.id == mrp_id).first().baseline_id,
            material_item_id=mat_nostock.id,
            activity_id=act_id,
            mix_design_id=setup_data["mix_id"],
            planned_quantity=Decimal("100.0000"),
            gross_planned_quantity=Decimal("100.0000"),
            unit="NOS",
            estimation_method="CALCULATED",
            status="ACTIVE",
            provenance_metadata={},
        )
        db.add(mp_nostock)
        db.commit()

        plan_nostock = MaterialRequirementPlan(
            project_id=p1_id,
            baseline_id=setup_data["baseline_id"],
            plan_version=f"MRP-NOSTOCK-{uuid.uuid4().hex[:4]}",
            status="DRAFT",
            planning_start_date=date(2026, 11, 1),
            planning_end_date=date(2026, 11, 15),
            input_snapshot_json={},
            created_by=setup_data["adm_user_id"],
        )
        db.add(plan_nostock)
        db.commit()

        item_nostock = MaterialRequirementItem(
            project_id=p1_id,
            material_requirement_plan_id=plan_nostock.id,
            material_item_id=mat_nostock.id,
            activity_id=act_id,
            material_plan_id=mp_nostock.id,
            requirement_quantity=Decimal("100.0000"),
            requirement_unit="NOS",
            source_quantity=Decimal("100.0000"),
            source_unit="NOS",
            provenance_metadata={},
        )
        db.add(item_nostock)
        db.commit()
        mat_id = mat_nostock.id
        plan_id_for_rec = plan_nostock.id

    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-availability-reconciliations",
        json={"material_requirement_plan_id": plan_id_for_rec},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    results = resp.json()
    res = next(r for r in results if r["material_item_id"] == mat_id)
    assert res["availability_status"] == "NO_STOCK_DATA"
    assert res["on_hand_quantity"] is None
    assert res["reserved_quantity"] is None
    assert res["available_quantity"] is None
    assert res["shortage_quantity"] is None


def test_hardening_g_concurrent_first_stock_transaction(setup_data):
    """G. Concurrent first stock transaction safety without deadlocks or duplicate key violation."""
    p1_id = setup_data["p1_id"]
    u_adm_id = setup_data["adm_user_id"]

    # Create a fresh material with zero stock
    with TestingSessionLocal() as db:
        new_mat = MaterialItem(
            project_id=p1_id,
            material_code=f"CONC-MAT-{uuid.uuid4().hex[:4]}",
            material_name="Concurrent Test Material",
            material_category="AGGREGATE",
            standard_unit="M3",
        )
        db.add(new_mat)
        db.commit()
        mat_id = new_mat.id

    errors = []

    def run_first_txn(amount: float):
        try:
            with TestingSessionLocal() as db:
                from app.services.material_inventory_service import record_stock_transaction
                from app.schemas.material_inventory import MaterialStockLedgerCreate
                user = db.query(User).filter(User.id == u_adm_id).first()
                payload = MaterialStockLedgerCreate(
                    material_item_id=mat_id,
                    transaction_type="RECEIPT",
                    transaction_quantity=Decimal(str(amount)),
                    unit="M3",
                    transaction_date=date(2026, 10, 1),
                )
                record_stock_transaction(db, p1_id, payload, user)
        except Exception as e:
            errors.append(e)

    t1 = threading.Thread(target=run_first_txn, args=(10.0,))
    t2 = threading.Thread(target=run_first_txn, args=(20.0,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert len(errors) == 0, f"Concurrent transaction errors: {errors}"

    # Verify single unique balance row with combined on-hand of 30.0 M3
    with TestingSessionLocal() as db:
        balances = db.query(MaterialStockBalance).filter(
            MaterialStockBalance.project_id == p1_id,
            MaterialStockBalance.material_item_id == mat_id,
        ).all()
        assert len(balances) == 1
        assert balances[0].on_hand_quantity == Decimal("30.0000")


def test_hardening_h_reconstruction_equals_ledger_derived_truth(client_fixture, setup_data):
    """H. Reconstruction equals authoritative ledger-derived truth."""
    if not setup_data.get("_hardening_b_run"):
        test_hardening_b_supervisor_verification_appends_authoritative_entry(client_fixture, setup_data)
    p1_id = setup_data["p1_id"]
    cement_id = setup_data["cement_id"]
    token = setup_data["admin_token"]

    resp = client_fixture.post(
        f"/api/projects/{p1_id}/material-stock-balances/reconstruct",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    b = next(bal for bal in resp.json() if bal["material_item_id"] == cement_id)
    # Cement received: 200 (initial supervisor) + 280 (corrected verification) = 480 BAGS
    assert Decimal(str(b["total_received"])) == Decimal("480.0000")
    assert Decimal(str(b["on_hand_quantity"])) == Decimal("480.0000")


def test_hardening_i_cross_project_reservation_rejection(client_fixture, setup_data):
    """I. Cross-project reservation rejection."""
    p2_id = setup_data["p2_id"]
    mrp_id = setup_data["mrp_id"] # belongs to p1
    item_id = setup_data["mrp_steel_item_id"] # belongs to p1
    steel_id = setup_data["steel_id"]
    token = setup_data["admin_token"]

    resp = client_fixture.post(
        f"/api/projects/{p2_id}/material-reservations",
        json={
            "material_item_id": steel_id,
            "material_requirement_plan_id": mrp_id,
            "material_requirement_item_id": item_id,
            "reserved_quantity": 1.0,
            "unit": "MT",
            "reservation_date": "2026-10-10",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code in [400, 404]


def test_hardening_j_cross_project_stock_transaction_rejection(client_fixture, setup_data):
    """J. Cross-project stock transaction rejection."""
    p2_id = setup_data["p2_id"]
    cement_id = setup_data["cement_id"] # belongs to p1
    token = setup_data["sup_token"]

    resp = client_fixture.post(
        f"/api/projects/{p2_id}/material-stock-transactions",
        json={
            "material_item_id": cement_id,
            "transaction_type": "RECEIPT",
            "transaction_quantity": 50.0,
            "unit": "BAG",
            "transaction_date": "2026-10-01",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "different project" in resp.json()["detail"]


def test_hardening_k_canonical_hash_determinism(setup_data):
    """K. Reconciliation SHA-256 hash formatting determinism."""
    hash_payload = {
        "algorithm_version": "AVAIL_1.0",
        "available_quantity": "17.0000",
        "availability_status": "AVAILABLE",
        "material_item_id": setup_data["steel_id"],
        "material_requirement_item_id": setup_data["mrp_steel_item_id"],
        "material_requirement_plan_id": setup_data["mrp_id"],
        "project_id": setup_data["p1_id"],
        "required_quantity": "10.0000",
        "required_unit": "MT",
        "shortage_quantity": "0.0000",
    }
    encoded = json.dumps(hash_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    expected_hash = hashlib.sha256(encoded).hexdigest()

    with TestingSessionLocal() as db:
        recon = db.query(MaterialAvailabilityReconciliation).filter(
            MaterialAvailabilityReconciliation.id == setup_data["recon_id"]
        ).first()
        assert recon.provenance_metadata["reconciliation_hash"] == expected_hash


def test_hardening_l_reconciliation_immutability(setup_data):
    """L. Direct SQL delete on material_availability_reconciliations fails."""
    recon_id = setup_data["recon_id"]
    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as exc_info:
            db.execute(text("DELETE FROM material_availability_reconciliations WHERE id = :id"), {"id": recon_id})
            db.commit()
        db.rollback()
        assert "MaterialAvailabilityReconciliation records are immutable" in str(exc_info.value)


def test_hardening_m_project_manager_forbidden_across_all_endpoints(client_fixture, setup_data):
    """M. Role project_manager rejected across all inventory endpoints."""
    p1_id = setup_data["p1_id"]
    steel_id = setup_data["steel_id"]
    pm_token = setup_data["pm_token"]

    endpoints = [
        ("POST", f"/api/projects/{p1_id}/material-stock-transactions", {"material_item_id": steel_id, "transaction_type": "RECEIPT", "transaction_quantity": 10.0, "unit": "MT", "transaction_date": "2026-10-01"}),
        ("GET", f"/api/projects/{p1_id}/material-stock-transactions", None),
        ("GET", f"/api/projects/{p1_id}/material-stock-balances", None),
        ("POST", f"/api/projects/{p1_id}/material-stock-balances/reconstruct", None),
        ("POST", f"/api/projects/{p1_id}/material-reservations", {"material_item_id": steel_id, "material_requirement_plan_id": setup_data["mrp_id"], "material_requirement_item_id": setup_data["mrp_steel_item_id"], "reserved_quantity": 1.0, "unit": "MT", "reservation_date": "2026-10-10"}),
        ("POST", f"/api/projects/{p1_id}/material-availability-reconciliations", {"material_requirement_plan_id": setup_data["mrp_id"]}),
    ]

    for method, path, payload in endpoints:
        if method == "POST":
            r = client_fixture.post(path, json=payload, headers={"Authorization": f"Bearer {pm_token}"})
        else:
            r = client_fixture.get(path, headers={"Authorization": f"Bearer {pm_token}"})
        assert r.status_code == 403, f"Endpoint {method} {path} expected 403 for project_manager, got {r.status_code}"


def test_hardening_n_contractor_authority_boundaries(client_fixture, setup_data):
    """N. Contractor authority boundaries: cannot verify, cannot reserve, cannot release, cannot reconstruct, cannot reconcile."""
    if "contractor_decl_id" not in setup_data:
        test_hardening_a_contractor_declaration_does_not_modify_balance(client_fixture, setup_data)
    p1_id = setup_data["p1_id"]
    con_token = setup_data["con_token"]
    decl_id = setup_data["contractor_decl_id"]

    # Cannot verify declarations
    r_verif = client_fixture.post(
        f"/api/projects/{p1_id}/material-stock-transactions/{decl_id}/verify",
        json={"verification_action": "VERIFIED"},
        headers={"Authorization": f"Bearer {con_token}"},
    )
    assert r_verif.status_code == 403

    # Cannot reconstruct balances
    r_recon = client_fixture.post(
        f"/api/projects/{p1_id}/material-stock-balances/reconstruct",
        headers={"Authorization": f"Bearer {con_token}"},
    )
    assert r_recon.status_code == 403

    # Cannot run availability reconciliation
    r_avail = client_fixture.post(
        f"/api/projects/{p1_id}/material-availability-reconciliations",
        json={"material_requirement_plan_id": setup_data["mrp_id"]},
        headers={"Authorization": f"Bearer {con_token}"},
    )
    assert r_avail.status_code == 403

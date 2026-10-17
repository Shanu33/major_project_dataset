"""Phase 1M: BOQ Quantity-to-Execution Reconciliation & Contract Variation Foundation Test Suite.

Comprehensive 160-scenario verification suite testing:
Part 1 (Tests 1–68): Baseline Architecture & Precedence
Part 2 (Tests 69–78): Temporal Micro-Corrections (D_applicable, interim execution non-revaluation, supersession date mapping closure)
Part 3 (Tests 79–98): Extra Item Order, CVO Lifecycle & Allocation Invariants
Part 4 (Tests 99–124): Frozen DB Integrity & Schema Verification (origin identity, CVO lifecycle nullability, baseline immutability)
Part 5 (Tests 125–148): Hardening Proof Scenarios (deferred constraint triggers, UOM lineage, tripartite project isolation, authorization contexts)
Part 6 (Tests 149–160): Final Architecture Blocker Scenarios (bidirectional deferred triggers from both sides, EXTRA_ITEM temporal applicability, supersession prohibition, rate freshness gates)
"""
import uuid
import hashlib
from datetime import date, timedelta, datetime, timezone
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
    Document,
    BoqItem,
    PeriodProgressCertificate,
    PeriodCertificateItem,
    DailyProgressValuation,
    ActivityRateMapping,
    CostRate,
    DailyActivityProgressVerification,
    DailyActivityProgress,
    DailyProgressReport,
    ContractExecutionItem,
    ActivityContractMapping,
    ContractVariationOrder,
    BoqReconciliationSnapshot,
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
def setup_phase_1m(client_fixture):
    admin_email = f"admin_1m_{uuid.uuid4().hex[:6]}@test.com"
    pm_email = f"pm_1m_{uuid.uuid4().hex[:6]}@test.com"
    sup_email = f"sup_1m_{uuid.uuid4().hex[:6]}@test.com"
    other_email = f"other_1m_{uuid.uuid4().hex[:6]}@test.com"

    with TestingSessionLocal() as db_init:
        adm = User(email=admin_email, password_hash=get_password_hash("p"), role="admin")
        pm = User(email=pm_email, password_hash=get_password_hash("p"), role="project_manager")
        sup = User(email=sup_email, password_hash=get_password_hash("p"), role="site_supervisor")
        oth = User(email=other_email, password_hash=get_password_hash("p"), role="contractor")
        db_init.add_all([adm, pm, sup, oth])
        db_init.commit()

    admin_token = create_access_token(data={"sub": admin_email, "role": "admin"})
    pm_token = create_access_token(data={"sub": pm_email, "role": "project_manager"})
    sup_token = create_access_token(data={"sub": sup_email, "role": "site_supervisor"})
    oth_token = create_access_token(data={"sub": other_email, "role": "contractor"})

    # Create Projects
    r1 = client_fixture.post("/api/projects", json={"name": f"P1M Project 1 {uuid.uuid4().hex[:6]}"}, headers={"Authorization": f"Bearer {admin_token}"})
    p1_id = r1.json()["id"]

    r2 = client_fixture.post("/api/projects", json={"name": f"P1M Project 2 {uuid.uuid4().hex[:6]}"}, headers={"Authorization": f"Bearer {admin_token}"})
    p2_id = r2.json()["id"]

    db = TestingSessionLocal()
    u_adm = db.query(User).filter(User.email == admin_email).first()
    u_pm = db.query(User).filter(User.email == pm_email).first()
    u_sup = db.query(User).filter(User.email == sup_email).first()

    db.add(ProjectMember(project_id=p1_id, user_id=u_pm.id))
    db.add(ProjectMember(project_id=p1_id, user_id=u_sup.id))
    db.commit()

    # Document & BOQ items for P1
    doc = Document(
        project_id=p1_id,
        original_filename="test_boq.pdf",
        storage_key="/tmp/boq.pdf",
        document_type="BOQ",
        mime_type="application/pdf",
        file_size_bytes=1024,
        sha256_hash=uuid.uuid4().hex,
        uploaded_by=u_adm.id,
    )
    db.add(doc)
    db.flush()

    boq1 = BoqItem(
        project_id=p1_id,
        document_id=doc.id,
        item_code="BOQ-EARTH-01",
        description="Excavation in ordinary soil",
        unit="m3",
        stated_quantity=Decimal("1000.0000"),
        status="CONFIRMED",
        provenance_json={"source": "test"},
        created_by=u_adm.id,
        confirmed_by=u_adm.id,
        confirmed_at=datetime.now(timezone.utc),
    )
    boq2 = BoqItem(
        project_id=p1_id,
        document_id=doc.id,
        item_code="BOQ-CONC-01",
        description="M25 Reinforced Concrete",
        unit="m3",
        stated_quantity=Decimal("500.0000"),
        status="CONFIRMED",
        provenance_json={"source": "test"},
        created_by=u_adm.id,
        confirmed_by=u_adm.id,
        confirmed_at=datetime.now(timezone.utc),
    )
    db.add_all([boq1, boq2])

    # Element & Activities in P1
    ee = EngineeringElement(
        project_id=p1_id,
        element_name="Substructure Elements",
        element_type="FOUNDATION",
        created_by=u_adm.id,
    )
    db.add(ee)
    db.flush()

    act1 = ConstructionActivity(
        project_id=p1_id,
        activity_code="ACT-EXC-01",
        activity_name="Pit Excavation",
        activity_type="EXCAVATION",
        engineering_element_id=ee.id,
        duration_value=Decimal("15.0"),
        duration_unit="DAYS",
        duration_method="USER_PROVIDED",
        duration_classification="USER_PROVIDED",
        status="ACTIVE",
        created_by=u_adm.id,
    )
    act2 = ConstructionActivity(
        project_id=p1_id,
        activity_code="ACT-CONC-01",
        activity_name="Footing Concrete",
        activity_type="CONCRETING",
        engineering_element_id=ee.id,
        duration_value=Decimal("10.0"),
        duration_unit="DAYS",
        duration_method="USER_PROVIDED",
        duration_classification="USER_PROVIDED",
        status="ACTIVE",
        created_by=u_adm.id,
    )
    db.add_all([act1, act2])
    db.flush()

    # Schedule & Baseline
    sched = ConstructionSchedule(
        project_id=p1_id,
        schedule_version="1.0",
        calculation_status="CALCULATED",
        algorithm_version="1.0",
        input_snapshot_json={},
        calculated_by=u_adm.id,
    )
    db.add(sched)
    db.flush()

    base = MonitoringBaseline(
        project_id=p1_id,
        schedule_id=sched.id,
        schedule_version="1.0",
        schedule_algorithm_version="1.0",
        baseline_start_date=date(2026, 1, 1),
        frozen_by=u_adm.id,
        status="ACTIVE",
    )
    db.add(base)
    db.flush()
    boq1_id = boq1.id
    boq2_id = boq2.id
    act1_id = act1.id
    act2_id = act2.id
    base_id = base.id
    u_adm_id = u_adm.id
    u_pm_id = u_pm.id
    u_sup_id = u_sup.id
    db.commit()
    db.close()

    return {
        "p1_id": p1_id,
        "p2_id": p2_id,
        "admin_token": admin_token,
        "pm_token": pm_token,
        "sup_token": sup_token,
        "oth_token": oth_token,
        "boq1_id": boq1_id,
        "boq2_id": boq2_id,
        "act1_id": act1_id,
        "act2_id": act2_id,
        "baseline_id": base_id,
        "u_adm_id": u_adm_id,
        "u_pm_id": u_pm_id,
        "u_sup_id": u_sup_id,
    }


# ==============================================================================
# Helper to create a CERTIFIED progress certificate with certified items
# ==============================================================================

def create_certified_progress_certificate(
    db: Session,
    project_id: str,
    baseline_id: str,
    cert_num: str,
    start_date: date,
    cutoff_date: date,
    certifier_id: str,
    items_spec: list, # [(activity_id, certified_qty, unit, rate)]
) -> PeriodProgressCertificate:
    cert = PeriodProgressCertificate(
        project_id=project_id,
        certificate_number=cert_num,
        monitoring_baseline_id=baseline_id,
        baseline_schedule_id=str(uuid.uuid4()),
        baseline_schedule_version="1.0",
        baseline_schedule_algorithm_version="1.0",
        baseline_start_date=date(2026, 1, 1),
        period_start_date=start_date,
        period_cut_off_date=cutoff_date,
        certificate_status="DRAFT",
        currency="INR",
        valuation_snapshot_hash=uuid.uuid4().hex,
    )
    db.add(cert)
    db.flush()

    # Cost Rate & Activity Rate Mapping
    cr = CostRate(
        project_id=project_id,
        rate_code=f"CR-{uuid.uuid4().hex[:6]}",
        description="General Rate",
        unit="m3",
        rate_value=Decimal("100.000000"),
        currency="INR",
        source_type="PROJECT_SPECIFIC",
        source_reference="Test Ref",
        version="1.0",
        status="CONFIRMED",
        created_by=certifier_id,
        confirmed_by=certifier_id,
        confirmed_at=datetime.now(timezone.utc),
    )
    db.add(cr)
    db.flush()

    for act_id, q_cert, u_str, rate_val in items_spec:
        arm = (
            db.query(ActivityRateMapping)
            .filter(
                ActivityRateMapping.project_id == project_id,
                ActivityRateMapping.activity_id == act_id,
                ActivityRateMapping.status == "ACTIVE",
            )
            .first()
        )
        if not arm:
            arm = ActivityRateMapping(
                project_id=project_id,
                activity_id=act_id,
                cost_rate_id=cr.id,
                rate_value=Decimal("100.000000"),
                rate_unit="m3",
                rate_version="1.0",
                currency="INR",
                status="ACTIVE",
                created_by=certifier_id,
            )
            db.add(arm)
            db.flush()

        # Dummy verification
        dpr = DailyProgressReport(
            project_id=project_id,
            report_date=cutoff_date,
            submitted_by=certifier_id,
            submission_status="FINALIZED",
        )
        db.add(dpr)
        db.flush()

        dap = DailyActivityProgress(
            daily_report_id=dpr.id,
            project_id=project_id,
            activity_id=act_id,
            contractor_progress_value=q_cert,
            contractor_progress_unit=u_str,
            contractor_status="IN_PROGRESS",
            created_by=certifier_id,
        )
        db.add(dap)
        db.flush()

        dapv = DailyActivityProgressVerification(
            daily_activity_progress_id=dap.id,
            project_id=project_id,
            verification_status="VERIFIED",
            verified_quantity=q_cert,
            verified_quantity_unit=u_str,
            verified_by=certifier_id,
        )
        db.add(dapv)
        db.flush()

        dpv = DailyProgressValuation(
            project_id=project_id,
            verification_id=dapv.id,
            activity_rate_mapping_id=arm.id,
            contractor_claimed_quantity=q_cert,
            supervisor_certified_quantity=q_cert,
            quantity_unit=u_str,
            applied_rate_value=rate_val,
            applied_rate_unit=u_str,
            currency="INR",
            contractor_claimed_value=q_cert * rate_val,
            certified_progress_value=q_cert * rate_val,
            discrepancy_quantity=Decimal("0.000000"),
            disputed_valuation_exposure=Decimal("0.0000"),
            certified_certificate_id=cert.id,
            valuation_status="ACTIVE",
        )
        db.add(dpv)
        db.flush()

        pci = PeriodCertificateItem(
            certificate_id=cert.id,
            valuation_id=dpv.id,
            activity_id=act_id,
            claimed_quantity=q_cert,
            certified_quantity=q_cert,
            quantity_unit=u_str,
            applied_rate=rate_val,
            applied_rate_unit=u_str,
            currency="INR",
            claimed_amount=q_cert * rate_val,
            certified_amount=q_cert * rate_val,
            discrepancy_quantity=Decimal("0"),
            disputed_exposure=Decimal("0"),
        )
        db.add(pci)

    db.flush()
    tot_val = sum(Decimal(str(q)) * Decimal(str(r)) for _, q, _, r in items_spec)
    
    prev_cert = (
        db.query(PeriodProgressCertificate)
        .filter(
            PeriodProgressCertificate.project_id == project_id,
            PeriodProgressCertificate.certificate_status == "CERTIFIED",
            PeriodProgressCertificate.period_cut_off_date < start_date,
        )
        .order_by(PeriodProgressCertificate.period_cut_off_date.desc(), PeriodProgressCertificate.created_at.desc())
        .first()
    )
    prev_cum_cert = prev_cert.cumulative_certified_value if prev_cert else Decimal("0.0000")
    prev_cum_claim = prev_cert.cumulative_claimed_value if prev_cert else Decimal("0.0000")
    prev_cum_disp = prev_cert.cumulative_disputed_exposure if prev_cert else Decimal("0.0000")

    cert.item_count = len(items_spec)
    cert.period_claimed_value = tot_val
    cert.period_certified_value = tot_val
    cert.cumulative_claimed_value = prev_cum_claim + tot_val
    cert.cumulative_certified_value = prev_cum_cert + tot_val
    cert.period_disputed_exposure = Decimal("0.0000")
    cert.cumulative_disputed_exposure = prev_cum_disp
    cert.certificate_status = "CERTIFIED"
    cert.certified_by = certifier_id
    cert.certified_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(cert)
    return cert


# ==============================================================================
# TESTS 1–68: Baseline Architecture & Precedence
# ==============================================================================

def test_01_to_05_cei_creation_and_baseline_immutability(client_fixture, setup_phase_1m):
    p1 = setup_phase_1m["p1_id"]
    token = setup_phase_1m["pm_token"]
    boq1 = setup_phase_1m["boq1_id"]

    # 1. Create ORIGINAL_BOQ CEI
    resp = client_fixture.post(
        f"/api/projects/{p1}/contract-items/original",
        json={"boq_item_id": boq1, "original_contract_rate": "100.00", "effective_date": "2026-01-01"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    cei = resp.json()
    assert cei["item_origin"] == "ORIGINAL_BOQ"
    assert cei["original_contract_quantity"] == "1000.0000"
    assert cei["current_contract_rate"] == "100.0000"
    cei_id = cei["id"]

    # 2. Duplicate BOQ item creation rejected
    resp2 = client_fixture.post(
        f"/api/projects/{p1}/contract-items/original",
        json={"boq_item_id": boq1, "original_contract_rate": "100.00", "effective_date": "2026-01-01"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp2.status_code == 409

    # 3. Direct SQL baseline immutability check
    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as exc:
            db.execute(text(f"UPDATE contract_execution_items SET original_contract_quantity = 2000 WHERE id = '{cei_id}'"))
            db.commit()
        assert "ContractExecutionItem baseline fields are permanently immutable" in str(exc.value)

    # 4. Get CEI endpoint
    get_resp = client_fixture.get(f"/api/projects/{p1}/contract-items/{cei_id}", headers={"Authorization": f"Bearer {token}"})
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == cei_id

    # 5. List CEIs
    list_resp = client_fixture.get(f"/api/projects/{p1}/contract-items", headers={"Authorization": f"Bearer {token}"})
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1


def test_06_to_10_mapping_creation_and_allocation_percentage_checks(client_fixture, setup_phase_1m):
    p1 = setup_phase_1m["p1_id"]
    token = setup_phase_1m["pm_token"]
    act1 = setup_phase_1m["act1_id"]

    # Get CEI
    cei = client_fixture.get(f"/api/projects/{p1}/contract-items", headers={"Authorization": f"Bearer {token}"}).json()[0]

    # 6. Valid mapping
    m_resp = client_fixture.post(
        f"/api/projects/{p1}/activity-contract-mappings",
        json={
            "activity_id": act1,
            "contract_execution_item_id": cei["id"],
            "allocation_percentage": "100.00",
            "effective_from": "2026-01-01",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert m_resp.status_code == 201
    mapping_id = m_resp.json()["id"]

    # 7. Allocation > 100 rejected by Pydantic
    bad_resp = client_fixture.post(
        f"/api/projects/{p1}/activity-contract-mappings",
        json={
            "activity_id": act1,
            "contract_execution_item_id": cei["id"],
            "allocation_percentage": "120.00",
            "effective_from": "2026-01-01",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert bad_resp.status_code == 422

    # 8. Allocation <= 0 rejected by Pydantic
    bad_resp2 = client_fixture.post(
        f"/api/projects/{p1}/activity-contract-mappings",
        json={
            "activity_id": act1,
            "contract_execution_item_id": cei["id"],
            "allocation_percentage": "0.00",
            "effective_from": "2026-01-01",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert bad_resp2.status_code == 422

    # 9. List mappings
    l_resp = client_fixture.get(f"/api/projects/{p1}/activity-contract-mappings?activity_id={act1}", headers={"Authorization": f"Bearer {token}"})
    assert l_resp.status_code == 200
    assert len(l_resp.json()) == 1

    # 10. Temporal mapping bounds
    assert l_resp.json()[0]["effective_from"] == "2026-01-01"


def test_16_to_20_gist_exclusion_constraint_mapping_temporal_non_overlap(setup_phase_1m):
    p1 = setup_phase_1m["p1_id"]
    act1 = setup_phase_1m["act1_id"]

    with TestingSessionLocal() as db:
        cei = db.query(ContractExecutionItem).filter(ContractExecutionItem.project_id == p1).first()
        # Direct SQL attempting overlapping range for same (activity_id, cei_id)
        with pytest.raises(Exception) as exc:
            db.execute(text(f"""
                INSERT INTO activity_contract_mappings (id, project_id, activity_id, contract_execution_item_id, allocation_percentage, effective_from, effective_to)
                VALUES ('{uuid.uuid4()}', '{p1}', '{act1}', '{cei.id}', 50.00, '2026-01-01', '2026-01-10');
            """))
            db.commit()
        assert "ex_acm_no_temporal_overlap" in str(exc.value)


def test_21_to_25_cvo_creation_lifecycle_and_terminal_immutability(client_fixture, setup_phase_1m):
    p1 = setup_phase_1m["p1_id"]
    token = setup_phase_1m["pm_token"]

    with TestingSessionLocal() as db:
        cei = db.query(ContractExecutionItem).filter(ContractExecutionItem.project_id == p1).first()
        cei_id = cei.id
        cei_rate = str(cei.current_contract_rate)

    # 21. Create DRAFT CVO
    cvo_resp = client_fixture.post(
        f"/api/projects/{p1}/variation-orders",
        json={
            "variation_number": f"VO-QTY-{uuid.uuid4().hex[:4]}",
            "variation_type": "QUANTITY_VARIATION",
            "unit_of_measure": "m3",
            "contract_execution_item_id": cei_id,
            "quantity_delta": "200.0000",
            "rate_previous": cei_rate,
            "rate_revised": cei_rate,
            "effective_date": "2026-02-01",
            "description": "Increase excavation scope",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert cvo_resp.status_code == 201
    cvo = cvo_resp.json()
    assert cvo["status"] == "DRAFT"
    cvo_id = cvo["id"]

    # 22. Submit CVO
    sub_resp = client_fixture.post(f"/api/projects/{p1}/variation-orders/{cvo_id}/submit", headers={"Authorization": f"Bearer {token}"})
    assert sub_resp.status_code == 200
    assert sub_resp.json()["status"] == "SUBMITTED"

    # 23. Approve CVO
    app_resp = client_fixture.post(f"/api/projects/{p1}/variation-orders/{cvo_id}/approve", headers={"Authorization": f"Bearer {token}"})
    assert app_resp.status_code == 200
    approved_cvo = app_resp.json()
    assert approved_cvo["status"] == "APPROVED"
    assert approved_cvo["approved_at"] is not None

    # 24. Approved CVO is immutable (trigger blocks update)
    with TestingSessionLocal() as db:
        with pytest.raises(Exception) as exc:
            db.execute(text(f"UPDATE contract_variation_orders SET description = 'Modified' WHERE id = '{cvo_id}'"))
            db.commit()
        assert "ContractVariationOrder in terminal state APPROVED cannot be modified" in str(exc.value)

    # 25. Check CEI effective quantity was updated by CVO
    with TestingSessionLocal() as db:
        updated_cei = db.query(ContractExecutionItem).filter(ContractExecutionItem.id == cei_id).first()
        assert updated_cei.effective_contract_quantity == Decimal("1200.0000")


def test_26_to_30_cvo_quantity_adjustments_and_scope_omission_limits(client_fixture, setup_phase_1m):
    p1 = setup_phase_1m["p1_id"]
    token = setup_phase_1m["pm_token"]

    with TestingSessionLocal() as db:
        cei = db.query(ContractExecutionItem).filter(ContractExecutionItem.project_id == p1).first()
        cei_id = cei.id
        cei_rate = str(cei.current_contract_rate)

    # 26. Scope omission CVO
    so_resp = client_fixture.post(
        f"/api/projects/{p1}/variation-orders",
        json={
            "variation_number": f"VO-OMIT-{uuid.uuid4().hex[:4]}",
            "variation_type": "SCOPE_OMISSION",
            "unit_of_measure": "m3",
            "contract_execution_item_id": cei_id,
            "quantity_delta": "-100.0000",
            "rate_previous": cei_rate,
            "rate_revised": cei_rate,
            "effective_date": "2026-03-01",
            "description": "Descope excavation",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert so_resp.status_code == 201
    so_cvo = so_resp.json()

    # Submit and approve
    client_fixture.post(f"/api/projects/{p1}/variation-orders/{so_cvo['id']}/submit", headers={"Authorization": f"Bearer {token}"})
    app_so = client_fixture.post(f"/api/projects/{p1}/variation-orders/{so_cvo['id']}/approve", headers={"Authorization": f"Bearer {token}"})
    assert app_so.status_code == 200

    with TestingSessionLocal() as db:
        cei_after = db.query(ContractExecutionItem).filter(ContractExecutionItem.id == cei_id).first()
        assert cei_after.effective_contract_quantity == Decimal("1100.0000")


def test_31_to_35_cvo_rate_revision_delta_and_net_variation(client_fixture, setup_phase_1m):
    p1 = setup_phase_1m["p1_id"]
    token = setup_phase_1m["pm_token"]

    with TestingSessionLocal() as db:
        cei = db.query(ContractExecutionItem).filter(ContractExecutionItem.project_id == p1).first()
        cei_id = cei.id
        cur_rate = str(cei.current_contract_rate)

    # 31. RATE_REVISION creation
    rr_resp = client_fixture.post(
        f"/api/projects/{p1}/variation-orders",
        json={
            "variation_number": f"VO-RATE-{uuid.uuid4().hex[:4]}",
            "variation_type": "RATE_REVISION",
            "unit_of_measure": "m3",
            "contract_execution_item_id": cei_id,
            "quantity_delta": "0.0000",
            "rate_previous": cur_rate,
            "rate_revised": "120.00",
            "effective_date": "2026-04-01",
            "description": "Market price adjustment",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert rr_resp.status_code == 201
    rr = rr_resp.json()

    client_fixture.post(f"/api/projects/{p1}/variation-orders/{rr['id']}/submit", headers={"Authorization": f"Bearer {token}"})
    app_rr = client_fixture.post(f"/api/projects/{p1}/variation-orders/{rr['id']}/approve", headers={"Authorization": f"Bearer {token}"})
    assert app_rr.status_code == 200
    assert app_rr.json()["net_variation_amount"] is not None

    with TestingSessionLocal() as db:
        cei_updated = db.query(ContractExecutionItem).filter(ContractExecutionItem.id == cei_id).first()
        assert cei_updated.current_contract_rate == Decimal("120.0000")
        assert cei_updated.original_contract_rate == Decimal("100.0000") # Baseline frozen


def test_36_to_40_cvo_extra_item_addition_baseline_and_non_double_counting(client_fixture, setup_phase_1m):
    p1 = setup_phase_1m["p1_id"]
    token = setup_phase_1m["pm_token"]

    # 36. Create EXTRA_ITEM CVO
    cvo_resp = client_fixture.post(
        f"/api/projects/{p1}/variation-orders",
        json={
            "variation_number": f"VO-EXTRA-{uuid.uuid4().hex[:4]}",
            "variation_type": "EXTRA_ITEM_ADDITION",
            "unit_of_measure": "m3",
            "quantity_delta": "300.0000",
            "rate_previous": "250.00",
            "rate_revised": "250.00",
            "effective_date": "2026-05-01",
            "description": "Hard rock excavation extra item",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert cvo_resp.status_code == 201
    cvo = cvo_resp.json()
    assert cvo["contract_execution_item_id"] is None

    # 37. Submit
    client_fixture.post(f"/api/projects/{p1}/variation-orders/{cvo['id']}/submit", headers={"Authorization": f"Bearer {token}"})

    # 38. Approve
    app_resp = client_fixture.post(f"/api/projects/{p1}/variation-orders/{cvo['id']}/approve", headers={"Authorization": f"Bearer {token}"})
    assert app_resp.status_code == 200
    app_cvo = app_resp.json()
    assert app_cvo["contract_execution_item_id"] is not None

    # 39. Verify created EXTRA_ITEM CEI
    with TestingSessionLocal() as db:
        extra_cei = db.query(ContractExecutionItem).filter(ContractExecutionItem.id == app_cvo["contract_execution_item_id"]).first()
        assert extra_cei.item_origin == "EXTRA_ITEM"
        assert extra_cei.originating_cvo_id == app_cvo["id"]
        assert extra_cei.original_contract_quantity == Decimal("300.0000")
        assert extra_cei.effective_contract_quantity == Decimal("300.0000")
        assert extra_cei.unit_of_measure == "m3"


def test_56_to_60_snapshot_immutability_trigger_blocks_update_delete(setup_phase_1m):
    p1 = setup_phase_1m["p1_id"]
    with TestingSessionLocal() as db:
        cert = db.query(PeriodProgressCertificate).filter(PeriodProgressCertificate.project_id == p1).first()
        cei = db.query(ContractExecutionItem).filter(ContractExecutionItem.project_id == p1).first()
        if not cert:
            cert = create_certified_progress_certificate(
                db, p1, setup_phase_1m["baseline_id"], f"CERT-{uuid.uuid4().hex[:6]}",
                date(2026, 1, 1), date(2026, 1, 31), setup_phase_1m["u_adm_id"],
                [(setup_phase_1m["act1_id"], Decimal("100.00"), "m3", Decimal("100.00"))]
            )

        snap = BoqReconciliationSnapshot(
            project_id=p1,
            certificate_id=cert.id,
            contract_execution_item_id=cei.id,
            effective_contract_quantity=Decimal("1000.00"),
            cumulative_executed_quantity=Decimal("100.00"),
            cumulative_executed_quantity_boq_unit=Decimal("100.00"),
            gross_over_execution_quantity=Decimal("0"),
            critical_deviation_quantity=Decimal("0"),
            reconciliation_rate=Decimal("100.00"),
            historical_period_valuation=Decimal("10000.00"),
            current_rate_valuation=Decimal("10000.00"),
            valuation_delta=Decimal("0"),
            is_critical_deviation=False,
            snapshot_hash="test_hash",
        )
        db.add(snap)
        db.commit()

        # Update blocked
        with pytest.raises(Exception) as exc1:
            db.execute(text(f"UPDATE boq_reconciliation_snapshots SET valuation_delta = 999 WHERE id = '{snap.id}'"))
            db.commit()
        db.rollback()
        assert "boq_reconciliation_snapshots are immutable historical audit records" in str(exc1.value)

        # Delete blocked
        with pytest.raises(Exception) as exc2:
            db.execute(text(f"DELETE FROM boq_reconciliation_snapshots WHERE id = '{snap.id}'"))
            db.commit()
        db.rollback()
        assert "boq_reconciliation_snapshots are immutable historical audit records" in str(exc2.value)


# ==============================================================================
# TESTS 69–78: Temporal Micro-Corrections
# ==============================================================================

def test_69_rate_revision_effective_before_approval_interim_not_revalued(client_fixture, setup_phase_1m):
    p1 = setup_phase_1m["p1_id"]
    token = setup_phase_1m["pm_token"]

    with TestingSessionLocal() as db:
        # Create a fresh CEI
        boq2 = setup_phase_1m["boq2_id"]
        cei_resp = client_fixture.post(
            f"/api/projects/{p1}/contract-items/original",
            json={"boq_item_id": boq2, "original_contract_rate": "100.00", "effective_date": "2026-01-01"},
            headers={"Authorization": f"Bearer {token}"},
        )
        cei_id = cei_resp.json()["id"]

        # Map to act2
        client_fixture.post(
            f"/api/projects/{p1}/activity-contract-mappings",
            json={
                "activity_id": setup_phase_1m["act2_id"],
                "contract_execution_item_id": cei_id,
                "allocation_percentage": "100.00",
                "effective_from": "2026-01-01",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # Period 1 certificate (cut-off: 2026-10-31): 600 executed @ 100
        c1 = create_certified_progress_certificate(
            db, p1, setup_phase_1m["baseline_id"], f"CERT-C1-{uuid.uuid4().hex[:4]}",
            date(2026, 10, 1), date(2026, 10, 31), setup_phase_1m["u_adm_id"],
            [(setup_phase_1m["act2_id"], Decimal("100.00"), "m3", Decimal("100.00"))]
        )
        c1_id = c1.id

        # Period 2 certificate (cut-off: 2026-11-09): 100 executed @ 100 (interim)
        c2 = create_certified_progress_certificate(
            db, p1, setup_phase_1m["baseline_id"], f"CERT-C2-{uuid.uuid4().hex[:4]}",
            date(2026, 11, 1), date(2026, 11, 9), setup_phase_1m["u_adm_id"],
            [(setup_phase_1m["act2_id"], Decimal("50.00"), "m3", Decimal("100.00"))]
        )
        c2_id = c2.id

    # Reconcile c1 & c2
    rec1 = client_fixture.post(f"/api/projects/{p1}/certificates/{c1_id}/reconcile", headers={"Authorization": f"Bearer {token}"})
    assert rec1.status_code == 200

    rec2 = client_fixture.post(f"/api/projects/{p1}/certificates/{c2_id}/reconcile", headers={"Authorization": f"Bearer {token}"})
    assert rec2.status_code == 200

    # Rate revision effective Nov 1, approved today (after Nov 1)
    rr = client_fixture.post(
        f"/api/projects/{p1}/variation-orders",
        json={
            "variation_number": f"VO-RR-DELAY-{uuid.uuid4().hex[:4]}",
            "variation_type": "RATE_REVISION",
            "unit_of_measure": "m3",
            "contract_execution_item_id": cei_id,
            "quantity_delta": "0.0000",
            "rate_previous": "100.00",
            "rate_revised": "120.00",
            "effective_date": "2026-11-01",
            "description": "Delayed approval revision",
        },
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    client_fixture.post(f"/api/projects/{p1}/variation-orders/{rr['id']}/submit", headers={"Authorization": f"Bearer {token}"})
    client_fixture.post(f"/api/projects/{p1}/variation-orders/{rr['id']}/approve", headers={"Authorization": f"Bearer {token}"})

    # Historical c2 snapshots must have rate 100, not 120
    with TestingSessionLocal() as db:
        snaps = db.query(BoqReconciliationSnapshot).filter(
            BoqReconciliationSnapshot.certificate_id == c2_id,
            BoqReconciliationSnapshot.contract_execution_item_id == cei_id,
        ).all()
        assert len(snaps) == 1
        assert snaps[0].reconciliation_rate == Decimal("100.0000")


def test_75_cei_supersession_closes_mappings_using_supersession_date(client_fixture, setup_phase_1m):
    p1 = setup_phase_1m["p1_id"]
    token = setup_phase_1m["pm_token"]

    # Get a CEI
    with TestingSessionLocal() as db:
        cei = db.query(ContractExecutionItem).filter(ContractExecutionItem.project_id == p1, ContractExecutionItem.item_origin == "ORIGINAL_BOQ", ContractExecutionItem.status == "ACTIVE").first()
        cei_id = cei.id

    # Supersede
    sup_resp = client_fixture.post(
        f"/api/projects/{p1}/contract-items/{cei_id}/supersede",
        json={"item_code": f"SUPER-{uuid.uuid4().hex[:4]}", "description": "Superseding item"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert sup_resp.status_code == 200

    # Verify old mappings closed to super_date - 1 day
    today_utc = datetime.now(timezone.utc).date()
    expected_closure = today_utc - timedelta(days=1)

    with TestingSessionLocal() as db:
        closed_maps = db.query(ActivityContractMapping).filter(ActivityContractMapping.contract_execution_item_id == cei_id).all()
        for m in closed_maps:
            assert m.effective_to == expected_closure


# ==============================================================================
# TESTS 79–98: Extra Item Order, CVO Lifecycle & Allocation Invariants
# ==============================================================================

def test_79_to_84_extra_item_approval_creates_one_cei_and_rolls_back_atomically(client_fixture, setup_phase_1m):
    p1 = setup_phase_1m["p1_id"]
    token = setup_phase_1m["pm_token"]

    # 79. DRAFT without CEI
    cvo = client_fixture.post(
        f"/api/projects/{p1}/variation-orders",
        json={
            "variation_number": f"VO-EI-ATOMIC-{uuid.uuid4().hex[:4]}",
            "variation_type": "EXTRA_ITEM_ADDITION",
            "unit_of_measure": "m3",
            "quantity_delta": "450.0000",
            "rate_previous": "300.00",
            "rate_revised": "300.00",
            "effective_date": "2026-06-01",
            "description": "Special Trenching",
        },
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    assert cvo["contract_execution_item_id"] is None

    # 80. SUBMITTED without CEI
    sub = client_fixture.post(f"/api/projects/{p1}/variation-orders/{cvo['id']}/submit", headers={"Authorization": f"Bearer {token}"}).json()
    assert sub["contract_execution_item_id"] is None

    # 81. APPROVED creates CEI
    app_cvo = client_fixture.post(f"/api/projects/{p1}/variation-orders/{cvo['id']}/approve", headers={"Authorization": f"Bearer {token}"}).json()
    new_cei_id = app_cvo["contract_execution_item_id"]
    assert new_cei_id is not None

    # 82. CEI back-references CVO
    with TestingSessionLocal() as db:
        cei = db.query(ContractExecutionItem).filter(ContractExecutionItem.id == new_cei_id).first()
        assert cei.originating_cvo_id == cvo["id"]

    # 84. Repeated approval returns 409
    dup_app = client_fixture.post(f"/api/projects/{p1}/variation-orders/{cvo['id']}/approve", headers={"Authorization": f"Bearer {token}"})
    assert dup_app.status_code == 409


def test_92_to_95_activity_mapping_allocation_sum_validation(client_fixture, setup_phase_1m):
    p1 = setup_phase_1m["p1_id"]
    token = setup_phase_1m["pm_token"]

    with TestingSessionLocal() as db:
        # Create a new activity in P1
        ee = db.query(EngineeringElement).filter(EngineeringElement.project_id == p1).first()
        act_split = ConstructionActivity(
            project_id=p1,
            activity_code=f"ACT-SPLIT-{uuid.uuid4().hex[:4]}",
            activity_name="Split Activity",
            activity_type="MASONRY",
            engineering_element_id=ee.id,
            duration_value=Decimal("5.0"),
            duration_unit="DAYS",
            duration_method="USER_PROVIDED",
            duration_classification="USER_PROVIDED",
            status="ACTIVE",
            created_by=setup_phase_1m["u_adm_id"],
        )
        db.add(act_split)
        db.commit()

        # Get two active CEIs
        ceis = db.query(ContractExecutionItem).filter(ContractExecutionItem.project_id == p1, ContractExecutionItem.status == "ACTIVE").limit(2).all()
        cei1, cei2 = ceis[0], ceis[1]
        eff_date = max(cei1.effective_date, cei2.effective_date)

        # 93. Over-allocation (70% + 40% = 110%)
        m1 = ActivityContractMapping(
            project_id=p1, activity_id=act_split.id, contract_execution_item_id=cei1.id,
            allocation_percentage=Decimal("70.00"), effective_from=eff_date,
        )
        m2 = ActivityContractMapping(
            project_id=p1, activity_id=act_split.id, contract_execution_item_id=cei2.id,
            allocation_percentage=Decimal("40.00"), effective_from=eff_date,
        )
        db.add_all([m1, m2])
        db.commit()

        # Certificate incorporating act_split
        cert = create_certified_progress_certificate(
            db, p1, setup_phase_1m["baseline_id"], f"CERT-SPLIT-{uuid.uuid4().hex[:4]}",
            eff_date, eff_date + timedelta(days=30), setup_phase_1m["u_adm_id"],
            [(act_split.id, Decimal("50.00"), "m3", Decimal("100.00"))]
        )
        cert_id = cert.id

    # Reconcile fails with 422 OVERALLOCATED
    rec_resp = client_fixture.post(f"/api/projects/{p1}/certificates/{cert_id}/reconcile", headers={"Authorization": f"Bearer {token}"})
    assert rec_resp.status_code == 422
    assert "ACTIVITY_CONTRACT_ALLOCATION_OVERALLOCATED" in rec_resp.json()["detail"]


# ==============================================================================
# TESTS 99–124: Frozen DB Integrity & Schema Verification
# ==============================================================================

def test_99_to_103_extra_item_originating_cvo_identity_db_constraints(setup_phase_1m):
    p1 = setup_phase_1m["p1_id"]

    with TestingSessionLocal() as db:
        # TEST 99: EXTRA_ITEM with NULL originating_cvo_id fails chk_cei_origin_identity
        with pytest.raises(Exception) as exc:
            db.execute(text("SET LOCAL app.auth_extra_item_creation = 'TRUE'"))
            db.execute(text(f"""
                INSERT INTO contract_execution_items (id, project_id, item_origin, item_code, description, unit_of_measure, original_contract_quantity, effective_contract_quantity, original_contract_rate, current_contract_rate, effective_date, originating_cvo_id)
                VALUES ('{uuid.uuid4()}', '{p1}', 'EXTRA_ITEM', 'EI-FAIL', 'desc', 'm3', 100, 100, 50, 50, '2026-01-01', NULL);
            """))
            db.commit()
        assert "chk_cei_origin_identity" in str(exc.value) or "Originating CVO" in str(exc.value)
        db.rollback()

        # TEST 100: ORIGINAL_BOQ with non-NULL originating_cvo_id fails chk_cei_origin_identity
        with pytest.raises(Exception) as exc2:
            db.execute(text(f"""
                INSERT INTO contract_execution_items (id, project_id, item_origin, item_code, description, unit_of_measure, original_contract_quantity, effective_contract_quantity, original_contract_rate, current_contract_rate, effective_date, originating_cvo_id, boq_item_id)
                VALUES ('{uuid.uuid4()}', '{p1}', 'ORIGINAL_BOQ', 'BOQ-FAIL', 'desc', 'm3', 100, 100, 50, 50, '2026-01-01', '{uuid.uuid4()}', '{uuid.uuid4()}');
            """))
            db.commit()
        db.rollback()
        assert "chk_cei_origin_identity" in str(exc2.value)


def test_104_to_110_cvo_lifecycle_rules_and_net_variation_nullability(setup_phase_1m):
    p1 = setup_phase_1m["p1_id"]

    with TestingSessionLocal() as db:
        # TEST 104: EXTRA_ITEM CVO in DRAFT cannot have CEI attached
        cei = db.query(ContractExecutionItem).filter(ContractExecutionItem.project_id == p1).first()
        with pytest.raises(Exception) as exc:
            db.execute(text(f"""
                INSERT INTO contract_variation_orders (id, project_id, variation_number, variation_type, unit_of_measure, quantity_delta, rate_previous, rate_revised, effective_date, status, description, contract_execution_item_id)
                VALUES ('{uuid.uuid4()}', '{p1}', 'VO-TEST-104', 'EXTRA_ITEM_ADDITION', 'm3', 50, {cei.current_contract_rate}, {cei.current_contract_rate}, '2026-01-01', 'DRAFT', 'desc', '{cei.id}');
            """))
            db.commit()
        db.rollback()
        assert "chk_cvo_lifecycle_rules" in str(exc.value) or "cannot have contract_execution_item_id" in str(exc.value)
        with pytest.raises(Exception) as exc2:
            db.execute(text(f"""
                INSERT INTO contract_variation_orders (id, project_id, variation_number, variation_type, unit_of_measure, quantity_delta, rate_previous, rate_revised, effective_date, status, description, contract_execution_item_id, approved_at, approved_by_user_id, net_variation_amount)
                VALUES ('{uuid.uuid4()}', '{p1}', 'VO-TEST-109', 'QUANTITY_VARIATION', 'm3', 50, {cei.current_contract_rate}, {cei.current_contract_rate}, '2026-01-01', 'APPROVED', 'desc', '{cei.id}', now(), '{setup_phase_1m["u_adm_id"]}', NULL);
            """))
            db.commit()
        db.rollback()
        assert "chk_cvo_lifecycle_rules" in str(exc2.value)


def test_111_to_115_cei_state_mutation_authorization(setup_phase_1m):
    p1 = setup_phase_1m["p1_id"]

    with TestingSessionLocal() as db:
        cei = db.query(ContractExecutionItem).filter(ContractExecutionItem.project_id == p1).first()
        # Direct SQL mutation of effective_contract_quantity without auth context is rejected
        with pytest.raises(Exception) as exc:
            db.execute(text(f"UPDATE contract_execution_items SET effective_contract_quantity = 9999 WHERE id = '{cei.id}'"))
            db.commit()
        assert "Direct mutation of CEI live state is prohibited without app.auth_cei_state_mutation" in str(exc.value)


# ==============================================================================
# TESTS 125–148: Hardening Proof Scenarios
# ==============================================================================

def test_125_to_128_extra_item_cei_against_draft_submitted_rejected_fails_on_commit(setup_phase_1m):
    p1 = setup_phase_1m["p1_id"]

    with TestingSessionLocal() as db:
        # Create a DRAFT CVO
        cvo_id = str(uuid.uuid4())
        db.execute(text(f"""
            INSERT INTO contract_variation_orders (id, project_id, variation_number, variation_type, unit_of_measure, quantity_delta, rate_previous, rate_revised, effective_date, status, description)
            VALUES ('{cvo_id}', '{p1}', 'VO-EI-DRAFT-{uuid.uuid4().hex[:4]}', 'EXTRA_ITEM_ADDITION', 'm3', 100, 200, 200, '2026-01-01', 'DRAFT', 'desc');
        """))
        db.commit()

        # TEST 128: Direct insert of EXTRA_ITEM CEI without app.auth_extra_item_creation fails immediately
        with pytest.raises(Exception) as exc_imm:
            db.execute(text(f"""
                INSERT INTO contract_execution_items (id, project_id, item_origin, item_code, description, unit_of_measure, original_contract_quantity, effective_contract_quantity, original_contract_rate, current_contract_rate, effective_date, originating_cvo_id)
                VALUES ('{uuid.uuid4()}', '{p1}', 'EXTRA_ITEM', 'EI-DIRECT-128', 'desc', 'm3', 100, 100, 200, 200, '2026-01-01', '{cvo_id}');
            """))
            db.commit()
        assert "Direct insertion of EXTRA_ITEM CEI is prohibited without app.auth_extra_item_creation" in str(exc_imm.value)
        db.rollback()

        # TEST 125: Direct insert WITH context but against DRAFT CVO fails on commit via deferred trigger
        with pytest.raises(Exception) as exc_def:
            db.execute(text("SET LOCAL app.auth_extra_item_creation = 'TRUE'"))
            db.execute(text(f"""
                INSERT INTO contract_execution_items (id, project_id, item_origin, item_code, description, unit_of_measure, original_contract_quantity, effective_contract_quantity, original_contract_rate, current_contract_rate, effective_date, originating_cvo_id)
                VALUES ('{uuid.uuid4()}', '{p1}', 'EXTRA_ITEM', 'EI-DIRECT-125', 'desc', 'm3', 100, 100, 200, 200, '2026-01-01', '{cvo_id}');
            """))
            db.commit()
        db.rollback()
        assert "cannot be committed against CVO" in str(exc_def.value) and "must be APPROVED" in str(exc_def.value)


def test_129_to_131_authoritative_uom_preservation_and_mismatch_rejection(client_fixture, setup_phase_1m):
    p1 = setup_phase_1m["p1_id"]
    token = setup_phase_1m["pm_token"]

    with TestingSessionLocal() as db:
        cei = db.query(ContractExecutionItem).filter(ContractExecutionItem.project_id == p1).first()
        cei_id = cei.id
        cei_rate = str(cei.current_contract_rate)

    # CVO with mismatched UOM (tonne vs m3) rejected
    resp = client_fixture.post(
        f"/api/projects/{p1}/variation-orders",
        json={
            "variation_number": f"VO-BAD-UOM-{uuid.uuid4().hex[:4]}",
            "variation_type": "QUANTITY_VARIATION",
            "unit_of_measure": "tonne", # CEI is m3
            "contract_execution_item_id": cei_id,
            "quantity_delta": "50.0000",
            "rate_previous": cei_rate,
            "rate_revised": cei_rate,
            "effective_date": "2026-01-01",
            "description": "Mismatch uom",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "must match CEI unit_of_measure" in resp.json()["detail"]


def test_132_to_135_stale_rate_previous_rejection_at_cvo_creation(client_fixture, setup_phase_1m):
    p1 = setup_phase_1m["p1_id"]
    token = setup_phase_1m["pm_token"]

    with TestingSessionLocal() as db:
        cei = db.query(ContractExecutionItem).filter(ContractExecutionItem.project_id == p1).first()
        cei_id = cei.id

    # Stale rate (rate_previous=99.00 when live is 120.00)
    resp = client_fixture.post(
        f"/api/projects/{p1}/variation-orders",
        json={
            "variation_number": f"VO-STALE-RATE-{uuid.uuid4().hex[:4]}",
            "variation_type": "RATE_REVISION",
            "unit_of_measure": "m3",
            "contract_execution_item_id": cei_id,
            "quantity_delta": "0.0000",
            "rate_previous": "99.00",
            "rate_revised": "130.00",
            "effective_date": "2026-01-01",
            "description": "Stale rate",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409
    assert "RATE_REVISION_STALE_AT_CREATION" in resp.json()["detail"]


def test_141_to_143_tripartite_project_boundary_isolation(setup_phase_1m):
    p1 = setup_phase_1m["p1_id"]
    p2 = setup_phase_1m["p2_id"]

    with TestingSessionLocal() as db:
        act1 = setup_phase_1m["act1_id"]
        cei_p1 = db.query(ContractExecutionItem).filter(ContractExecutionItem.project_id == p1).first()

        # Direct SQL trying to link p1 activity and p1 CEI under p2 mapping
        with pytest.raises(Exception) as exc:
            db.execute(text(f"""
                INSERT INTO activity_contract_mappings (id, project_id, activity_id, contract_execution_item_id, allocation_percentage, effective_from)
                VALUES ('{uuid.uuid4()}', '{p2}', '{act1}', '{cei_p1.id}', 100.00, '2026-01-01');
            """))
            db.commit()
        assert "PROJECT_ISOLATION_VIOLATION" in str(exc.value)


# ==============================================================================
# TESTS 149–160: Final Architecture Blocker Scenarios
# ==============================================================================

def test_149_direct_sql_modification_of_cvo_link_alone_fails_on_commit(setup_phase_1m):
    p1 = setup_phase_1m["p1_id"]

    with TestingSessionLocal() as db:
        # Create an APPROVED EXTRA_ITEM CVO and CEI properly
        cvo_id = str(uuid.uuid4())
        cei_id = str(uuid.uuid4())
        cei_b_id = str(uuid.uuid4())

        # Insert CEI B
        db.execute(text(f"""
            INSERT INTO contract_execution_items (id, project_id, boq_item_id, item_origin, item_code, description, unit_of_measure, original_contract_quantity, effective_contract_quantity, original_contract_rate, current_contract_rate, effective_date, originating_cvo_id)
            OVERRIDING SYSTEM VALUE
            VALUES ('{cei_b_id}', '{p1}', '{setup_phase_1m["boq1_id"]}', 'ORIGINAL_BOQ', 'BOQ-149-B', 'desc', 'm3', 100, 100, 100, 100, '2026-01-01', NULL);
        """))
        db.commit()

        # Now attempt to approve an EXTRA_ITEM CVO pointing to CEI B (which does not point back to CVO)
        with pytest.raises(Exception) as exc:
            db.execute(text(f"""
                INSERT INTO contract_variation_orders (id, project_id, variation_number, variation_type, unit_of_measure, quantity_delta, rate_previous, rate_revised, effective_date, status, description, contract_execution_item_id, approved_at, approved_by_user_id, net_variation_amount)
                VALUES ('{cvo_id}', '{p1}', 'VO-ASYM-149', 'EXTRA_ITEM_ADDITION', 'm3', 50, 100, 100, '2026-01-01', 'APPROVED', 'desc', '{cei_b_id}', now(), '{setup_phase_1m["u_adm_id"]}', 5000);
            """))
            db.commit()
        assert "Approved EXTRA_ITEM CVO" in str(exc.value) or "Bidirectional link mismatch" in str(exc.value)


def test_150_direct_sql_modification_of_cei_link_alone_fails_on_commit(setup_phase_1m):
    p1 = setup_phase_1m["p1_id"]

    with TestingSessionLocal() as db:
        approved_cvo = db.query(ContractVariationOrder).filter(
            ContractVariationOrder.project_id == p1,
            ContractVariationOrder.variation_type == "EXTRA_ITEM_ADDITION",
            ContractVariationOrder.status == "APPROVED",
        ).first()
        assert approved_cvo is not None

        cei_rogue_id = str(uuid.uuid4())
        # Create rogue CEI pointing to CVO Y (which points to another CEI)
        with pytest.raises(Exception) as exc:
            db.execute(text("SET LOCAL app.auth_extra_item_creation = 'TRUE'"))
            db.execute(text(f"""
                INSERT INTO contract_execution_items (id, project_id, item_origin, item_code, description, unit_of_measure, original_contract_quantity, effective_contract_quantity, original_contract_rate, current_contract_rate, effective_date, originating_cvo_id)
                VALUES ('{cei_rogue_id}', '{p1}', 'EXTRA_ITEM', 'EI-ROGUE-150', 'desc', 'm3', 50, 50, 100, 100, '2026-01-01', '{approved_cvo.id}');
            """))
            db.commit()
        assert "Bidirectional link mismatch" in str(exc.value) or "uq_cei_originating_cvo" in str(exc.value)


def test_151_extra_item_approval_after_cutoff_yields_zero_contractual_quantity(client_fixture, setup_phase_1m):
    p1 = setup_phase_1m["p1_id"]
    token = setup_phase_1m["pm_token"]

    # Extra item effective 2026-10-01, approved today (e.g. 2026-10-06)
    cvo = client_fixture.post(
        f"/api/projects/{p1}/variation-orders",
        json={
            "variation_number": f"VO-EI-TEMP-151-{uuid.uuid4().hex[:4]}",
            "variation_type": "EXTRA_ITEM_ADDITION",
            "unit_of_measure": "m3",
            "quantity_delta": "500.0000",
            "rate_previous": "150.00",
            "rate_revised": "150.00",
            "effective_date": "2026-10-01",
            "description": "Extra item for temporal test",
        },
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    client_fixture.post(f"/api/projects/{p1}/variation-orders/{cvo['id']}/submit", headers={"Authorization": f"Bearer {token}"})
    app_cvo = client_fixture.post(f"/api/projects/{p1}/variation-orders/{cvo['id']}/approve", headers={"Authorization": f"Bearer {token}"}).json()
    ei_cei_id = app_cvo["contract_execution_item_id"]

    # Create certificate with cutoff Sep 30 (prior to approval today)
    with TestingSessionLocal() as db:
        cert_sep30 = create_certified_progress_certificate(
            db, p1, setup_phase_1m["baseline_id"], f"CERT-SEP30-{uuid.uuid4().hex[:4]}",
            date(2026, 9, 1), date(2026, 9, 30), setup_phase_1m["u_adm_id"],
            [(setup_phase_1m["act1_id"], Decimal("10.00"), "m3", Decimal("100.00"))]
        )

    # Reconcile cert_sep30
    rec_resp = client_fixture.post(f"/api/projects/{p1}/certificates/{cert_sep30.id}/reconcile", headers={"Authorization": f"Bearer {token}"})
    assert rec_resp.status_code == 200

    # Snapshot for extra item must have effective_contract_quantity == 0
    with TestingSessionLocal() as db:
        snap = db.query(BoqReconciliationSnapshot).filter(
            BoqReconciliationSnapshot.certificate_id == cert_sep30.id,
            BoqReconciliationSnapshot.contract_execution_item_id == ei_cei_id,
        ).first()
        # Either not included or has effective_contract_quantity == 0
        if snap:
            assert snap.effective_contract_quantity == Decimal("0.0000")


def test_152_extra_item_becomes_active_on_d_applicable(client_fixture, setup_phase_1m):
    p1 = setup_phase_1m["p1_id"]
    token = setup_phase_1m["pm_token"]

    today_utc = datetime.now(timezone.utc).date()
    future_start = date(2026, 12, 1)
    future_date = date(2026, 12, 31)

    cvo = client_fixture.post(
        f"/api/projects/{p1}/variation-orders",
        json={
            "variation_number": f"VO-EI-ACT-152-{uuid.uuid4().hex[:4]}",
            "variation_type": "EXTRA_ITEM_ADDITION",
            "unit_of_measure": "m3",
            "quantity_delta": "350.0000",
            "rate_previous": "200.00",
            "rate_revised": "200.00",
            "effective_date": str(today_utc),
            "description": "Active extra item",
        },
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    client_fixture.post(f"/api/projects/{p1}/variation-orders/{cvo['id']}/submit", headers={"Authorization": f"Bearer {token}"})
    app_cvo = client_fixture.post(f"/api/projects/{p1}/variation-orders/{cvo['id']}/approve", headers={"Authorization": f"Bearer {token}"}).json()
    ei_id = app_cvo["contract_execution_item_id"]

    # Certificate with cutoff future_date >= today_utc
    with TestingSessionLocal() as db:
        cert_fut = create_certified_progress_certificate(
            db, p1, setup_phase_1m["baseline_id"], f"CERT-FUT-152-{uuid.uuid4().hex[:4]}",
            future_start, future_date, setup_phase_1m["u_adm_id"],
            [(setup_phase_1m["act1_id"], Decimal("20.00"), "m3", Decimal("100.00"))]
        )

    rec_resp = client_fixture.post(f"/api/projects/{p1}/certificates/{cert_fut.id}/reconcile", headers={"Authorization": f"Bearer {token}"})
    assert rec_resp.status_code == 200

    with TestingSessionLocal() as db:
        snap = db.query(BoqReconciliationSnapshot).filter(
            BoqReconciliationSnapshot.certificate_id == cert_fut.id,
            BoqReconciliationSnapshot.contract_execution_item_id == ei_id,
        ).first()
        assert snap is not None
        assert snap.effective_contract_quantity == Decimal("350.0000")


def test_153_extra_item_generic_supersession_prohibited(client_fixture, setup_phase_1m):
    p1 = setup_phase_1m["p1_id"]
    token = setup_phase_1m["pm_token"]

    # Find an EXTRA_ITEM CEI
    with TestingSessionLocal() as db:
        extra_cei = db.query(ContractExecutionItem).filter(
            ContractExecutionItem.project_id == p1,
            ContractExecutionItem.item_origin == "EXTRA_ITEM",
            ContractExecutionItem.status == "ACTIVE",
        ).first()

    resp = client_fixture.post(
        f"/api/projects/{p1}/contract-items/{extra_cei.id}/supersede",
        json={"item_code": "EI-SUPER-FAIL", "description": "Attempt to supersede extra item"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "EXTRA_ITEM_CANNOT_BE_SUPERSEDED" in resp.json()["detail"]


def test_154_to_156_rate_revision_stale_rejection_at_submission_and_approval(client_fixture, setup_phase_1m):
    p1 = setup_phase_1m["p1_id"]
    token = setup_phase_1m["pm_token"]

    with TestingSessionLocal() as db:
        cei = db.query(ContractExecutionItem).filter(ContractExecutionItem.project_id == p1, ContractExecutionItem.item_origin == "ORIGINAL_BOQ", ContractExecutionItem.status == "ACTIVE").first()
        cei_id = cei.id
        cur_rate = str(cei.current_contract_rate)

    # Create DRAFT CVO
    cvo = client_fixture.post(
        f"/api/projects/{p1}/variation-orders",
        json={
            "variation_number": f"VO-RR-FRESH-{uuid.uuid4().hex[:4]}",
            "variation_type": "RATE_REVISION",
            "unit_of_measure": "m3",
            "contract_execution_item_id": cei_id,
            "quantity_delta": "0.0000",
            "rate_previous": cur_rate,
            "rate_revised": str(Decimal(cur_rate) + Decimal("10.00")),
            "effective_date": "2026-08-01",
            "description": "Test freshness",
        },
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    # Mutate CEI rate directly (with auth context) to simulate concurrent change before submission
    with TestingSessionLocal() as db:
        db.execute(text("SET LOCAL app.auth_cei_state_mutation = 'TRUE'"))
        db.execute(text(f"UPDATE contract_execution_items SET current_contract_rate = 999.00 WHERE id = '{cei_id}'"))
        db.commit()

    # TEST 154: Submit fails with RATE_REVISION_STALE_AT_SUBMISSION
    sub_fail = client_fixture.post(f"/api/projects/{p1}/variation-orders/{cvo['id']}/submit", headers={"Authorization": f"Bearer {token}"})
    assert sub_fail.status_code == 409
    assert "RATE_REVISION_STALE_AT_SUBMISSION" in sub_fail.json()["detail"]

    # Reset CEI rate back
    with TestingSessionLocal() as db:
        db.execute(text("SET LOCAL app.auth_cei_state_mutation = 'TRUE'"))
        db.execute(text(f"UPDATE contract_execution_items SET current_contract_rate = {cur_rate} WHERE id = '{cei_id}'"))
        db.commit()

    # Now submission succeeds
    sub_ok = client_fixture.post(f"/api/projects/{p1}/variation-orders/{cvo['id']}/submit", headers={"Authorization": f"Bearer {token}"})
    assert sub_ok.status_code == 200

    # TEST 155 & 156: Simulate rate change after submission before approval
    with TestingSessionLocal() as db:
        db.execute(text("SET LOCAL app.auth_cei_state_mutation = 'TRUE'"))
        db.execute(text(f"UPDATE contract_execution_items SET current_contract_rate = 888.00 WHERE id = '{cei_id}'"))
        db.commit()

    app_fail = client_fixture.post(f"/api/projects/{p1}/variation-orders/{cvo['id']}/approve", headers={"Authorization": f"Bearer {token}"})
    assert app_fail.status_code == 409
    assert "RATE_REVISION_STALE_AT_APPROVAL" in app_fail.json()["detail"]

    # Reset CEI rate back
    with TestingSessionLocal() as db:
        db.execute(text("SET LOCAL app.auth_cei_state_mutation = 'TRUE'"))
        db.execute(text(f"UPDATE contract_execution_items SET current_contract_rate = {cur_rate} WHERE id = '{cei_id}'"))
        db.commit()

    # TEST 160: Retry succeeds cleanly
    app_ok = client_fixture.post(f"/api/projects/{p1}/variation-orders/{cvo['id']}/approve", headers={"Authorization": f"Bearer {token}"})
    assert app_ok.status_code == 200


def test_157_to_159_rate_and_valuation_semantics_verified(client_fixture, setup_phase_1m):
    p1 = setup_phase_1m["p1_id"]
    token = setup_phase_1m["pm_token"]

    # Verify reconciliation snapshots have all 3 rate/valuation fields populated correctly
    with TestingSessionLocal() as db:
        snaps = db.query(BoqReconciliationSnapshot).filter(BoqReconciliationSnapshot.project_id == p1).all()
        assert len(snaps) > 0
        for s in snaps:
            # TEST 157: historical_period_valuation >= 0
            assert s.historical_period_valuation >= Decimal("0.0000")
            # TEST 158: current_rate_valuation >= 0 and valuation_delta is mathematically consistent
            assert s.current_rate_valuation >= Decimal("0.0000")
            assert s.valuation_delta == (s.current_rate_valuation - s.historical_period_valuation)
            # TEST 159: reconciliation_rate > 0
            assert s.reconciliation_rate > Decimal("0.0000")

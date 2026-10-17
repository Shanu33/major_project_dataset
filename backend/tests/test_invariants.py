import pytest
import os
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import engine, get_db
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_migration_objects_exist():
    db = TestingSessionLocal()
    idx = db.execute(text("SELECT indexname FROM pg_indexes WHERE indexname = 'uq_active_baseline'")).scalar()
    assert idx == 'uq_active_baseline', "uq_active_baseline index missing"
    
    trgs = db.execute(text("SELECT tgname FROM pg_trigger WHERE tgname IN ('prevent_update_delete_report_trg', 'prevent_audit_modification_trg')")).scalars().all()
    assert 'prevent_update_delete_report_trg' in trgs, "Report immutability trigger missing"
    assert 'prevent_audit_modification_trg' in trgs, "Audit immutability trigger missing"
    db.close()

def test_role_security_bootstrap():
    res = client.post("/api/auth/register/admin", json={"email": "admin1@test.com", "password": "pass", "role": "contractor"})
    assert res.status_code == 200
    assert res.json()["role"] == "admin"
    
    res = client.post("/api/auth/register/admin", json={"email": "admin2@test.com", "password": "pass", "role": "admin"})
    assert res.status_code == 403
    
    res = client.post("/api/auth/register/public", json={"email": "hacker@test.com", "password": "pass"})
    assert res.status_code == 200
    assert res.json()["role"] == "contractor"

def test_auth_and_project_creation():
    res_a = client.post("/api/auth/login", data={"username": "admin1@test.com", "password": "pass"})
    admin_token = res_a.json()["access_token"]

    client.post("/api/auth/users", json={"email": "c1@test.com", "password": "p", "role": "contractor"}, headers={"Authorization": f"Bearer {admin_token}"})
    client.post("/api/auth/users", json={"email": "c2@test.com", "password": "p", "role": "contractor"}, headers={"Authorization": f"Bearer {admin_token}"})
    client.post("/api/auth/users", json={"email": "s1@test.com", "password": "p", "role": "supervisor"}, headers={"Authorization": f"Bearer {admin_token}"})
    
    c1_t = client.post("/api/auth/login", data={"username": "c1@test.com", "password": "p"}).json()["access_token"]
    c2_t = client.post("/api/auth/login", data={"username": "c2@test.com", "password": "p"}).json()["access_token"]
    s1_t = client.post("/api/auth/login", data={"username": "s1@test.com", "password": "p"}).json()["access_token"]
    
    res = client.post("/api/projects/", json={"name": "P1"}, headers={"Authorization": f"Bearer {c1_t}"})
    assert res.status_code == 200
    project_id = res.json()["id"]
    
    res = client.get(f"/api/projects/{project_id}", headers={"Authorization": f"Bearer {c2_t}"})
    assert res.status_code == 403
    
    db = TestingSessionLocal()
    s1_id = db.execute(text("SELECT id FROM users WHERE email = 's1@test.com'")).scalar()
    db.close()
    
    res = client.post(f"/api/projects/{project_id}/members?user_id={s1_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    
    res = client.get(f"/api/projects/{project_id}", headers={"Authorization": f"Bearer {s1_t}"})
    assert res.status_code == 200
    
    return project_id, c1_t, s1_t, c2_t, admin_token

def test_baseline_freeze():
    project_id, c1_t, s1_t, c2_t, admin_t = test_auth_and_project_creation()
    
    res = client.post(f"/api/projects/{project_id}/baselines/freeze", json={}, headers={"Authorization": f"Bearer {c1_t}"})
    assert res.status_code == 403
    
    res = client.post(f"/api/projects/{project_id}/baselines/freeze", json={"reason_for_revision": "Initial"}, headers={"Authorization": f"Bearer {s1_t}"})
    assert res.status_code == 200
    assert res.json()["revision_number"] == 0
    
    res = client.post(f"/api/projects/{project_id}/baselines/freeze", json={"reason_for_revision": "Rev 1"}, headers={"Authorization": f"Bearer {s1_t}"})
    assert res.status_code == 200
    assert res.json()["revision_number"] == 1
    
    db = TestingSessionLocal()
    active_count = db.execute(text(f"SELECT COUNT(*) FROM project_baselines WHERE project_id='{project_id}' AND is_active=true")).scalar()
    db.close()
    assert active_count == 1
    
    return project_id, c1_t, s1_t

def test_report_immutability():
    project_id, c1_t, s1_t = test_baseline_freeze()
    
    res = client.post(
        f"/api/projects/{project_id}/reports/",
        json={"contractor_declared_work": {"concrete": 10}},
        headers={"Authorization": f"Bearer {c1_t}"}
    )
    assert res.status_code == 200
    report_id = res.json()["id"]
    
    res = client.delete(f"/api/projects/{project_id}/reports/{report_id}", headers={"Authorization": f"Bearer {c1_t}"})
    assert res.status_code == 405
    
    db = TestingSessionLocal()
    try:
        db.execute(text(f"DELETE FROM daily_reports WHERE id='{report_id}'"))
        db.commit()
        pytest.fail("DELETE on daily_reports succeeded, trigger failed!")
    except Exception as e:
        db.rollback()
        assert "Cannot update or delete" in str(e) or "Cannot update or delete a finalized daily report" in str(e)
        
    try:
        db.execute(text(f"UPDATE daily_reports SET is_finalized=false WHERE id='{report_id}'"))
        db.commit()
        pytest.fail("UPDATE on daily_reports succeeded, trigger failed!")
    except Exception as e:
        db.rollback()
        assert "Cannot update or delete" in str(e) or "Cannot update or delete a finalized daily report" in str(e)
    db.close()

def test_audit_log_immutability():
    db = TestingSessionLocal()
    
    try:
        db.execute(text("DELETE FROM audit_log"))
        db.commit()
        pytest.fail("DELETE on audit_log succeeded, trigger failed!")
    except Exception as e:
        db.rollback()
        assert "Audit log records" in str(e) or "append-only" in str(e)

    try:
        db.execute(text("UPDATE audit_log SET action='HACKED'"))
        db.commit()
        pytest.fail("UPDATE on audit_log succeeded, trigger failed!")
    except Exception as e:
        db.rollback()
        assert "Audit log records" in str(e) or "append-only" in str(e)
        
    db.close()

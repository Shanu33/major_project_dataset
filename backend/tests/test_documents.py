import pytest
import os
import hashlib
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import get_db, engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.storage.service import storage

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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
    
    # 1. Admin login/creation
    res = client_fixture.post("/api/auth/register/admin", json={"email": "admin_doc@test.com", "password": "pass", "role": "admin"})
    
    # 2. Contractor and Supervisor creation
    admin_token = client_fixture.post("/api/auth/login", data={"username": "admin_doc@test.com", "password": "pass"}).json()["access_token"]
    client_fixture.post("/api/auth/users", json={"email": "c1_doc@test.com", "password": "p", "role": "contractor"}, headers={"Authorization": f"Bearer {admin_token}"})
    client_fixture.post("/api/auth/users", json={"email": "c2_doc@test.com", "password": "p", "role": "contractor"}, headers={"Authorization": f"Bearer {admin_token}"})
    
    c1_token = client_fixture.post("/api/auth/login", data={"username": "c1_doc@test.com", "password": "p"}).json()["access_token"]
    c2_token = client_fixture.post("/api/auth/login", data={"username": "c2_doc@test.com", "password": "p"}).json()["access_token"]
    
    # 3. Create projects
    res = client_fixture.post("/api/projects/", json={"name": "Project 1"}, headers={"Authorization": f"Bearer {c1_token}"})
    p1_id = res.json()["id"]
    
    res = client_fixture.post("/api/projects/", json={"name": "Project 2"}, headers={"Authorization": f"Bearer {c2_token}"})
    p2_id = res.json()["id"]
    
    return p1_id, p2_id, c1_token, c2_token

def test_successful_pdf_upload(client_fixture, setup_auth):
    p1_id, p2_id, c1_token, c2_token = setup_auth
    
    file_content = b"%PDF-1.4 Fake PDF content"
    files = {'file': ('test.pdf', file_content, 'application/pdf')}
    data = {'document_type': 'ARCHITECTURAL_DRAWING'}
    
    res = client_fixture.post(
        f"/api/projects/{p1_id}/documents/",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 200
    doc = res.json()
    
    # B. Document metadata is persisted correctly.
    assert doc["project_id"] == p1_id
    assert doc["original_filename"] == "test.pdf"
    assert doc["document_type"] == "ARCHITECTURAL_DRAWING"
    assert doc["mime_type"] == "application/pdf"
    assert doc["file_size_bytes"] == len(file_content)
    assert doc["processing_status"] == "UPLOADED"
    
    # C. SHA-256 hash is correct.
    expected_hash = hashlib.sha256(file_content).hexdigest()
    assert doc["sha256_hash"] == expected_hash
    
    # D. File actually exists in configured storage.
    db = TestingSessionLocal()
    db_doc = db.execute(text(f"SELECT storage_key FROM documents WHERE id='{doc['id']}'")).fetchone()
    db.close()
    
    storage_key = db_doc[0]
    assert storage.exists(storage_key)
    
    # E. Original filename is preserved only as metadata (not as the storage path)
    assert storage_key != "test.pdf"
    assert storage_key.endswith(".pdf")
    
    # O. Successful upload creates an audit event.
    db = TestingSessionLocal()
    audit_count = db.execute(text(f"SELECT COUNT(*) FROM audit_log WHERE action='DOCUMENT_UPLOADED' AND entity_id='{doc['id']}'")).scalar()
    db.close()
    assert audit_count == 1
    
    return doc, expected_hash, file_content

def test_path_traversal_prevention(client_fixture, setup_auth):
    p1_id, p2_id, c1_token, c2_token = setup_auth
    file_content = b"%PDF-1.4 Malicious"
    
    # F. Storage path/key cannot be controlled through malicious filename input.
    files = {'file': ('../../../etc/passwd.pdf', file_content, 'application/pdf')}
    data = {'document_type': 'UNKNOWN'}
    
    res = client_fixture.post(
        f"/api/projects/{p1_id}/documents/",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 200
    
    db = TestingSessionLocal()
    db_doc = db.execute(text(f"SELECT storage_key FROM documents WHERE id='{res.json()['id']}'")).fetchone()
    db.close()
    
    storage_key = db_doc[0]
    # Verify that the actual path doesn't contain the traversal elements
    full_path = storage.get(storage_key)
    assert "../" not in full_path

def test_unsupported_file_type(client_fixture, setup_auth):
    p1_id, p2_id, c1_token, c2_token = setup_auth
    
    # G. Unsupported file type is rejected.
    file_content = b"Fake EXE content"
    files = {'file': ('test.exe', file_content, 'application/x-msdownload')}
    
    res = client_fixture.post(
        f"/api/projects/{p1_id}/documents/",
        files=files,
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 400
    assert "Unsupported file format" in res.json()["detail"]

def test_file_size_limit(client_fixture, setup_auth, monkeypatch):
    p1_id, p2_id, c1_token, c2_token = setup_auth
    
    # Temporarily override settings.MAX_UPLOAD_SIZE
    from app.core.config import settings
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE", 10)
    
    # H. File exceeding configured size is rejected.
    file_content = b"%PDF-1.4 Huge content" # 21 bytes
    files = {'file': ('large.pdf', file_content, 'application/pdf')}
    
    res = client_fixture.post(
        f"/api/projects/{p1_id}/documents/",
        files=files,
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 400
    assert "File size exceeds limit" in res.json()["detail"]

def test_unauthorized_upload_access(client_fixture, setup_auth):
    p1_id, p2_id, c1_token, c2_token = setup_auth
    
    file_content = b"%PDF-1.4 Auth test"
    files = {'file': ('test.pdf', file_content, 'application/pdf')}
    
    # I. Unauthorized user cannot upload to another project. (c2 trying to upload to p1)
    res = client_fixture.post(
        f"/api/projects/{p1_id}/documents/",
        files=files,
        headers={"Authorization": f"Bearer {c2_token}"}
    )
    assert res.status_code == 403
    
    # J. Unauthorized user cannot access another project's documents.
    res = client_fixture.get(f"/api/projects/{p1_id}/documents/", headers={"Authorization": f"Bearer {c2_token}"})
    assert res.status_code == 403

def test_list_and_get_documents(client_fixture, setup_auth):
    p1_id, p2_id, c1_token, c2_token = setup_auth
    
    # K. Authorized project member can list documents.
    res = client_fixture.get(f"/api/projects/{p1_id}/documents/", headers={"Authorization": f"Bearer {c1_token}"})
    assert res.status_code == 200
    docs = res.json()
    assert len(docs) > 0 # From previous successful tests
    
    # L. Authorized project member can retrieve document metadata.
    doc_id = docs[0]["id"]
    res = client_fixture.get(f"/api/projects/{p1_id}/documents/{doc_id}", headers={"Authorization": f"Bearer {c1_token}"})
    assert res.status_code == 200
    assert res.json()["id"] == doc_id

def test_duplicate_document_policy(client_fixture, setup_auth):
    p1_id, p2_id, c1_token, c2_token = setup_auth
    
    file_content = b"%PDF-1.4 Duplicate content"
    files1 = {'file': ('dup.pdf', file_content, 'application/pdf')}
    
    res1 = client_fixture.post(f"/api/projects/{p1_id}/documents/", files=files1, headers={"Authorization": f"Bearer {c1_token}"})
    assert res1.status_code == 200
    
    # M. Duplicate content within the same project is rejected.
    files2 = {'file': ('dup2.pdf', file_content, 'application/pdf')}
    res2 = client_fixture.post(f"/api/projects/{p1_id}/documents/", files=files2, headers={"Authorization": f"Bearer {c1_token}"})
    assert res2.status_code == 409
    assert "identical content already exists" in res2.json()["detail"]
    
    # N. Same content in a different project is allowed.
    files3 = {'file': ('dup3.pdf', file_content, 'application/pdf')}
    res3 = client_fixture.post(f"/api/projects/{p2_id}/documents/", files=files3, headers={"Authorization": f"Bearer {c2_token}"})
    assert res3.status_code == 200
    assert res3.json()["sha256_hash"] == res1.json()["sha256_hash"]

def test_db_failure_cleanup(client_fixture, setup_auth, monkeypatch):
    p1_id, p2_id, c1_token, c2_token = setup_auth
    
    # P. Database failure does not leave an orphaned file.
    # We will simulate a database failure by patching db.commit() to raise an exception
    import sqlalchemy.orm
    original_commit = sqlalchemy.orm.Session.commit
    def mock_commit(*args, **kwargs):
        raise Exception("Mock DB Failure")
    
    monkeypatch.setattr("sqlalchemy.orm.Session.commit", mock_commit)
    
    file_content = b"%PDF-1.4 Failure content"
    files = {'file': ('fail.pdf', file_content, 'application/pdf')}
    
    res = client_fixture.post(
        f"/api/projects/{p1_id}/documents/",
        files=files,
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    assert res.status_code == 500
    assert "Database transaction failed" in res.json()["detail"]
    
    # Find the orphaned file in storage. It shouldn't exist.
    # Since we don't have the storage key easily, we check if ANY file with this content exists.
    # A bit hard to verify without hooking, but we can verify our directory state hasn't grown unmanaged.
    # Let's write a small patch on local storage to capture the key
    saved_key = None
    original_save = storage.save
    def mock_save(key, obj):
        nonlocal saved_key
        saved_key = key
        original_save(key, obj)
        
    monkeypatch.setattr(storage, "save", mock_save)
    
    # Try again
    res = client_fixture.post(
        f"/api/projects/{p1_id}/documents/",
        files=files,
        headers={"Authorization": f"Bearer {c1_token}"}
    )
    
    assert saved_key is not None
    assert not storage.exists(saved_key) # Confirm file was cleaned up!

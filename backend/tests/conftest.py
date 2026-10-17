import os
os.environ["TESTING"] = "1"
os.environ["SECRET_KEY"] = "test_key_for_ci_cd"

import pytest
from app.db.database import engine
from sqlalchemy import text
from alembic.config import Config
from alembic import command

@pytest.fixture(scope="module", autouse=True)
def setup_db_session():
    alembic_cfg = Config("alembic.ini")
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    command.upgrade(alembic_cfg, "head")
    yield
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))

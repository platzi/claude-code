"""
Shared pytest fixtures.
"""
import pytest
from sqlalchemy.orm import Session
from app.db.base import engine


@pytest.fixture
def db_session():
    """
    Transactional database session for tests that hit the real database.

    Everything runs inside an outer transaction that is rolled back at the end,
    so tests never leave data behind in platziflix_db. session.commit() inside
    a test only releases a SAVEPOINT (join_transaction_mode="create_savepoint").
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    yield session

    session.close()
    transaction.rollback()
    connection.close()

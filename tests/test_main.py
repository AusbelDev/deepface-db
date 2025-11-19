import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import Base, app, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown_database():
    # Create the tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop the tables
    Base.metadata.drop_all(bind=engine)


def test_create_user():
    response = client.post(
        "/users/",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "phone": "1234567890",
            "birthday": "2000-01-01",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data


def test_read_user():
    # First, create a user to read
    response = client.post(
        "/users/",
        json={
            "name": "Test User 2",
            "email": "test2@example.com",
            "phone": "0987654321",
            "birthday": "2000-01-02",
        },
    )
    assert response.status_code == 200
    user_id = response.json()["id"]

    # Now, read the user
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test2@example.com"


def test_read_users():
    response = client.get("/users/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_update_user():
    # First, create a user to update
    response = client.post(
        "/users/",
        json={
            "name": "Test User 3",
            "email": "test3@example.com",
            "phone": "1122334455",
            "birthday": "2000-01-03",
        },
    )
    assert response.status_code == 200
    user_id = response.json()["id"]

    # Now, update the user
    response = client.put(
        f"/users/{user_id}",
        json={
            "name": "Updated Test User 3",
            "email": "test3.updated@example.com",
            "phone": "5544332211",
            "birthday": "2000-01-04",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Test User 3"
    assert data["email"] == "test3.updated@example.com"


def test_delete_user():
    # First, create a user to delete
    response = client.post(
        "/users/",
        json={
            "name": "Test User 4",
            "email": "test4@example.com",
            "phone": "6677889900",
            "birthday": "2000-01-05",
        },
    )
    assert response.status_code == 200
    user_id = response.json()["id"]

    # Now, delete the user
    response = client.delete(f"/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id

    # Verify the user is deleted
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 404

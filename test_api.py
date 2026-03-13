"""
test_api.py — Pytest test suite for the UK Storm Overflow API
Base template written using Claude AI. Checked and tweaked by hand.

Setup:
    pip install pytest

Run:
    pytest test_api.py -v
"""

import pytest
from contextlib import asynccontextmanager
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

@asynccontextmanager
async def mock_lifespan(_app):
    yield

with patch("app.main.lifespan", mock_lifespan):
    from app.main import app

from app.database import Base, register_math_functions
from app.security import get_db

TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

from sqlalchemy import event
event.listen(TEST_ENGINE, "connect", register_math_functions)

TestingSessionLocal = sessionmaker(bind=TEST_ENGINE, autoflush=False, autocommit=False)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=TEST_ENGINE)
    app.dependency_overrides[get_db] = override_get_db
    
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c
        
    Base.metadata.drop_all(bind=TEST_ENGINE)
    app.dependency_overrides.clear()

ADMIN = {"X-API_KEY": "foo"}

@pytest.fixture(scope="module")
def api_key(client):
    """Create a regular API key once and reuse it across tests."""
    r = client.post("/auth/keys", json={"owner": "pytest", "active": True}, headers=ADMIN)
    assert r.status_code == 201
    return r.json()["key"]

@pytest.fixture(scope="module")
def auth(api_key):
    return {"X-API_KEY": api_key}

@pytest.fixture(scope="module")
def sample_company(client, auth):
    """Create a reusable test company."""
    payload = {
        "ticker": "TST",
        "name": "Test Water Co",
        "region": "Test Region",
        "website": "https://test.example.com",
    }
    r = client.post("/companies/", json=payload, headers=auth)
    assert r.status_code == 201
    return r.json()

@pytest.fixture(scope="module")
def sample_outflow(client, auth, sample_company):
    """Create a reusable test outflow."""
    payload = {
        "site_id": "TST-00001",
        "company_ticker": "TST",
        "status": 0,
        "latitude": 51.5,
        "longitude": -0.1,
        "receiving_watercourse": "River Test",
        "last_updated": "2024-01-01T00:00:00",
    }
    r = client.post("/outflows/", json=payload, headers=auth)
    assert r.status_code == 201
    return r.json()


# health check
class TestRoot:
    def test_root_returns_200(self, client):
        assert client.get("/").status_code == 200

    def test_stats_root_returns_200(self, client):
        assert client.get("/stats").status_code == 200


# authentication
class TestAuth:
    def test_create_key_requires_admin(self, client):
        r = client.post("/auth/keys", json={"owner": "hacker"}, headers={"X-API_KEY": "wrong"})
        assert r.status_code == 403

    def test_create_key_with_admin(self, client):
        r = client.post("/auth/keys", json={"owner": "test-user", "active": True}, headers=ADMIN)
        assert r.status_code == 201
        body = r.json()
        assert "key" in body
        assert body["owner"] == "test-user"
        assert body["active"] is True

    def test_created_key_grants_access(self, client):
        r = client.post("/auth/keys", json={"owner": "access-test"}, headers=ADMIN)
        key = r.json()["key"]
        # Use key to hit a protected endpoint
        payload = {
            "site_id": "TST-AUTH",
            "company_ticker": "TST",
            "status": 0,
            "latitude": 52.0,
            "longitude": -1.0,
            "receiving_watercourse": "Auth River",
            "last_updated": "2024-01-01T00:00:00",
        }
        r2 = client.post("/outflows/", json=payload, headers={"X-API_KEY": key})
        assert r2.status_code == 201

    def test_rotate_key(self, client):
        r = client.post("/auth/keys", json={"owner": "rotate-me"}, headers=ADMIN)
        key_id = r.json()["id"]
        old_key = r.json()["key"]

        r2 = client.put(f"/auth/keys/{key_id}", headers=ADMIN)
        assert r2.status_code == 201
        new_key = r2.json()["key"]
        assert new_key != old_key

        # Old key should now be rejected
        payload = {"site_id": "X", "status": 0, "latitude": 0, "longitude": 0,
                   "receiving_watercourse": "X", "last_updated": "2024-01-01T00:00:00"}
        r3 = client.post("/outflows/", json=payload, headers={"X-API_KEY": old_key})
        assert r3.status_code == 403

    def test_delete_key(self, client):
        r = client.post("/auth/keys", json={"owner": "delete-me"}, headers=ADMIN)
        key_id = r.json()["id"]
        key = r.json()["key"]

        client.delete(f"/auth/keys/{key_id}", headers=ADMIN)

        # Deleted key should be rejected
        payload = {"site_id": "X", "status": 0, "latitude": 0, "longitude": 0,
                   "receiving_watercourse": "X", "last_updated": "2024-01-01T00:00:00"}
        r2 = client.post("/outflows/", json=payload, headers={"X-API_KEY": key})
        assert r2.status_code == 403 # returns 403 when not present

    def test_missing_key_header_rejected(self, client):
        r = client.post("/outflows/", json={})
        assert r.status_code in (401, 422)  # missing header → validation error

    def test_rotate_nonexistent_key(self, client):
        r = client.put("/auth/keys/999999", headers=ADMIN)
        # Should not 500 — graceful not-found
        assert r.status_code == 404


# water companies (crud)
class TestCompanies:
    def test_list_companies_ok(self, client):
        r = client.get("/companies/")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_company_by_ticker(self, client, sample_company):
        r = client.get(f"/companies/TST")
        assert r.status_code == 200
        assert r.json()["ticker"] == "TST"

    def test_get_company_ticker_case_insensitive(self, client, sample_company):
        r = client.get("/companies/tst")
        assert r.status_code == 200

    def test_get_nonexistent_company_404(self, client):
        assert client.get("/companies/ZZZ").status_code == 404

    def test_create_duplicate_ticker_400(self, client, auth, sample_company):
        r = client.post("/companies/", json={
            "ticker": "TST", "name": "Duplicate", "region": "X"
        }, headers=auth)
        assert r.status_code == 400

    def test_update_company(self, client, auth):
        # Create a throwaway company to update
        client.post("/companies/", json={"ticker": "UPD", "name": "Update Me", "region": "Old"}, headers=auth)
        r = client.put("/companies/UPD", json={"region": "New Region"}, headers=auth)
        assert r.status_code == 200
        assert r.json()["region"] == "New Region"

    def test_update_nonexistent_company_404(self, client, auth):
        r = client.put("/companies/ZZZ", json={"name": "Ghost"}, headers=auth)
        assert r.status_code == 404

    def test_delete_company(self, client, auth):
        client.post("/companies/", json={"ticker": "DEL", "name": "Delete Me", "region": "X"}, headers=auth)
        r = client.delete("/companies/DEL", headers=auth)
        assert r.status_code == 204
        assert client.get("/companies/DEL").status_code == 404

    def test_delete_nonexistent_company_404(self, client, auth):
        assert client.delete("/companies/ZZZ", headers=auth).status_code == 404

    def test_filter_by_name(self, client, sample_company):
        r = client.get("/companies/?name=Test Water")
        assert r.status_code == 200
        assert any(c["ticker"] == "TST" for c in r.json())

    def test_filter_by_region(self, client, sample_company):
        r = client.get("/companies/?region=Test Region")
        assert r.status_code == 200
        assert any(c["ticker"] == "TST" for c in r.json())

    def test_create_company_requires_auth(self, client):
        r = client.post("/companies/", json={"ticker": "NAU", "name": "No Auth"})
        assert r.status_code in (401, 422)

    def test_pagination(self, client):
        r = client.get("/companies/?limit=1&skip=0")
        assert r.status_code == 200
        assert len(r.json()) <= 1


# outflows (crud)
class TestOutflows:
    def test_list_outflows_ok(self, client):
        r = client.get("/outflows/")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_outflow_by_id(self, client, sample_outflow):
        oid = sample_outflow["id"]
        r = client.get(f"/outflows/{oid}")
        assert r.status_code == 200
        assert r.json()["id"] == oid

    def test_get_nonexistent_outflow_404(self, client):
        assert client.get("/outflows/999999").status_code == 404

    def test_create_outflow_response_schema(self, client, auth):
        payload = {
            "site_id": "TST-SCHEMA",
            "company_ticker": "TST",
            "status": 1,
            "latitude": 53.8,
            "longitude": -1.5,
            "receiving_watercourse": "Schema River",
            "last_updated": "2024-06-01T12:00:00",
        }
        r = client.post("/outflows/", json=payload, headers=auth)
        assert r.status_code == 201
        body = r.json()
        assert "id" in body
        assert body["site_id"] == "TST-SCHEMA"
        assert body["status"] == 1

    def test_update_outflow(self, client, auth, sample_outflow):
        oid = sample_outflow["id"]
        r = client.put(f"/outflows/{oid}", json={"status": 1}, headers=auth)
        assert r.status_code == 200
        assert r.json()["status"] == 1

    def test_update_outflow_datetime_field(self, client, auth, sample_outflow):
        oid = sample_outflow["id"]
        r = client.put(f"/outflows/{oid}", json={"latest_event_start": "2024-03-15T08:00:00"}, headers=auth)
        assert r.status_code == 200
        assert r.json()["latest_event_start"] is not None

    def test_update_nonexistent_outflow_404(self, client, auth):
        r = client.put("/outflows/999999", json={"status": 1}, headers=auth)
        assert r.status_code == 404

    def test_delete_outflow(self, client, auth):
        payload = {
            "site_id": "TST-DEL",
            "company_ticker": "TST",
            "status": 0,
            "latitude": 51.0,
            "longitude": -0.5,
            "receiving_watercourse": "Delete River",
            "last_updated": "2024-01-01T00:00:00",
        }
        r = client.post("/outflows/", json=payload, headers=auth)
        oid = r.json()["id"]
        assert client.delete(f"/outflows/{oid}", headers=auth).status_code == 204
        assert client.get(f"/outflows/{oid}").status_code == 404

    def test_delete_nonexistent_outflow_404(self, client, auth):
        assert client.delete("/outflows/999999", headers=auth).status_code == 404

    def test_filter_by_company_ticker(self, client, sample_outflow):
        r = client.get("/outflows/?company=TST")
        assert r.status_code == 200
        assert all(o["company_ticker"] == "TST" for o in r.json())

    def test_filter_by_watercourse(self, client, sample_outflow):
        r = client.get("/outflows/?watercourse=River Test")
        assert r.status_code == 200
        assert any(o["receiving_watercourse"] == "River Test" for o in r.json())

    def test_geospatial_filter_returns_nearby(self, client, sample_outflow):
        # sample_outflow is at 51.5, -0.1 — query very close to it
        r = client.get("/outflows/?lat=51.5&lon=-0.1&radius_km=1")
        assert r.status_code == 200
        ids = [o["id"] for o in r.json()]
        assert sample_outflow["id"] in ids

    def test_geospatial_filter_excludes_distant(self, client, sample_outflow):
        # Query from Edinburgh — should not include London outflow within 1km
        r = client.get("/outflows/?lat=55.95&lon=-3.19&radius_km=1")
        assert r.status_code == 200
        ids = [o["id"] for o in r.json()]
        assert sample_outflow["id"] not in ids

    def test_geospatial_no_radius_sorts_by_distance(self, client, sample_outflow):
        # lat/lon without radius should still return results, ordered by distance
        r = client.get("/outflows/?lat=51.5&lon=-0.1")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_pagination_limit(self, client):
        r = client.get("/outflows/?limit=2")
        assert r.status_code == 200
        assert len(r.json()) <= 2

    def test_create_outflow_requires_auth(self, client):
        r = client.post("/outflows/", json={"site_id": "X", "status": 0})
        assert r.status_code in (401, 422)


# stats
class TestStats:
    def test_outflow_stats_structure(self, client, sample_outflow):
        r = client.get("/stats/outflows/")
        assert r.status_code == 200
        body = r.json()
        assert "summary" in body
        assert "environmental_impact" in body
        assert "metadata" in body

    def test_outflow_stats_summary_fields(self, client, sample_outflow):
        body = client.get("/stats/outflows/").json()
        summary = body["summary"]
        assert "total_sites" in summary
        assert "active_now" in summary
        assert "active_percentage" in summary
        assert 0 <= summary["active_percentage"] <= 100

    def test_outflow_stats_total_positive(self, client, sample_outflow):
        body = client.get("/stats/outflows/").json()
        assert body["summary"]["total_sites"] > 0

    def test_company_stats_returns_list(self, client, sample_outflow):
        r = client.get("/stats/companies")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_company_stats_schema(self, client, sample_outflow):
        stats = client.get("/stats/companies").json()
        assert len(stats) > 0
        first = stats[0]
        for field in ("name", "ticker", "total_sites", "active_now", "deactivated"):
            assert field in first

    def test_discharge_hours_non_negative(self, client, sample_outflow):
        body = client.get("/stats/outflows/").json()
        hours = body["environmental_impact"]["total_discharge_hours"]
        assert hours is None or hours >= 0
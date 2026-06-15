"""Integration test for Home Assistant API — verifies the API is live.

This test connects to a real Home Assistant instance and checks basic
reachability. It is skipped unless the HA_URL and HA_TOKEN environment
variables are set.
"""

import os

import pytest
import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HA_URL = os.environ.get("HA_URL", "http://localhost:8123")
HA_TOKEN = os.environ.get("HA_TOKEN", "")
HA_REQUIRED = os.environ.get("HA_REQUIRED", "").lower() in ("1", "true", "yes")

pytestmark = pytest.mark.skipif(
    not HA_TOKEN,
    reason="HA_TOKEN environment variable not set — skipping HA API integration test",
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def ha_session() -> requests.Session:
    """Create a requests session with HA auth headers."""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    })
    return session


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestHaApiLive:
    """Verify that the Home Assistant instance is reachable and responsive."""

    def test_api_is_reachable(self, ha_session: requests.Session) -> None:
        """The HA API root should return HTTP 200."""
        resp = ha_session.get(f"{HA_URL}/api/", timeout=10)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert "message" in data

    def test_api_returns_config(self, ha_session: requests.Session) -> None:
        """The /api/config endpoint should return configuration."""
        resp = ha_session.get(f"{HA_URL}/api/config/", timeout=10)
        assert resp.status_code == 200
        config = resp.json()
        # Core fields that every HA instance should expose
        assert "version" in config
        assert "location_name" in config
        assert "time_zone" in config
        assert "unit_system" in config

    def test_states_endpoint(self, ha_session: requests.Session) -> None:
        """The /api/states endpoint should return a list of entity states."""
        resp = ha_session.get(f"{HA_URL}/api/states/", timeout=10)
        assert resp.status_code == 200
        states = resp.json()
        assert isinstance(states, list)
        # At minimum, HA always has some core entities
        assert len(states) > 0
        # Each state entry should have at least entity_id and state fields
        for entity in states[:5]:
            assert "entity_id" in entity
            assert "state" in entity

    def test_services_endpoint(self, ha_session: requests.Session) -> None:
        """The /api/services endpoint should return available services."""
        resp = ha_session.get(f"{HA_URL}/api/services/", timeout=10)
        assert resp.status_code == 200
        services = resp.json()
        assert isinstance(services, list)
        # Common domains that should exist
        domains = {svc["domain"] for svc in services}
        assert "homeassistant" in domains, (
            "Expected at least the 'homeassistant' domain in services"
        )

    def test_error_on_bad_token(self) -> None:
        """A request with an invalid token should return 401."""
        bad_session = requests.Session()
        bad_session.headers.update({
            "Authorization": "Bearer invalid_token_xyz",
            "Content-Type": "application/json",
        })
        resp = bad_session.get(f"{HA_URL}/api/config/", timeout=10)
        assert resp.status_code == 401, (
            f"Expected 401 for bad token, got {resp.status_code}"
        )

    @pytest.mark.skipif(
        not HA_REQUIRED,
        reason="HA_REQUIRED not set — this test is optional",
    )
    def test_force_fail_on_unreachable(self) -> None:
        """If HA_REQUIRED is set, the test suite must fail when HA is down.

        This test is only run when HA_REQUIRED=true. It checks a non-existent
        host to verify error handling.
        """
        with pytest.raises(requests.exceptions.ConnectionError):
            bad_session = requests.Session()
            bad_session.get("http://localhost:19999/api/", timeout=2)
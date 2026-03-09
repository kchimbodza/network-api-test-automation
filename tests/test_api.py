import pytest
from app.api import app, DEVICES, ALARMS, SLA

AUTH = {"Authorization": "Bearer mvot-test-token-2026"}
BAD_AUTH = {"Authorization": "Bearer wrong-token"}


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        # Reset mutable state before each test
        DEVICES["dev-001"]["status"] = "online"
        ALARMS["alm-001"]["resolved"] = False
        ALARMS["alm-002"]["resolved"] = False
        yield client


# ── HEALTH ──────────────────────────────────────────────────────────────────

def test_health_returns_200(client):
    r = client.get("/health")
    assert r.status_code == 200

def test_health_returns_ok_status(client):
    r = client.get("/health")
    assert r.get_json()["status"] == "ok"

def test_health_requires_no_auth(client):
    r = client.get("/health")
    assert r.status_code == 200  # public endpoint


# ── AUTH ─────────────────────────────────────────────────────────────────────

def test_devices_no_token_returns_401(client):
    r = client.get("/devices")
    assert r.status_code == 401

def test_devices_wrong_token_returns_401(client):
    r = client.get("/devices", headers=BAD_AUTH)
    assert r.status_code == 401

def test_alarms_no_token_returns_401(client):
    r = client.get("/alarms")
    assert r.status_code == 401

def test_sla_no_token_returns_401(client):
    r = client.get("/sla/dev-001")
    assert r.status_code == 401

def test_resolve_no_token_returns_401(client):
    r = client.post("/alarms/alm-001/resolve")
    assert r.status_code == 401

def test_401_response_has_error_field(client):
    r = client.get("/devices")
    assert "error" in r.get_json()


# ── DEVICES ──────────────────────────────────────────────────────────────────

def test_get_devices_returns_200(client):
    r = client.get("/devices", headers=AUTH)
    assert r.status_code == 200

def test_get_devices_returns_list(client):
    r = client.get("/devices", headers=AUTH)
    assert isinstance(r.get_json(), list)

def test_get_devices_returns_correct_count(client):
    r = client.get("/devices", headers=AUTH)
    assert len(r.get_json()) == 2

def test_get_devices_have_required_fields(client):
    r = client.get("/devices", headers=AUTH)
    for device in r.get_json():
        assert "id" in device
        assert "name" in device
        assert "status" in device

def test_get_device_by_valid_id(client):
    r = client.get("/devices/dev-001", headers=AUTH)
    assert r.status_code == 200
    assert r.get_json()["id"] == "dev-001"

def test_get_device_name_is_correct(client):
    r = client.get("/devices/dev-001", headers=AUTH)
    assert r.get_json()["name"] == "Router-A"

def test_get_device_status_is_online(client):
    r = client.get("/devices/dev-001", headers=AUTH)
    assert r.get_json()["status"] == "online"

def test_get_device_offline_status(client):
    r = client.get("/devices/dev-002", headers=AUTH)
    assert r.get_json()["status"] == "offline"

def test_get_device_invalid_id_returns_404(client):
    r = client.get("/devices/dev-999", headers=AUTH)
    assert r.status_code == 404

def test_get_device_404_has_error_field(client):
    r = client.get("/devices/dev-999", headers=AUTH)
    assert "error" in r.get_json()


# ── ALARMS ───────────────────────────────────────────────────────────────────

def test_get_alarms_returns_200(client):
    r = client.get("/alarms", headers=AUTH)
    assert r.status_code == 200

def test_get_alarms_returns_list(client):
    r = client.get("/alarms", headers=AUTH)
    assert isinstance(r.get_json(), list)

def test_get_alarms_returns_correct_count(client):
    r = client.get("/alarms", headers=AUTH)
    assert len(r.get_json()) == 2

def test_alarms_have_required_fields(client):
    r = client.get("/alarms", headers=AUTH)
    for alarm in r.get_json():
        assert "id" in alarm
        assert "device_id" in alarm
        assert "severity" in alarm
        assert "resolved" in alarm

def test_alarm_severity_values_are_valid(client):
    valid = {"critical", "warning", "info"}
    r = client.get("/alarms", headers=AUTH)
    for alarm in r.get_json():
        assert alarm["severity"] in valid

def test_alarms_unresolved_by_default(client):
    r = client.get("/alarms", headers=AUTH)
    for alarm in r.get_json():
        assert alarm["resolved"] is False

def test_resolve_alarm_returns_200(client):
    r = client.post("/alarms/alm-001/resolve", headers=AUTH)
    assert r.status_code == 200

def test_resolve_alarm_sets_resolved_true(client):
    client.post("/alarms/alm-001/resolve", headers=AUTH)
    r = client.get("/alarms", headers=AUTH)
    alarm = next(a for a in r.get_json() if a["id"] == "alm-001")
    assert alarm["resolved"] is True

def test_resolve_alarm_only_affects_target(client):
    client.post("/alarms/alm-001/resolve", headers=AUTH)
    r = client.get("/alarms", headers=AUTH)
    alarm = next(a for a in r.get_json() if a["id"] == "alm-002")
    assert alarm["resolved"] is False

def test_resolve_invalid_alarm_returns_404(client):
    r = client.post("/alarms/alm-999/resolve", headers=AUTH)
    assert r.status_code == 404

def test_resolve_same_alarm_twice_stays_resolved(client):
    client.post("/alarms/alm-001/resolve", headers=AUTH)
    client.post("/alarms/alm-001/resolve", headers=AUTH)
    r = client.get("/alarms", headers=AUTH)
    alarm = next(a for a in r.get_json() if a["id"] == "alm-001")
    assert alarm["resolved"] is True


# ── SLA ───────────────────────────────────────────────────────────────────────

def test_get_sla_valid_device_returns_200(client):
    r = client.get("/sla/dev-001", headers=AUTH)
    assert r.status_code == 200

def test_get_sla_has_required_fields(client):
    r = client.get("/sla/dev-001", headers=AUTH)
    data = r.get_json()
    assert "device_id" in data
    assert "uptime_percent" in data
    assert "threshold" in data
    assert "compliant" in data

def test_sla_compliant_device_is_true(client):
    r = client.get("/sla/dev-001", headers=AUTH)
    assert r.get_json()["compliant"] is True

def test_sla_non_compliant_device_is_false(client):
    r = client.get("/sla/dev-002", headers=AUTH)
    assert r.get_json()["compliant"] is False

def test_sla_uptime_above_threshold_when_compliant(client):
    r = client.get("/sla/dev-001", headers=AUTH)
    data = r.get_json()
    assert data["uptime_percent"] >= data["threshold"]

def test_sla_uptime_below_threshold_when_non_compliant(client):
    r = client.get("/sla/dev-002", headers=AUTH)
    data = r.get_json()
    assert data["uptime_percent"] < data["threshold"]

def test_sla_invalid_device_returns_404(client):
    r = client.get("/sla/dev-999", headers=AUTH)
    assert r.status_code == 404

def test_sla_404_has_error_field(client):
    r = client.get("/sla/dev-999", headers=AUTH)
    assert "error" in r.get_json()


# ── EDGE CASES ────────────────────────────────────────────────────────────────

def test_unknown_route_returns_404(client):
    r = client.get("/unknown", headers=AUTH)
    assert r.status_code == 404

def test_wrong_method_on_devices_returns_405(client):
    r = client.post("/devices", headers=AUTH)
    assert r.status_code == 405

def test_wrong_method_on_health_returns_405(client):
    r = client.post("/health")
    assert r.status_code == 405

def test_all_responses_are_json(client):
    endpoints = ["/health", "/devices", "/alarms", "/sla/dev-001"]
    for endpoint in endpoints:
        r = client.get(endpoint, headers=AUTH)
        assert r.content_type == "application/json"

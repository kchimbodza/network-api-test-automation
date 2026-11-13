# Network API Test Automation

Automated functional test suite for a mock telecom network management REST API. Built to demonstrate API test design, CI/CD integration, and structured defect reporting.

![CI](https://github.com/kchimbodza/network-api-test-automation/actions/workflows/test.yml/badge.svg)

## Key results

- **42 automated tests, 42 passing**, locally and in GitHub Actions on every push to `main`.
- **CI history:** 5 runs, 4 green. The one red run was the first push, and it was a pipeline mistake, not a code bug (see [What worked and what didn't](#what-worked-and-what-didnt)).
- **Fast feedback:** the whole suite runs in about 0.1 s locally; a full CI job takes 13–28 s.

## Architecture

<p align="center"><img src="docs/architecture.svg" width="100%" alt="Lane 1, every push or pull request to main: checkout, Python 3.12 on ubuntu-latest, pip install requirements.txt, pytest runs 42 tests, report.html uploaded as an artifact even on failure. Lane 2, inside pytest for each test: a fixture resets alarm and device state, the Flask test client sends the request in-process, a bearer token check returns 401 if the token is missing or wrong, the Flask API serves 6 routes with JSON errors, and data comes from memory (2 devices, 2 alarms, 2 SLA records). Tests by group: health 3, auth 6, devices 10, alarms 11, SLA 8, edge cases 4."></p>

1. **The API** (`app/api.py`) is a small Flask app that stands in for a network management system: devices, alarms and SLA records, all behind a bearer token except `/health`.
2. **The tests** (`tests/test_api.py`) call it through Flask's test client. A fixture resets the data before every test.
3. **CI** (`.github/workflows/test.yml`) runs the suite on every push and pull request to `main` and uploads `report.html`.

**Why this architecture**

| Choice | Why |
|---|---|
| In-memory data (Python dicts) | Every run starts from the same known data, with no database to set up. |
| Flask test client, not a running server | No port, no start-up wait, no network: the suite runs in about 0.1 s. |
| One fixture that resets state | Resolving an alarm changes data; resetting it before each test keeps tests independent of order. |
| pytest-html | One self-contained `report.html` per run, easy to attach to a defect report. |
| GitHub Actions, report uploaded `if: always()` | Every change is tested on a clean machine, and a failed run still leaves its report. |

## What it tests

| Endpoint | Method | Coverage |
|---|---|---|
| `/health` | GET | Service availability |
| `/devices` | GET | List devices, field validation |
| `/devices/<id>` | GET | Single device, 404 handling |
| `/alarms` | GET | List alarms, field and value validation |
| `/alarms/<id>/resolve` | POST | State change, isolation, idempotency |
| `/sla/<device_id>` | GET | SLA compliance logic, 404 handling |

## Test breakdown

- 42 automated test cases across health, auth, devices, alarms, SLA, and edge cases
- Auth: valid token, missing token, wrong token
- Happy path: correct responses and field presence
- Error handling: 404, 401, 405
- State: alarm resolution affects only the target record
- Edge cases: unknown routes, wrong HTTP methods, JSON content-type on all responses

## Results

| Group | Tests | Result |
|---|---|---|
| Health | 3 | ✅ 3 passed |
| Auth | 6 | ✅ 6 passed |
| Devices | 10 | ✅ 10 passed |
| Alarms | 11 | ✅ 11 passed |
| SLA | 8 | ✅ 8 passed |
| Edge cases | 4 | ✅ 4 passed |
| **Total** | **42** | **✅ 42 passed in 0.11 s** |

<sub>Re-run on 2026-11-13: Linux, Python 3.14.8, Flask 3.1.3, pytest 9.2.0. CI uses Python 3.12.</sub>

**CI runs** ([Actions](https://github.com/kchimbodza/network-api-test-automation/actions))

| Date | Commit | Result | Time |
|---|---|---|---|
| 2026-03-09 | Add network management API with 42 automated tests | ❌ failed (exit code 127) | 24 s |
| 2026-03-09 | Fix requirements.txt | ✅ passed | 15 s |
| 2026-03-09 | Add README | ✅ passed | 13 s |
| 2026-03-09 | Add screenshots and update README | ✅ passed | 13 s |
| 2026-04-27 | Fix language detection | ✅ passed | 28 s |

## What worked and what didn't

| | What happened | Why / what I did |
|---|---|---|
| ✅ | 42/42 tests pass locally and in every CI run since the fix | Known data, reset before each test, so results repeat. |
| ✅ | State tests catch side effects | Resolving `alm-001` is checked to leave `alm-002` unresolved, and resolving twice stays resolved. |
| ❌ | First CI run failed with exit code 127 (command not found) | `requirements.txt` was committed empty, so nothing was installed. Adding the four dependencies fixed it on the next push. |
| ❌ | GitHub showed the repo as mostly HTML | The committed `report.html` counted as code. A `.gitattributes` rule (`linguist-detectable=false`) fixed it. |
| ⚠️ | Limits | It is a mock API with in-memory data and a token in the source, and tests run in-process, so real HTTP, a real database and load are not tested. CI now warns that the Node.js 20 actions it uses are deprecated. |

## Stack

Python 3.12 | Flask | pytest | pytest-html | GitHub Actions

## Screenshots

### API running
![API running](screenshots/01-api-running.png)

### Health check
![Health check](screenshots/02-health-check.png)

### Devices with valid auth
![Devices auth](screenshots/03-devices-auth.png)

### No auth — 401
![No auth 401](screenshots/04-no-auth-401.png)

### Invalid device — 404
![Device 404](screenshots/05-device-404.png)

### pytest — 42 passed
![pytest pass](screenshots/06-pytest-pass.png)

### HTML test report
![HTML report](screenshots/07-html-report.png)

### GitHub Actions CI
![GitHub Actions](screenshots/08-github-actions.png)

## Run locally
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. pytest
```

HTML report is generated at `report.html` after each run.

## Author

**Kudzayi Chimbodza** · [GitHub @kchimbodza](https://github.com/kchimbodza)

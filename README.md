# TripMate — Automated Test Framework

Built by Kiran Dsouza | QA Engineering Lead

A full-stack test automation framework for TripMate using **Playwright** (frontend) and **Python Requests** (backend API), with cross-browser support and CI/CD integration via GitHub Actions.

---

## Framework Structure

```
tests/
├── conftest.py                    # Shared fixtures, browser setup, screenshot on failure
├── pytest.ini                     # Test config, markers, HTML report settings
├── requirements.txt               # All dependencies
├── .env.example                   # Environment variables template
├── .github/
│   └── workflows/
│       └── test.yml               # CI/CD pipeline — GitHub Actions
├── tests/
│   ├── frontend/
│   │   ├── test_auth.py           # Login, Signup, Logout tests (12 checkpoints)
│   │   ├── test_trip_creation.py  # Trip creation tests (7 checkpoints)
│   │   └── test_ai_itinerary.py   # AI itinerary generation tests (7 checkpoints)
│   └── backend/
│       └── test_api.py            # Supabase + Netlify API tests (16 checkpoints)
└── reports/                       # Auto-generated HTML reports + screenshots
```

**Total: 42 automated checkpoints**

---

## Tech Stack

| Layer | Tool |
|---|---|
| Frontend UI Testing | Playwright (Python) |
| Backend API Testing | Python Requests |
| Test Runner | Pytest |
| Cross Browser | Chromium, Firefox, WebKit (Safari) |
| Reporting | pytest-html (HTML reports) |
| CI/CD | GitHub Actions |
| Test Data | Faker library |
| Environment | python-dotenv |

---

## Setup

### 1. Clone the repo and navigate to tests folder
```bash
cd tripmate/tests
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Install Playwright browsers
```bash
playwright install
```

### 4. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your actual values
```

---

## Running Tests

### Run smoke tests only (quick — 2-3 mins)
```bash
pytest -m smoke
```

### Run all frontend tests
```bash
pytest tests/frontend/
```

### Run all backend API tests
```bash
pytest tests/backend/
```

### Run full regression suite
```bash
pytest
```

### Run specific test file
```bash
pytest tests/frontend/test_auth.py
```

### Run on specific browser
```bash
pytest tests/frontend/ --browser firefox
pytest tests/frontend/ --browser webkit
```

### Run with visible browser (not headless)
```bash
HEADLESS=false pytest tests/frontend/
```

---

## Test Reports

HTML reports auto-generated after every run:
```
tests/reports/test_report.html
```

Open in browser to see:
- Pass/fail per test
- Screenshots on failure
- Full error details
- Test duration

---

## CI/CD Pipeline

### Triggers:
- **Every push to main/develop** → Smoke tests run automatically
- **Every pull request** → Smoke tests run automatically
- **Daily at 8am PST** → Full regression across all 3 browsers
- **Manual trigger** → Run any suite via GitHub Actions UI

### GitHub Secrets Required:
Add these in GitHub → Settings → Secrets → Actions:
```
BASE_URL
SUPABASE_URL
SUPABASE_ANON_KEY
TEST_USER_EMAIL
TEST_USER_PASSWORD
API_BASE_URL
```

---

## Test Markers

| Marker | What it runs |
|---|---|
| `smoke` | Quick happy path tests only |
| `regression` | Full suite |
| `frontend` | All Playwright UI tests |
| `backend` | All API tests |
| `auth` | Login/signup/logout tests |
| `trip` | Trip creation tests |
| `ai` | AI itinerary generation tests |

---

## Checkpoint Summary

| # | Area | Test | Type |
|---|---|---|---|
| 1-5 | Auth | Signup — happy path, duplicate, invalid email, weak password, empty | Frontend |
| 6-9 | Auth | Login — happy path, wrong password, no account, empty | Frontend |
| 10 | Auth | Login cross-browser — Chrome, Firefox, Safari | Frontend |
| 11-12 | Auth | Logout — success, session invalidated | Frontend |
| 13-18 | Trip | Create — happy path, validation, dates, dashboard, multiple | Frontend |
| 19 | Trip | Trip creation cross-browser | Frontend |
| 20-25 | AI | Generate — happy path, destination match, day count, loading, not empty, regenerate | Frontend |
| 26 | AI | AI generation cross-browser | Frontend |
| 27-31 | Auth API | Signup, duplicate, login, wrong password, non-existent | Backend |
| 32-36 | Trip API | Create, get, missing field, unauthenticated, delete | Backend |
| 37-42 | AI API | Generate, empty check, destination match, missing field, performance, empty body | Backend |

---

## Built With

- **Playwright** — Microsoft's modern browser automation library
- **pytest** — Python's most popular test framework
- **Supabase** — Backend database and auth
- **Netlify Functions** — Serverless Claude API proxy
- **GitHub Actions** — CI/CD automation

---

*TripMate Test Framework — built to demonstrate real-world QA automation at scale*

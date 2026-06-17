import pytest
import os
from playwright.sync_api import sync_playwright, Page, Browser
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://tripmateapp.netlify.app")
TEST_EMAIL = os.getenv("TEST_USER_EMAIL", "testuser@tripmate.com")
TEST_PASSWORD = os.getenv("TEST_USER_PASSWORD", "TestPassword123!")
TEST_NAME = os.getenv("TEST_USER_NAME", "TripMate Tester")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
SLOW_MO = int(os.getenv("SLOW_MO", "0"))


# ── Browser Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def browser_context_args():
    """Global browser context settings"""
    return {
        "viewport": {"width": 1280, "height": 720},
        "record_video_dir": "reports/videos/",
    }


@pytest.fixture(scope="session", params=["chromium", "firefox", "webkit"])
def cross_browser(request):
    """Cross browser fixture — runs tests on Chrome, Firefox, Safari"""
    with sync_playwright() as p:
        browser_type = getattr(p, request.param)
        browser = browser_type.launch(headless=HEADLESS, slow_mo=SLOW_MO)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=f"reports/videos/{request.param}/",
        )
        page = context.new_page()
        page.set_default_timeout(30000)
        yield page
        context.close()
        browser.close()


@pytest.fixture(scope="function")
def page_fixture():
    """Single browser fixture for quick tests — uses Chromium only"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS, slow_mo=SLOW_MO)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()
        page.set_default_timeout(30000)
        yield page
        context.close()
        browser.close()


# ── Auth Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def logged_in_page(page_fixture):
    """Returns a page that is already logged in — reused across tests"""
    page = page_fixture
    page.goto(BASE_URL)
    
    # Click login/signin button
    page.click("text=Sign In")
    
    # Fill credentials
    page.fill("input[type='email']", TEST_EMAIL)
    page.fill("input[type='password']", TEST_PASSWORD)
    
    # Submit
    page.click("button[type='submit']")
    
    # Wait for dashboard to load
    page.wait_for_url(f"{BASE_URL}/dashboard", timeout=10000)
    
    yield page


# ── API Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def api_headers():
    """Common headers for API requests"""
    return {
        "Content-Type": "application/json",
        "apikey": os.getenv("SUPABASE_ANON_KEY", ""),
        "Authorization": f"Bearer {os.getenv('SUPABASE_ANON_KEY', '')}",
    }


@pytest.fixture(scope="session")
def api_base_url():
    return os.getenv("API_BASE_URL", "https://tripmateapp.netlify.app/.netlify/functions")


# ── Helper: Screenshot on Failure ─────────────────────────────────────────────

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    
    if report.failed:
        # Take screenshot on any test failure
        if "page_fixture" in item.fixturenames:
            page = item.funcargs.get("page_fixture")
            if page:
                screenshot_path = f"reports/screenshots/{item.name}.png"
                os.makedirs("reports/screenshots", exist_ok=True)
                page.screenshot(path=screenshot_path)
                print(f"\nScreenshot saved: {screenshot_path}")

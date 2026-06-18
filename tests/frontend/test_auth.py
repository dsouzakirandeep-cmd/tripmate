"""
TripMate Frontend Tests — Authentication
Tests: User Signup, Login, Logout, Negative scenarios
"""
import pytest
import os
from faker import Faker

fake = Faker()
BASE_URL = os.getenv("BASE_URL", "https://tripmateapp.netlify.app")
TEST_EMAIL = os.getenv("TEST_USER_EMAIL", "testuser@tripmate.com")
TEST_PASSWORD = os.getenv("TEST_USER_PASSWORD", "TestPassword123!")


class TestUserSignup:
    """Test Suite: New User Registration"""

    @pytest.mark.frontend
    @pytest.mark.smoke
    @pytest.mark.auth
    def test_signup_happy_path(self, page_fixture):
        """
        CHECKPOINT 1: New user can successfully create an account
        """
        page = page_fixture
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        # Fill registration form directly — form is on home page
        page.fill("input[placeholder='Your name']", fake.name())
        page.fill("input[placeholder='Email address']", fake.email())
        page.fill("input[placeholder='Password']", "TestPass123!")

        # Click Create account
        page.click("text=Create account")

        # Verify success
        page.wait_for_timeout(3000)
        assert (
            page.locator("text=Verify your email").is_visible() or
            page.locator("text=Welcome").is_visible() or
            page.url != BASE_URL
        ), "Signup did not complete successfully"

    @pytest.mark.frontend
    @pytest.mark.auth
    def test_signup_duplicate_email(self, page_fixture):
        """
        CHECKPOINT 2: Duplicate email shows error
        """
        page = page_fixture
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        page.fill("input[placeholder='Your name']", "Duplicate User")
        page.fill("input[placeholder='Email address']", TEST_EMAIL)
        page.fill("input[placeholder='Password']", "TestPass123!")
        page.click("text=Create account")

        page.wait_for_timeout(3000)
        error = page.locator("text=already, text=exists, text=registered").first
        assert error.is_visible(timeout=5000), "No error shown for duplicate email"

    @pytest.mark.frontend
    @pytest.mark.auth
    def test_signup_empty_fields(self, page_fixture):
        """
        CHECKPOINT 3: Empty form submission blocked
        """
        page = page_fixture
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        # Click Create account without filling anything
        page.click("text=Create account")
        page.wait_for_timeout(1000)

        # Should stay on same page
        assert page.locator("input[placeholder='Email address']").is_visible(), \
            "Empty form was submitted"


class TestUserLogin:
    """Test Suite: User Login"""

    @pytest.mark.frontend
    @pytest.mark.smoke
    @pytest.mark.auth
    def test_login_happy_path(self, page_fixture):
        """
        CHECKPOINT 4: Valid credentials — user logs in successfully
        """
        page = page_fixture
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        # Click "Sign in" link
        page.click("text=Sign in")
        page.wait_for_timeout(1000)

        # Fill login form
        page.fill("input[placeholder='Email address']", TEST_EMAIL)
        page.fill("input[placeholder='Password']", TEST_PASSWORD)

        # Submit
        page.click("button[type='submit'], text=Sign in, text=Log in")
        page.wait_for_timeout(5000)

        # Verify logged in — URL changed or dashboard visible
        assert page.url != BASE_URL or \
               page.locator("text=My Trips, text=Dashboard, text=Sign out, text=Logout").first.is_visible(timeout=10000), \
               "User not logged in after valid credentials"

    @pytest.mark.frontend
    @pytest.mark.auth
    def test_login_wrong_password(self, page_fixture):
        """
        CHECKPOINT 5: Wrong password shows error
        """
        page = page_fixture
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        page.click("text=Sign in")
        page.wait_for_timeout(1000)

        page.fill("input[placeholder='Email address']", TEST_EMAIL)
        page.fill("input[placeholder='Password']", "WrongPassword999!")
        page.click("button[type='submit'], text=Sign in, text=Log in")

        page.wait_for_timeout(3000)
        error = page.locator("text=Invalid, text=incorrect, text=wrong, text=error").first
        assert error.is_visible(timeout=5000), "No error shown for wrong password"

    @pytest.mark.frontend
    @pytest.mark.auth
    def test_login_empty_fields(self, page_fixture):
        """
        CHECKPOINT 6: Empty login form blocked
        """
        page = page_fixture
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        page.click("text=Sign in")
        page.wait_for_timeout(1000)

        page.click("button[type='submit'], text=Sign in, text=Log in")
        page.wait_for_timeout(1000)

        assert page.locator("input[placeholder='Email address']").is_visible(), \
            "Empty login form submitted"

    @pytest.mark.frontend
    @pytest.mark.auth
    def test_login_cross_browser(self, cross_browser):
        """
        CHECKPOINT 7: Login works across Chrome, Firefox, Safari
        """
        page = cross_browser
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        page.click("text=Sign in")
        page.wait_for_timeout(1000)

        page.fill("input[placeholder='Email address']", TEST_EMAIL)
        page.fill("input[placeholder='Password']", TEST_PASSWORD)
        page.click("button[type='submit'], text=Sign in, text=Log in")
        page.wait_for_timeout(5000)

        assert page.url != BASE_URL or \
               page.locator("text=My Trips, text=Dashboard, text=Sign out").first.is_visible(timeout=10000), \
               f"Login failed on {page.context.browser.browser_type.name}"

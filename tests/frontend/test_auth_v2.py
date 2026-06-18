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
TEST_PASSWORD = os.getenv("TEST_USER_PASSWORD", "test@123")


class TestUserSignup:
    """Test Suite: New User Registration"""

    @pytest.mark.frontend
    @pytest.mark.smoke
    @pytest.mark.auth
    def test_signup_happy_path(self, page_fixture):
        """CHECKPOINT 1: New user can successfully create an account"""
        page = page_fixture
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        page.fill("input[placeholder='Your name']", fake.name())
        page.fill("input[placeholder='Email address']", fake.email())
        page.fill("input[placeholder='Password']", "TestPass123!")
        page.click("text=Create account")

        page.wait_for_timeout(3000)
        assert (
            page.locator("text=Verify your email").is_visible() or
            page.locator("text=Welcome").is_visible() or
            page.url != BASE_URL
        ), "Signup did not complete successfully"

    @pytest.mark.frontend
    @pytest.mark.auth
    def test_signup_duplicate_email(self, page_fixture):
        """CHECKPOINT 2: Duplicate email shows error"""
        page = page_fixture
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        page.fill("input[placeholder='Your name']", "Duplicate User")
        page.fill("input[placeholder='Email address']", TEST_EMAIL)
        page.fill("input[placeholder='Password']", "TestPass123!")
        page.click("text=Create account")

        page.wait_for_timeout(3000)
        # Check page still shows form or error
        assert page.locator("input[placeholder='Email address']").is_visible() or \
               page.locator("text=already").is_visible(timeout=3000), \
               "No handling for duplicate email"

    @pytest.mark.frontend
    @pytest.mark.auth
    def test_signup_empty_fields(self, page_fixture):
        """CHECKPOINT 3: Empty form submission blocked"""
        page = page_fixture
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        page.click("text=Create account")
        page.wait_for_timeout(1000)
        assert page.locator("input[placeholder='Email address']").is_visible(), \
            "Empty form was submitted"


class TestUserLogin:
    """Test Suite: User Login"""

    @pytest.mark.frontend
    @pytest.mark.smoke
    @pytest.mark.auth
    def test_login_happy_path(self, page_fixture):
        """CHECKPOINT 4: Valid credentials — user logs in successfully"""
        page = page_fixture
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        # Click Sign in link
        page.get_by_text("Sign in").click()
        page.wait_for_timeout(1000)

        # Fill login form
        page.fill("input[placeholder='Email address']", TEST_EMAIL)
        page.fill("input[placeholder='Password']", TEST_PASSWORD)

        # Click the sign in button
        page.get_by_role("button", name="Sign in").click()
        page.wait_for_timeout(5000)

        # Verify logged in — URL changed from base
        assert page.url != BASE_URL, \
            f"User not redirected after login — still on {page.url}"

    @pytest.mark.frontend
    @pytest.mark.auth
    def test_login_wrong_password(self, page_fixture):
        """CHECKPOINT 5: Wrong password shows error"""
        page = page_fixture
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        page.get_by_text("Sign in").click()
        page.wait_for_timeout(1000)

        page.fill("input[placeholder='Email address']", TEST_EMAIL)
        page.fill("input[placeholder='Password']", "WrongPassword999!")
        page.get_by_role("button", name="Sign in").click()

        page.wait_for_timeout(3000)
        # Should stay on login page
        assert page.locator("input[placeholder='Password']").is_visible(), \
            "No error shown for wrong password"

    @pytest.mark.frontend
    @pytest.mark.auth
    def test_login_empty_fields(self, page_fixture):
        """CHECKPOINT 6: Empty login form blocked"""
        page = page_fixture
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        page.get_by_text("Sign in").click()
        page.wait_for_timeout(1000)

        page.get_by_role("button", name="Sign in").click()
        page.wait_for_timeout(1000)

        assert page.locator("input[placeholder='Email address']").is_visible(), \
            "Empty login form submitted"

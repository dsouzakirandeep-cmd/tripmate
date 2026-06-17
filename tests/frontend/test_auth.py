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
        Steps: Navigate → Click Signup → Fill details → Submit → Verify success
        """
        page = page_fixture
        page.goto(BASE_URL)

        # Click signup
        page.click("text=Sign Up")

        # Fill registration form
        page.fill("input[name='name']", fake.name())
        page.fill("input[type='email']", fake.email())
        page.fill("input[type='password']", "TestPass123!")

        # Submit
        page.click("button[type='submit']")

        # Verify success — redirected or confirmation message shown
        assert (
            page.url != BASE_URL or
            page.locator("text=Verify your email").is_visible() or
            page.locator("text=Welcome").is_visible()
        ), "Signup did not complete successfully"

    @pytest.mark.frontend
    @pytest.mark.auth
    def test_signup_duplicate_email(self, page_fixture):
        """
        CHECKPOINT 2: Duplicate email shows error — not silent fail
        """
        page = page_fixture
        page.goto(BASE_URL)
        page.click("text=Sign Up")

        # Use already registered email
        page.fill("input[name='name']", "Duplicate User")
        page.fill("input[type='email']", TEST_EMAIL)
        page.fill("input[type='password']", "TestPass123!")
        page.click("button[type='submit']")

        # Expect error message
        error = page.locator("text=already registered, text=already exists, text=email taken").first
        assert error.is_visible(timeout=5000), "No error shown for duplicate email"

    @pytest.mark.frontend
    @pytest.mark.auth
    def test_signup_invalid_email_format(self, page_fixture):
        """
        CHECKPOINT 3: Invalid email format rejected
        """
        page = page_fixture
        page.goto(BASE_URL)
        page.click("text=Sign Up")

        page.fill("input[type='email']", "notanemail")
        page.fill("input[type='password']", "TestPass123!")
        page.click("button[type='submit']")

        # Either HTML5 validation or app error
        assert (
            page.locator("input[type='email']:invalid").count() > 0 or
            page.locator("text=valid email").is_visible(timeout=3000)
        ), "Invalid email was accepted"

    @pytest.mark.frontend
    @pytest.mark.auth
    def test_signup_weak_password(self, page_fixture):
        """
        CHECKPOINT 4: Weak password rejected
        """
        page = page_fixture
        page.goto(BASE_URL)
        page.click("text=Sign Up")

        page.fill("input[type='email']", fake.email())
        page.fill("input[type='password']", "123")
        page.click("button[type='submit']")

        error = page.locator("text=password, text=weak, text=characters").first
        assert error.is_visible(timeout=5000), "Weak password was accepted"

    @pytest.mark.frontend
    @pytest.mark.auth
    def test_signup_empty_fields(self, page_fixture):
        """
        CHECKPOINT 5: Empty form submission blocked
        """
        page = page_fixture
        page.goto(BASE_URL)
        page.click("text=Sign Up")
        page.click("button[type='submit']")

        # Should not navigate away
        assert "signup" in page.url.lower() or page.locator("input[type='email']").is_visible(), \
            "Empty form was submitted"


class TestUserLogin:
    """Test Suite: User Login"""

    @pytest.mark.frontend
    @pytest.mark.smoke
    @pytest.mark.auth
    def test_login_happy_path(self, page_fixture):
        """
        CHECKPOINT 6: Valid credentials — user logs in successfully
        """
        page = page_fixture
        page.goto(BASE_URL)
        page.click("text=Sign In")

        page.fill("input[type='email']", TEST_EMAIL)
        page.fill("input[type='password']", TEST_PASSWORD)
        page.click("button[type='submit']")

        # Verify dashboard loads
        page.wait_for_url(f"{BASE_URL}/dashboard", timeout=10000)
        assert "/dashboard" in page.url, "User not redirected to dashboard after login"

    @pytest.mark.frontend
    @pytest.mark.auth
    def test_login_wrong_password(self, page_fixture):
        """
        CHECKPOINT 7: Wrong password shows error — not silent fail
        """
        page = page_fixture
        page.goto(BASE_URL)
        page.click("text=Sign In")

        page.fill("input[type='email']", TEST_EMAIL)
        page.fill("input[type='password']", "WrongPassword999!")
        page.click("button[type='submit']")

        error = page.locator("text=Invalid, text=incorrect, text=wrong").first
        assert error.is_visible(timeout=5000), "No error shown for wrong password"

    @pytest.mark.frontend
    @pytest.mark.auth
    def test_login_nonexistent_email(self, page_fixture):
        """
        CHECKPOINT 8: Non-existent email shows error
        """
        page = page_fixture
        page.goto(BASE_URL)
        page.click("text=Sign In")

        page.fill("input[type='email']", "doesnotexist@tripmate.com")
        page.fill("input[type='password']", "TestPass123!")
        page.click("button[type='submit']")

        error = page.locator("text=Invalid, text=not found, text=no account").first
        assert error.is_visible(timeout=5000), "No error shown for non-existent email"

    @pytest.mark.frontend
    @pytest.mark.auth
    def test_login_empty_fields(self, page_fixture):
        """
        CHECKPOINT 9: Empty login form blocked
        """
        page = page_fixture
        page.goto(BASE_URL)
        page.click("text=Sign In")
        page.click("button[type='submit']")

        assert "signin" in page.url.lower() or \
               page.locator("input[type='email']").is_visible(), \
               "Empty login form submitted"

    @pytest.mark.frontend
    @pytest.mark.auth
    def test_login_cross_browser(self, cross_browser):
        """
        CHECKPOINT 10: Login works across Chrome, Firefox, Safari
        """
        page = cross_browser
        page.goto(BASE_URL)
        page.click("text=Sign In")

        page.fill("input[type='email']", TEST_EMAIL)
        page.fill("input[type='password']", TEST_PASSWORD)
        page.click("button[type='submit']")

        page.wait_for_url(f"{BASE_URL}/dashboard", timeout=10000)
        assert "/dashboard" in page.url, f"Login failed on {page.context.browser.browser_type.name}"


class TestUserLogout:
    """Test Suite: User Logout"""

    @pytest.mark.frontend
    @pytest.mark.auth
    def test_logout_success(self, logged_in_page):
        """
        CHECKPOINT 11: Logged in user can logout successfully
        """
        page = logged_in_page
        page.click("text=Logout, text=Sign Out")
        page.wait_for_url(BASE_URL, timeout=5000)

        assert "/dashboard" not in page.url, "User still on dashboard after logout"

    @pytest.mark.frontend
    @pytest.mark.auth
    def test_dashboard_inaccessible_after_logout(self, logged_in_page):
        """
        CHECKPOINT 12: Dashboard not accessible after logout — session invalidated
        """
        page = logged_in_page

        # Logout
        page.click("text=Logout, text=Sign Out")
        page.wait_for_url(BASE_URL, timeout=5000)

        # Try to access dashboard directly
        page.goto(f"{BASE_URL}/dashboard")

        # Should redirect to login
        assert "/dashboard" not in page.url or \
               page.locator("text=Sign In").is_visible(), \
               "Dashboard still accessible after logout — session not invalidated"

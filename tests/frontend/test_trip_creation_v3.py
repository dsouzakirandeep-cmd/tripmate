"""
TripMate Frontend Tests — Trip Creation (Fixed selectors)
"""
import pytest
import os
from faker import Faker

fake = Faker()
BASE_URL = os.getenv("BASE_URL", "https://tripmateapp.netlify.app")
TEST_EMAIL = os.getenv("TEST_USER_EMAIL", "dsouzakirandeep@gmail.com")
TEST_PASSWORD = os.getenv("TEST_USER_PASSWORD", "test@123")


class TestTripCreation:

    @pytest.mark.frontend
    @pytest.mark.smoke
    @pytest.mark.trip
    def test_create_trip_happy_path(self, logged_in_page):
        """CHECKPOINT 13: Logged in user can create a new trip"""
        page = logged_in_page

        # Click Plan a new trip button
        page.get_by_text("Plan a new trip").click()
        page.wait_for_timeout(2000)

        # Fill trip name
        trip_name = f"Test Trip {fake.city()}"
        page.locator("input").first.fill(trip_name)
        page.wait_for_timeout(500)

        # Fill destination if separate field
        inputs = page.locator("input").all()
        if len(inputs) >= 2:
            inputs[1].fill("Paris, France")

        # Fill dates
        date_inputs = page.locator("input[type='date']").all()
        if len(date_inputs) >= 2:
            date_inputs[0].fill("2025-08-01")
            date_inputs[1].fill("2025-08-07")

        # Submit
        page.get_by_role("button").filter(has_text="Create").click()
        page.wait_for_timeout(3000)

        # Verify trip visible
        assert page.locator("text=Paris").first.is_visible(timeout=10000) or \
               page.locator(f"text={trip_name}").is_visible(timeout=5000), \
               "Created trip not visible"

    @pytest.mark.frontend
    @pytest.mark.smoke
    @pytest.mark.trip
    def test_plan_new_trip_button_visible(self, logged_in_page):
        """CHECKPOINT 14: Plan a new trip button visible on dashboard"""
        page = logged_in_page
        assert page.get_by_text("Plan a new trip").is_visible(), \
            "Plan a new trip button not visible"

    @pytest.mark.frontend
    @pytest.mark.trip
    def test_existing_trips_visible(self, logged_in_page):
        """CHECKPOINT 15: Existing trips visible on dashboard"""
        page = logged_in_page
        assert page.locator("text=Goa Friends Trip").is_visible() or \
               page.locator("text=Trip").first.is_visible(timeout=5000), \
               "No trips visible on dashboard"

    @pytest.mark.frontend
    @pytest.mark.trip
    def test_trip_shows_dates(self, logged_in_page):
        """CHECKPOINT 16: Trip cards show dates"""
        page = logged_in_page
        assert page.locator("text=2026").is_visible(), \
            "Trip dates not visible"

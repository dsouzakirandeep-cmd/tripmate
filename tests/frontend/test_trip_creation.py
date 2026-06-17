"""
TripMate Frontend Tests — Trip Creation
Tests: Create trip, validate fields, edit, delete
"""
import pytest
import os
from faker import Faker

fake = Faker()
BASE_URL = os.getenv("BASE_URL", "https://tripmateapp.netlify.app")


class TestTripCreation:
    """Test Suite: Trip Creation Flow"""

    @pytest.mark.frontend
    @pytest.mark.smoke
    @pytest.mark.trip
    def test_create_trip_happy_path(self, logged_in_page):
        """
        CHECKPOINT 13: Logged in user can create a new trip successfully
        """
        page = logged_in_page

        # Click create trip
        page.click("text=Create Trip, text=New Trip, text=Add Trip")

        # Fill trip details
        page.fill("input[name='destination'], input[placeholder*='destination']", "Paris, France")
        page.fill("input[name='startDate'], input[type='date']", "2025-08-01")
        page.fill("input[name='endDate']", "2025-08-10")

        # Submit
        page.click("button[type='submit'], text=Create, text=Save")

        # Verify trip appears in list
        assert page.locator("text=Paris").is_visible(timeout=10000), \
            "Created trip not visible in trip list"

    @pytest.mark.frontend
    @pytest.mark.trip
    def test_create_trip_empty_destination(self, logged_in_page):
        """
        CHECKPOINT 14: Empty destination field blocked
        """
        page = logged_in_page
        page.click("text=Create Trip, text=New Trip, text=Add Trip")

        # Leave destination empty
        page.fill("input[name='startDate'], input[type='date']", "2025-08-01")
        page.click("button[type='submit'], text=Create")

        # Should show error or stay on form
        assert page.locator("input[name='destination']:invalid").count() > 0 or \
               page.locator("text=required, text=enter destination").is_visible(timeout=3000), \
               "Empty destination was accepted"

    @pytest.mark.frontend
    @pytest.mark.trip
    def test_create_trip_end_date_before_start(self, logged_in_page):
        """
        CHECKPOINT 15: End date before start date rejected
        """
        page = logged_in_page
        page.click("text=Create Trip, text=New Trip, text=Add Trip")

        page.fill("input[name='destination']", "Tokyo, Japan")
        page.fill("input[name='startDate']", "2025-08-10")
        page.fill("input[name='endDate']", "2025-08-01")  # Before start date
        page.click("button[type='submit'], text=Create")

        error = page.locator("text=invalid date, text=end date, text=before start").first
        assert error.is_visible(timeout=5000), "End date before start date was accepted"

    @pytest.mark.frontend
    @pytest.mark.trip
    def test_create_trip_past_date(self, logged_in_page):
        """
        CHECKPOINT 16: Past dates handled gracefully
        """
        page = logged_in_page
        page.click("text=Create Trip, text=New Trip, text=Add Trip")

        page.fill("input[name='destination']", "Rome, Italy")
        page.fill("input[name='startDate']", "2020-01-01")  # Past date
        page.fill("input[name='endDate']", "2020-01-10")
        page.click("button[type='submit'], text=Create")

        # Either blocked or allowed with warning
        is_blocked = page.locator("text=past, text=future date").is_visible(timeout=3000)
        is_created = page.locator("text=Rome").is_visible(timeout=3000)
        assert is_blocked or is_created, "Past date handling unclear"

    @pytest.mark.frontend
    @pytest.mark.trip
    def test_trip_visible_in_dashboard(self, logged_in_page):
        """
        CHECKPOINT 17: Created trip appears on dashboard
        """
        page = logged_in_page
        destination = f"Berlin {fake.city()}"

        # Create trip
        page.click("text=Create Trip, text=New Trip")
        page.fill("input[name='destination']", destination)
        page.fill("input[name='startDate']", "2025-09-01")
        page.fill("input[name='endDate']", "2025-09-07")
        page.click("button[type='submit'], text=Create")

        # Go to dashboard
        page.goto(f"{BASE_URL}/dashboard")

        assert page.locator(f"text={destination}").is_visible(timeout=5000), \
            "Trip not visible on dashboard after creation"

    @pytest.mark.frontend
    @pytest.mark.trip
    def test_create_multiple_trips(self, logged_in_page):
        """
        CHECKPOINT 18: User can create multiple trips
        """
        page = logged_in_page
        destinations = ["London, UK", "New York, USA"]

        for destination in destinations:
            page.click("text=Create Trip, text=New Trip")
            page.fill("input[name='destination']", destination)
            page.fill("input[name='startDate']", "2025-10-01")
            page.fill("input[name='endDate']", "2025-10-07")
            page.click("button[type='submit'], text=Create")
            page.wait_for_timeout(1000)

        # Both trips should be visible
        for destination in destinations:
            city = destination.split(",")[0]
            assert page.locator(f"text={city}").is_visible(timeout=5000), \
                f"Trip to {city} not visible"

    @pytest.mark.frontend
    @pytest.mark.trip
    def test_trip_cross_browser(self, cross_browser):
        """
        CHECKPOINT 19: Trip creation works across Chrome, Firefox, Safari
        """
        page = cross_browser
        page.goto(BASE_URL)

        # Login first
        page.click("text=Sign In")
        page.fill("input[type='email']", os.getenv("TEST_USER_EMAIL"))
        page.fill("input[type='password']", os.getenv("TEST_USER_PASSWORD"))
        page.click("button[type='submit']")
        page.wait_for_url(f"{BASE_URL}/dashboard", timeout=10000)

        # Create trip
        page.click("text=Create Trip, text=New Trip")
        page.fill("input[name='destination']", "Sydney, Australia")
        page.fill("input[name='startDate']", "2025-11-01")
        page.fill("input[name='endDate']", "2025-11-14")
        page.click("button[type='submit'], text=Create")

        assert page.locator("text=Sydney").is_visible(timeout=10000), \
            f"Trip creation failed on {page.context.browser.browser_type.name}"

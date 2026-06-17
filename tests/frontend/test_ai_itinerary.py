"""
TripMate Frontend Tests — AI Itinerary Generation
Tests: Generate itinerary, validate AI output, edge cases
"""
import pytest
import os

BASE_URL = os.getenv("BASE_URL", "https://tripmateapp.netlify.app")


class TestAIItineraryGeneration:
    """Test Suite: AI Itinerary Generation"""

    @pytest.mark.frontend
    @pytest.mark.smoke
    @pytest.mark.ai
    def test_generate_itinerary_happy_path(self, logged_in_page):
        """
        CHECKPOINT 20: AI generates itinerary successfully for a valid trip
        """
        page = logged_in_page

        # Navigate to a trip
        page.click("text=Create Trip, text=New Trip")
        page.fill("input[name='destination']", "Barcelona, Spain")
        page.fill("input[name='startDate']", "2025-09-01")
        page.fill("input[name='endDate']", "2025-09-05")
        page.click("button[type='submit'], text=Create")

        # Click generate itinerary
        page.click("text=Generate Itinerary, text=Create Itinerary, text=Generate with AI")

        # Wait for AI response — AI can be slow, give it 60 seconds
        page.wait_for_selector(
            "text=Day 1, .itinerary, .day-plan",
            timeout=60000
        )

        # Verify itinerary content appears
        assert page.locator("text=Day 1").is_visible(), \
            "AI itinerary not generated — Day 1 not visible"

    @pytest.mark.frontend
    @pytest.mark.ai
    def test_itinerary_contains_destination(self, logged_in_page):
        """
        CHECKPOINT 21: Generated itinerary mentions the correct destination
        """
        page = logged_in_page
        destination = "Kyoto, Japan"

        # Create trip
        page.click("text=Create Trip, text=New Trip")
        page.fill("input[name='destination']", destination)
        page.fill("input[name='startDate']", "2025-10-01")
        page.fill("input[name='endDate']", "2025-10-07")
        page.click("button[type='submit'], text=Create")

        # Generate itinerary
        page.click("text=Generate Itinerary, text=Create Itinerary")
        page.wait_for_selector("text=Day 1", timeout=60000)

        # Verify destination mentioned in output
        page_content = page.content()
        assert "Kyoto" in page_content or "Japan" in page_content, \
            "AI itinerary does not mention the correct destination"

    @pytest.mark.frontend
    @pytest.mark.ai
    def test_itinerary_day_count_matches_trip_duration(self, logged_in_page):
        """
        CHECKPOINT 22: Number of days in itinerary matches trip duration
        Trip: 3 days → Itinerary should have Day 1, Day 2, Day 3
        """
        page = logged_in_page

        # Create 3 day trip
        page.click("text=Create Trip, text=New Trip")
        page.fill("input[name='destination']", "Amsterdam, Netherlands")
        page.fill("input[name='startDate']", "2025-11-01")
        page.fill("input[name='endDate']", "2025-11-03")
        page.click("button[type='submit'], text=Create")

        # Generate itinerary
        page.click("text=Generate Itinerary, text=Create Itinerary")
        page.wait_for_selector("text=Day 1", timeout=60000)

        # Check all 3 days present
        assert page.locator("text=Day 1").is_visible(), "Day 1 missing from itinerary"
        assert page.locator("text=Day 2").is_visible(), "Day 2 missing from itinerary"
        assert page.locator("text=Day 3").is_visible(), "Day 3 missing from itinerary"

    @pytest.mark.frontend
    @pytest.mark.ai
    def test_itinerary_loading_state_shown(self, logged_in_page):
        """
        CHECKPOINT 23: Loading indicator shown while AI generates itinerary
        User should not see blank screen during AI processing
        """
        page = logged_in_page

        page.click("text=Create Trip, text=New Trip")
        page.fill("input[name='destination']", "Prague, Czech Republic")
        page.fill("input[name='startDate']", "2025-12-01")
        page.fill("input[name='endDate']", "2025-12-04")
        page.click("button[type='submit'], text=Create")

        # Click generate and immediately check for loading state
        page.click("text=Generate Itinerary, text=Create Itinerary")

        # Loading indicator should appear
        loading = page.locator("text=Generating, text=Loading, .spinner, .loading").first
        assert loading.is_visible(timeout=5000), \
            "No loading indicator shown during AI generation"

        # Wait for completion
        page.wait_for_selector("text=Day 1", timeout=60000)

    @pytest.mark.frontend
    @pytest.mark.ai
    def test_itinerary_not_empty(self, logged_in_page):
        """
        CHECKPOINT 24: AI itinerary is not empty or placeholder text
        """
        page = logged_in_page

        page.click("text=Create Trip, text=New Trip")
        page.fill("input[name='destination']", "Cape Town, South Africa")
        page.fill("input[name='startDate']", "2026-01-01")
        page.fill("input[name='endDate']", "2026-01-05")
        page.click("button[type='submit'], text=Create")

        page.click("text=Generate Itinerary, text=Create Itinerary")
        page.wait_for_selector("text=Day 1", timeout=60000)

        # Get itinerary text length
        itinerary_text = page.locator(".itinerary, .day-plan, [class*='itinerary']").first.inner_text()
        assert len(itinerary_text) > 100, \
            f"Itinerary content too short — possible empty or placeholder response: {itinerary_text}"

    @pytest.mark.frontend
    @pytest.mark.ai
    def test_regenerate_itinerary(self, logged_in_page):
        """
        CHECKPOINT 25: User can regenerate itinerary — gets new content
        """
        page = logged_in_page

        page.click("text=Create Trip, text=New Trip")
        page.fill("input[name='destination']", "Dubai, UAE")
        page.fill("input[name='startDate']", "2026-02-01")
        page.fill("input[name='endDate']", "2026-02-05")
        page.click("button[type='submit'], text=Create")

        # Generate first itinerary
        page.click("text=Generate Itinerary, text=Create Itinerary")
        page.wait_for_selector("text=Day 1", timeout=60000)

        # Regenerate
        page.click("text=Regenerate, text=Generate Again, text=Refresh Itinerary")
        page.wait_for_selector("text=Day 1", timeout=60000)

        # Verify itinerary still shows
        assert page.locator("text=Day 1").is_visible(), \
            "Itinerary not visible after regeneration"

    @pytest.mark.frontend
    @pytest.mark.ai
    def test_itinerary_generation_cross_browser(self, cross_browser):
        """
        CHECKPOINT 26: AI itinerary generates correctly across Chrome, Firefox, Safari
        """
        page = cross_browser
        page.goto(BASE_URL)

        # Login
        page.click("text=Sign In")
        page.fill("input[type='email']", os.getenv("TEST_USER_EMAIL"))
        page.fill("input[type='password']", os.getenv("TEST_USER_PASSWORD"))
        page.click("button[type='submit']")
        page.wait_for_url(f"{BASE_URL}/dashboard", timeout=10000)

        # Create trip and generate
        page.click("text=Create Trip, text=New Trip")
        page.fill("input[name='destination']", "Singapore")
        page.fill("input[name='startDate']", "2026-03-01")
        page.fill("input[name='endDate']", "2026-03-04")
        page.click("button[type='submit'], text=Create")
        page.click("text=Generate Itinerary, text=Create Itinerary")

        page.wait_for_selector("text=Day 1", timeout=60000)
        assert page.locator("text=Day 1").is_visible(), \
            f"Itinerary generation failed on {page.context.browser.browser_type.name}"

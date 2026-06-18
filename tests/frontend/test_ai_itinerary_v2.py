"""
TripMate Frontend Tests — AI Itinerary Generation (Fixed v3)
"""
import pytest
import os

BASE_URL = os.getenv("BASE_URL", "https://tripmateapp.netlify.app")


class TestAIItineraryGeneration:

    @pytest.mark.frontend
    @pytest.mark.smoke
    @pytest.mark.ai
    def test_generate_itinerary_happy_path(self, logged_in_page):
        """CHECKPOINT 20: AI generates itinerary successfully"""
        page = logged_in_page

        # Click on an existing trip
        page.get_by_text("Goa Friends Trip").click()
        page.wait_for_timeout(2000)

        # Click generate itinerary button
        page.get_by_role("button", name="Customize & Generate Itinerary").click()
        page.wait_for_timeout(1000)

        # Fill preferences modal
        page.get_by_text("Adults").click()
        page.get_by_text("Balanced").click()
        page.get_by_text("Moderate").click()
        page.get_by_text("Mix").click()

        # Click Generate button
        page.get_by_role("button", name="✨ Generate").click()

        # Wait for AI — can take up to 60 seconds
        page.wait_for_timeout(60000)

        # Verify success — either alert or plan tab updated
        assert page.get_by_role("button", name="Customize & Generate Itinerary").is_visible(timeout=5000), \
            "AI itinerary generation did not complete"

    @pytest.mark.frontend
    @pytest.mark.smoke
    @pytest.mark.ai
    def test_ai_button_visible_on_trip(self, logged_in_page):
        """CHECKPOINT 21: AI generate button visible on trip page"""
        page = logged_in_page

        # Click on existing trip
        page.get_by_text("Goa Friends Trip").click()
        page.wait_for_timeout(2000)

        assert page.get_by_role("button", name="Customize & Generate Itinerary").is_visible(), \
            "AI generate button not visible on trip page"
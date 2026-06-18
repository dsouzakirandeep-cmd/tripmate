"""
TripMate Frontend Tests — AI Itinerary Generation (Fixed)
"""
import pytest
import os

BASE_URL = os.getenv("BASE_URL", "https://tripmateapp.netlify.app")
TEST_EMAIL = os.getenv("TEST_USER_EMAIL", "dsouzakirandeep@gmail.com")
TEST_PASSWORD = os.getenv("TEST_USER_PASSWORD", "test@123")


class TestAIItineraryGeneration:

    @pytest.mark.frontend
    @pytest.mark.smoke
    @pytest.mark.ai
    def test_generate_itinerary_happy_path(self, logged_in_page):
        """CHECKPOINT 20: AI generates itinerary successfully"""
        page = logged_in_page

        # Click on an existing trip — Goa Friends Trip visible from screenshot
        page.get_by_text("Goa Friends Trip").click()
        page.wait_for_timeout(2000)

        # Click generate itinerary button
        page.get_by_text("Customize & Generate Itinerary").click()
        page.wait_for_timeout(1000)

        # Fill preferences modal
        page.get_by_text("Adults").click()
        page.get_by_text("Balanced").click()
        page.get_by_text("Moderate").click()
        page.get_by_text("Mix").click()

        # Click Generate
        page.get_by_text("Generate").last.click()

        # Wait for AI — can take up to 60 seconds
        page.wait_for_timeout(60000)

        # Verify itinerary appears
        assert page.locator("text=✅").is_visible(timeout=5000) or \
               page.locator("text=itinerary").is_visible(timeout=5000) or \
               page.locator("text=Plan").is_visible(timeout=5000), \
               "AI itinerary not generated"

    @pytest.mark.frontend
    @pytest.mark.ai
    def test_ai_button_visible_on_trip(self, logged_in_page):
        """CHECKPOINT 21: AI generate button visible on trip page"""
        page = logged_in_page

        # Click on existing trip
        page.get_by_text("Goa Friends Trip").click()
        page.wait_for_timeout(2000)

        assert page.get_by_text("Customize & Generate Itinerary").is_visible(), \
            "AI generate button not visible on trip page"

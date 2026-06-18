"""
TripMate Backend API Tests - Fixed version
"""
import pytest
import requests
import os
import json
import time
from faker import Faker

fake = Faker()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")
API_BASE = os.getenv("API_BASE_URL", "https://tripmateapp.netlify.app/.netlify/functions")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "60"))

HEADERS = {
    "Content-Type": "application/json",
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}


def get_auth_token():
    url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    payload = {
        "email": os.getenv("TEST_USER_EMAIL"),
        "password": os.getenv("TEST_USER_PASSWORD"),
    }
    response = requests.post(url, json=payload, headers=HEADERS, timeout=30)
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json().get("access_token")


class TestAuthAPI:

    @pytest.mark.backend
    @pytest.mark.smoke
    @pytest.mark.auth
    def test_signup_api_success(self):
        """CHECKPOINT 27: New user signup returns success"""
        url = f"{SUPABASE_URL}/auth/v1/signup"
        payload = {
            "email": fake.email(),
            "password": "TestPass123!",
            "data": {"name": fake.name()}
        }
        response = requests.post(url, json=payload, headers=HEADERS, timeout=30)
        assert response.status_code in [200, 201], \
            f"Signup failed. Status: {response.status_code}, Body: {response.text}"

    @pytest.mark.backend
    @pytest.mark.smoke
    @pytest.mark.auth
    def test_login_api_success(self):
        """CHECKPOINT 29: Valid credentials return JWT token"""
        url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
        payload = {
            "email": os.getenv("TEST_USER_EMAIL"),
            "password": os.getenv("TEST_USER_PASSWORD"),
        }
        response = requests.post(url, json=payload, headers=HEADERS, timeout=30)
        assert response.status_code == 200, \
            f"Login API failed. Status: {response.status_code}, Body: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access token in login response"

    @pytest.mark.backend
    @pytest.mark.auth
    def test_signup_api_duplicate_email(self):
        """CHECKPOINT 28: Duplicate email returns error"""
        url = f"{SUPABASE_URL}/auth/v1/signup"
        payload = {
            "email": os.getenv("TEST_USER_EMAIL"),
            "password": "TestPass123!"
        }
        response = requests.post(url, json=payload, headers=HEADERS, timeout=30)
        assert response.status_code in [400, 422], \
            f"Duplicate email should fail. Status: {response.status_code}"

    @pytest.mark.backend
    @pytest.mark.auth
    def test_login_api_wrong_password(self):
        """CHECKPOINT 30: Wrong password returns 400"""
        url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
        payload = {
            "email": os.getenv("TEST_USER_EMAIL"),
            "password": "WrongPassword999!",
        }
        response = requests.post(url, json=payload, headers=HEADERS, timeout=30)
        assert response.status_code in [400, 401], \
            f"Wrong password should fail. Status: {response.status_code}"


class TestTripAPI:

    @pytest.fixture(autouse=True)
    def setup_auth(self):
        self.token = get_auth_token()
        self.auth_headers = {
            **HEADERS,
            "Authorization": f"Bearer {self.token}",
        }

    @pytest.mark.backend
    @pytest.mark.smoke
    @pytest.mark.trip
    def test_create_trip_api_success(self):
        """CHECKPOINT 32: Trip created successfully with all required fields"""
        url = f"{SUPABASE_URL}/rest/v1/trips"
        payload = {
            "name": "Test Trip Paris",        # ← name field required
            "destination": "Paris, France",
            "start_date": "2025-08-01",
            "end_date": "2025-08-07",
            "emoji": "✈️"    
        }
        response = requests.post(
            url,
            json=payload,
            headers={**self.auth_headers, "Prefer": "return=representation"},
            timeout=30
        )
        assert response.status_code in [200, 201], \
            f"Trip creation failed. Status: {response.status_code}, Body: {response.text}"
        data = response.json()
        assert len(data) > 0, "No trip data returned"
        assert data[0]["destination"] == "Paris, France", "Destination mismatch"

    @pytest.mark.backend
    @pytest.mark.trip
    def test_get_trips_api_success(self):
        """CHECKPOINT 33: GET trips returns list"""
        url = f"{SUPABASE_URL}/rest/v1/trips"
        response = requests.get(url, headers=self.auth_headers, timeout=30)
        assert response.status_code == 200, \
            f"Get trips failed. Status: {response.status_code}"
        assert isinstance(response.json(), list), "Response should be a list"

    @pytest.mark.backend
    @pytest.mark.trip
    def test_unauthenticated_trip_access_blocked(self):
        """CHECKPOINT 35: No auth token — access denied"""
        url = f"{SUPABASE_URL}/rest/v1/trips"
        headers = {"Content-Type": "application/json", "apikey": SUPABASE_KEY}
        response = requests.get(url, headers=headers, timeout=30)
        assert response.status_code in [401, 403], \
            f"Unauthenticated access should be blocked. Status: {response.status_code}"


class TestAIItineraryAPI:

    @pytest.mark.backend
    @pytest.mark.smoke
    @pytest.mark.ai
    def test_generate_itinerary_api_success(self):
        """CHECKPOINT 37: AI itinerary returns valid response"""
        url = f"{API_BASE}/generate-itinerary"
        payload = {
            "destination": "Tokyo, Japan",
            "start_date": "2025-09-01",
            "end_date": "2025-09-05",
            "prefs": {
                "ageGroups": "adults",
                "travelStyle": "balanced",
                "budget": "moderate",
                "transport": "mixed",
                "restrictions": ""
            }
        }
        response = requests.post(url, json=payload, timeout=API_TIMEOUT)
        assert response.status_code == 200, \
            f"Itinerary generation failed. Status: {response.status_code}, Body: {response.text}"

        # Function returns array directly
        data = response.json()
        assert isinstance(data, list) and len(data) > 0, \
            f"Expected non-empty array, got: {type(data)}"

    @pytest.mark.backend
    @pytest.mark.ai
    def test_generate_itinerary_response_time(self):
        """CHECKPOINT 41: AI response within 60 seconds"""
        url = f"{API_BASE}/generate-itinerary"
        payload = {
            "destination": "Dubai, UAE",
            "start_date": "2026-01-01",
            "end_date": "2026-01-03",
            "prefs": {
                "ageGroups": "adults",
                "travelStyle": "relaxed",
                "budget": "moderate",
                "transport": "taxi",
                "restrictions": ""
            }
        }
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=API_TIMEOUT)
        elapsed = time.time() - start_time

        assert response.status_code == 200, f"Request failed: {response.status_code}"
        assert elapsed < 60, f"AI response too slow: {elapsed:.2f}s"
        print(f"\nAI response time: {elapsed:.2f}s")

    @pytest.mark.backend
    @pytest.mark.ai
    def test_generate_itinerary_empty_body(self):
        """CHECKPOINT 42: Empty body returns error not server crash"""
        url = f"{API_BASE}/generate-itinerary"
        response = requests.post(url, json={}, timeout=API_TIMEOUT)
        assert response.status_code != 500, \
            "Empty body caused server error — should return 400 not 500"

"""
TripMate Backend API Tests
Tests: Supabase Auth API, Trip CRUD API, AI Itinerary Netlify Function
"""
import pytest
import requests
import os
import json
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


# ── Helper: Get Auth Token ────────────────────────────────────────────────────

def get_auth_token():
    """Login and return JWT token for authenticated requests"""
    url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    payload = {
        "email": os.getenv("TEST_USER_EMAIL"),
        "password": os.getenv("TEST_USER_PASSWORD"),
    }
    response = requests.post(url, json=payload, headers=HEADERS, timeout=30)
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json().get("access_token")


# ── Auth API Tests ────────────────────────────────────────────────────────────

class TestAuthAPI:
    """Test Suite: Supabase Authentication API"""

    @pytest.mark.backend
    @pytest.mark.smoke
    @pytest.mark.auth
    def test_signup_api_success(self):
        """
        CHECKPOINT 27: POST /auth/v1/signup — new user created successfully
        """
        url = f"{SUPABASE_URL}/auth/v1/signup"
        payload = {
            "email": fake.email(),
            "password": "TestPass123!",
            "data": {"name": fake.name()}
        }
        response = requests.post(url, json=payload, headers=HEADERS, timeout=30)

        assert response.status_code in [200, 201], \
            f"Signup failed. Status: {response.status_code}, Body: {response.text}"
        assert "id" in response.json() or "user" in response.json(), \
            "No user ID in signup response"

    @pytest.mark.backend
    @pytest.mark.auth
    def test_signup_api_duplicate_email(self):
        """
        CHECKPOINT 28: POST /auth/v1/signup — duplicate email returns error
        """
        url = f"{SUPABASE_URL}/auth/v1/signup"
        payload = {
            "email": os.getenv("TEST_USER_EMAIL"),
            "password": "TestPass123!"
        }
        response = requests.post(url, json=payload, headers=HEADERS, timeout=30)

        assert response.status_code in [400, 422], \
            f"Duplicate email should fail. Status: {response.status_code}"

    @pytest.mark.backend
    @pytest.mark.smoke
    @pytest.mark.auth
    def test_login_api_success(self):
        """
        CHECKPOINT 29: POST /auth/v1/token — valid credentials return JWT token
        """
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
        assert "token_type" in data, "No token type in login response"
        assert data["token_type"] == "bearer", "Token type should be bearer"

    @pytest.mark.backend
    @pytest.mark.auth
    def test_login_api_wrong_password(self):
        """
        CHECKPOINT 30: POST /auth/v1/token — wrong password returns 400
        """
        url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
        payload = {
            "email": os.getenv("TEST_USER_EMAIL"),
            "password": "WrongPassword999!",
        }
        response = requests.post(url, json=payload, headers=HEADERS, timeout=30)

        assert response.status_code in [400, 401], \
            f"Wrong password should fail. Status: {response.status_code}"

    @pytest.mark.backend
    @pytest.mark.auth
    def test_login_api_nonexistent_user(self):
        """
        CHECKPOINT 31: POST /auth/v1/token — non-existent email returns error
        """
        url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
        payload = {
            "email": "doesnotexist999@tripmate.com",
            "password": "TestPass123!",
        }
        response = requests.post(url, json=payload, headers=HEADERS, timeout=30)

        assert response.status_code in [400, 401], \
            f"Non-existent user should fail. Status: {response.status_code}"


# ── Trip API Tests ────────────────────────────────────────────────────────────

class TestTripAPI:
    """Test Suite: Trip CRUD via Supabase REST API"""

    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Get auth token before each test"""
        self.token = get_auth_token()
        self.auth_headers = {
            **HEADERS,
            "Authorization": f"Bearer {self.token}",
        }

    @pytest.mark.backend
    @pytest.mark.smoke
    @pytest.mark.trip
    def test_create_trip_api_success(self):
        """
        CHECKPOINT 32: POST /rest/v1/trips — trip created successfully
        """
        url = f"{SUPABASE_URL}/rest/v1/trips"
        payload = {
            "destination": "Paris, France",
            "start_date": "2025-08-01",
            "end_date": "2025-08-07",
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
        """
        CHECKPOINT 33: GET /rest/v1/trips — returns list of user trips
        """
        url = f"{SUPABASE_URL}/rest/v1/trips"
        response = requests.get(url, headers=self.auth_headers, timeout=30)

        assert response.status_code == 200, \
            f"Get trips failed. Status: {response.status_code}"
        assert isinstance(response.json(), list), "Response should be a list"

    @pytest.mark.backend
    @pytest.mark.trip
    def test_create_trip_missing_destination(self):
        """
        CHECKPOINT 34: POST /rest/v1/trips — missing destination returns error
        """
        url = f"{SUPABASE_URL}/rest/v1/trips"
        payload = {
            "start_date": "2025-08-01",
            "end_date": "2025-08-07",
            # destination intentionally missing
        }
        response = requests.post(url, json=payload, headers=self.auth_headers, timeout=30)

        assert response.status_code in [400, 422], \
            f"Missing destination should fail. Status: {response.status_code}"

    @pytest.mark.backend
    @pytest.mark.trip
    def test_unauthenticated_trip_access_blocked(self):
        """
        CHECKPOINT 35: GET /rest/v1/trips without auth token — access denied
        """
        url = f"{SUPABASE_URL}/rest/v1/trips"
        # Use headers without auth token
        headers = {"Content-Type": "application/json", "apikey": SUPABASE_KEY}
        response = requests.get(url, headers=headers, timeout=30)

        assert response.status_code in [401, 403], \
            f"Unauthenticated access should be blocked. Status: {response.status_code}"

    @pytest.mark.backend
    @pytest.mark.trip
    def test_delete_trip_api_success(self):
        """
        CHECKPOINT 36: DELETE /rest/v1/trips — trip deleted successfully
        """
        # First create a trip to delete
        create_url = f"{SUPABASE_URL}/rest/v1/trips"
        payload = {
            "destination": "DELETE ME",
            "start_date": "2025-08-01",
            "end_date": "2025-08-02",
        }
        create_response = requests.post(
            create_url,
            json=payload,
            headers={**self.auth_headers, "Prefer": "return=representation"},
            timeout=30
        )
        trip_id = create_response.json()[0]["id"]

        # Now delete it
        delete_url = f"{SUPABASE_URL}/rest/v1/trips?id=eq.{trip_id}"
        delete_response = requests.delete(delete_url, headers=self.auth_headers, timeout=30)

        assert delete_response.status_code in [200, 204], \
            f"Trip deletion failed. Status: {delete_response.status_code}"


# ── AI Itinerary API Tests ────────────────────────────────────────────────────

class TestAIItineraryAPI:
    """Test Suite: AI Itinerary Generation via Netlify Serverless Function"""

    @pytest.mark.backend
    @pytest.mark.smoke
    @pytest.mark.ai
    def test_generate_itinerary_api_success(self):
        """
        CHECKPOINT 37: POST /generate-itinerary — returns valid itinerary
        """
        url = f"{API_BASE}/generate-itinerary"
        payload = {
            "destination": "Tokyo, Japan",
            "start_date": "2025-09-01",
            "end_date": "2025-09-05",
            "preferences": "food, culture, history"
        }
        response = requests.post(url, json=payload, timeout=API_TIMEOUT)

        assert response.status_code == 200, \
            f"Itinerary generation failed. Status: {response.status_code}, Body: {response.text}"

        data = response.json()
        assert "itinerary" in data or "content" in data, \
            "No itinerary content in response"

    @pytest.mark.backend
    @pytest.mark.ai
    def test_generate_itinerary_content_not_empty(self):
        """
        CHECKPOINT 38: Generated itinerary content is not empty or too short
        """
        url = f"{API_BASE}/generate-itinerary"
        payload = {
            "destination": "London, UK",
            "start_date": "2025-10-01",
            "end_date": "2025-10-04",
        }
        response = requests.post(url, json=payload, timeout=API_TIMEOUT)

        assert response.status_code == 200, f"Request failed: {response.status_code}"

        data = response.json()
        content = data.get("itinerary") or data.get("content") or ""
        assert len(content) > 200, \
            f"Itinerary too short — possible empty AI response. Length: {len(content)}"

    @pytest.mark.backend
    @pytest.mark.ai
    def test_generate_itinerary_mentions_destination(self):
        """
        CHECKPOINT 39: AI response mentions the requested destination
        """
        url = f"{API_BASE}/generate-itinerary"
        destination = "Barcelona"
        payload = {
            "destination": f"{destination}, Spain",
            "start_date": "2025-11-01",
            "end_date": "2025-11-03",
        }
        response = requests.post(url, json=payload, timeout=API_TIMEOUT)

        assert response.status_code == 200, f"Request failed: {response.status_code}"

        content = json.dumps(response.json()).lower()
        assert destination.lower() in content or "spain" in content, \
            "AI response does not mention the requested destination — possible hallucination"

    @pytest.mark.backend
    @pytest.mark.ai
    def test_generate_itinerary_missing_destination(self):
        """
        CHECKPOINT 40: POST without destination — returns 400 error
        """
        url = f"{API_BASE}/generate-itinerary"
        payload = {
            "start_date": "2025-11-01",
            "end_date": "2025-11-03",
            # destination missing
        }
        response = requests.post(url, json=payload, timeout=API_TIMEOUT)

        assert response.status_code in [400, 422], \
            f"Missing destination should return error. Status: {response.status_code}"

    @pytest.mark.backend
    @pytest.mark.ai
    def test_generate_itinerary_response_time(self):
        """
        CHECKPOINT 41: AI response returns within acceptable time (60 seconds)
        Performance test — AI should not timeout
        """
        import time
        url = f"{API_BASE}/generate-itinerary"
        payload = {
            "destination": "Dubai, UAE",
            "start_date": "2026-01-01",
            "end_date": "2026-01-03",
        }

        start_time = time.time()
        response = requests.post(url, json=payload, timeout=API_TIMEOUT)
        elapsed = time.time() - start_time

        assert response.status_code == 200, f"Request failed: {response.status_code}"
        assert elapsed < 60, f"AI response took too long: {elapsed:.2f}s — expected under 60s"
        print(f"\nAI response time: {elapsed:.2f}s")

    @pytest.mark.backend
    @pytest.mark.ai
    def test_generate_itinerary_empty_body(self):
        """
        CHECKPOINT 42: POST with empty body — returns error not server crash
        """
        url = f"{API_BASE}/generate-itinerary"
        response = requests.post(url, json={}, timeout=API_TIMEOUT)

        assert response.status_code in [400, 422], \
            f"Empty body should return error. Status: {response.status_code}"
        assert response.status_code != 500, \
            "Empty body caused server error — should return 400 not 500"

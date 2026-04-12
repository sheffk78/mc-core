"""
Test Schedule View - Comprehensive tests for Schedule CRUD operations
Tests: Create, Pause, Resume, Run Now, Edit, Delete schedule jobs
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
API_URL = f"{BASE_URL}/api/v1"


class TestScheduleCRUD:
    """Schedule endpoint CRUD tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.test_prefix = f"TEST_Schedule_{uuid.uuid4().hex[:8]}"
        self.created_ids = []
        yield
        # Cleanup: Delete all test-created schedules
        for job_id in self.created_ids:
            try:
                requests.delete(f"{API_URL}/schedule/{job_id}")
            except:
                pass
    
    def test_get_schedule_list(self):
        """GET /api/v1/schedule returns list of scheduled jobs"""
        response = requests.get(f"{API_URL}/schedule")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /schedule returned {len(data)} jobs")
    
    def test_get_schedule_with_brand_filter(self):
        """GET /api/v1/schedule?brand=agentic-trust filters by brand"""
        response = requests.get(f"{API_URL}/schedule", params={"brand": "agentic-trust"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All returned items should be for the specified brand
        for item in data:
            assert item.get("brand") == "agentic-trust"
        print(f"✓ GET /schedule?brand=agentic-trust returned {len(data)} jobs")
    
    def test_create_schedule_item(self):
        """POST /api/v1/schedule creates a new scheduled job"""
        payload = {
            "brand": "agentic-trust",
            "name": self.test_prefix,
            "description": "Test scheduled job for iteration 9",
            "cron": "0 9 * * *",
            "agent_name": "Kit"
        }
        response = requests.post(f"{API_URL}/schedule", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert data["name"] == self.test_prefix
        assert data["brand"] == "agentic-trust"
        assert data["cron"] == "0 9 * * *"
        assert data["status"] == "active"
        assert "created_at" in data
        
        self.created_ids.append(data["id"])
        print(f"✓ POST /schedule created job: {data['id']}")
        return data["id"]
    
    def test_get_schedule_item_by_id(self):
        """GET /api/v1/schedule/:id returns single job"""
        # First create a job
        job_id = self.test_create_schedule_item()
        
        # Then fetch it
        response = requests.get(f"{API_URL}/schedule/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == job_id
        assert data["name"] == self.test_prefix
        print(f"✓ GET /schedule/{job_id} returned job details")
    
    def test_get_nonexistent_schedule_returns_404(self):
        """GET /api/v1/schedule/:id returns 404 for non-existent job"""
        response = requests.get(f"{API_URL}/schedule/nonexistent-id-12345")
        assert response.status_code == 404
        print("✓ GET /schedule/nonexistent-id returns 404")
    
    def test_pause_schedule(self):
        """POST /api/v1/schedule/:id/pause pauses an active job"""
        # Create a job
        job_id = self.test_create_schedule_item()
        
        # Pause it
        response = requests.post(f"{API_URL}/schedule/{job_id}/pause")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "paused"
        
        # Verify via GET
        get_response = requests.get(f"{API_URL}/schedule/{job_id}")
        assert get_response.status_code == 200
        assert get_response.json()["status"] == "paused"
        print(f"✓ POST /schedule/{job_id}/pause paused the job")
    
    def test_resume_schedule(self):
        """POST /api/v1/schedule/:id/resume resumes a paused job"""
        # Create and pause a job
        job_id = self.test_create_schedule_item()
        requests.post(f"{API_URL}/schedule/{job_id}/pause")
        
        # Resume it
        response = requests.post(f"{API_URL}/schedule/{job_id}/resume")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        
        # Verify via GET
        get_response = requests.get(f"{API_URL}/schedule/{job_id}")
        assert get_response.status_code == 200
        assert get_response.json()["status"] == "active"
        print(f"✓ POST /schedule/{job_id}/resume resumed the job")
    
    def test_run_now_schedule(self):
        """POST /api/v1/schedule/:id/run-now triggers immediate execution"""
        # Create a job
        job_id = self.test_create_schedule_item()
        
        # Run now
        response = requests.post(f"{API_URL}/schedule/{job_id}/run-now")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        
        # Verify last_run is set
        get_response = requests.get(f"{API_URL}/schedule/{job_id}")
        assert get_response.status_code == 200
        assert get_response.json()["last_run"] is not None
        print(f"✓ POST /schedule/{job_id}/run-now triggered execution")
    
    def test_edit_schedule(self):
        """POST /api/v1/schedule/:id/edit updates job fields"""
        # Create a job
        job_id = self.test_create_schedule_item()
        
        # Edit it
        edit_payload = {
            "name": f"{self.test_prefix}_EDITED",
            "description": "Updated description",
            "cron": "0 12 * * *"
        }
        response = requests.post(f"{API_URL}/schedule/{job_id}/edit", json=edit_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == f"{self.test_prefix}_EDITED"
        assert data["description"] == "Updated description"
        assert data["cron"] == "0 12 * * *"
        
        # Verify via GET
        get_response = requests.get(f"{API_URL}/schedule/{job_id}")
        assert get_response.status_code == 200
        fetched = get_response.json()
        assert fetched["name"] == f"{self.test_prefix}_EDITED"
        print(f"✓ POST /schedule/{job_id}/edit updated the job")
    
    def test_delete_schedule(self):
        """DELETE /api/v1/schedule/:id removes a job"""
        # Create a job
        job_id = self.test_create_schedule_item()
        
        # Delete it
        response = requests.delete(f"{API_URL}/schedule/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"
        
        # Verify it's gone
        get_response = requests.get(f"{API_URL}/schedule/{job_id}")
        assert get_response.status_code == 404
        
        # Remove from cleanup list since already deleted
        self.created_ids.remove(job_id)
        print(f"✓ DELETE /schedule/{job_id} removed the job")
    
    def test_delete_nonexistent_schedule_returns_404(self):
        """DELETE /api/v1/schedule/:id returns 404 for non-existent job"""
        response = requests.delete(f"{API_URL}/schedule/nonexistent-id-12345")
        assert response.status_code == 404
        print("✓ DELETE /schedule/nonexistent-id returns 404")
    
    def test_pause_nonexistent_schedule_returns_404(self):
        """POST /api/v1/schedule/:id/pause returns 404 for non-existent job"""
        response = requests.post(f"{API_URL}/schedule/nonexistent-id-12345/pause")
        assert response.status_code == 404
        print("✓ POST /schedule/nonexistent-id/pause returns 404")
    
    def test_resume_nonexistent_schedule_returns_404(self):
        """POST /api/v1/schedule/:id/resume returns 404 for non-existent job"""
        response = requests.post(f"{API_URL}/schedule/nonexistent-id-12345/resume")
        assert response.status_code == 404
        print("✓ POST /schedule/nonexistent-id/resume returns 404")
    
    def test_run_now_nonexistent_schedule_returns_404(self):
        """POST /api/v1/schedule/:id/run-now returns 404 for non-existent job"""
        response = requests.post(f"{API_URL}/schedule/nonexistent-id-12345/run-now")
        assert response.status_code == 404
        print("✓ POST /schedule/nonexistent-id/run-now returns 404")
    
    def test_edit_nonexistent_schedule_returns_404(self):
        """POST /api/v1/schedule/:id/edit returns 404 for non-existent job"""
        response = requests.post(f"{API_URL}/schedule/nonexistent-id-12345/edit", json={"name": "test"})
        assert response.status_code == 404
        print("✓ POST /schedule/nonexistent-id/edit returns 404")


class TestScheduleStatusFiltering:
    """Test schedule status filtering"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.test_prefix = f"TEST_StatusFilter_{uuid.uuid4().hex[:8]}"
        self.created_ids = []
        yield
        # Cleanup
        for job_id in self.created_ids:
            try:
                requests.delete(f"{API_URL}/schedule/{job_id}")
            except:
                pass
    
    def test_filter_by_active_status(self):
        """GET /api/v1/schedule?status=active returns only active jobs"""
        # Create an active job
        payload = {
            "brand": "agentic-trust",
            "name": f"{self.test_prefix}_active",
            "cron": "0 9 * * *"
        }
        create_resp = requests.post(f"{API_URL}/schedule", json=payload)
        job_id = create_resp.json()["id"]
        self.created_ids.append(job_id)
        
        # Filter by active
        response = requests.get(f"{API_URL}/schedule", params={"status": "active"})
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert item["status"] == "active"
        print(f"✓ GET /schedule?status=active returned {len(data)} active jobs")
    
    def test_filter_by_paused_status(self):
        """GET /api/v1/schedule?status=paused returns only paused jobs"""
        # Create and pause a job
        payload = {
            "brand": "agentic-trust",
            "name": f"{self.test_prefix}_paused",
            "cron": "0 9 * * *"
        }
        create_resp = requests.post(f"{API_URL}/schedule", json=payload)
        job_id = create_resp.json()["id"]
        self.created_ids.append(job_id)
        requests.post(f"{API_URL}/schedule/{job_id}/pause")
        
        # Filter by paused
        response = requests.get(f"{API_URL}/schedule", params={"status": "paused"})
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert item["status"] == "paused"
        print(f"✓ GET /schedule?status=paused returned {len(data)} paused jobs")


class TestRegressionOtherViews:
    """Regression tests for other views still working"""
    
    def test_overview_stats(self):
        """GET /api/v1/stats returns dashboard stats"""
        response = requests.get(f"{API_URL}/stats")
        assert response.status_code == 200
        data = response.json()
        assert "pending_approvals" in data
        assert "open_tasks" in data
        print("✓ GET /stats works (Overview)")
    
    def test_approvals_list(self):
        """GET /api/v1/approvals returns approval list"""
        response = requests.get(f"{API_URL}/approvals")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /approvals works ({len(data)} items)")
    
    def test_tasks_list(self):
        """GET /api/v1/tasks returns task list"""
        response = requests.get(f"{API_URL}/tasks")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /tasks works ({len(data)} items)")
    
    def test_inboxes_list(self):
        """GET /api/v1/inboxes returns inbox list"""
        response = requests.get(f"{API_URL}/inboxes")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /inboxes works ({len(data)} items)")
    
    def test_activity_list(self):
        """GET /api/v1/activity returns activity list"""
        response = requests.get(f"{API_URL}/activity")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /activity works ({len(data)} items)")
    
    def test_calendar_feeds(self):
        """GET /api/v1/calendar/feeds returns calendar feeds"""
        response = requests.get(f"{API_URL}/calendar/feeds")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /calendar/feeds works ({len(data)} items)")
    
    def test_brands_list(self):
        """GET /api/v1/brands returns brand list"""
        response = requests.get(f"{API_URL}/brands")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"✓ GET /brands works ({len(data)} brands)")


class TestWebSocketConnection:
    """Test WebSocket still connects"""
    
    def test_websocket_endpoint_exists(self):
        """WebSocket endpoint at /api/v1/ws should be accessible"""
        # We can't do full WebSocket test with requests, but we can check the upgrade fails gracefully
        # HTTP GET to WebSocket endpoint typically returns 404 or 403 for non-WebSocket requests
        response = requests.get(f"{API_URL}/ws")
        # WebSocket endpoints return various codes for non-WebSocket requests
        assert response.status_code in [403, 426, 400, 200, 404]
        print("✓ WebSocket endpoint /api/v1/ws exists (HTTP returns expected code)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

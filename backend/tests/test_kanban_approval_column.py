"""
Test suite for Kanban Board 4-column layout with Approval column
Tests: status validation, completed_at timestamps, archived task exclusion
"""
import pytest
import requests
import os
from datetime import datetime, timezone, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestTaskStatusValidation:
    """Test PATCH /api/v1/tasks/:id/status endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Create a test task for each test"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Create a test task
        response = self.session.post(f"{BASE_URL}/api/v1/tasks", json={
            "title": "TEST_Kanban_Status_Test",
            "brand": "agentic-trust",
            "priority": "normal"
        })
        assert response.status_code == 200, f"Failed to create test task: {response.text}"
        self.task = response.json()
        self.task_id = self.task["id"]
        yield
        # Cleanup - delete test task (if endpoint exists, otherwise leave for manual cleanup)
    
    def test_status_open_valid(self):
        """Test setting status to 'open'"""
        response = self.session.patch(
            f"{BASE_URL}/api/v1/tasks/{self.task_id}/status",
            json={"status": "open"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "open"
        
        # Verify via GET
        get_resp = self.session.get(f"{BASE_URL}/api/v1/tasks/{self.task_id}")
        assert get_resp.status_code == 200
        task = get_resp.json()
        assert task["status"] == "open"
        # completed_at should be cleared
        assert task.get("completed_at") is None
    
    def test_status_in_progress_valid(self):
        """Test setting status to 'in_progress'"""
        response = self.session.patch(
            f"{BASE_URL}/api/v1/tasks/{self.task_id}/status",
            json={"status": "in_progress"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"
        
        # Verify via GET
        get_resp = self.session.get(f"{BASE_URL}/api/v1/tasks/{self.task_id}")
        assert get_resp.status_code == 200
        task = get_resp.json()
        assert task["status"] == "in_progress"
        assert task.get("completed_at") is None
    
    def test_status_approval_valid(self):
        """Test setting status to 'approval' - NEW COLUMN"""
        response = self.session.patch(
            f"{BASE_URL}/api/v1/tasks/{self.task_id}/status",
            json={"status": "approval"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approval"
        
        # Verify via GET
        get_resp = self.session.get(f"{BASE_URL}/api/v1/tasks/{self.task_id}")
        assert get_resp.status_code == 200
        task = get_resp.json()
        assert task["status"] == "approval"
        assert task.get("completed_at") is None
    
    def test_status_completed_sets_completed_at(self):
        """Test setting status to 'completed' sets completed_at timestamp"""
        response = self.session.patch(
            f"{BASE_URL}/api/v1/tasks/{self.task_id}/status",
            json={"status": "completed"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        
        # Verify via GET - completed_at should be set
        get_resp = self.session.get(f"{BASE_URL}/api/v1/tasks/{self.task_id}")
        assert get_resp.status_code == 200
        task = get_resp.json()
        assert task["status"] == "completed"
        assert task.get("completed_at") is not None
        # Verify it's a valid ISO timestamp
        completed_at = task["completed_at"]
        assert "T" in completed_at  # ISO format check
    
    def test_status_open_clears_completed_at(self):
        """Test setting status back to 'open' clears completed_at"""
        # First complete the task
        self.session.patch(
            f"{BASE_URL}/api/v1/tasks/{self.task_id}/status",
            json={"status": "completed"}
        )
        
        # Verify completed_at is set
        get_resp = self.session.get(f"{BASE_URL}/api/v1/tasks/{self.task_id}")
        task = get_resp.json()
        assert task.get("completed_at") is not None
        
        # Now reopen the task
        response = self.session.patch(
            f"{BASE_URL}/api/v1/tasks/{self.task_id}/status",
            json={"status": "open"}
        )
        assert response.status_code == 200
        
        # Verify completed_at is cleared
        get_resp = self.session.get(f"{BASE_URL}/api/v1/tasks/{self.task_id}")
        task = get_resp.json()
        assert task["status"] == "open"
        assert task.get("completed_at") is None
    
    def test_invalid_status_returns_400(self):
        """Test that invalid status returns 400 error"""
        response = self.session.patch(
            f"{BASE_URL}/api/v1/tasks/{self.task_id}/status",
            json={"status": "invalid_status"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid status" in data["detail"]
    
    def test_archived_status_returns_400(self):
        """Test that 'archived' status is not valid via API (only set by background task)"""
        response = self.session.patch(
            f"{BASE_URL}/api/v1/tasks/{self.task_id}/status",
            json={"status": "archived"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "Invalid status" in data["detail"]


class TestArchivedTaskExclusion:
    """Test GET /api/v1/tasks excludes archived tasks by default"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_get_tasks_excludes_archived_by_default(self):
        """Test that GET /api/v1/tasks excludes archived tasks"""
        response = self.session.get(f"{BASE_URL}/api/v1/tasks")
        assert response.status_code == 200
        tasks = response.json()
        
        # No task should have status 'archived'
        for task in tasks:
            assert task.get("status") != "archived", f"Found archived task in default response: {task['id']}"
    
    def test_get_tasks_with_include_archived_true(self):
        """Test that GET /api/v1/tasks?include_archived=true includes archived tasks"""
        response = self.session.get(f"{BASE_URL}/api/v1/tasks?include_archived=true")
        assert response.status_code == 200
        tasks = response.json()
        # This should return all tasks including archived ones
        # We can't guarantee there are archived tasks, but the endpoint should work
        assert isinstance(tasks, list)
    
    def test_get_tasks_with_status_filter(self):
        """Test that status filter works correctly"""
        # Test each valid status
        for status in ["open", "in_progress", "approval", "completed"]:
            response = self.session.get(f"{BASE_URL}/api/v1/tasks?status={status}")
            assert response.status_code == 200
            tasks = response.json()
            for task in tasks:
                assert task.get("status") == status, f"Expected status {status}, got {task.get('status')}"


class TestTaskStatusTransitions:
    """Test full status transition flows"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Create a test task
        response = self.session.post(f"{BASE_URL}/api/v1/tasks", json={
            "title": "TEST_Status_Transition_Test",
            "brand": "agentic-trust",
            "priority": "high"
        })
        assert response.status_code == 200
        self.task = response.json()
        self.task_id = self.task["id"]
        yield
    
    def test_full_kanban_flow_open_to_completed(self):
        """Test full flow: Open -> In Progress -> Approval -> Completed"""
        # Start at open
        get_resp = self.session.get(f"{BASE_URL}/api/v1/tasks/{self.task_id}")
        task = get_resp.json()
        assert task["status"] == "open"
        
        # Move to in_progress
        resp = self.session.patch(
            f"{BASE_URL}/api/v1/tasks/{self.task_id}/status",
            json={"status": "in_progress"}
        )
        assert resp.status_code == 200
        
        # Move to approval
        resp = self.session.patch(
            f"{BASE_URL}/api/v1/tasks/{self.task_id}/status",
            json={"status": "approval"}
        )
        assert resp.status_code == 200
        
        # Move to completed
        resp = self.session.patch(
            f"{BASE_URL}/api/v1/tasks/{self.task_id}/status",
            json={"status": "completed"}
        )
        assert resp.status_code == 200
        
        # Verify final state
        get_resp = self.session.get(f"{BASE_URL}/api/v1/tasks/{self.task_id}")
        task = get_resp.json()
        assert task["status"] == "completed"
        assert task.get("completed_at") is not None
    
    def test_completed_back_to_open(self):
        """Test moving completed task back to open"""
        # Complete the task first
        self.session.patch(
            f"{BASE_URL}/api/v1/tasks/{self.task_id}/status",
            json={"status": "completed"}
        )
        
        # Move back to open
        resp = self.session.patch(
            f"{BASE_URL}/api/v1/tasks/{self.task_id}/status",
            json={"status": "open"}
        )
        assert resp.status_code == 200
        
        # Verify
        get_resp = self.session.get(f"{BASE_URL}/api/v1/tasks/{self.task_id}")
        task = get_resp.json()
        assert task["status"] == "open"
        assert task.get("completed_at") is None
    
    def test_approval_to_in_progress(self):
        """Test moving from approval back to in_progress"""
        # Move to approval
        self.session.patch(
            f"{BASE_URL}/api/v1/tasks/{self.task_id}/status",
            json={"status": "approval"}
        )
        
        # Move back to in_progress
        resp = self.session.patch(
            f"{BASE_URL}/api/v1/tasks/{self.task_id}/status",
            json={"status": "in_progress"}
        )
        assert resp.status_code == 200
        
        # Verify
        get_resp = self.session.get(f"{BASE_URL}/api/v1/tasks/{self.task_id}")
        task = get_resp.json()
        assert task["status"] == "in_progress"


class TestRegressionStats:
    """Regression tests for stats and overview"""
    
    def test_stats_endpoint_works(self):
        """Test GET /api/v1/stats returns correct structure"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/v1/stats")
        assert response.status_code == 200
        data = response.json()
        
        # Verify expected fields
        assert "pending_approvals" in data
        assert "active_agents" in data
        assert "total_agents" in data
        assert "open_tasks" in data
        assert "pending_emails" in data
    
    def test_stats_with_brand_filter(self):
        """Test GET /api/v1/stats?brand=agentic-trust"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/v1/stats?brand=agentic-trust")
        assert response.status_code == 200
        data = response.json()
        assert "open_tasks" in data


class TestRegressionOtherViews:
    """Regression tests for other views"""
    
    def test_brands_endpoint(self):
        """Test GET /api/v1/brands"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/v1/brands")
        assert response.status_code == 200
        brands = response.json()
        assert isinstance(brands, list)
        assert len(brands) > 0
    
    def test_approvals_endpoint(self):
        """Test GET /api/v1/approvals"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/v1/approvals")
        assert response.status_code == 200
        approvals = response.json()
        assert isinstance(approvals, list)
    
    def test_activity_endpoint(self):
        """Test GET /api/v1/activity"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/v1/activity")
        assert response.status_code == 200
        activity = response.json()
        assert isinstance(activity, list)
    
    def test_inboxes_endpoint(self):
        """Test GET /api/v1/inboxes"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/v1/inboxes")
        assert response.status_code == 200
        inboxes = response.json()
        assert isinstance(inboxes, list)
    
    def test_agents_endpoint(self):
        """Test GET /api/v1/agents"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/v1/agents")
        assert response.status_code == 200
        agents = response.json()
        assert isinstance(agents, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

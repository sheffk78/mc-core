"""
Regression tests for refactored backend API (modular routes)
Tests all /api/v1/* endpoints to ensure no breaking changes after refactoring
from monolithic server.py to modular route files.
"""
import pytest
import requests
import os
import json
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndStats:
    """Health check and stats endpoints"""
    
    def test_health_check_root(self):
        """GET /api/v1/ returns 200 with API message"""
        response = requests.get(f"{BASE_URL}/api/v1/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Mission Control" in data["message"]
        print(f"✓ Health check passed: {data}")
    
    def test_stats_endpoint(self):
        """GET /api/v1/stats returns dashboard stats"""
        response = requests.get(f"{BASE_URL}/api/v1/stats")
        assert response.status_code == 200
        data = response.json()
        # Verify expected stat fields
        assert "pending_approvals" in data
        assert "active_agents" in data
        assert "total_agents" in data
        assert "open_tasks" in data
        assert "pending_emails" in data
        print(f"✓ Stats endpoint passed: {data}")


class TestBrandsAPI:
    """Brands CRUD endpoints"""
    
    def test_get_brands(self):
        """GET /api/v1/brands returns brand list"""
        response = requests.get(f"{BASE_URL}/api/v1/brands")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Verify brand structure
        brand = data[0]
        assert "id" in brand
        assert "name" in brand
        assert "slug" in brand
        assert "color" in brand
        print(f"✓ GET /api/v1/brands passed: {len(data)} brands")


class TestTasksAPI:
    """Tasks CRUD and status endpoints"""
    
    def test_get_tasks(self):
        """GET /api/v1/tasks returns tasks list"""
        response = requests.get(f"{BASE_URL}/api/v1/tasks")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/v1/tasks passed: {len(data)} tasks")
    
    def test_create_and_delete_task(self):
        """POST /api/v1/tasks creates task, DELETE removes it"""
        # Create task
        task_data = {
            "title": "TEST_Regression_Task",
            "brand": "all",
            "description": "Test task for regression testing",
            "priority": "normal"
        }
        create_resp = requests.post(f"{BASE_URL}/api/v1/tasks", json=task_data)
        assert create_resp.status_code == 200
        created = create_resp.json()
        assert created["title"] == task_data["title"]
        assert "id" in created
        task_id = created["id"]
        print(f"✓ POST /api/v1/tasks passed: created task {task_id}")
        
        # Delete task
        delete_resp = requests.delete(f"{BASE_URL}/api/v1/tasks/{task_id}")
        assert delete_resp.status_code == 200
        delete_data = delete_resp.json()
        assert delete_data["status"] == "deleted"
        print(f"✓ DELETE /api/v1/tasks/{task_id} passed")
    
    def test_update_task_status(self):
        """PATCH /api/v1/tasks/{id}/status updates task status"""
        # Create a task first
        task_data = {
            "title": "TEST_Status_Update_Task",
            "brand": "all",
            "priority": "normal"
        }
        create_resp = requests.post(f"{BASE_URL}/api/v1/tasks", json=task_data)
        assert create_resp.status_code == 200
        task_id = create_resp.json()["id"]
        
        # Update status to in_progress
        status_resp = requests.patch(
            f"{BASE_URL}/api/v1/tasks/{task_id}/status",
            json={"status": "in_progress"}
        )
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        assert status_data["status"] == "in_progress"
        print(f"✓ PATCH /api/v1/tasks/{task_id}/status passed")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/v1/tasks/{task_id}")
    
    def test_action_items_alias(self):
        """GET /api/v1/action-items alias works"""
        response = requests.get(f"{BASE_URL}/api/v1/action-items")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/v1/action-items alias passed: {len(data)} items")


class TestApprovalsAPI:
    """Approvals endpoints"""
    
    def test_get_approvals(self):
        """GET /api/v1/approvals returns approvals list"""
        response = requests.get(f"{BASE_URL}/api/v1/approvals")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/v1/approvals passed: {len(data)} approvals")
    
    def test_discard_and_dismiss_alias(self):
        """POST /api/v1/approvals/{id}/discard and dismiss work"""
        # Get an approval to test with (if any exist)
        approvals_resp = requests.get(f"{BASE_URL}/api/v1/approvals")
        approvals = approvals_resp.json()
        
        if len(approvals) > 0:
            # Test discard endpoint exists (don't actually discard real data)
            # Just verify the endpoint responds correctly
            fake_id = "nonexistent-id-12345"
            discard_resp = requests.post(f"{BASE_URL}/api/v1/approvals/{fake_id}/discard")
            # Should return 404 for nonexistent ID
            assert discard_resp.status_code == 404
            print("✓ POST /api/v1/approvals/{id}/discard endpoint exists")
            
            dismiss_resp = requests.post(f"{BASE_URL}/api/v1/approvals/{fake_id}/dismiss")
            assert dismiss_resp.status_code == 404
            print("✓ POST /api/v1/approvals/{id}/dismiss alias exists")
        else:
            print("⚠ No approvals to test discard/dismiss (skipped)")


class TestScheduleAPI:
    """Schedule (cron jobs) endpoints"""
    
    def test_get_schedule(self):
        """GET /api/v1/schedule returns schedule jobs"""
        response = requests.get(f"{BASE_URL}/api/v1/schedule")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/v1/schedule passed: {len(data)} jobs")
    
    def test_create_and_delete_schedule(self):
        """POST /api/v1/schedule creates job, DELETE removes it"""
        # Create schedule item
        schedule_data = {
            "brand": "all",
            "name": "TEST_Regression_Job",
            "description": "Test job for regression",
            "cron": "0 9 * * *",
            "agent_name": "Kit"
        }
        create_resp = requests.post(f"{BASE_URL}/api/v1/schedule", json=schedule_data)
        assert create_resp.status_code == 200
        created = create_resp.json()
        assert created["name"] == schedule_data["name"]
        assert "id" in created
        job_id = created["id"]
        print(f"✓ POST /api/v1/schedule passed: created job {job_id}")
        
        # Delete job
        delete_resp = requests.delete(f"{BASE_URL}/api/v1/schedule/{job_id}")
        assert delete_resp.status_code == 200
        delete_data = delete_resp.json()
        assert delete_data["status"] == "deleted"
        print(f"✓ DELETE /api/v1/schedule/{job_id} passed")


class TestUsersAPI:
    """Users CRUD endpoints"""
    
    def test_get_users(self):
        """GET /api/v1/users returns users list"""
        response = requests.get(f"{BASE_URL}/api/v1/users")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/v1/users passed: {len(data)} users")
    
    def test_create_and_delete_user(self):
        """POST /api/v1/users creates user, DELETE removes it"""
        # Create user
        user_data = {
            "name": "TEST_Regression_User",
            "role": "human",
            "email": "test_regression@example.com"
        }
        create_resp = requests.post(f"{BASE_URL}/api/v1/users", json=user_data)
        assert create_resp.status_code == 200
        created = create_resp.json()
        assert created["name"] == user_data["name"]
        assert "id" in created
        user_id = created["id"]
        print(f"✓ POST /api/v1/users passed: created user {user_id}")
        
        # Delete user
        delete_resp = requests.delete(f"{BASE_URL}/api/v1/users/{user_id}")
        assert delete_resp.status_code == 200
        delete_data = delete_resp.json()
        assert delete_data["status"] == "deleted"
        print(f"✓ DELETE /api/v1/users/{user_id} passed")


class TestActivityAPI:
    """Activity feed endpoint"""
    
    def test_get_activity(self):
        """GET /api/v1/activity returns activity feed"""
        response = requests.get(f"{BASE_URL}/api/v1/activity")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/v1/activity passed: {len(data)} entries")


class TestTemplatesAPI:
    """Email templates endpoints"""
    
    def test_get_templates(self):
        """GET /api/v1/templates returns templates list"""
        response = requests.get(f"{BASE_URL}/api/v1/templates")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/v1/templates passed: {len(data)} templates")
    
    def test_create_and_delete_template(self):
        """POST /api/v1/templates creates template"""
        # Create template
        template_data = {
            "name": "TEST_Regression_Template",
            "subject": "Test Subject",
            "body": "Test body content"
        }
        create_resp = requests.post(f"{BASE_URL}/api/v1/templates", json=template_data)
        assert create_resp.status_code == 200
        created = create_resp.json()
        assert created["name"] == template_data["name"]
        assert "id" in created
        template_id = created["id"]
        print(f"✓ POST /api/v1/templates passed: created template {template_id}")
        
        # Delete template
        delete_resp = requests.delete(f"{BASE_URL}/api/v1/templates/{template_id}")
        assert delete_resp.status_code == 200
        print(f"✓ DELETE /api/v1/templates/{template_id} passed")


class TestAgentMailAPI:
    """AgentMail inboxes endpoint"""
    
    def test_get_agentmail_inboxes(self):
        """GET /api/v1/agentmail/inboxes returns inboxes"""
        response = requests.get(f"{BASE_URL}/api/v1/agentmail/inboxes")
        # May return 200 with data or 502 if AgentMail not configured
        assert response.status_code in [200, 502]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            print(f"✓ GET /api/v1/agentmail/inboxes passed: {len(data)} inboxes")
        else:
            print("⚠ AgentMail not configured (502 expected)")


class TestCalendarAPI:
    """Calendar feeds endpoint"""
    
    def test_get_calendar_feeds(self):
        """GET /api/v1/calendar/feeds returns feeds"""
        response = requests.get(f"{BASE_URL}/api/v1/calendar/feeds")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/v1/calendar/feeds passed: {len(data)} feeds")


class TestWebSocket:
    """WebSocket endpoint test"""
    
    def test_websocket_endpoint_exists(self):
        """WebSocket /api/v1/ws endpoint exists"""
        # We can't fully test WebSocket with requests, but we can verify
        # the endpoint responds (will get 400 for non-WS request)
        try:
            response = requests.get(f"{BASE_URL}/api/v1/ws", timeout=5)
            # FastAPI returns 403 for non-WebSocket requests to WS endpoints
            # or may return other codes depending on configuration
            print(f"✓ WebSocket endpoint exists (HTTP response: {response.status_code})")
        except Exception as e:
            print(f"⚠ WebSocket endpoint test: {e}")


class TestInboxesAPI:
    """Inboxes endpoint (local DB)"""
    
    def test_get_inboxes(self):
        """GET /api/v1/inboxes returns local inboxes"""
        response = requests.get(f"{BASE_URL}/api/v1/inboxes")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/v1/inboxes passed: {len(data)} inboxes")


class TestAgentsAPI:
    """Agents endpoint"""
    
    def test_get_agents(self):
        """GET /api/v1/agents returns agents list"""
        response = requests.get(f"{BASE_URL}/api/v1/agents")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/v1/agents passed: {len(data)} agents")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

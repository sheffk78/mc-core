"""
Test /api/v1/* API Migration - All endpoints must be at /api/v1/ prefix
Tests: approvals, action-items, schedule, inboxes, activity, stats, brands, templates
WebSocket at /api/v1/ws
"""
import pytest
import requests
import os
import uuid
import asyncio
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
API_V1 = f"{BASE_URL}/api/v1"


# === Approvals Endpoints ===

class TestApprovalsV1:
    """Tests for /api/v1/approvals endpoints"""
    
    def test_get_approvals_list(self):
        """GET /api/v1/approvals returns approval list (not 404)"""
        response = requests.get(f"{API_V1}/approvals")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of approvals"
        print(f"✓ GET /api/v1/approvals returns {len(data)} approvals")
    
    def test_get_single_approval(self):
        """GET /api/v1/approvals/:id returns single approval"""
        # Get list first
        approvals = requests.get(f"{API_V1}/approvals").json()
        if not approvals:
            pytest.skip("No approvals to test")
        
        approval_id = approvals[0]['id']
        response = requests.get(f"{API_V1}/approvals/{approval_id}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data['id'] == approval_id
        print(f"✓ GET /api/v1/approvals/{approval_id[:8]}... returns single approval")
    
    def test_approve_item(self):
        """POST /api/v1/approvals/:id/approve works"""
        approvals = requests.get(f"{API_V1}/approvals", params={"status": "pending"}).json()
        if not approvals:
            pytest.skip("No pending approvals to test")
        
        approval_id = approvals[0]['id']
        response = requests.post(f"{API_V1}/approvals/{approval_id}/approve")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get('status') == 'approved'
        print(f"✓ POST /api/v1/approvals/{approval_id[:8]}../approve works")
    
    def test_reject_item(self):
        """POST /api/v1/approvals/:id/reject works"""
        approvals = requests.get(f"{API_V1}/approvals", params={"status": "pending"}).json()
        if not approvals:
            pytest.skip("No pending approvals to test")
        
        approval_id = approvals[0]['id']
        response = requests.post(f"{API_V1}/approvals/{approval_id}/reject")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get('status') == 'rejected'
        print(f"✓ POST /api/v1/approvals/{approval_id[:8]}../reject works")
    
    def test_dismiss_item(self):
        """POST /api/v1/approvals/:id/dismiss works (alias for discard)"""
        approvals = requests.get(f"{API_V1}/approvals", params={"status": "pending"}).json()
        if not approvals:
            pytest.skip("No pending approvals to test")
        
        approval_id = approvals[0]['id']
        response = requests.post(f"{API_V1}/approvals/{approval_id}/dismiss")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get('status') == 'discarded'
        print(f"✓ POST /api/v1/approvals/{approval_id[:8]}../dismiss works")
    
    def test_edit_approve_item(self):
        """POST /api/v1/approvals/:id/edit-approve works with modified fields"""
        approvals = requests.get(f"{API_V1}/approvals", params={"status": "pending"}).json()
        if not approvals:
            pytest.skip("No pending approvals to test")
        
        approval_id = approvals[0]['id']
        edit_data = {
            "subject": "Modified Subject for Test",
            "to_address": "test@example.com",
            "body": "Modified body content"
        }
        response = requests.post(f"{API_V1}/approvals/{approval_id}/edit-approve", json=edit_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get('status') == 'approved'
        print(f"✓ POST /api/v1/approvals/{approval_id[:8]}../edit-approve works")


# === Action Items Endpoints (alias for tasks) ===

class TestActionItemsV1:
    """Tests for /api/v1/action-items endpoints"""
    
    def test_get_action_items_list(self):
        """GET /api/v1/action-items returns action items list (not 404)"""
        response = requests.get(f"{API_V1}/action-items")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of action items"
        print(f"✓ GET /api/v1/action-items returns {len(data)} items")
    
    def test_get_single_action_item(self):
        """GET /api/v1/action-items/:id returns single item"""
        items = requests.get(f"{API_V1}/action-items").json()
        if not items:
            pytest.skip("No action items to test")
        
        item_id = items[0]['id']
        response = requests.get(f"{API_V1}/action-items/{item_id}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data['id'] == item_id
        print(f"✓ GET /api/v1/action-items/{item_id[:8]}... returns single item")
    
    def test_complete_action_item(self):
        """POST /api/v1/action-items/:id/complete works"""
        # Create a test task first
        task_data = {
            "title": f"TEST_ActionItem_{uuid.uuid4().hex[:8]}",
            "brand": "agentic-trust"
        }
        create_resp = requests.post(f"{API_V1}/tasks", json=task_data)
        assert create_resp.status_code == 200
        item_id = create_resp.json()['id']
        
        response = requests.post(f"{API_V1}/action-items/{item_id}/complete")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get('status') == 'completed'
        print(f"✓ POST /api/v1/action-items/{item_id[:8]}../complete works")
    
    def test_defer_action_item(self):
        """POST /api/v1/action-items/:id/defer works"""
        # Create a test task first
        task_data = {
            "title": f"TEST_DeferActionItem_{uuid.uuid4().hex[:8]}",
            "brand": "agentic-trust"
        }
        create_resp = requests.post(f"{API_V1}/tasks", json=task_data)
        assert create_resp.status_code == 200
        item_id = create_resp.json()['id']
        
        defer_data = {
            "due_date": "2026-05-01T10:00:00Z",
            "reason": "Need more time"
        }
        response = requests.post(f"{API_V1}/action-items/{item_id}/defer", json=defer_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get('status') == 'deferred'
        print(f"✓ POST /api/v1/action-items/{item_id[:8]}../defer works")
    
    def test_redirect_action_item(self):
        """POST /api/v1/action-items/:id/redirect works"""
        # Create a test task first
        task_data = {
            "title": f"TEST_RedirectActionItem_{uuid.uuid4().hex[:8]}",
            "brand": "agentic-trust"
        }
        create_resp = requests.post(f"{API_V1}/tasks", json=task_data)
        assert create_resp.status_code == 200
        item_id = create_resp.json()['id']
        
        redirect_data = {
            "note": "Please review and update",
            "priority": "high"
        }
        response = requests.post(f"{API_V1}/action-items/{item_id}/redirect", json=redirect_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get('status') == 'redirected'
        print(f"✓ POST /api/v1/action-items/{item_id[:8]}../redirect works")


# === Schedule Endpoints ===

class TestScheduleV1:
    """Tests for /api/v1/schedule endpoints"""
    
    def test_get_schedule_list(self):
        """GET /api/v1/schedule returns schedule list (not 404)"""
        response = requests.get(f"{API_V1}/schedule")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of schedule items"
        print(f"✓ GET /api/v1/schedule returns {len(data)} items")
    
    def test_create_schedule_item(self):
        """POST /api/v1/schedule creates a new scheduled job"""
        schedule_data = {
            "brand": "agentic-trust",
            "name": f"TEST_Schedule_{uuid.uuid4().hex[:8]}",
            "description": "Test scheduled job",
            "cron": "0 10 * * *",
            "agent_name": "Kit"
        }
        response = requests.post(f"{API_V1}/schedule", json=schedule_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert 'id' in data
        assert data['name'] == schedule_data['name']
        assert data['status'] == 'active'
        print(f"✓ POST /api/v1/schedule creates job: {data['id'][:8]}...")
        return data['id']
    
    def test_pause_schedule(self):
        """POST /api/v1/schedule/:id/pause pauses a job"""
        # Create a schedule first
        schedule_data = {
            "brand": "agentic-trust",
            "name": f"TEST_PauseSchedule_{uuid.uuid4().hex[:8]}",
            "cron": "0 10 * * *"
        }
        create_resp = requests.post(f"{API_V1}/schedule", json=schedule_data)
        assert create_resp.status_code == 200
        job_id = create_resp.json()['id']
        
        response = requests.post(f"{API_V1}/schedule/{job_id}/pause")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get('status') == 'paused'
        print(f"✓ POST /api/v1/schedule/{job_id[:8]}../pause works")
        return job_id
    
    def test_resume_schedule(self):
        """POST /api/v1/schedule/:id/resume resumes a job"""
        # Create and pause a schedule first
        schedule_data = {
            "brand": "agentic-trust",
            "name": f"TEST_ResumeSchedule_{uuid.uuid4().hex[:8]}",
            "cron": "0 10 * * *"
        }
        create_resp = requests.post(f"{API_V1}/schedule", json=schedule_data)
        assert create_resp.status_code == 200
        job_id = create_resp.json()['id']
        
        # Pause first
        requests.post(f"{API_V1}/schedule/{job_id}/pause")
        
        # Resume
        response = requests.post(f"{API_V1}/schedule/{job_id}/resume")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get('status') == 'active'
        print(f"✓ POST /api/v1/schedule/{job_id[:8]}../resume works")
    
    def test_run_now_schedule(self):
        """POST /api/v1/schedule/:id/run-now triggers immediate run"""
        # Create a schedule first
        schedule_data = {
            "brand": "agentic-trust",
            "name": f"TEST_RunNowSchedule_{uuid.uuid4().hex[:8]}",
            "cron": "0 10 * * *"
        }
        create_resp = requests.post(f"{API_V1}/schedule", json=schedule_data)
        assert create_resp.status_code == 200
        job_id = create_resp.json()['id']
        
        response = requests.post(f"{API_V1}/schedule/{job_id}/run-now")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get('status') == 'running'
        print(f"✓ POST /api/v1/schedule/{job_id[:8]}../run-now works")
    
    def test_edit_schedule(self):
        """POST /api/v1/schedule/:id/edit updates job fields"""
        # Create a schedule first
        schedule_data = {
            "brand": "agentic-trust",
            "name": f"TEST_EditSchedule_{uuid.uuid4().hex[:8]}",
            "cron": "0 10 * * *"
        }
        create_resp = requests.post(f"{API_V1}/schedule", json=schedule_data)
        assert create_resp.status_code == 200
        job_id = create_resp.json()['id']
        
        edit_data = {
            "name": "Updated Schedule Name",
            "description": "Updated description",
            "cron": "0 12 * * *"
        }
        response = requests.post(f"{API_V1}/schedule/{job_id}/edit", json=edit_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data['name'] == edit_data['name']
        assert data['description'] == edit_data['description']
        assert data['cron'] == edit_data['cron']
        print(f"✓ POST /api/v1/schedule/{job_id[:8]}../edit works")


# === Inboxes Endpoint ===

class TestInboxesV1:
    """Tests for /api/v1/inboxes endpoint"""
    
    def test_get_inboxes_list(self):
        """GET /api/v1/inboxes returns inbox list (not 404)"""
        response = requests.get(f"{API_V1}/inboxes")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of inboxes"
        print(f"✓ GET /api/v1/inboxes returns {len(data)} inboxes")


# === Activity Endpoint ===

class TestActivityV1:
    """Tests for /api/v1/activity endpoint"""
    
    def test_get_activity_list(self):
        """GET /api/v1/activity returns activity entries (not 404)"""
        response = requests.get(f"{API_V1}/activity")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of activity entries"
        print(f"✓ GET /api/v1/activity returns {len(data)} entries")


# === Stats Endpoint ===

class TestStatsV1:
    """Tests for /api/v1/stats endpoint"""
    
    def test_get_stats(self):
        """GET /api/v1/stats works"""
        response = requests.get(f"{API_V1}/stats")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert 'pending_approvals' in data
        assert 'open_tasks' in data
        assert 'active_agents' in data
        print(f"✓ GET /api/v1/stats works - {data.get('open_tasks')} open tasks")


# === Brands Endpoint ===

class TestBrandsV1:
    """Tests for /api/v1/brands endpoint"""
    
    def test_get_brands(self):
        """GET /api/v1/brands works"""
        response = requests.get(f"{API_V1}/brands")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "Should have at least one brand"
        print(f"✓ GET /api/v1/brands returns {len(data)} brands")


# === Templates Endpoint ===

class TestTemplatesV1:
    """Tests for /api/v1/templates endpoint"""
    
    def test_get_templates(self):
        """GET /api/v1/templates works"""
        response = requests.get(f"{API_V1}/templates")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/v1/templates returns {len(data)} templates")


# === WebSocket Tests ===

class TestWebSocketV1:
    """Tests for WebSocket at /api/v1/ws"""
    
    def test_websocket_v1_ping_pong(self):
        """WebSocket at /api/v1/ws connects and responds to ping"""
        import websockets
        
        async def test():
            ws_url = BASE_URL.replace('https:', 'wss:').replace('http:', 'ws:') + '/api/v1/ws'
            async with websockets.connect(ws_url, close_timeout=5) as ws:
                await ws.send(json.dumps({'type': 'ping'}))
                response = await asyncio.wait_for(ws.recv(), timeout=5)
                msg = json.loads(response)
                assert msg.get('type') == 'pong', f"Expected pong, got {msg}"
                return True
        
        result = asyncio.run(test())
        assert result, "WebSocket ping/pong failed"
        print("✓ WebSocket at /api/v1/ws connects and responds to ping")
    
    def test_websocket_v1_sync_state(self):
        """WebSocket at /api/v1/ws returns sync_state data"""
        import websockets
        
        async def test():
            ws_url = BASE_URL.replace('https:', 'wss:').replace('http:', 'ws:') + '/api/v1/ws'
            async with websockets.connect(ws_url, close_timeout=5) as ws:
                await ws.send(json.dumps({'type': 'sync_state'}))
                response = await asyncio.wait_for(ws.recv(), timeout=5)
                msg = json.loads(response)
                assert msg.get('type') == 'sync_state', f"Expected sync_state, got {msg}"
                data = msg.get('data', {})
                assert 'approvalQueue' in data, "Missing approvalQueue"
                assert 'actionItems' in data, "Missing actionItems"
                return True
        
        result = asyncio.run(test())
        assert result
        print("✓ WebSocket at /api/v1/ws returns sync_state data")


# === Old API Endpoint Tests ===

class TestOldAPIRemoved:
    """Tests that old /api/ws is removed"""
    
    def test_old_ws_returns_error(self):
        """Old /api/ws returns 403 or 404 (removed)"""
        # WebSocket upgrade request to old endpoint
        response = requests.get(f"{BASE_URL}/api/ws")
        # Should return 404 (not found) or 403 (forbidden)
        assert response.status_code in [403, 404], f"Expected 403 or 404, got {response.status_code}"
        print(f"✓ Old /api/ws returns {response.status_code} (removed)")


# Cleanup fixture
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_data():
    """Cleanup TEST_ prefixed data after tests"""
    yield
    try:
        # Cleanup templates
        templates = requests.get(f"{API_V1}/templates").json()
        for t in templates:
            if t.get("name", "").startswith("TEST_"):
                requests.delete(f"{API_V1}/templates/{t['id']}")
        
        # Note: Schedule and Tasks don't have delete endpoints
    except Exception as e:
        print(f"Cleanup error: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

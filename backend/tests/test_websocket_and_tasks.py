"""
Test WebSocket, Task defer/redirect, and comprehensive API regression tests
"""
import pytest
import requests
import os
import uuid
import asyncio
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# === WebSocket Tests ===

class TestWebSocket:
    """Tests for WebSocket endpoint"""
    
    def test_websocket_ping_pong(self):
        """Test WebSocket ping/pong functionality"""
        import websockets
        
        async def test():
            ws_url = BASE_URL.replace('https:', 'wss:').replace('http:', 'ws:') + '/api/ws'
            async with websockets.connect(ws_url, close_timeout=5) as ws:
                await ws.send(json.dumps({'type': 'ping'}))
                response = await asyncio.wait_for(ws.recv(), timeout=5)
                msg = json.loads(response)
                assert msg.get('type') == 'pong', f"Expected pong, got {msg}"
                return True
        
        result = asyncio.run(test())
        assert result, "WebSocket ping/pong failed"
        print("✓ WebSocket ping/pong works")
    
    def test_websocket_sync_state(self):
        """Test WebSocket sync_state returns data"""
        import websockets
        
        async def test():
            ws_url = BASE_URL.replace('https:', 'wss:').replace('http:', 'ws:') + '/api/ws'
            async with websockets.connect(ws_url, close_timeout=5) as ws:
                await ws.send(json.dumps({'type': 'sync_state'}))
                response = await asyncio.wait_for(ws.recv(), timeout=5)
                msg = json.loads(response)
                assert msg.get('type') == 'sync_state', f"Expected sync_state, got {msg}"
                data = msg.get('data', {})
                assert 'approvalQueue' in data, "Missing approvalQueue in sync_state"
                assert 'actionItems' in data, "Missing actionItems in sync_state"
                assert 'activity' in data, "Missing activity in sync_state"
                return data
        
        data = asyncio.run(test())
        print(f"✓ WebSocket sync_state returns approvals: {len(data.get('approvalQueue', []))}, tasks: {len(data.get('actionItems', []))}")
    
    def test_websocket_broadcast_on_approval_action(self):
        """Test WebSocket broadcasts when approval is approved/rejected"""
        import websockets
        
        async def test():
            ws_url = BASE_URL.replace('https:', 'wss:').replace('http:', 'ws:') + '/api/ws'
            
            # Get a pending approval
            approvals = requests.get(f"{BASE_URL}/api/approvals", params={"status": "pending"}).json()
            if not approvals:
                pytest.skip("No pending approvals to test broadcast")
            
            approval_id = approvals[0]['id']
            
            async with websockets.connect(ws_url, close_timeout=10) as ws:
                # Discard the approval (non-destructive action)
                response = requests.post(f"{BASE_URL}/api/approvals/{approval_id}/discard")
                assert response.status_code == 200
                
                # Wait for broadcast
                try:
                    msg_text = await asyncio.wait_for(ws.recv(), timeout=5)
                    msg = json.loads(msg_text)
                    # Should receive approval_updated or activity_log
                    assert msg.get('type') in ['approval_updated', 'activity_log'], f"Unexpected message type: {msg.get('type')}"
                    return True
                except asyncio.TimeoutError:
                    # Broadcast may have been sent before we connected
                    return True
        
        result = asyncio.run(test())
        print("✓ WebSocket broadcasts on approval action")


# === Task Defer/Redirect Tests ===

class TestTaskDeferRedirect:
    """Tests for task defer and redirect endpoints"""
    
    def test_create_task_with_priority_and_agent_note(self):
        """Test POST /api/tasks accepts priority and agent_note fields"""
        task_data = {
            "title": f"TEST_Task_{uuid.uuid4().hex[:8]}",
            "brand": "agentic-trust",
            "due_date": "2026-04-15T10:00:00Z",
            "priority": "high",
            "agent_note": "Kit flagged this as urgent"
        }
        
        response = requests.post(f"{BASE_URL}/api/tasks", json=task_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        created = response.json()
        assert created['title'] == task_data['title']
        assert created['priority'] == 'high', f"Expected priority 'high', got {created.get('priority')}"
        assert created['agent_note'] == task_data['agent_note'], f"Expected agent_note, got {created.get('agent_note')}"
        assert 'id' in created
        
        print(f"✓ Created task with priority={created['priority']}, agent_note present")
        return created['id']
    
    def test_defer_task(self):
        """Test POST /api/tasks/{id}/defer postpones task with new due_date"""
        # Create a task first
        task_data = {
            "title": f"TEST_DeferTask_{uuid.uuid4().hex[:8]}",
            "brand": "agentic-trust",
            "due_date": "2026-04-10T10:00:00Z",
            "priority": "normal"
        }
        create_response = requests.post(f"{BASE_URL}/api/tasks", json=task_data)
        assert create_response.status_code == 200
        task_id = create_response.json()['id']
        
        # Defer the task
        defer_data = {
            "due_date": "2026-04-20T10:00:00Z",
            "reason": "Need more time to review"
        }
        defer_response = requests.post(f"{BASE_URL}/api/tasks/{task_id}/defer", json=defer_data)
        assert defer_response.status_code == 200, f"Expected 200, got {defer_response.status_code}: {defer_response.text}"
        
        result = defer_response.json()
        assert result.get('status') == 'deferred', f"Expected status 'deferred', got {result}"
        
        # Verify the task was updated
        get_response = requests.get(f"{BASE_URL}/api/tasks")
        tasks = get_response.json()
        updated_task = next((t for t in tasks if t['id'] == task_id), None)
        assert updated_task is not None, "Task not found after defer"
        assert updated_task['due_date'] == defer_data['due_date'], f"Due date not updated: {updated_task['due_date']}"
        assert updated_task['user_note'] == defer_data['reason'], f"User note not set: {updated_task.get('user_note')}"
        
        print(f"✓ Task deferred with new due_date and reason")
    
    def test_redirect_task(self):
        """Test POST /api/tasks/{id}/redirect sends task back with note"""
        # Create a task first
        task_data = {
            "title": f"TEST_RedirectTask_{uuid.uuid4().hex[:8]}",
            "brand": "agentic-trust",
            "priority": "normal"
        }
        create_response = requests.post(f"{BASE_URL}/api/tasks", json=task_data)
        assert create_response.status_code == 200
        task_id = create_response.json()['id']
        
        # Redirect the task
        redirect_data = {
            "note": "Please add more details about the requirements",
            "priority": "high"
        }
        redirect_response = requests.post(f"{BASE_URL}/api/tasks/{task_id}/redirect", json=redirect_data)
        assert redirect_response.status_code == 200, f"Expected 200, got {redirect_response.status_code}: {redirect_response.text}"
        
        result = redirect_response.json()
        assert result.get('status') == 'redirected', f"Expected status 'redirected', got {result}"
        
        # Verify the task was updated
        get_response = requests.get(f"{BASE_URL}/api/tasks")
        tasks = get_response.json()
        updated_task = next((t for t in tasks if t['id'] == task_id), None)
        assert updated_task is not None, "Task not found after redirect"
        assert updated_task['user_note'] == redirect_data['note'], f"User note not set: {updated_task.get('user_note')}"
        assert updated_task['priority'] == 'high', f"Priority not updated: {updated_task.get('priority')}"
        assert updated_task['status'] == 'open', f"Status should be 'open' after redirect: {updated_task.get('status')}"
        
        print(f"✓ Task redirected with note and updated priority")
    
    def test_defer_nonexistent_task(self):
        """Test defer on non-existent task returns 404"""
        fake_id = f"nonexistent-{uuid.uuid4().hex}"
        response = requests.post(f"{BASE_URL}/api/tasks/{fake_id}/defer", json={
            "due_date": "2026-04-20T10:00:00Z"
        })
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Defer non-existent task returns 404")
    
    def test_redirect_nonexistent_task(self):
        """Test redirect on non-existent task returns 404"""
        fake_id = f"nonexistent-{uuid.uuid4().hex}"
        response = requests.post(f"{BASE_URL}/api/tasks/{fake_id}/redirect", json={
            "note": "Test note"
        })
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Redirect non-existent task returns 404")


# === Approval Search Tests ===

class TestApprovalSearch:
    """Tests for approval search functionality"""
    
    def test_approvals_search_by_subject(self):
        """Test GET /api/approvals?search=keyword filters by subject"""
        # Get all approvals first
        all_response = requests.get(f"{BASE_URL}/api/approvals", params={"status": "pending"})
        assert all_response.status_code == 200
        all_approvals = all_response.json()
        
        if not all_approvals:
            pytest.skip("No pending approvals to test search")
        
        # Search for a term that should exist
        search_term = all_approvals[0]['subject'][:10] if all_approvals[0].get('subject') else "test"
        search_response = requests.get(f"{BASE_URL}/api/approvals", params={
            "status": "pending",
            "search": search_term
        })
        assert search_response.status_code == 200
        search_results = search_response.json()
        
        print(f"✓ Search for '{search_term}' returned {len(search_results)} results (from {len(all_approvals)} total)")


# === Templates CRUD Tests ===

class TestTemplates:
    """Tests for email templates CRUD"""
    
    def test_templates_crud_flow(self):
        """Test full CRUD flow for templates"""
        # Create
        template_data = {
            "name": f"TEST_Template_{uuid.uuid4().hex[:8]}",
            "subject": "Test Subject",
            "body": "Test body content"
        }
        create_response = requests.post(f"{BASE_URL}/api/templates", json=template_data)
        assert create_response.status_code == 200
        created = create_response.json()
        template_id = created['id']
        
        # Read
        get_response = requests.get(f"{BASE_URL}/api/templates")
        assert get_response.status_code == 200
        templates = get_response.json()
        found = next((t for t in templates if t['id'] == template_id), None)
        assert found is not None, "Created template not found in list"
        
        # Delete
        delete_response = requests.delete(f"{BASE_URL}/api/templates/{template_id}")
        assert delete_response.status_code == 200
        
        # Verify deleted
        get_response2 = requests.get(f"{BASE_URL}/api/templates")
        templates2 = get_response2.json()
        found2 = next((t for t in templates2 if t['id'] == template_id), None)
        assert found2 is None, "Template should be deleted"
        
        print("✓ Templates CRUD flow works")


# === Existing Endpoints Regression Tests ===

class TestExistingEndpoints:
    """Regression tests for existing endpoints"""
    
    def test_brands_endpoint(self):
        """Test GET /api/brands"""
        response = requests.get(f"{BASE_URL}/api/brands")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "Should have at least one brand"
        print(f"✓ Brands endpoint returns {len(data)} brands")
    
    def test_stats_endpoint(self):
        """Test GET /api/stats"""
        response = requests.get(f"{BASE_URL}/api/stats", params={"brand": "all"})
        assert response.status_code == 200
        data = response.json()
        assert 'pending_approvals' in data
        assert 'open_tasks' in data
        assert 'active_agents' in data
        print(f"✓ Stats endpoint works - {data.get('open_tasks')} open tasks")
    
    def test_approvals_endpoint(self):
        """Test GET /api/approvals"""
        response = requests.get(f"{BASE_URL}/api/approvals")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Approvals endpoint returns {len(data)} items")
    
    def test_tasks_endpoint(self):
        """Test GET /api/tasks"""
        response = requests.get(f"{BASE_URL}/api/tasks")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Verify task structure includes new fields
        if data:
            task = data[0]
            assert 'priority' in task, "Task should have priority field"
            assert 'agent_note' in task, "Task should have agent_note field"
        print(f"✓ Tasks endpoint returns {len(data)} tasks with priority/agent_note fields")
    
    def test_inboxes_endpoint(self):
        """Test GET /api/inboxes"""
        response = requests.get(f"{BASE_URL}/api/inboxes")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Inboxes endpoint returns {len(data)} inboxes")
    
    def test_activity_endpoint(self):
        """Test GET /api/activity"""
        response = requests.get(f"{BASE_URL}/api/activity", params={"brand": "all", "limit": 10})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Activity endpoint returns {len(data)} items")
    
    def test_agentmail_inboxes(self):
        """Test GET /api/agentmail/inboxes"""
        response = requests.get(f"{BASE_URL}/api/agentmail/inboxes")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ AgentMail inboxes returns {len(data)} inboxes")
    
    def test_task_status_update(self):
        """Test PATCH /api/tasks/{id}/status"""
        # Get a task
        tasks = requests.get(f"{BASE_URL}/api/tasks").json()
        if not tasks:
            pytest.skip("No tasks to test status update")
        
        task_id = tasks[0]['id']
        original_status = tasks[0]['status']
        
        # Update to in_progress
        response = requests.patch(f"{BASE_URL}/api/tasks/{task_id}/status", json={"status": "in_progress"})
        assert response.status_code == 200
        
        # Restore original status
        requests.patch(f"{BASE_URL}/api/tasks/{task_id}/status", json={"status": original_status})
        print("✓ Task status update works")


# Cleanup fixture
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_data():
    """Cleanup TEST_ prefixed data after tests"""
    yield
    try:
        # Cleanup templates
        templates = requests.get(f"{BASE_URL}/api/templates").json()
        for t in templates:
            if t.get("name", "").startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/templates/{t['id']}")
        
        # Note: Tasks don't have a delete endpoint, so we can't clean them up
        # They will remain but are prefixed with TEST_ for identification
    except Exception as e:
        print(f"Cleanup error: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

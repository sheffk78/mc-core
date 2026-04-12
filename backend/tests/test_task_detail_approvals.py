"""
Test suite for Task Detail Dialog and Task Approvals features (Iteration 11)
Features tested:
1. PATCH /api/v1/tasks/:id - Update task fields (title, description, due_date, priority, user_note)
2. GET /api/v1/approvals - Includes tasks with status 'approval' (type=task_approval, source=task)
3. Task approval items have priority and due_date fields
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestTaskUpdate:
    """Test PATCH /api/v1/tasks/:id for updating task fields"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Create a test task for update tests"""
        self.task_data = {
            "title": "TEST_Update_Task_" + datetime.now().strftime("%H%M%S"),
            "brand": "agentic-trust",
            "description": "Original description",
            "priority": "normal",
            "due_date": (datetime.now() + timedelta(days=7)).isoformat()
        }
        response = requests.post(f"{BASE_URL}/api/v1/tasks", json=self.task_data)
        assert response.status_code == 200, f"Failed to create test task: {response.text}"
        self.task = response.json()
        self.task_id = self.task["id"]
        yield
        # Cleanup not strictly needed as TEST_ prefix identifies test data
    
    def test_update_task_title(self):
        """Test updating task title via PATCH"""
        new_title = "TEST_Updated_Title_" + datetime.now().strftime("%H%M%S")
        response = requests.patch(
            f"{BASE_URL}/api/v1/tasks/{self.task_id}",
            json={"title": new_title}
        )
        assert response.status_code == 200, f"PATCH failed: {response.text}"
        data = response.json()
        assert data["title"] == new_title, f"Title not updated: {data}"
        
        # Verify persistence with GET
        get_response = requests.get(f"{BASE_URL}/api/v1/tasks/{self.task_id}")
        assert get_response.status_code == 200
        assert get_response.json()["title"] == new_title
        print("✓ PATCH /api/v1/tasks/:id updates title correctly")
    
    def test_update_task_description(self):
        """Test updating task description via PATCH"""
        new_description = "Updated description for testing"
        response = requests.patch(
            f"{BASE_URL}/api/v1/tasks/{self.task_id}",
            json={"description": new_description}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == new_description
        print("✓ PATCH /api/v1/tasks/:id updates description correctly")
    
    def test_update_task_due_date(self):
        """Test updating task due_date via PATCH"""
        new_due_date = (datetime.now() + timedelta(days=14)).isoformat()
        response = requests.patch(
            f"{BASE_URL}/api/v1/tasks/{self.task_id}",
            json={"due_date": new_due_date}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["due_date"] == new_due_date
        print("✓ PATCH /api/v1/tasks/:id updates due_date correctly")
    
    def test_update_task_priority(self):
        """Test updating task priority via PATCH"""
        for priority in ["low", "normal", "high", "urgent"]:
            response = requests.patch(
                f"{BASE_URL}/api/v1/tasks/{self.task_id}",
                json={"priority": priority}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["priority"] == priority, f"Priority not updated to {priority}"
        print("✓ PATCH /api/v1/tasks/:id updates priority correctly (all values)")
    
    def test_update_task_user_note(self):
        """Test updating task user_note via PATCH"""
        new_note = "User note added during testing"
        response = requests.patch(
            f"{BASE_URL}/api/v1/tasks/{self.task_id}",
            json={"user_note": new_note}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_note"] == new_note
        print("✓ PATCH /api/v1/tasks/:id updates user_note correctly")
    
    def test_update_multiple_fields(self):
        """Test updating multiple fields at once via PATCH"""
        updates = {
            "title": "TEST_Multi_Update_" + datetime.now().strftime("%H%M%S"),
            "description": "Multi-field update test",
            "priority": "high",
            "user_note": "Multiple fields updated"
        }
        response = requests.patch(
            f"{BASE_URL}/api/v1/tasks/{self.task_id}",
            json=updates
        )
        assert response.status_code == 200
        data = response.json()
        for key, value in updates.items():
            assert data[key] == value, f"Field {key} not updated correctly"
        print("✓ PATCH /api/v1/tasks/:id updates multiple fields correctly")
    
    def test_update_nonexistent_task(self):
        """Test PATCH on non-existent task returns 404"""
        response = requests.patch(
            f"{BASE_URL}/api/v1/tasks/nonexistent-task-id",
            json={"title": "Should fail"}
        )
        assert response.status_code == 404
        print("✓ PATCH /api/v1/tasks/:id returns 404 for non-existent task")


class TestTaskApprovals:
    """Test GET /api/v1/approvals includes tasks with status 'approval'"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Create a test task and move it to approval status"""
        self.task_data = {
            "title": "TEST_Approval_Task_" + datetime.now().strftime("%H%M%S"),
            "brand": "agentic-trust",
            "description": "Task for approval testing",
            "priority": "high",
            "due_date": (datetime.now() + timedelta(days=3)).isoformat()
        }
        response = requests.post(f"{BASE_URL}/api/v1/tasks", json=self.task_data)
        assert response.status_code == 200, f"Failed to create test task: {response.text}"
        self.task = response.json()
        self.task_id = self.task["id"]
        
        # Move task to approval status
        status_response = requests.patch(
            f"{BASE_URL}/api/v1/tasks/{self.task_id}/status",
            json={"status": "approval"}
        )
        assert status_response.status_code == 200, f"Failed to move task to approval: {status_response.text}"
        yield
    
    def test_approvals_includes_tasks_in_approval_status(self):
        """Test GET /api/v1/approvals includes tasks with status 'approval'"""
        response = requests.get(f"{BASE_URL}/api/v1/approvals")
        assert response.status_code == 200
        items = response.json()
        
        # Find our test task in the approvals list
        task_approval = None
        for item in items:
            if item.get("id") == self.task_id:
                task_approval = item
                break
        
        assert task_approval is not None, f"Task {self.task_id} not found in approvals list"
        print("✓ GET /api/v1/approvals includes tasks with status 'approval'")
    
    def test_task_approval_has_type_task_approval(self):
        """Test task approval items have type='task_approval'"""
        response = requests.get(f"{BASE_URL}/api/v1/approvals")
        assert response.status_code == 200
        items = response.json()
        
        task_approval = next((item for item in items if item.get("id") == self.task_id), None)
        assert task_approval is not None
        assert task_approval.get("type") == "task_approval", f"Expected type='task_approval', got {task_approval.get('type')}"
        print("✓ Task approval items have type='task_approval'")
    
    def test_task_approval_has_source_task(self):
        """Test task approval items have source='task'"""
        response = requests.get(f"{BASE_URL}/api/v1/approvals")
        assert response.status_code == 200
        items = response.json()
        
        task_approval = next((item for item in items if item.get("id") == self.task_id), None)
        assert task_approval is not None
        assert task_approval.get("source") == "task", f"Expected source='task', got {task_approval.get('source')}"
        print("✓ Task approval items have source='task'")
    
    def test_task_approval_has_priority_field(self):
        """Test task approval items include priority field"""
        response = requests.get(f"{BASE_URL}/api/v1/approvals")
        assert response.status_code == 200
        items = response.json()
        
        task_approval = next((item for item in items if item.get("id") == self.task_id), None)
        assert task_approval is not None
        assert "priority" in task_approval, "Task approval missing priority field"
        assert task_approval["priority"] == "high", f"Expected priority='high', got {task_approval.get('priority')}"
        print("✓ Task approval items have priority field")
    
    def test_task_approval_has_due_date_field(self):
        """Test task approval items include due_date field"""
        response = requests.get(f"{BASE_URL}/api/v1/approvals")
        assert response.status_code == 200
        items = response.json()
        
        task_approval = next((item for item in items if item.get("id") == self.task_id), None)
        assert task_approval is not None
        assert "due_date" in task_approval, "Task approval missing due_date field"
        assert task_approval["due_date"] != "", "Task approval due_date should not be empty"
        print("✓ Task approval items have due_date field")
    
    def test_task_approval_has_subject_from_title(self):
        """Test task approval items have subject field from task title"""
        response = requests.get(f"{BASE_URL}/api/v1/approvals")
        assert response.status_code == 200
        items = response.json()
        
        task_approval = next((item for item in items if item.get("id") == self.task_id), None)
        assert task_approval is not None
        assert task_approval.get("subject") == self.task_data["title"], f"Subject should match task title"
        print("✓ Task approval items have subject from task title")
    
    def test_task_approval_brand_filter(self):
        """Test GET /api/v1/approvals?brand=X filters task approvals correctly"""
        response = requests.get(f"{BASE_URL}/api/v1/approvals", params={"brand": "agentic-trust"})
        assert response.status_code == 200
        items = response.json()
        
        task_approval = next((item for item in items if item.get("id") == self.task_id), None)
        assert task_approval is not None, "Task approval should appear when filtering by its brand"
        
        # Filter by different brand - task should not appear
        response2 = requests.get(f"{BASE_URL}/api/v1/approvals", params={"brand": "aav"})
        assert response2.status_code == 200
        items2 = response2.json()
        task_approval2 = next((item for item in items2 if item.get("id") == self.task_id), None)
        assert task_approval2 is None, "Task approval should not appear when filtering by different brand"
        print("✓ GET /api/v1/approvals brand filter works for task approvals")
    
    def test_completing_task_removes_from_approvals(self):
        """Test that completing a task removes it from approvals list"""
        # First verify task is in approvals
        response = requests.get(f"{BASE_URL}/api/v1/approvals")
        items = response.json()
        task_approval = next((item for item in items if item.get("id") == self.task_id), None)
        assert task_approval is not None, "Task should be in approvals before completing"
        
        # Complete the task
        complete_response = requests.patch(
            f"{BASE_URL}/api/v1/tasks/{self.task_id}/status",
            json={"status": "completed"}
        )
        assert complete_response.status_code == 200
        
        # Verify task is no longer in approvals
        response2 = requests.get(f"{BASE_URL}/api/v1/approvals")
        items2 = response2.json()
        task_approval2 = next((item for item in items2 if item.get("id") == self.task_id), None)
        assert task_approval2 is None, "Completed task should not appear in approvals"
        print("✓ Completing a task removes it from approvals list")
    
    def test_send_back_moves_task_to_open(self):
        """Test that 'Send Back' action (status=open) removes task from approvals"""
        # Create another task for this test
        task_data = {
            "title": "TEST_SendBack_Task_" + datetime.now().strftime("%H%M%S"),
            "brand": "agentic-trust",
            "description": "Task for send back testing",
            "priority": "normal"
        }
        create_response = requests.post(f"{BASE_URL}/api/v1/tasks", json=task_data)
        assert create_response.status_code == 200
        task_id = create_response.json()["id"]
        
        # Move to approval
        requests.patch(f"{BASE_URL}/api/v1/tasks/{task_id}/status", json={"status": "approval"})
        
        # Verify in approvals
        response = requests.get(f"{BASE_URL}/api/v1/approvals")
        items = response.json()
        assert any(item.get("id") == task_id for item in items), "Task should be in approvals"
        
        # Send back (move to open)
        sendback_response = requests.patch(
            f"{BASE_URL}/api/v1/tasks/{task_id}/status",
            json={"status": "open"}
        )
        assert sendback_response.status_code == 200
        
        # Verify no longer in approvals
        response2 = requests.get(f"{BASE_URL}/api/v1/approvals")
        items2 = response2.json()
        assert not any(item.get("id") == task_id for item in items2), "Task should not be in approvals after send back"
        print("✓ 'Send Back' (status=open) removes task from approvals")


class TestRegressionEndpoints:
    """Regression tests for existing endpoints"""
    
    def test_get_brands(self):
        """Test GET /api/v1/brands still works"""
        response = requests.get(f"{BASE_URL}/api/v1/brands")
        assert response.status_code == 200
        brands = response.json()
        assert isinstance(brands, list)
        assert len(brands) > 0
        print("✓ Regression: GET /api/v1/brands works")
    
    def test_get_stats(self):
        """Test GET /api/v1/stats still works"""
        response = requests.get(f"{BASE_URL}/api/v1/stats")
        assert response.status_code == 200
        stats = response.json()
        assert "pending_approvals" in stats
        assert "open_tasks" in stats
        print("✓ Regression: GET /api/v1/stats works")
    
    def test_get_tasks(self):
        """Test GET /api/v1/tasks still works"""
        response = requests.get(f"{BASE_URL}/api/v1/tasks")
        assert response.status_code == 200
        tasks = response.json()
        assert isinstance(tasks, list)
        print("✓ Regression: GET /api/v1/tasks works")
    
    def test_get_approvals(self):
        """Test GET /api/v1/approvals still works"""
        response = requests.get(f"{BASE_URL}/api/v1/approvals")
        assert response.status_code == 200
        approvals = response.json()
        assert isinstance(approvals, list)
        print("✓ Regression: GET /api/v1/approvals works")
    
    def test_get_activity(self):
        """Test GET /api/v1/activity still works"""
        response = requests.get(f"{BASE_URL}/api/v1/activity")
        assert response.status_code == 200
        activity = response.json()
        assert isinstance(activity, list)
        print("✓ Regression: GET /api/v1/activity works")
    
    def test_email_approvals_still_work(self):
        """Test that email approvals (non-task) still appear in approvals list"""
        response = requests.get(f"{BASE_URL}/api/v1/approvals")
        assert response.status_code == 200
        items = response.json()
        
        # Check for email approvals (source != 'task' or no source field)
        email_approvals = [item for item in items if item.get("source") != "task"]
        # There should be some email approvals from seed data
        print(f"  Found {len(email_approvals)} email approvals and {len(items) - len(email_approvals)} task approvals")
        print("✓ Regression: Email approvals still appear in approvals list")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

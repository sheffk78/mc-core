"""
Test Settings Page Features (Users CRUD, Brands CRUD) and Task Assignee Features
Tests for iteration 12 - Settings page and task assignment functionality
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestUsersAPI:
    """Tests for Users CRUD endpoints at /api/v1/users"""
    
    def test_get_users_returns_jeff_and_kit(self):
        """GET /api/v1/users should return Jeff and Kit"""
        response = requests.get(f"{BASE_URL}/api/v1/users")
        assert response.status_code == 200
        users = response.json()
        assert isinstance(users, list)
        names = [u['name'] for u in users]
        assert 'Jeff' in names, "Jeff should be in users list"
        assert 'Kit' in names, "Kit should be in users list"
        # Verify Jeff is human and Kit is agent
        jeff = next((u for u in users if u['name'] == 'Jeff'), None)
        kit = next((u for u in users if u['name'] == 'Kit'), None)
        assert jeff['role'] == 'human', "Jeff should have role 'human'"
        assert kit['role'] == 'agent', "Kit should have role 'agent'"
    
    def test_create_user(self):
        """POST /api/v1/users creates a new user"""
        unique_name = f"TEST_User_{uuid.uuid4().hex[:6]}"
        payload = {
            "name": unique_name,
            "role": "human",
            "email": "test@example.com",
            "avatar_color": "#c85a2a"
        }
        response = requests.post(f"{BASE_URL}/api/v1/users", json=payload)
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        user = response.json()
        assert user['name'] == unique_name
        assert user['role'] == 'human'
        assert user['email'] == 'test@example.com'
        assert 'id' in user
        # Cleanup
        requests.delete(f"{BASE_URL}/api/v1/users/{user['id']}")
    
    def test_update_user(self):
        """PATCH /api/v1/users/:id updates a user"""
        # First create a user
        unique_name = f"TEST_Update_{uuid.uuid4().hex[:6]}"
        create_resp = requests.post(f"{BASE_URL}/api/v1/users", json={
            "name": unique_name,
            "role": "human",
            "email": "",
            "avatar_color": "#c85a2a"
        })
        assert create_resp.status_code in [200, 201]
        user = create_resp.json()
        user_id = user['id']
        
        # Update the user
        update_resp = requests.patch(f"{BASE_URL}/api/v1/users/{user_id}", json={
            "name": f"{unique_name}_Updated",
            "role": "agent",
            "email": "updated@example.com"
        })
        assert update_resp.status_code == 200, f"Expected 200, got {update_resp.status_code}: {update_resp.text}"
        updated = update_resp.json()
        assert updated['name'] == f"{unique_name}_Updated"
        assert updated['role'] == 'agent'
        assert updated['email'] == 'updated@example.com'
        
        # Verify persistence with GET
        get_resp = requests.get(f"{BASE_URL}/api/v1/users")
        users = get_resp.json()
        found = next((u for u in users if u['id'] == user_id), None)
        assert found is not None
        assert found['name'] == f"{unique_name}_Updated"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/v1/users/{user_id}")
    
    def test_delete_user(self):
        """DELETE /api/v1/users/:id deletes a user"""
        # Create a user to delete
        unique_name = f"TEST_Delete_{uuid.uuid4().hex[:6]}"
        create_resp = requests.post(f"{BASE_URL}/api/v1/users", json={
            "name": unique_name,
            "role": "human",
            "email": "",
            "avatar_color": "#c85a2a"
        })
        user = create_resp.json()
        user_id = user['id']
        
        # Delete the user
        delete_resp = requests.delete(f"{BASE_URL}/api/v1/users/{user_id}")
        assert delete_resp.status_code in [200, 204], f"Expected 200/204, got {delete_resp.status_code}"
        
        # Verify user is gone
        get_resp = requests.get(f"{BASE_URL}/api/v1/users")
        users = get_resp.json()
        found = next((u for u in users if u['id'] == user_id), None)
        assert found is None, "Deleted user should not appear in users list"


class TestBrandsAPI:
    """Tests for Brands CRUD endpoints at /api/v1/brands"""
    
    def test_get_brands_returns_all_brands(self):
        """GET /api/v1/brands should return all 8+ brands"""
        response = requests.get(f"{BASE_URL}/api/v1/brands")
        assert response.status_code == 200
        brands = response.json()
        assert isinstance(brands, list)
        assert len(brands) >= 8, f"Expected at least 8 brands, got {len(brands)}"
        # Check for expected brands
        slugs = [b['slug'] for b in brands]
        expected_slugs = ['all', 'agentic-trust', 'aav', 'safe-spend', 'arl', 'true-joy-birthing', 'trustoffice', 'wingpoint']
        for slug in expected_slugs:
            assert slug in slugs, f"Brand '{slug}' should be in brands list"
    
    def test_create_brand(self):
        """POST /api/v1/brands creates a new brand"""
        unique_slug = f"test-brand-{uuid.uuid4().hex[:6]}"
        payload = {
            "name": f"Test Brand {unique_slug}",
            "slug": unique_slug,
            "color": "#ff5500"
        }
        response = requests.post(f"{BASE_URL}/api/v1/brands", json=payload)
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        brand = response.json()
        assert brand['name'] == payload['name']
        assert brand['slug'] == unique_slug
        assert brand['color'] == '#ff5500'
        # Cleanup
        requests.delete(f"{BASE_URL}/api/v1/brands/{unique_slug}")
    
    def test_update_brand(self):
        """PATCH /api/v1/brands/:slug updates a brand"""
        # Create a brand to update
        unique_slug = f"test-update-{uuid.uuid4().hex[:6]}"
        create_resp = requests.post(f"{BASE_URL}/api/v1/brands", json={
            "name": "Original Name",
            "slug": unique_slug,
            "color": "#000000"
        })
        assert create_resp.status_code in [200, 201]
        
        # Update the brand
        update_resp = requests.patch(f"{BASE_URL}/api/v1/brands/{unique_slug}", json={
            "name": "Updated Name",
            "color": "#ffffff"
        })
        assert update_resp.status_code == 200, f"Expected 200, got {update_resp.status_code}: {update_resp.text}"
        updated = update_resp.json()
        assert updated['name'] == 'Updated Name'
        assert updated['color'] == '#ffffff'
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/v1/brands/{unique_slug}")
    
    def test_delete_brand(self):
        """DELETE /api/v1/brands/:slug deletes a brand"""
        # Create a brand to delete
        unique_slug = f"test-delete-{uuid.uuid4().hex[:6]}"
        create_resp = requests.post(f"{BASE_URL}/api/v1/brands", json={
            "name": "To Delete",
            "slug": unique_slug,
            "color": "#123456"
        })
        assert create_resp.status_code in [200, 201]
        
        # Delete the brand
        delete_resp = requests.delete(f"{BASE_URL}/api/v1/brands/{unique_slug}")
        assert delete_resp.status_code in [200, 204], f"Expected 200/204, got {delete_resp.status_code}"
        
        # Verify brand is gone
        get_resp = requests.get(f"{BASE_URL}/api/v1/brands")
        brands = get_resp.json()
        found = next((b for b in brands if b['slug'] == unique_slug), None)
        assert found is None, "Deleted brand should not appear in brands list"
    
    def test_cannot_delete_all_brand(self):
        """DELETE /api/v1/brands/all should fail - 'all' is protected"""
        response = requests.delete(f"{BASE_URL}/api/v1/brands/all")
        # Should return 400 or 403 or similar error
        assert response.status_code in [400, 403, 404], f"Expected error status for deleting 'all' brand, got {response.status_code}"


class TestTaskAssigneeFeatures:
    """Tests for task assignee field and filtering"""
    
    def test_get_tasks_with_assignee_filter(self):
        """GET /api/v1/tasks?assignee=Jeff filters by assignee"""
        response = requests.get(f"{BASE_URL}/api/v1/tasks", params={"assignee": "Jeff"})
        assert response.status_code == 200
        tasks = response.json()
        # All returned tasks should have assignee=Jeff
        for task in tasks:
            assert task.get('assignee') == 'Jeff', f"Task {task['id']} has assignee '{task.get('assignee')}', expected 'Jeff'"
    
    def test_get_tasks_with_assignee_kit(self):
        """GET /api/v1/tasks?assignee=Kit filters by Kit"""
        response = requests.get(f"{BASE_URL}/api/v1/tasks", params={"assignee": "Kit"})
        assert response.status_code == 200
        tasks = response.json()
        for task in tasks:
            assert task.get('assignee') == 'Kit', f"Task {task['id']} has assignee '{task.get('assignee')}', expected 'Kit'"
    
    def test_create_task_with_assignee(self):
        """POST /api/v1/tasks accepts assignee field"""
        unique_title = f"TEST_Task_Assignee_{uuid.uuid4().hex[:6]}"
        payload = {
            "title": unique_title,
            "brand": "agentic-trust",
            "assignee": "Jeff",
            "priority": "normal"
        }
        response = requests.post(f"{BASE_URL}/api/v1/tasks", json=payload)
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        task = response.json()
        assert task['title'] == unique_title
        assert task['assignee'] == 'Jeff', f"Expected assignee 'Jeff', got '{task.get('assignee')}'"
        
        # Verify it appears in filtered list
        filter_resp = requests.get(f"{BASE_URL}/api/v1/tasks", params={"assignee": "Jeff"})
        tasks = filter_resp.json()
        found = next((t for t in tasks if t['id'] == task['id']), None)
        assert found is not None, "Created task should appear in Jeff's filtered tasks"
    
    def test_update_task_assignee(self):
        """PATCH /api/v1/tasks/:id accepts assignee field"""
        # Create a task
        unique_title = f"TEST_Update_Assignee_{uuid.uuid4().hex[:6]}"
        create_resp = requests.post(f"{BASE_URL}/api/v1/tasks", json={
            "title": unique_title,
            "brand": "agentic-trust",
            "assignee": "Jeff"
        })
        task = create_resp.json()
        task_id = task['id']
        
        # Update assignee to Kit
        update_resp = requests.patch(f"{BASE_URL}/api/v1/tasks/{task_id}", json={
            "assignee": "Kit"
        })
        assert update_resp.status_code == 200
        updated = update_resp.json()
        assert updated['assignee'] == 'Kit', f"Expected assignee 'Kit', got '{updated.get('assignee')}'"
        
        # Verify it now appears in Kit's list, not Jeff's
        kit_tasks = requests.get(f"{BASE_URL}/api/v1/tasks", params={"assignee": "Kit"}).json()
        jeff_tasks = requests.get(f"{BASE_URL}/api/v1/tasks", params={"assignee": "Jeff"}).json()
        
        found_in_kit = next((t for t in kit_tasks if t['id'] == task_id), None)
        found_in_jeff = next((t for t in jeff_tasks if t['id'] == task_id), None)
        
        assert found_in_kit is not None, "Task should appear in Kit's filtered list"
        assert found_in_jeff is None, "Task should NOT appear in Jeff's filtered list after reassignment"
    
    def test_tasks_have_assignee_field(self):
        """GET /api/v1/tasks returns tasks with assignee field (for newly created tasks)"""
        # Create a new task to ensure it has assignee field
        unique_title = f"TEST_Assignee_Field_{uuid.uuid4().hex[:6]}"
        create_resp = requests.post(f"{BASE_URL}/api/v1/tasks", json={
            "title": unique_title,
            "brand": "agentic-trust",
            "assignee": ""
        })
        task = create_resp.json()
        assert 'assignee' in task, "Newly created task should have 'assignee' field"
        # Note: Older tasks may not have assignee field due to data migration


class TestRegressionChecks:
    """Regression tests to ensure existing functionality still works"""
    
    def test_kanban_has_4_columns_statuses(self):
        """Tasks can have all 4 Kanban statuses"""
        # Create tasks with each status
        statuses = ['open', 'in_progress', 'approval', 'completed']
        for status in statuses:
            unique_title = f"TEST_Status_{status}_{uuid.uuid4().hex[:6]}"
            create_resp = requests.post(f"{BASE_URL}/api/v1/tasks", json={
                "title": unique_title,
                "brand": "agentic-trust"
            })
            task = create_resp.json()
            # Update to target status
            update_resp = requests.patch(f"{BASE_URL}/api/v1/tasks/{task['id']}/status", json={"status": status})
            assert update_resp.status_code == 200, f"Failed to set status to {status}"
    
    def test_overview_stats_endpoint(self):
        """GET /api/v1/stats works"""
        response = requests.get(f"{BASE_URL}/api/v1/stats")
        assert response.status_code == 200
        stats = response.json()
        assert 'pending_approvals' in stats
        assert 'open_tasks' in stats
    
    def test_approvals_endpoint(self):
        """GET /api/v1/approvals works"""
        response = requests.get(f"{BASE_URL}/api/v1/approvals")
        assert response.status_code == 200
    
    def test_inboxes_endpoint(self):
        """GET /api/v1/inboxes works"""
        response = requests.get(f"{BASE_URL}/api/v1/inboxes")
        assert response.status_code == 200
    
    def test_activity_endpoint(self):
        """GET /api/v1/activity works"""
        response = requests.get(f"{BASE_URL}/api/v1/activity")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

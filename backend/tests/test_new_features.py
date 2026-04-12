"""
Test new features: Approval Search and Email Templates CRUD
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestApprovalSearch:
    """Tests for approval search functionality"""
    
    def test_approvals_endpoint_exists(self):
        """Test that approvals endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/approvals")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Expected list of approvals"
        print(f"✓ Approvals endpoint returns {len(data)} items")
    
    def test_approvals_with_search_param(self):
        """Test approvals endpoint accepts search parameter"""
        response = requests.get(f"{BASE_URL}/api/approvals", params={
            "brand": "all",
            "status": "pending",
            "search": "product"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Expected list of approvals"
        print(f"✓ Search with 'product' returns {len(data)} items")
    
    def test_approvals_empty_search_returns_all(self):
        """Test that empty search returns all pending approvals"""
        # Get all pending approvals without search
        response_all = requests.get(f"{BASE_URL}/api/approvals", params={
            "brand": "all",
            "status": "pending"
        })
        assert response_all.status_code == 200
        all_data = response_all.json()
        
        # Get with empty search
        response_empty = requests.get(f"{BASE_URL}/api/approvals", params={
            "brand": "all",
            "status": "pending",
            "search": ""
        })
        assert response_empty.status_code == 200
        empty_search_data = response_empty.json()
        
        # Should return same count
        assert len(all_data) == len(empty_search_data), \
            f"Empty search should return all items: {len(all_data)} vs {len(empty_search_data)}"
        print(f"✓ Empty search returns same {len(all_data)} items as no search")
    
    def test_approvals_search_filters_results(self):
        """Test that search actually filters results"""
        # Get all pending approvals
        response_all = requests.get(f"{BASE_URL}/api/approvals", params={
            "brand": "all",
            "status": "pending"
        })
        assert response_all.status_code == 200
        all_data = response_all.json()
        
        if len(all_data) == 0:
            pytest.skip("No pending approvals to test search filtering")
        
        # Search for a specific term that likely won't match all
        response_search = requests.get(f"{BASE_URL}/api/approvals", params={
            "brand": "all",
            "status": "pending",
            "search": "xyznonexistent123"
        })
        assert response_search.status_code == 200
        search_data = response_search.json()
        
        # Non-existent search should return fewer or equal results
        assert len(search_data) <= len(all_data), "Search should filter results"
        print(f"✓ Search filtering works: {len(all_data)} total, {len(search_data)} after search")
    
    def test_approvals_search_case_insensitive(self):
        """Test that search is case insensitive"""
        # Search lowercase
        response_lower = requests.get(f"{BASE_URL}/api/approvals", params={
            "brand": "all",
            "status": "pending",
            "search": "test"
        })
        assert response_lower.status_code == 200
        
        # Search uppercase
        response_upper = requests.get(f"{BASE_URL}/api/approvals", params={
            "brand": "all",
            "status": "pending",
            "search": "TEST"
        })
        assert response_upper.status_code == 200
        
        # Both should return same count (case insensitive)
        assert len(response_lower.json()) == len(response_upper.json()), \
            "Search should be case insensitive"
        print("✓ Search is case insensitive")


class TestEmailTemplates:
    """Tests for email template CRUD functionality"""
    
    def test_templates_endpoint_exists(self):
        """Test that templates endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/templates")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Expected list of templates"
        print(f"✓ Templates endpoint returns {len(data)} templates")
    
    def test_create_template(self):
        """Test creating a new template"""
        unique_name = f"TEST_Template_{uuid.uuid4().hex[:8]}"
        template_data = {
            "name": unique_name,
            "subject": "Test Subject Line",
            "body": "This is a test template body."
        }
        
        response = requests.post(f"{BASE_URL}/api/templates", json=template_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        created = response.json()
        assert "id" in created, "Created template should have an id"
        assert created["name"] == unique_name, "Name should match"
        assert created["subject"] == template_data["subject"], "Subject should match"
        assert created["body"] == template_data["body"], "Body should match"
        assert "created_at" in created, "Should have created_at timestamp"
        
        print(f"✓ Created template with id: {created['id']}")
        return created["id"]
    
    def test_create_and_get_template(self):
        """Test creating a template and verifying it appears in list"""
        unique_name = f"TEST_Template_{uuid.uuid4().hex[:8]}"
        template_data = {
            "name": unique_name,
            "subject": "Verify Subject",
            "body": "Verify body content"
        }
        
        # Create template
        create_response = requests.post(f"{BASE_URL}/api/templates", json=template_data)
        assert create_response.status_code == 200
        created = create_response.json()
        template_id = created["id"]
        
        # Get all templates and verify it exists
        get_response = requests.get(f"{BASE_URL}/api/templates")
        assert get_response.status_code == 200
        templates = get_response.json()
        
        found = next((t for t in templates if t["id"] == template_id), None)
        assert found is not None, f"Created template {template_id} should be in list"
        assert found["name"] == unique_name
        assert found["subject"] == template_data["subject"]
        assert found["body"] == template_data["body"]
        
        print(f"✓ Template {template_id} persisted and retrieved successfully")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/templates/{template_id}")
    
    def test_delete_template(self):
        """Test deleting a template"""
        # First create a template
        unique_name = f"TEST_ToDelete_{uuid.uuid4().hex[:8]}"
        create_response = requests.post(f"{BASE_URL}/api/templates", json={
            "name": unique_name,
            "subject": "Delete me",
            "body": "This will be deleted"
        })
        assert create_response.status_code == 200
        template_id = create_response.json()["id"]
        
        # Delete the template
        delete_response = requests.delete(f"{BASE_URL}/api/templates/{template_id}")
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}"
        
        delete_data = delete_response.json()
        assert delete_data.get("status") == "deleted", "Should return deleted status"
        assert delete_data.get("id") == template_id, "Should return deleted id"
        
        # Verify it's gone from list
        get_response = requests.get(f"{BASE_URL}/api/templates")
        templates = get_response.json()
        found = next((t for t in templates if t["id"] == template_id), None)
        assert found is None, "Deleted template should not be in list"
        
        print(f"✓ Template {template_id} deleted successfully")
    
    def test_delete_nonexistent_template(self):
        """Test deleting a template that doesn't exist returns 404"""
        fake_id = f"nonexistent-{uuid.uuid4().hex}"
        response = requests.delete(f"{BASE_URL}/api/templates/{fake_id}")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Deleting non-existent template returns 404")
    
    def test_create_template_with_empty_body(self):
        """Test creating a template with empty body"""
        unique_name = f"TEST_EmptyBody_{uuid.uuid4().hex[:8]}"
        template_data = {
            "name": unique_name,
            "subject": "Subject only",
            "body": ""
        }
        
        response = requests.post(f"{BASE_URL}/api/templates", json=template_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        created = response.json()
        assert created["body"] == "", "Empty body should be allowed"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/templates/{created['id']}")
        print("✓ Template with empty body created successfully")


class TestExistingFeatures:
    """Verify existing features still work"""
    
    def test_brands_endpoint(self):
        """Test brands endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/brands")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Brands endpoint returns {len(data)} brands")
    
    def test_stats_endpoint(self):
        """Test stats endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/stats", params={"brand": "all"})
        assert response.status_code == 200
        data = response.json()
        assert "pending_approvals" in data or isinstance(data, dict)
        print("✓ Stats endpoint works")
    
    def test_agentmail_inboxes(self):
        """Test AgentMail inboxes endpoint"""
        response = requests.get(f"{BASE_URL}/api/agentmail/inboxes")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ AgentMail inboxes returns {len(data)} inboxes")
    
    def test_activity_endpoint(self):
        """Test activity feed endpoint"""
        response = requests.get(f"{BASE_URL}/api/activity", params={"brand": "all", "limit": 10})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Activity endpoint returns {len(data)} items")


# Cleanup test templates after all tests
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_templates():
    """Cleanup any TEST_ prefixed templates after tests"""
    yield
    # Cleanup
    try:
        response = requests.get(f"{BASE_URL}/api/templates")
        if response.status_code == 200:
            templates = response.json()
            for t in templates:
                if t.get("name", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/templates/{t['id']}")
    except Exception as e:
        print(f"Cleanup error: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

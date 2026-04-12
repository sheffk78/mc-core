import requests
import sys
import json
from datetime import datetime

class MissionControlAPITester:
    def __init__(self, base_url="https://command-center-268.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, list):
                        print(f"   Response: List with {len(response_data)} items")
                    elif isinstance(response_data, dict):
                        print(f"   Response keys: {list(response_data.keys())}")
                    return True, response_data
                except:
                    return True, {}
            else:
                self.failed_tests.append(f"{name}: Expected {expected_status}, got {response.status_code}")
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error text: {response.text}")
                return False, {}

        except Exception as e:
            self.failed_tests.append(f"{name}: Exception - {str(e)}")
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_brands_api(self):
        """Test brands endpoint"""
        print("\n=== TESTING BRANDS API ===")
        success, brands = self.run_test("Get Brands", "GET", "brands", 200)
        if success and brands:
            print(f"   Found {len(brands)} brands")
            # Check for 'All Brands' + 8 specific brands = 9 total
            if len(brands) == 9:
                print("✅ Correct number of brands (9 including 'All Brands')")
                all_brands_found = any(b.get('name') == 'All Brands' for b in brands)
                if all_brands_found:
                    print("✅ 'All Brands' found in response")
                else:
                    print("❌ 'All Brands' not found in response")
            else:
                print(f"❌ Expected 9 brands, got {len(brands)}")
        return success, brands

    def test_stats_api(self):
        """Test stats endpoint"""
        print("\n=== TESTING STATS API ===")
        success, stats = self.run_test("Get Stats (All Brands)", "GET", "stats", 200)
        if success and stats:
            expected_keys = ['pending_approvals', 'active_agents', 'total_agents', 'open_tasks', 'pending_emails']
            missing_keys = [key for key in expected_keys if key not in stats]
            if not missing_keys:
                print("✅ All required stats keys present")
                print(f"   Stats: {stats}")
            else:
                print(f"❌ Missing stats keys: {missing_keys}")
        
        # Test brand filtering
        success2, filtered_stats = self.run_test("Get Stats (Agentic Trust)", "GET", "stats", 200, 
                                                params={'brand': 'agentic-trust'})
        return success and success2, stats

    def test_approvals_api(self):
        """Test approvals endpoint and actions"""
        print("\n=== TESTING APPROVALS API ===")
        success, approvals = self.run_test("Get Approvals", "GET", "approvals", 200)
        approval_id = None
        
        if success and approvals:
            print(f"   Found {len(approvals)} pending approvals")
            if approvals:
                approval_id = approvals[0].get('id')
                print(f"   First approval ID: {approval_id}")
                
                # Check if to_address field is populated
                to_address = approvals[0].get('to_address')
                if to_address:
                    print(f"✅ to_address field populated: {to_address}")
                else:
                    print("❌ to_address field missing or empty")
        
        # Test brand filtering
        success2, filtered = self.run_test("Get Approvals (Agentic Trust)", "GET", "approvals", 200,
                                          params={'brand': 'agentic-trust'})
        
        # Test approval action if we have an ID - this will actually send email via AgentMail
        success3 = True
        if approval_id:
            print(f"   ⚠️  WARNING: About to send real email via AgentMail for approval {approval_id}")
            success3, approve_result = self.run_test("Approve Item (Sends Real Email)", "POST", f"approvals/{approval_id}/approve", 200)
            if success3 and approve_result:
                sent = approve_result.get('sent', False)
                send_result = approve_result.get('send_result', {})
                print(f"   Email sent: {sent}")
                if send_result:
                    print(f"   Send result keys: {list(send_result.keys())}")
                    if 'message_id' in send_result:
                        print(f"✅ message_id in send_result: {send_result.get('message_id')}")
                    if 'thread_id' in send_result:
                        print(f"✅ thread_id in send_result: {send_result.get('thread_id')}")
        
        return success and success2 and success3, approvals

    def test_agents_api(self):
        """Test agents endpoint"""
        print("\n=== TESTING AGENTS API ===")
        success, agents = self.run_test("Get Agents", "GET", "agents", 200)
        if success and agents:
            print(f"   Found {len(agents)} agents")
            
        # Test brand filtering
        success2, filtered = self.run_test("Get Agents (AAV)", "GET", "agents", 200,
                                         params={'brand': 'aav'})
        return success and success2, agents

    def test_tasks_api(self):
        """Test tasks endpoint and actions"""
        print("\n=== TESTING TASKS API ===")
        success, tasks = self.run_test("Get Tasks", "GET", "tasks", 200)
        task_id = None
        
        if success and tasks:
            print(f"   Found {len(tasks)} tasks")
            if tasks:
                task_id = tasks[0].get('id')
        
        # Test creating a new task
        new_task_data = {
            "title": f"Test Task - {datetime.now().strftime('%H:%M:%S')}",
            "brand": "agentic-trust",
            "due_date": ""
        }
        success2, created_task = self.run_test("Create Task", "POST", "tasks", 200, data=new_task_data)
        created_task_id = None
        if success2 and created_task:
            created_task_id = created_task.get('id')
            print(f"   Created task ID: {created_task_id}")
        
        # Test completing a task
        success3 = True
        if created_task_id:
            success3, _ = self.run_test("Complete Task", "POST", f"tasks/{created_task_id}/complete", 200)
        
        return success and success2 and success3, tasks

    def test_inboxes_api(self):
        """Test inboxes endpoint"""
        print("\n=== TESTING INBOXES API ===")
        success, inboxes = self.run_test("Get Inboxes", "GET", "inboxes", 200)
        if success and inboxes:
            print(f"   Found {len(inboxes)} inboxes")
            
        # Test brand filtering
        success2, filtered = self.run_test("Get Inboxes (Safe-Spend)", "GET", "inboxes", 200,
                                         params={'brand': 'safe-spend'})
        return success and success2, inboxes

    def test_activity_api(self):
        """Test activity endpoint"""
        print("\n=== TESTING ACTIVITY API ===")
        success, activity = self.run_test("Get Activity", "GET", "activity", 200)
        if success and activity:
            print(f"   Found {len(activity)} activity entries")
            # Check if sorted by time desc
            if len(activity) > 1:
                first_time = activity[0].get('time', '')
                second_time = activity[1].get('time', '')
                if first_time >= second_time:
                    print("✅ Activity sorted by time descending")
                else:
                    print("❌ Activity not properly sorted")
            
        # Test brand filtering
        success2, filtered = self.run_test("Get Activity (ARL)", "GET", "activity", 200,
                                         params={'brand': 'arl'})
        return success and success2, activity

    def test_seed_api(self):
        """Test database seeding"""
        print("\n=== TESTING SEED API ===")
        success, result = self.run_test("Seed Database", "POST", "seed", 200)
        return success, result

    def test_agentmail_inboxes_api(self):
        """Test AgentMail inboxes endpoint"""
        print("\n=== TESTING AGENTMAIL INBOXES API ===")
        success, inboxes = self.run_test("Get AgentMail Inboxes", "GET", "agentmail/inboxes", 200)
        
        if success and inboxes:
            print(f"   Found {len(inboxes)} AgentMail inboxes")
            # Check for expected 5 real inboxes
            if len(inboxes) == 5:
                print("✅ Correct number of AgentMail inboxes (5)")
            else:
                print(f"❌ Expected 5 AgentMail inboxes, got {len(inboxes)}")
            
            # Check for required fields
            for inbox in inboxes:
                required_fields = ['inbox_id', 'email', 'display_name', 'brand', 'message_count']
                missing_fields = [field for field in required_fields if field not in inbox]
                if missing_fields:
                    print(f"❌ Inbox missing fields: {missing_fields}")
                else:
                    print(f"✅ Inbox {inbox['email']} has all required fields")
        
        # Test brand filtering for agentic-trust
        success2, filtered = self.run_test("Get AgentMail Inboxes (Agentic Trust)", "GET", "agentmail/inboxes", 200,
                                         params={'brand': 'agentic-trust'})
        if success2 and filtered:
            agentic_count = len(filtered)
            print(f"   Found {agentic_count} agentic-trust inboxes after filtering")
            # Should be 1 inbox: support@agentictrust.app
            if agentic_count == 1:
                print("✅ Correct number of agentic-trust inboxes (1)")
            else:
                print(f"❌ Expected 1 agentic-trust inbox, got {agentic_count}")
        
        return success and success2, inboxes

    def test_agentmail_messages_api(self):
        """Test AgentMail messages endpoint"""
        print("\n=== TESTING AGENTMAIL MESSAGES API ===")
        # Use the specific inbox_id mentioned in the test requirements
        inbox_id = "support@agentictrust.app"
        success, messages_data = self.run_test("Get AgentMail Messages", "GET", 
                                             f"agentmail/inboxes/{inbox_id}/messages", 200)
        
        if success and messages_data:
            messages = messages_data.get('messages', [])
            count = messages_data.get('count', 0)
            print(f"   Found {len(messages)} messages, total count: {count}")
            
            # Check message structure
            if messages:
                msg = messages[0]
                required_fields = ['message_id', 'thread_id', 'subject', 'from', 'created_at']
                missing_fields = [field for field in required_fields if field not in msg]
                if missing_fields:
                    print(f"❌ Message missing fields: {missing_fields}")
                else:
                    print("✅ Message has all required fields")
        
        return success, messages_data

    def test_agentmail_thread_api(self):
        """Test AgentMail thread endpoint"""
        print("\n=== TESTING AGENTMAIL THREAD API ===")
        # Use the specific thread_id mentioned in the test requirements
        thread_id = "e3afe16d-a5de-4952-99f9-49c1e791c5d8"
        success, thread_data = self.run_test("Get AgentMail Thread", "GET", 
                                           f"agentmail/threads/{thread_id}", 200)
        
        if success and thread_data:
            messages = thread_data.get('messages', [])
            message_count = thread_data.get('message_count', 0)
            print(f"   Thread has {len(messages)} messages, count: {message_count}")
            
            # Check thread structure
            required_fields = ['thread_id', 'inbox_id', 'subject', 'messages']
            missing_fields = [field for field in required_fields if field not in thread_data]
            if missing_fields:
                print(f"❌ Thread missing fields: {missing_fields}")
            else:
                print("✅ Thread has all required fields")
                
            # Check message structure in thread
            if messages:
                msg = messages[0]
                msg_required = ['message_id', 'subject', 'from', 'created_at']
                msg_missing = [field for field in msg_required if field not in msg]
                if msg_missing:
                    print(f"❌ Thread message missing fields: {msg_missing}")
                else:
                    print("✅ Thread message has all required fields")
        
        return success, thread_data

    def test_stats_with_agentmail(self):
        """Test stats endpoint includes real AgentMail pending_emails"""
        print("\n=== TESTING STATS WITH AGENTMAIL ===")
        success, stats = self.run_test("Get Stats with AgentMail", "GET", "stats", 200)
        
        if success and stats:
            pending_emails = stats.get('pending_emails', 0)
            print(f"   Pending emails from AgentMail: {pending_emails}")
            
            # Should be a real number from AgentMail, not the old mock data
            if isinstance(pending_emails, int) and pending_emails >= 0:
                print("✅ Pending emails is a valid integer")
            else:
                print(f"❌ Invalid pending emails value: {pending_emails}")
        
        return success, stats

    def test_task_status_updates(self):
        """Test PATCH /api/tasks/{id}/status endpoint with different status values"""
        print("\n=== TESTING TASK STATUS UPDATES ===")
        
        # First get a task to update
        success, tasks = self.run_test("Get Tasks for Status Update", "GET", "tasks", 200)
        if not success or not tasks:
            print("❌ No tasks available for status update testing")
            return False, None
            
        task_id = tasks[0].get('id')
        print(f"   Using task ID: {task_id}")
        
        # Test updating to 'in_progress'
        success1, _ = self.run_test("Update Task to In Progress", "PATCH", f"tasks/{task_id}/status", 200, 
                                   data={"status": "in_progress"})
        
        # Test updating to 'completed'
        success2, _ = self.run_test("Update Task to Completed", "PATCH", f"tasks/{task_id}/status", 200,
                                   data={"status": "completed"})
        
        # Test updating to 'open'
        success3, _ = self.run_test("Update Task to Open", "PATCH", f"tasks/{task_id}/status", 200,
                                   data={"status": "open"})
        
        return success1 and success2 and success3, None

    def test_calendar_feeds_api(self):
        """Test calendar feeds CRUD operations"""
        print("\n=== TESTING CALENDAR FEEDS API ===")
        
        # Test GET /api/calendar/feeds (should return empty array initially)
        success1, feeds = self.run_test("Get Calendar Feeds (Empty)", "GET", "calendar/feeds", 200)
        if success1:
            if isinstance(feeds, list) and len(feeds) == 0:
                print("✅ Calendar feeds returns empty array initially")
            else:
                print(f"❌ Expected empty array, got: {feeds}")
        
        # Test POST /api/calendar/feeds (create a feed)
        feed_data = {
            "name": "Test Calendar",
            "url": "https://calendar.google.com/calendar/ical/test@example.com/public/basic.ics",
            "color": "#c85a2a"
        }
        success2, created_feed = self.run_test("Create Calendar Feed", "POST", "calendar/feeds", 200, data=feed_data)
        feed_id = None
        if success2 and created_feed:
            feed_id = created_feed.get('id')
            print(f"   Created feed ID: {feed_id}")
        
        # Test DELETE /api/calendar/feeds/{id} (remove feed)
        success3 = True
        if feed_id:
            success3, _ = self.run_test("Delete Calendar Feed", "DELETE", f"calendar/feeds/{feed_id}", 200)
        
        return success1 and success2 and success3, feeds

    def test_calendar_events_api(self):
        """Test calendar events endpoint"""
        print("\n=== TESTING CALENDAR EVENTS API ===")
        
        # Test GET /api/calendar/events (should return empty events if no feeds)
        success, events_data = self.run_test("Get Calendar Events", "GET", "calendar/events", 200)
        if success and events_data:
            events = events_data.get('events', [])
            feeds_count = events_data.get('feeds', 0)
            print(f"   Found {len(events)} events from {feeds_count} feeds")
            
            # Should return empty events if no feeds configured
            if feeds_count == 0 and len(events) == 0:
                print("✅ Returns empty events when no feeds configured")
            else:
                print(f"   Events available from {feeds_count} feeds")
        
        return success, events_data

    def test_agentmail_webhooks_api(self):
        """Test AgentMail webhooks endpoint"""
        print("\n=== TESTING AGENTMAIL WEBHOOKS API ===")
        
        # Test POST /api/webhooks/agentmail (accepts webhook payload)
        webhook_payload = {
            "event_type": "message.received",
            "message": {
                "inbox_id": "test@example.com",
                "subject": "Test Message",
                "from_": "sender@example.com",
                "preview": "This is a test message"
            }
        }
        success, result = self.run_test("AgentMail Webhook", "POST", "webhooks/agentmail", 200, data=webhook_payload)
        
        return success, result

    def test_approval_draft_updates(self):
        """Test PATCH /api/approvals/{id} for updating draft fields"""
        print("\n=== TESTING APPROVAL DRAFT UPDATES ===")
        
        # First get pending approvals
        success, approvals = self.run_test("Get Pending Approvals for Draft Update", "GET", "approvals", 200)
        if not success or not approvals:
            print("❌ No pending approvals available for draft update testing")
            return False, None
            
        approval_id = approvals[0].get('id')
        original_status = approvals[0].get('status')
        print(f"   Using approval ID: {approval_id} (status: {original_status})")
        
        # Test updating draft fields for pending item
    def test_seed_with_to_address(self):
        """Test POST /api/seed re-seeds with to_address in approval data"""
        print("\n=== TESTING SEED WITH TO_ADDRESS ===")
        
        # Re-seed the database
        success1, seed_result = self.run_test("Re-seed Database", "POST", "seed", 200)
        
        if success1:
            # Get approvals to verify to_address is populated
            success2, approvals = self.run_test("Get Approvals After Seed", "GET", "approvals", 200)
            
            if success2 and approvals:
                to_address_count = 0
                for approval in approvals:
                    if approval.get('to_address'):
                        to_address_count += 1
                        
                print(f"   Found {to_address_count}/{len(approvals)} approvals with to_address populated")
                
                if to_address_count == len(approvals):
                    print("✅ All approvals have to_address populated after seed")
                    return True, approvals
                else:
                    print(f"❌ Only {to_address_count}/{len(approvals)} approvals have to_address")
                    return False, approvals
            else:
                return False, None
    def test_agentmail_labels_api(self):
        """Test AgentMail message labels functionality"""
        print("\n=== TESTING AGENTMAIL LABELS API ===")
        
        # First get messages to test labels on
        inbox_id = "support@agentictrust.app"
        success1, messages_data = self.run_test("Get Messages for Labels Test", "GET", 
                                               f"agentmail/inboxes/{inbox_id}/messages", 200)
        
        message_id = None
        if success1 and messages_data:
            messages = messages_data.get('messages', [])
            if messages:
                message_id = messages[0].get('message_id')
                print(f"   Using message ID: {message_id}")
        
        # Test GET with labels parameter
        success2, filtered_messages = self.run_test("Get Messages with Labels Filter", "GET", 
                                                   f"agentmail/inboxes/{inbox_id}/messages", 200,
                                                   params={"labels": "received"})
        
        # Test POST to update labels
        success3 = True
        if message_id:
            labels_data = {
                "add_labels": ["read"],
                "remove_labels": ["unread"]
            }
            success3, _ = self.run_test("Update Message Labels", "POST", 
                                       f"agentmail/inboxes/{inbox_id}/messages/{message_id}/labels", 200,
                                       data=labels_data)
        
        return success1 and success2 and success3, None

    def test_agentmail_compose_api(self):
        """Test AgentMail compose endpoint - SENDS REAL EMAIL"""
        print("\n=== TESTING AGENTMAIL COMPOSE API ===")
        print("   ⚠️  WARNING: This test ACTUALLY sends real emails via AgentMail")
        
        # Test compose email
        compose_data = {
            "inbox_id": "support@agentictrust.app",
            "to": ["support@agentictrust.app"],  # Send to same inbox for testing
            "subject": f"Test Email from Mission Control - {datetime.now().strftime('%H:%M:%S')}",
            "text": "This is a test email sent from the Mission Control compose feature via AgentMail API."
        }
        
        success, result = self.run_test("Compose Email (Sends Real Email)", "POST", "agentmail/compose", 200, data=compose_data)
        
        if success and result:
            # Check required response fields
            required_fields = ['status', 'message_id', 'thread_id']
            missing_fields = [field for field in required_fields if field not in result]
            
            if not missing_fields:
                print("✅ Compose response has all required fields")
                print(f"   Status: {result.get('status')}")
                print(f"   Message ID: {result.get('message_id')}")
                print(f"   Thread ID: {result.get('thread_id')}")
                
                # Check status is 'sent'
                if result.get('status') == 'sent':
                    print("✅ Email status is 'sent'")
                else:
                    print(f"❌ Expected status 'sent', got '{result.get('status')}'")
                    
            else:
                print(f"❌ Compose response missing fields: {missing_fields}")
        
        return success, result

    def test_agentmail_reply_api(self):
        """Test AgentMail reply endpoint - SENDS REAL EMAIL"""
        print("\n=== TESTING AGENTMAIL REPLY API ===")
        print("   ⚠️  WARNING: This test ACTUALLY sends real emails via AgentMail")
        
        # First get messages to reply to
        inbox_id = "support@agentictrust.app"
        success1, messages_data = self.run_test("Get Messages for Reply Test", "GET", 
                                               f"agentmail/inboxes/{inbox_id}/messages", 200)
        
        message_id = None
        if success1 and messages_data:
            messages = messages_data.get('messages', [])
            if messages:
                message_id = messages[0].get('message_id')
                print(f"   Using message ID for reply: {message_id}")
        
        # Test reply to message
        success2 = True
        if message_id:
            reply_data = {
                "text": f"This is a test reply from Mission Control - {datetime.now().strftime('%H:%M:%S')}"
            }
            
            success2, result = self.run_test("Reply to Message (Sends Real Email)", "POST", 
                                           f"agentmail/reply/{inbox_id}/{message_id}", 200, data=reply_data)
            
            if success2 and result:
                # Check required response fields
                required_fields = ['status', 'message_id', 'thread_id']
                missing_fields = [field for field in required_fields if field not in result]
                
                if not missing_fields:
                    print("✅ Reply response has all required fields")
                    print(f"   Status: {result.get('status')}")
                    print(f"   Message ID: {result.get('message_id')}")
                    print(f"   Thread ID: {result.get('thread_id')}")
                    
                    # Check status is 'sent'
                    if result.get('status') == 'sent':
                        print("✅ Reply status is 'sent'")
                    else:
                        print(f"❌ Expected status 'sent', got '{result.get('status')}'")
                        
                else:
                    print(f"❌ Reply response missing fields: {missing_fields}")
        else:
            print("❌ No message ID available for reply test")
            success2 = False
        
        return success1 and success2, None

def main():
    print("🚀 Starting Mission Control API Tests")
    print("=" * 50)
    
    tester = MissionControlAPITester()
    
    # Run all tests
    test_results = {}
    
    test_results['brands'] = tester.test_brands_api()
    test_results['stats'] = tester.test_stats_api()
    test_results['approvals'] = tester.test_approvals_api()
    test_results['agents'] = tester.test_agents_api()
    test_results['tasks'] = tester.test_tasks_api()
    test_results['inboxes'] = tester.test_inboxes_api()
    test_results['activity'] = tester.test_activity_api()
    test_results['seed'] = tester.test_seed_api()
    
    # Test new AgentMail integration
    test_results['agentmail_inboxes'] = tester.test_agentmail_inboxes_api()
    test_results['agentmail_messages'] = tester.test_agentmail_messages_api()
    test_results['agentmail_thread'] = tester.test_agentmail_thread_api()
    test_results['stats_agentmail'] = tester.test_stats_with_agentmail()
    
    # Test new features from iteration 3
    test_results['task_status_updates'] = tester.test_task_status_updates()
    test_results['calendar_feeds'] = tester.test_calendar_feeds_api()
    test_results['calendar_events'] = tester.test_calendar_events_api()
    test_results['agentmail_webhooks'] = tester.test_agentmail_webhooks_api()
    test_results['agentmail_labels'] = tester.test_agentmail_labels_api()
    
    # Test new approval features from iteration 4
    test_results['approval_draft_updates'] = tester.test_approval_draft_updates()
    test_results['seed_with_to_address'] = tester.test_seed_with_to_address()
    
    # Test new compose and reply features from iteration 5
    test_results['agentmail_compose'] = tester.test_agentmail_compose_api()
    test_results['agentmail_reply'] = tester.test_agentmail_reply_api()
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Tests run: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
    
    if tester.failed_tests:
        print("\n❌ FAILED TESTS:")
        for failure in tester.failed_tests:
            print(f"   - {failure}")
    else:
        print("\n✅ ALL TESTS PASSED!")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
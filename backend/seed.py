from db import db, now_iso, ago_iso
from models import (
    Brand, Agent, ApprovalItem, TaskItem, InboxItem, ActivityEntry, UserProfile
)

BRANDS_DATA = [
    {"name": "All Brands", "slug": "all", "color": "#8a8480", "order": 0},
    {"name": "Agentic Trust", "slug": "agentic-trust", "color": "#c85a2a", "order": 1},
    {"name": "AAV", "slug": "aav", "color": "#2d6a4f", "order": 2},
    {"name": "Safe-Spend", "slug": "safe-spend", "color": "#2a5c8a", "order": 3},
    {"name": "ARL", "slug": "arl", "color": "#7c5cbf", "order": 4},
    {"name": "True Joy Birthing", "slug": "true-joy-birthing", "color": "#c2756b", "order": 5},
    {"name": "TrustOffice", "slug": "trustoffice", "color": "#5a8a6a", "order": 6},
    {"name": "WingPoint", "slug": "wingpoint", "color": "#b06a10", "order": 7},
    {"name": "AnchorPoint", "slug": "anchorpoint", "color": "#6a7c8a", "order": 8},
]

async def seed_database():
    for col in ["brands", "agents", "approvals", "tasks", "inboxes", "activity"]:
        await db[col].delete_many({})

    for b in BRANDS_DATA:
        brand = Brand(**b)
        await db.brands.insert_one(brand.model_dump())

    user_count = await db.users.count_documents({})
    if user_count == 0:
        default_users = [
            {"name": "Jeff", "role": "human", "email": "", "avatar_color": "#c85a2a", "active": True, "created_at": now_iso()},
            {"name": "Kit", "role": "agent", "email": "", "avatar_color": "#2d6a4f", "active": True, "created_at": now_iso()},
        ]
        for u in default_users:
            user = UserProfile(**u)
            await db.users.insert_one(user.model_dump())

    agents_data = [
        {"name": "Kit -- Content", "brand": "agentic-trust", "role": "Drafts blog posts, social copy, and email sequences", "status": "active", "last_activity": ago_iso(minutes=3), "initials": "KC", "avatar_color": "#c85a2a"},
        {"name": "Kit -- Outreach", "brand": "agentic-trust", "role": "Manages cold outreach and partnership emails", "status": "waiting", "last_activity": ago_iso(minutes=45), "initials": "KO", "avatar_color": "#a04520"},
        {"name": "Kit -- Research", "brand": "aav", "role": "Market research and competitive analysis", "status": "active", "last_activity": ago_iso(minutes=12), "initials": "KR", "avatar_color": "#2d6a4f"},
        {"name": "Kit -- Finance", "brand": "safe-spend", "role": "Invoice processing and expense tracking", "status": "idle", "last_activity": ago_iso(hours=4), "initials": "KF", "avatar_color": "#2a5c8a"},
        {"name": "Kit -- Support", "brand": "arl", "role": "Customer support ticket triage and response drafting", "status": "active", "last_activity": ago_iso(minutes=1), "initials": "KS", "avatar_color": "#7c5cbf"},
        {"name": "Kit -- Scheduling", "brand": "true-joy-birthing", "role": "Appointment scheduling and follow-up reminders", "status": "waiting", "last_activity": ago_iso(hours=1), "initials": "KD", "avatar_color": "#c2756b"},
        {"name": "Kit -- Legal", "brand": "trustoffice", "role": "Contract review and compliance monitoring", "status": "idle", "last_activity": ago_iso(hours=8), "initials": "KL", "avatar_color": "#5a8a6a"},
        {"name": "Kit -- Analytics", "brand": "wingpoint", "role": "Weekly performance reports and data synthesis", "status": "active", "last_activity": ago_iso(minutes=20), "initials": "KA", "avatar_color": "#b06a10"},
    ]
    for a in agents_data:
        agent = Agent(**a)
        await db.agents.insert_one(agent.model_dump())

    approvals_data = [
        {"brand": "agentic-trust", "type": "content", "agent_name": "Kit -- Content", "from_address": "support@agentictrust.app", "to_address": "newsletter@agentictrust.com", "inbox": "content-drafts", "subject": "Q2 Thought Leadership: \"Why Agents Need Guardrails\"", "preview": "The article argues that autonomous agents without human oversight create liability risks for enterprises...", "created_at": ago_iso(hours=2), "status": "pending"},
        {"brand": "agentic-trust", "type": "content", "agent_name": "Kit -- Outreach", "from_address": "support@agentictrust.app", "to_address": "partnerships@anthropic.com", "inbox": "outreach", "subject": "Partnership Proposal to Anthropic -- Draft Email", "preview": "Dear Anthropic team, I'm writing on behalf of Agentic Trust to explore a potential integration partnership...", "created_at": ago_iso(hours=5), "status": "pending"},
        {"brand": "aav", "type": "content", "agent_name": "Kit -- Research", "from_address": "support@agentictrust.app", "to_address": "team@aav.io", "inbox": "research-reports", "subject": "Competitive Landscape Update -- March 2026", "preview": "Key findings: Three new entrants in the autonomous vehicle verification space...", "created_at": ago_iso(hours=1), "status": "pending"},
        {"brand": "safe-spend", "type": "purchase", "agent_name": "Kit -- Finance", "from_address": "support@agentictrust.app", "to_address": "billing@datadoghq.com", "inbox": "procurement", "subject": "Renewal: DataDog Pro Plan -- $2,400/yr", "preview": "Annual renewal for DataDog monitoring. Current plan covers 10 hosts...", "created_at": ago_iso(hours=3), "status": "pending"},
        {"brand": "arl", "type": "content", "agent_name": "Kit -- Support", "from_address": "support@agentictrust.app", "to_address": "marcus.chen@enterprise-client.com", "inbox": "support-drafts", "subject": "Response to Enterprise Client -- Data Migration Issue", "preview": "Hi Marcus, Thank you for flagging the data migration issue...", "created_at": ago_iso(minutes=30), "status": "pending"},
        {"brand": "true-joy-birthing", "type": "content", "agent_name": "Kit -- Scheduling", "from_address": "support@truejoybirthing.com", "to_address": "week32-group@truejoy.care", "inbox": "client-comms", "subject": "Prenatal Class Reminder -- Week 32 Group", "preview": "Dear expecting parents, This is a gentle reminder about your upcoming Week 32 prenatal class...", "created_at": ago_iso(hours=6), "status": "pending"},
        {"brand": "wingpoint", "type": "trigger", "agent_name": "Kit -- Analytics", "from_address": "support@agentictrust.app", "to_address": "leadership@wingpoint.co", "inbox": "reports", "subject": "Weekly Performance Report -- Trigger Send to Stakeholders", "preview": "Weekly metrics compiled: Revenue up 12% WoW, churn rate steady at 2.1%, NPS improved from 42 to 47...", "created_at": ago_iso(hours=1, minutes=30), "status": "pending"},
        {"brand": "trustoffice", "type": "content", "agent_name": "Kit -- Legal", "from_address": "contact@trustoffice.app", "to_address": "legal@cloudsecure.inc", "inbox": "contract-review", "subject": "NDA Review -- Potential Vendor (CloudSecure Inc.)", "preview": "Reviewed the mutual NDA from CloudSecure Inc. Two clauses flagged...", "created_at": ago_iso(hours=4), "status": "pending"},
    ]
    for a in approvals_data:
        item = ApprovalItem(**a)
        await db.approvals.insert_one(item.model_dump())

    tasks_data = [
        {"title": "Review and finalize Q2 content calendar", "brand": "agentic-trust", "due_date": ago_iso(days=2), "status": "open", "assignee": "Jeff", "created_at": ago_iso(days=5)},
        {"title": "Approve vendor shortlist for design refresh", "brand": "aav", "due_date": ago_iso(days=1), "status": "open", "assignee": "Jeff", "created_at": ago_iso(days=3)},
        {"title": "Sign off on updated privacy policy", "brand": "safe-spend", "due_date": ago_iso(days=-2), "status": "open", "assignee": "Jeff", "created_at": ago_iso(days=7)},
        {"title": "Schedule investor update call", "brand": "agentic-trust", "due_date": ago_iso(days=-5), "status": "open", "assignee": "Kit", "created_at": ago_iso(days=2)},
        {"title": "Review support escalation process", "brand": "arl", "due_date": ago_iso(days=3), "status": "open", "assignee": "Jeff", "created_at": ago_iso(days=4)},
        {"title": "Prepare board deck for March meeting", "brand": "trustoffice", "due_date": ago_iso(days=5), "status": "open", "assignee": "Kit", "created_at": ago_iso(days=10)},
        {"title": "Update client onboarding checklist", "brand": "true-joy-birthing", "due_date": ago_iso(days=-3), "status": "open", "assignee": "Jeff", "created_at": ago_iso(days=6)},
        {"title": "Review analytics dashboard mockups", "brand": "wingpoint", "due_date": ago_iso(days=-4), "status": "open", "assignee": "Kit", "created_at": ago_iso(days=3)},
        {"title": "Finalize partnership agreement terms", "brand": "anchorpoint", "due_date": ago_iso(days=1), "status": "open", "assignee": "Jeff", "created_at": ago_iso(days=8)},
    ]
    for t in tasks_data:
        task = TaskItem(**t)
        await db.tasks.insert_one(task.model_dump())

    inboxes_data = [
        {"email": "content@agentictrust.com", "agent_name": "Kit -- Content", "brand": "agentic-trust", "pending_count": 4, "last_activity": ago_iso(minutes=3)},
        {"email": "outreach@agentictrust.com", "agent_name": "Kit -- Outreach", "brand": "agentic-trust", "pending_count": 2, "last_activity": ago_iso(minutes=45)},
        {"email": "research@aav.io", "agent_name": "Kit -- Research", "brand": "aav", "pending_count": 1, "last_activity": ago_iso(minutes=12)},
        {"email": "finance@safe-spend.com", "agent_name": "Kit -- Finance", "brand": "safe-spend", "pending_count": 3, "last_activity": ago_iso(hours=4)},
        {"email": "support@arl.dev", "agent_name": "Kit -- Support", "brand": "arl", "pending_count": 7, "last_activity": ago_iso(minutes=1)},
        {"email": "scheduling@truejoy.care", "agent_name": "Kit -- Scheduling", "brand": "true-joy-birthing", "pending_count": 2, "last_activity": ago_iso(hours=1)},
        {"email": "legal@trustoffice.law", "agent_name": "Kit -- Legal", "brand": "trustoffice", "pending_count": 0, "last_activity": ago_iso(hours=8)},
        {"email": "reports@wingpoint.co", "agent_name": "Kit -- Analytics", "brand": "wingpoint", "pending_count": 1, "last_activity": ago_iso(minutes=20)},
    ]
    for i in inboxes_data:
        inbox = InboxItem(**i)
        await db.inboxes.insert_one(inbox.model_dump())

    activity_data = [
        {"brand": "arl", "type": "approval", "text": "Kit -- Support draft approved and sent", "detail": "Response to Enterprise Client -- Data Migration Issue", "time": ago_iso(minutes=5)},
        {"brand": "agentic-trust", "type": "system", "text": "Kit -- Content started drafting", "detail": "Q2 Thought Leadership article", "time": ago_iso(minutes=15)},
        {"brand": "aav", "type": "task", "text": "New task created by Kit -- Research", "detail": "Approve vendor shortlist for design refresh", "time": ago_iso(minutes=30)},
        {"brand": "wingpoint", "type": "system", "text": "Kit -- Analytics compiled weekly report", "detail": "Revenue up 12% WoW, NPS improved to 47", "time": ago_iso(hours=1)},
        {"brand": "safe-spend", "type": "approval", "text": "DataDog renewal submitted for approval", "detail": "$2,400/yr -- Pro Plan", "time": ago_iso(hours=1, minutes=30)},
        {"brand": "true-joy-birthing", "type": "system", "text": "Kit -- Scheduling sent 12 appointment reminders", "detail": "Week 32 prenatal group", "time": ago_iso(hours=2)},
        {"brand": "trustoffice", "type": "task", "text": "Task completed: Monthly compliance check", "detail": "All items within threshold", "time": ago_iso(hours=3)},
        {"brand": "agentic-trust", "type": "approval", "text": "Partnership email draft rejected", "detail": "Needs revised positioning -- too formal", "time": ago_iso(hours=4)},
        {"brand": "arl", "type": "error", "text": "Kit -- Support flagged unusual ticket volume", "detail": "47 tickets in last hour (3x normal)", "time": ago_iso(hours=5)},
        {"brand": "safe-spend", "type": "system", "text": "Kit -- Finance processed 23 invoices", "detail": "Total: $14,200 -- all within budget", "time": ago_iso(hours=6)},
        {"brand": "wingpoint", "type": "task", "text": "New task: Review analytics dashboard mockups", "detail": "Due in 4 days", "time": ago_iso(hours=7)},
        {"brand": "aav", "type": "system", "text": "Kit -- Research completed patent scan", "detail": "3 new filings in sensor fusion space", "time": ago_iso(hours=8)},
        {"brand": "agentic-trust", "type": "approval", "text": "Social media batch approved (5 posts)", "detail": "LinkedIn and Twitter -- scheduled for this week", "time": ago_iso(hours=10)},
        {"brand": "trustoffice", "type": "system", "text": "Kit -- Legal flagged contract clause", "detail": "Non-compete exceeds standard duration", "time": ago_iso(hours=12)},
        {"brand": "anchorpoint", "type": "task", "text": "Task overdue: Finalize partnership agreement", "detail": "Originally due 6 days ago", "time": ago_iso(hours=14)},
    ]
    for a in activity_data:
        entry = ActivityEntry(**a)
        await db.activity.insert_one(entry.model_dump())

    return {"message": "Database seeded successfully"}

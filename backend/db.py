from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import WebSocket
from typing import List
from datetime import datetime, timezone, timedelta
import os
import json
import logging
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mission_control")

# AgentMail configuration
AGENTMAIL_API_KEY = os.environ.get('AGENTMAIL_API_KEY', '')
AGENTMAIL_BASE_URL = "https://api.agentmail.to/v0"
AGENTMAIL_HEADERS = {
    "Authorization": f"Bearer {AGENTMAIL_API_KEY}",
    "Content-Type": "application/json",
}

# Inbox-brand mapping
INBOX_BRAND_MAP = {
    'agentictrust.app': 'agentic-trust',
    'trustoffice.app': 'trustoffice',
    'truejoybirthing.com': 'true-joy-birthing',
    'agentmail.to': 'all',
}

def resolve_inbox_brand(email):
    domain = email.split('@')[-1] if '@' in email else ''
    return INBOX_BRAND_MAP.get(domain, 'all')

BRAND_SEND_INBOX = {
    'agentic-trust': 'support@agentictrust.app',
    'trustoffice': 'contact@trustoffice.app',
    'true-joy-birthing': 'support@truejoybirthing.com',
}

def get_send_inbox(brand):
    return BRAND_SEND_INBOX.get(brand, 'support@agentictrust.app')


# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, event_type: str, data: dict):
        message = json.dumps({"type": event_type, "data": data})
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

ws_manager = ConnectionManager()


# Helpers
def now_iso():
    return datetime.now(timezone.utc).isoformat()

def ago_iso(minutes=0, hours=0, days=0):
    t = datetime.now(timezone.utc) - timedelta(minutes=minutes, hours=hours, days=days)
    return t.isoformat()

# Sync interval
SYNC_INTERVAL_SECONDS = int(os.environ.get("SYNC_INTERVAL_SECONDS", "120"))

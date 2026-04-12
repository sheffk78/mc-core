from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid


class Brand(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    slug: str
    color: str
    order: int = 0

class Agent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    brand: str
    role: str
    status: str = "idle"
    last_activity: str = ""
    initials: str = ""
    avatar_color: str = "#8a8480"

class ApprovalItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    brand: str
    type: str = "content"
    agent_name: str = ""
    from_address: str = ""
    to_address: str = ""
    inbox: str = ""
    subject: str = ""
    preview: str = ""
    description: str = ""
    agent_note: str = ""
    amount: Optional[float] = None
    expires_at: Optional[str] = None
    created_at: str = ""
    status: str = "pending"
    metadata: Optional[dict] = None

class TaskItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    brand: str
    description: str = ""
    due_date: str = ""
    status: str = "open"
    priority: str = "normal"
    assignee: str = ""
    agent_note: str = ""
    user_note: str = ""
    created_at: str = ""
    completed_at: Optional[str] = None
    metadata: Optional[dict] = None

class TaskCreate(BaseModel):
    title: str
    brand: str
    description: Optional[str] = ""
    due_date: Optional[str] = ""
    priority: Optional[str] = "normal"
    assignee: Optional[str] = ""
    agent_note: Optional[str] = ""
    metadata: Optional[dict] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = None
    assignee: Optional[str] = None
    agent_note: Optional[str] = None
    user_note: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[dict] = None
    append_agent_note: Optional[str] = None

class TaskStatusUpdate(BaseModel):
    status: str

class TaskDeferUpdate(BaseModel):
    due_date: str
    reason: Optional[str] = ""

class TaskRedirectUpdate(BaseModel):
    note: str
    priority: Optional[str] = None

class LabelUpdate(BaseModel):
    add_labels: Optional[List[str]] = []
    remove_labels: Optional[List[str]] = []

class CalendarFeedCreate(BaseModel):
    name: str
    url: str
    color: Optional[str] = "#c85a2a"

class ApprovalDraftUpdate(BaseModel):
    to_address: Optional[str] = None
    subject: Optional[str] = None
    preview: Optional[str] = None
    status: Optional[str] = None

class ComposeEmail(BaseModel):
    inbox_id: str
    to: List[str]
    subject: str
    text: str
    html: Optional[str] = None

class ReplyEmail(BaseModel):
    text: str
    html: Optional[str] = None

class EmailTemplate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    subject: str = ""
    body: str = ""
    created_at: str = ""

class EmailTemplateCreate(BaseModel):
    name: str
    subject: str = ""
    body: str = ""

class ScheduleItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    brand: str
    name: str
    description: str = ""
    cron: str = ""
    agent_name: str = "Kit"
    status: str = "active"
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    created_at: str = ""
    metadata: Optional[dict] = None

class ScheduleCreate(BaseModel):
    brand: str
    name: str
    description: str = ""
    cron: str = ""
    agent_name: str = "Kit"

class ScheduleEdit(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cron: Optional[str] = None

class EditApproveBody(BaseModel):
    subject: Optional[str] = None
    to_address: Optional[str] = None
    body: Optional[str] = None

class UserProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    role: str = "human"
    email: str = ""
    avatar_color: str = "#c85a2a"
    active: bool = True
    created_at: str = ""

class UserCreate(BaseModel):
    name: str
    role: str = "human"
    email: str = ""
    avatar_color: str = "#c85a2a"

class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    avatar_color: Optional[str] = None
    active: Optional[bool] = None

class BrandCreate(BaseModel):
    name: str
    slug: str
    color: str = "#8a8480"

class BrandUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    active: Optional[bool] = None

class InboxItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    agent_name: str = ""
    brand: str
    pending_count: int = 0
    last_activity: str = ""

class ActivityEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    brand: str
    type: str = "system"
    text: str = ""
    detail: str = ""
    time: str = ""

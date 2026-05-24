from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from datetime import datetime
from enum import Enum


class SeverityLevel(str, Enum):
    NONE = "None"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class SeverityTrend(str, Enum):
    STABLE = "stable"
    ESCALATING = "escalating"
    DEESCALATING = "de-escalating"


class Message(BaseModel):
    timestamp: datetime
    username: str
    content: str
    is_system: bool = False


class TaggedMessage(BaseModel):
    message: Message
    severity: SeverityLevel = SeverityLevel.NONE
    severity_confidence: float = Field(ge=0, le=100, default=0.0)


class ChatContext(BaseModel):
    room_name: str
    region: str
    online_users: int
    admin_username: Optional[str] = None
    admin_last_active: Optional[datetime] = None
    users_joined: int = 0
    users_left: int = 0
    failed_peacemaker_attempts: int = 0
    ai_was_attacked: bool = False


class Agent1Output(BaseModel):
    severity: SeverityLevel
    confidence: float = Field(ge=0, le=100)
    intervention_needed: bool
    trajectory: Literal["stable", "escalating", "de-escalating"]
    signals_detected: List[str]
    reasoning: str


class AdminAlertDetail(BaseModel):
    severity: Literal["low", "medium", "high"]
    summary: str
    timestamp_range: str
    users_departed: int
    ai_intervened_before: bool
    ai_was_attacked: bool


class Agent2Output(BaseModel):
    chat_message: Optional[str] = None
    admin_alert: Optional[AdminAlertDetail] = None
    reasoning: str


class InterventionMode(str, Enum):
    SUBTLE_REDIRECT = "subtle_redirect"
    ACKNOWLEDGE_REDIRECT = "acknowledge_redirect"
    DIRECT_INTERVENTION = "direct_intervention"


class AdminAlert(BaseModel):
    severity: SeverityLevel
    timestamp: datetime
    summary: str
    users_left: int
    ai_already_intervened: bool
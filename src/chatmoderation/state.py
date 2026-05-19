from typing import List, Optional, Deque
from collections import deque
from datetime import datetime, timedelta

from .models import (
    Message,
    TaggedMessage,
    ChatContext,
    SeverityLevel,
    SeverityTrend,
)
from .config import DEFAULT_CONFIG, INTERVENTION_CONFIG


class StateTracker:
    def __init__(
        self,
        room_name: str = "Unknown Room",
        region: str = "unknown",
        admin_username: Optional[str] = None,
        admin_last_active: Optional[datetime] = None,
        window_size: int = DEFAULT_CONFIG.rolling_window_size,
    ):
        self._messages: deque[TaggedMessage] = deque(maxlen=window_size)
        self._room_name = room_name
        self._region = region
        self._admin_username = admin_username
        self._admin_last_active = admin_last_active

        self._online_users: int = 0
        self._users_joined: int = 0
        self._users_left: int = 0
        self._failed_peacemaker_attempts: int = 0
        self._ai_was_attacked: bool = False
        self._ai_intervened: bool = False

        self._last_intervention_time: Optional[datetime] = None
        self._intervention_count: int = 0
        self._conflict_cycle_start: Optional[datetime] = None
        self._last_alert_time: Optional[datetime] = None
        self._previous_severity_trend: Optional[SeverityTrend] = None

    def add_message(self, message: Message, severity: SeverityLevel = SeverityLevel.NONE, confidence: float = 0.0):
        tagged = TaggedMessage(
            message=message,
            severity=severity,
            severity_confidence=confidence,
        )
        self._messages.append(tagged)

    def update_user_count(self, count: int):
        self._online_users = count

    def record_user_joined(self):
        self._users_joined += 1

    def record_user_left(self):
        self._users_left += 1

    def record_failed_peacemaker(self):
        self._failed_peacemaker_attempts += 1

    def record_ai_attacked(self):
        self._ai_was_attacked = True

    def record_ai_intervention(self):
        self._ai_intervened = True
        self._last_intervention_time = datetime.now()
        self._intervention_count += 1
        if self._conflict_cycle_start is None:
            self._conflict_cycle_start = datetime.now()

    def can_intervene(self, current_severity: SeverityLevel = SeverityLevel.LOW) -> bool:
        cooldown = INTERVENTION_CONFIG.intervention_cooldown_seconds
        max_count = INTERVENTION_CONFIG.max_interventions_per_cycle

        if self._intervention_count >= max_count:
            return False

        if self._last_intervention_time is None:
            if self._intervention_count == 0:
                return current_severity >= SeverityLevel.MEDIUM
            return False

        elapsed = (datetime.now() - self._last_intervention_time).total_seconds()
        if elapsed < cooldown:
            return False

        if self._intervention_count == 1:
            return current_severity == SeverityLevel.HIGH

        return False

    def should_reset_intervention_cycle(self, current_trend: SeverityTrend) -> bool:
        if self._previous_severity_trend in (SeverityTrend.STABLE, SeverityTrend.DEESCALATING):
            if current_trend in (SeverityTrend.STABLE, SeverityTrend.DEESCALATING):
                recent = list(self._messages)[-3:]
                if len(recent) >= 3 and all(s.severity == SeverityLevel.NONE for s in recent):
                    return True
        return False

    def reset_intervention_cycle(self):
        self._intervention_count = 0
        self._conflict_cycle_start = None

    def record_alert_sent(self):
        self._last_alert_time = datetime.now()

    def can_send_alert(self) -> bool:
        cooldown = INTERVENTION_CONFIG.alert_cooldown_seconds
        if self._last_alert_time is None:
            return True
        elapsed = (datetime.now() - self._last_alert_time).total_seconds()
        return elapsed >= cooldown

    def update_previous_trend(self, trend: SeverityTrend):
        self._previous_severity_trend = trend

    def get_chat_context(self) -> ChatContext:
        return ChatContext(
            room_name=self._room_name,
            region=self._region,
            online_users=self._online_users,
            admin_username=self._admin_username,
            admin_last_active=self._admin_last_active,
            users_joined=self._users_joined,
            users_left=self._users_left,
            failed_peacemaker_attempts=self._failed_peacemaker_attempts,
            ai_was_attacked=self._ai_was_attacked,
        )

    def get_rolling_window(self) -> List[TaggedMessage]:
        return list(self._messages)

    def get_severity_trend(self) -> SeverityTrend:
        if len(self._messages) < 3:
            return SeverityTrend.STABLE

        recent = list(self._messages)[-3:]
        severity_values = [self._severity_to_int(s.severity) for s in recent]

        if severity_values[-1] > severity_values[0]:
            return SeverityTrend.ESCALATING
        elif severity_values[-1] < severity_values[0]:
            return SeverityTrend.DEESCALATING
        else:
            return SeverityTrend.STABLE

    @staticmethod
    def _severity_to_int(severity: SeverityLevel) -> int:
        mapping = {
            SeverityLevel.NONE: 0,
            SeverityLevel.LOW: 1,
            SeverityLevel.MEDIUM: 2,
            SeverityLevel.HIGH: 3,
        }
        return mapping.get(severity, 0)

    def get_last_message(self) -> Optional[TaggedMessage]:
        if self._messages:
            return self._messages[-1]
        return None

    @property
    def ai_has_intervened(self) -> bool:
        return self._ai_intervened

    @property
    def ai_was_attacked(self) -> bool:
        return self._ai_was_attacked

    @property
    def users_left_count(self) -> int:
        return self._users_left

    @property
    def intervention_count(self) -> int:
        return self._intervention_count

    @property
    def last_intervention_time(self) -> Optional[datetime]:
        return self._last_intervention_time

    def get_recent_severities(self) -> List[SeverityLevel]:
        return [tagged.severity for tagged in self._messages]

    def reset(self):
        self._messages.clear()
        self._users_joined = 0
        self._users_left = 0
        self._failed_peacemaker_attempts = 0
        self._ai_was_attacked = False
        self._ai_intervened = False
        self._last_intervention_time = None
        self._intervention_count = 0
        self._conflict_cycle_start = None
        self._last_alert_time = None
        self._previous_severity_trend = None
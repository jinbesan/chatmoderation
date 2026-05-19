from typing import Optional, List
from datetime import datetime
import re

from .models import (
    Message,
    Agent1Output,
    Agent2Output,
    SeverityLevel,
    SeverityTrend,
)
from .state import StateTracker
from .agent1_classifier import ConflictClassifier
from .agent2_intervention import InterventionWriter
from .llm import LLMClient
from .config import DEFAULT_CONFIG


class ConflictMediator:
    def __init__(
        self,
        llm_client: LLMClient,
        room_name: str = "Voice Chat Room",
        region: str = "unknown",
        admin_username: Optional[str] = None,
        admin_last_active: Optional[datetime] = None,
        confidence_threshold: float = DEFAULT_CONFIG.confidence_threshold,
        window_size: int = DEFAULT_CONFIG.rolling_window_size,
    ):
        self.llm_client = llm_client
        self.confidence_threshold = confidence_threshold

        self.state = StateTracker(
            room_name=room_name,
            region=region,
            admin_username=admin_username,
            admin_last_active=admin_last_active,
            window_size=window_size,
        )

        self.classifier = ConflictClassifier(llm_client)
        self.intervention_writer = InterventionWriter(llm_client)

    def process_message(self, raw_message: str, timestamp: Optional[datetime] = None) -> Optional[Agent2Output]:
        if timestamp is None:
            timestamp = datetime.now()

        message = self._parse_message(raw_message, timestamp)

        if message.is_system:
            self._handle_system_event(raw_message)
            return None

        chat_context = self.state.get_chat_context()
        rolling_window = self.state.get_rolling_window()
        severity_trend = self.state.get_severity_trend()

        agent1_output = self.classifier.classify(
            message=message,
            chat_context=chat_context,
            rolling_window=rolling_window,
            severity_trend=severity_trend,
        )

        self.state.add_message(
            message=message,
            severity=agent1_output.severity,
            confidence=agent1_output.confidence,
        )

        current_trend = self.state.get_severity_trend()
        self.state.update_previous_trend(current_trend)

        if self.state.should_reset_intervention_cycle(current_trend):
            self.state.reset_intervention_cycle()

        if agent1_output.intervention_needed and agent1_output.confidence >= self.confidence_threshold:
            if not self.state.can_intervene(agent1_output.severity):
                return None

            severity_trend_str = current_trend.value

            agent2_output = self.intervention_writer.write(
                chat_context=chat_context,
                rolling_window=rolling_window,
                agent1_output=agent1_output,
                ai_was_attacked=self.state.ai_was_attacked,
                severity_trend=severity_trend_str,
            )

            if agent2_output.chat_message:
                self.state.record_ai_intervention()

            if agent2_output.admin_alert:
                self._send_admin_alert(agent2_output.admin_alert)

            if not agent2_output.chat_message and agent1_output.severity >= SeverityLevel.MEDIUM:
                if self.state.can_send_alert():
                    self.state.record_alert_sent()
                    self._send_admin_alert(
                        f"[AUTO-ALERT] Severity: {agent1_output.severity.value} | Trend: {severity_trend_str} | Users Left: {chat_context.users_left}"
                    )

            return agent2_output

        if agent1_output.severity >= SeverityLevel.MEDIUM and agent1_output.confidence >= self.confidence_threshold:
            if self.state.can_send_alert():
                self.state.record_alert_sent()
                self._send_admin_alert(
                    f"[AUTO-ALERT] Severity: {agent1_output.severity.value} | Confidence: {agent1_output.confidence}% | Trend: {current_trend.value} | Users Left: {chat_context.users_left}"
                )

        return None

    def _parse_message(self, raw: str, timestamp: datetime) -> Message:
        system_join_pattern = r"\*\* (.+?) (joined|left) the room \*\*"
        match = re.match(system_join_pattern, raw)
        if match:
            username = match.group(1)
            action = match.group(2)
            if action == "joined":
                return Message(
                    timestamp=timestamp,
                    username=username,
                    content=f"{username} joined",
                    is_system=True,
                )
            else:
                return Message(
                    timestamp=timestamp,
                    username=username,
                    content=f"{username} left",
                    is_system=True,
                )

        chat_pattern = r"\[(\d{2}:\d{2}:\d{2})\] (.+?): (.+)"
        match = re.match(chat_pattern, raw)
        if match:
            time_str = match.group(1)
            username = match.group(2)
            content = match.group(3)

            try:
                msg_time = datetime.strptime(time_str, "%H:%M:%S")
                msg_time = timestamp.replace(
                    hour=msg_time.hour,
                    minute=msg_time.minute,
                    second=msg_time.second,
                )
            except ValueError:
                msg_time = timestamp

            return Message(
                timestamp=msg_time,
                username=username,
                content=content,
                is_system=False,
            )

        return Message(
            timestamp=timestamp,
            username="Unknown",
            content=raw,
            is_system=False,
        )

    def _handle_system_event(self, raw: str):
        if "joined" in raw:
            self.state.record_user_joined()
            self.state.update_user_count(self.state.get_chat_context().online_users + 1)
        elif "left" in raw:
            self.state.record_user_left()
            self.state.update_user_count(max(0, self.state.get_chat_context().online_users - 1))

    def _send_admin_alert(self, message: str):
        print(f"ADMIN ALERT: {message}")

    def get_status(self) -> dict:
        return {
            "room": self.state.get_chat_context().room_name,
            "online_users": self.state.get_chat_context().online_users,
            "users_left": self.state.users_left_count,
            "ai_intervened": self.state.ai_has_intervened,
            "intervention_count": self.state.intervention_count,
            "last_intervention": self.state.last_intervention_time.isoformat() if self.state.last_intervention_time else None,
            "severity_trend": self.state.get_severity_trend().value,
            "recent_severities": [s.value for s in self.state.get_recent_severities()],
        }


def create_mediator(
    api_key: str,
    model: str = "nvidia/nemotron-3-super-120b-a12b:free",
    **kwargs,
) -> ConflictMediator:
    client = LLMClient(api_key=api_key, model=model)
    return ConflictMediator(llm_client=client, **kwargs)
from typing import List, Optional
from datetime import datetime

from .models import (
    Message,
    TaggedMessage,
    ChatContext,
    Agent1Output,
    Agent2Output,
    SeverityLevel,
    AdminAlert,
    InterventionMode,
)
from .llm import LLMClient
from .config import INTERVENTION_CONFIG


AGENT2_SYSTEM_PROMPT = """You are an AI intervention writer for a voice chat room. Your job is to defuse tensions and cool down conflicts WITHOUT sounding like a robot or making things worse.

## Behavioral Modes by Severity

### Low (Subtle Redirect)
- Make a casual comment that shifts topic naturally
- Don't acknowledge the conflict directly
- Keep it brief, casual, not preachy
- Be creative - change the subject in unexpected ways

### Medium (Acknowledge + Redirect)
- Briefly acknowledge there's some tension without naming names
- Offer a gentle redirect to a new topic
- Be warm but not lecturing
- Give an easy exit to save face

### High (Direct but Not Preachy)
- Be clear that the behavior is not okay without being harsh
- Don't lecture or be moralistic
- Direct but not aggressive
- Be brief and decisive

## Critical Rules

1. **Match the chat's register**: If users are using casual/slang language, match that tone
2. **Never sound like a bot**: Avoid formal language, corporate speak, or robotic phrases
3. **VARY YOUR APPROACH**: Don't repeat similar phrasing. Be creative with how you redirect - use jokes, questions, casual observations, topic changes. NOT every response should end with "change the subject" or similar.
4. **Don't make it worse**: Don't call people out by name aggressively
5. **Provide face-saving exits**: Let people step back without losing dignity
6. **If the AI was already attacked**: Do NOT generate a chat message - only generate admin alert

## Output Format

Return JSON with:
- mode: "subtle_redirect" | "acknowledge_redirect" | "direct_intervention"
- message: the intervention message (null if AI was attacked)
- admin_alert: structured admin alert (only if AI was attacked or severity is High)
- reasoning: brief explanation of your approach
"""


def build_intervention_prompt(
    chat_context: ChatContext,
    rolling_window: List[TaggedMessage],
    agent1_output: Agent1Output,
    ai_was_attacked: bool,
    severity_trend: str,
) -> str:
    context_lines = [
        "## CHAT CONTEXT",
        f"Room: {chat_context.room_name}",
        f"Region: {chat_context.region}",
        f"Online Users: {chat_context.online_users}",
        f"Users Left: {chat_context.users_left}",
        f"Admin: {chat_context.admin_username or 'None'}",
        "",
    ]

    window_lines = ["## RECENT MESSAGES"]
    for tagged in rolling_window[-8:]:
        line = f"[{tagged.message.timestamp.strftime('%H:%M:%S')}] {tagged.message.username}: {tagged.message.content}"
        window_lines.append(line)

    severity_info = [
        "",
        "## AGENT 1 ANALYSIS",
        f"Severity: {agent1_output.severity.value}",
        f"Confidence: {agent1_output.confidence}%",
        f"Intervention Needed: {agent1_output.intervention_needed}",
        f"Severity Trend: {severity_trend}",
        f"AI Was Previously Attacked: {ai_was_attacked}",
    ]

    prompt = "\n".join(context_lines + window_lines + severity_info)
    prompt += "\n\nGenerate the appropriate intervention message."

    return prompt


def generate_intervention_with_llm(
    llm_client: LLMClient,
    chat_context: ChatContext,
    rolling_window: List[TaggedMessage],
    agent1_output: Agent1Output,
    ai_was_attacked: bool,
    severity_trend: str,
) -> dict:
    user_prompt = build_intervention_prompt(
        chat_context, rolling_window, agent1_output, ai_was_attacked, severity_trend
    )

    response = llm_client.chat_json(
        system_prompt=AGENT2_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.5,
    )

    return response


def create_admin_alert(
    severity: SeverityLevel,
    timestamp: datetime,
    summary: str,
    users_left: int,
    ai_already_intervened: bool,
) -> AdminAlert:
    return AdminAlert(
        severity=severity,
        timestamp=timestamp,
        summary=summary,
        users_left=users_left,
        ai_already_intervened=ai_already_intervened,
    )


def generate_intervention(
    llm_client: LLMClient,
    chat_context: ChatContext,
    rolling_window: List[TaggedMessage],
    agent1_output: Agent1Output,
    ai_was_attacked: bool,
    severity_trend: str,
) -> Agent2Output:
    if ai_was_attacked:
        admin_alert = create_admin_alert(
            severity=agent1_output.severity,
            timestamp=datetime.now(),
            summary=f"Severity {agent1_output.severity.value} conflict - AI intervention rejected by users",
            users_left=chat_context.users_left,
            ai_already_intervened=True,
        )

        return Agent2Output(
            chat_message=None,
            admin_alert=f"[ALERT] Severity: {admin_alert.severity.value} | Time: {admin_alert.timestamp.strftime('%H:%M:%S')} | Summary: {admin_alert.summary} | Left: {admin_alert.users_left} | AI Intervened: Yes",
            severity=agent1_output.severity,
            timestamp=admin_alert.timestamp,
            summary=admin_alert.summary,
            users_left_count=chat_context.users_left,
            ai_intervened_before=True,
        )

    llm_response = generate_intervention_with_llm(
        llm_client=llm_client,
        chat_context=chat_context,
        rolling_window=rolling_window,
        agent1_output=agent1_output,
        ai_was_attacked=ai_was_attacked,
        severity_trend=severity_trend,
    )

    chat_message = llm_response.get("message")
    admin_alert = None

    if agent1_output.severity == SeverityLevel.HIGH:
        summary = f"High severity conflict in {chat_context.room_name}. Users attacking each other personally, {chat_context.users_left} users left."
        admin_alert = create_admin_alert(
            severity=SeverityLevel.HIGH,
            timestamp=datetime.now(),
            summary=summary,
            users_left=chat_context.users_left,
            ai_already_intervened=False,
        )

    return Agent2Output(
        chat_message=chat_message,
        admin_alert=f"[ALERT] Severity: {admin_alert.severity.value} | Time: {admin_alert.timestamp.strftime('%H:%M:%S')} | Summary: {admin_alert.summary} | Left: {admin_alert.users_left} | AI Intervened: No" if admin_alert else None,
        severity=agent1_output.severity,
        timestamp=datetime.now(),
        summary=summary if agent1_output.severity == SeverityLevel.HIGH else None,
        users_left_count=chat_context.users_left,
        ai_intervened_before=False,
    )


class InterventionWriter:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def write(
        self,
        chat_context: ChatContext,
        rolling_window: List[TaggedMessage],
        agent1_output: Agent1Output,
        ai_was_attacked: bool,
        severity_trend: str,
    ) -> Agent2Output:
        return generate_intervention(
            llm_client=self.llm_client,
            chat_context=chat_context,
            rolling_window=rolling_window,
            agent1_output=agent1_output,
            ai_was_attacked=ai_was_attacked,
            severity_trend=severity_trend,
        )
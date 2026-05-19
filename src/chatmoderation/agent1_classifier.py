import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from .models import (
    Message,
    TaggedMessage,
    ChatContext,
    Agent1Output,
    SeverityLevel,
    SeverityTrend,
)
from .llm import LLMClient
from .config import DEFAULT_CONFIG, DEFAULT_BLACKLIST


AGENT1_SYSTEM_PROMPT = """You are a conflict detection classifier for a voice chat room. Your job is to analyze chat messages and determine if the conversation has crossed from healthy debate into hostile territory.

## Severity Levels

- **None**: Normal conversation, friendly banter, no conflict
- **Low**: Minor tension, hints of disagreement, but no personal attacks
- **Medium**: Clear personal attacks, escalating hostility, or targeted insults
- **High**: Severe hostility, threats, harassment, or multiple people leaving due to conflict

## Contextual Signals to Watch

1. **Topic Shift**: Conflict moving from attacking content (e.g., "that drama is trash") to attacking the person (e.g., "you're dumb")
2. **Pronoun Shift**: Changes from "that show is bad" to "you have bad taste" to "you're stupid"
3. **Reciprocity Check**: Both users playfully trading banter = OK. One-sided attacks = concerning
4. **Failed Peacemaker**: Someone tried to calm things down and was shut down
5. **User Departures**: People leaving the room during conflict is a strong signal
6. **Emoji Reactions**: 😬😬 signals discomfort from bystanders
7. **Speed of Escalation**: Rapid back-and-back with increasing hostility

## Blacklist Consideration

The message may contain blacklisted words. Take this into account when evaluating severity - the presence of blacklisted words should ADD to the severity score, not automatically override it.

## Decision Logic

- Start with None, escalate based on signals
- A single harsh word can elevate to Medium/High
- Multiple signals compound (e.g., topic shift + emoji + leaving users = High)
- If severity is Low or above AND confidence >= 70%, recommend intervention

## Output Format

Return JSON with:
- severity: "None" | "Low" | "Medium" | "High"
- confidence: 0-100 (how confident you are in this classification)
- intervention_needed: true | false
- reasoning: brief explanation of your decision (1-2 sentences)
"""


def count_blacklisted_words(content: str, blacklist: set) -> int:
    content_lower = content.lower()
    count = 0
    for word in blacklist:
        if word in content_lower:
            count += 1
    return count


def build_user_prompt(
    message: Message,
    chat_context: ChatContext,
    rolling_window: List[TaggedMessage],
    severity_trend: SeverityTrend,
    blacklist: set = DEFAULT_BLACKLIST,
) -> str:
    blacklist_count = count_blacklisted_words(message.content, blacklist)

    context_lines = [
        "## CHAT CONTEXT",
        f"Room: {chat_context.room_name}",
        f"Region: {chat_context.region}",
        f"Online Users: {chat_context.online_users}",
        f"Admin: {chat_context.admin_username or 'None'}",
        f"Admin Last Active: {chat_context.admin_last_active or 'N/A'}",
        f"Users Joined: {chat_context.users_joined}",
        f"Users Left: {chat_context.users_left}",
        f"Failed Peacemaker Attempts: {chat_context.failed_peacemaker_attempts}",
        f"AI Was Previously Attacked: {chat_context.ai_was_attacked}",
        f"Severity Trend: {severity_trend.value}",
        "",
    ]

    window_lines = ["## RECENT MESSAGES (most recent last)"]
    for tagged in rolling_window:
        sev_tag = f"[{tagged.severity.value}]" if tagged.severity != SeverityLevel.NONE else ""
        line = f"[{tagged.message.timestamp.strftime('%H:%M:%S')}] {tagged.message.username}: {tagged.message.content} {sev_tag}"
        window_lines.append(line)

    prompt = "\n".join(context_lines + window_lines)
    prompt += "\n\nAnalyze the LAST message in the window. Determine its severity level and whether intervention is needed."

    if blacklist_count > 0:
        prompt += f"\n\nNOTE: The last message contains {blacklist_count} blacklisted word(s). Factor this into your severity score."

    return prompt


def classify_with_llm(
    message: Message,
    llm_client: LLMClient,
    chat_context: ChatContext,
    rolling_window: List[TaggedMessage],
    severity_trend: SeverityTrend,
    blacklist: set = DEFAULT_BLACKLIST,
) -> Agent1Output:
    user_prompt = build_user_prompt(message, chat_context, rolling_window, severity_trend, blacklist)

    response = llm_client.chat_json(
        system_prompt=AGENT1_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.2,
    )

    severity_str = response.get("severity", "None")
    try:
        severity = SeverityLevel(severity_str)
    except ValueError:
        severity = SeverityLevel.NONE

    confidence = float(response.get("confidence", 0))
    intervention_needed = bool(response.get("intervention_needed", False))

    return Agent1Output(
        severity=severity,
        confidence=confidence,
        intervention_needed=intervention_needed,
    )


def check_blacklist_override(
    content: str,
    blacklist: set = DEFAULT_BLACKLIST,
) -> bool:
    content_lower = content.lower()
    for word in blacklist:
        if word in content_lower:
            return True
    return False


def classify_message(
    message: Message,
    chat_context: ChatContext,
    rolling_window: List[TaggedMessage],
    severity_trend: SeverityTrend,
    llm_client: Optional[LLMClient] = None,
    blacklist: set = DEFAULT_BLACKLIST,
) -> Agent1Output:
    if llm_client is None:
        raise ValueError("LLM client is required for classification")

    return classify_with_llm(
        message=message,
        llm_client=llm_client,
        chat_context=chat_context,
        rolling_window=rolling_window,
        severity_trend=severity_trend,
        blacklist=blacklist,
    )


class ConflictClassifier:
    def __init__(
        self,
        llm_client: LLMClient,
        blacklist: set = DEFAULT_BLACKLIST,
    ):
        self.llm_client = llm_client
        self.blacklist = blacklist

    def classify(
        self,
        message: Message,
        chat_context: ChatContext,
        rolling_window: List[TaggedMessage],
        severity_trend: SeverityTrend,
    ) -> Agent1Output:
        return classify_message(
            message=message,
            chat_context=chat_context,
            rolling_window=rolling_window,
            severity_trend=severity_trend,
            llm_client=self.llm_client,
            blacklist=self.blacklist,
        )
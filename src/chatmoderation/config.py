import json
import os
from typing import Set
from pydantic import BaseModel


def load_blacklist_from_json(filepath: str = None) -> Set[str]:
    if filepath is None:
        filepath = os.path.join(os.path.dirname(__file__), "words.json")

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            words = json.load(f)
            return set(w.lower() for w in words)
    except FileNotFoundError:
        return set()


class ModerationConfig(BaseModel):
    rolling_window_size: int = 10
    confidence_threshold: float = 80.0
    blacklist: Set[str] = set()

    class Config:
        arbitrary_types_allowed = True


DEFAULT_BLACKLIST = load_blacklist_from_json()

DEFAULT_CONFIG = ModerationConfig(
    rolling_window_size=10,
    confidence_threshold=80.0,
    blacklist=DEFAULT_BLACKLIST,
)


class InterventionConfig(BaseModel):
    low_severity_mode: str = "subtle_redirect"
    medium_severity_mode: str = "acknowledge_redirect"
    high_severity_mode: str = "direct_intervention"
    max_intervention_length: int = 200
    intervention_cooldown_seconds: int = 120
    max_interventions_per_cycle: int = 2
    alert_cooldown_seconds: int = 300


INTERVENTION_CONFIG = InterventionConfig()
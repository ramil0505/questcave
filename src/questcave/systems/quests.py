"""Quest definitions and tracking.

Quests live in data/quests.json. Each one specifies which challenge type to
launch and what data to feed it. See data/quests.json for the schema.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .. import config


@dataclass
class QuestReward:
    xp: int = 0
    gems: int = 0
    badge_id: Optional[str] = None


@dataclass
class Quest:
    quest_id: str
    title: str
    re_topic: str
    description: str
    challenge_type: str           # name registered in challenges/registry.py
    challenge_data: Dict[str, Any]
    reward: QuestReward


def load_quests() -> List[Quest]:
    path: Path = config.DATA_DIR / "quests.json"
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        Quest(
            quest_id=q["quest_id"],
            title=q["title"],
            re_topic=q.get("re_topic", "General RE"),
            description=q.get("description", ""),
            challenge_type=q["challenge_type"],
            challenge_data=q.get("challenge_data", {}),
            reward=QuestReward(**q.get("reward", {})),
        )
        for q in raw
    ]


def find_quest(quest_id: str) -> Optional[Quest]:
    for q in load_quests():
        if q.quest_id == quest_id:
            return q
    return None

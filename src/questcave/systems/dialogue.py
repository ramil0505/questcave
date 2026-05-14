"""NPC dialogue loaded from data/dialogue.json.

Each dialogue key maps to a list of lines. The DialogueBox UI walks through
them one at a time when the player clicks or presses space.
"""
from __future__ import annotations

import json
from typing import Dict, List

from .. import config


def load_dialogue() -> Dict[str, List[str]]:
    path = config.DATA_DIR / "dialogue.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def get_dialogue(key: str) -> List[str]:
    data = load_dialogue()
    return data.get(key, [f"... ({key} dialogue missing)"])

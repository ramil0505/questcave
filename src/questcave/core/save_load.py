"""JSON-based save/load.

Save schema (saves/savegame.json):
{
  "version": 1,
  "player": {
      "name": str, "explorer_class": str,
      "level": int, "xp": int, "gems": int,
      "cave_depth": int,
      "completed_quests": [str, ...],
      "earned_badges": [str, ...]
  }
}
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from ..config import SAVE_FILE

SAVE_VERSION = 1


def save_game(player_state: Dict[str, Any]) -> None:
    """Persist current player state."""
    data = {"version": SAVE_VERSION, "player": player_state}
    SAVE_FILE.write_text(json.dumps(data, indent=2))


def load_game() -> Optional[Dict[str, Any]]:
    """Return the saved player state, or None if no save exists / is invalid."""
    if not SAVE_FILE.exists():
        return None
    try:
        data = json.loads(SAVE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    if data.get("version") != SAVE_VERSION:
        # Future: write migration code per version bump.
        return None
    return data.get("player")


def delete_save() -> None:
    if SAVE_FILE.exists():
        SAVE_FILE.unlink()

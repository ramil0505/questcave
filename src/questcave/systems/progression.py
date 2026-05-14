"""XP, levels, gems and knowledge badges.

A single ProgressionSystem instance lives on Game and is referenced by any
scene that needs to query or modify player progress (HUD, challenges, save).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional

from .. import config


@dataclass
class KnowledgeBadge:
    """Awarded for mastering an RE topic."""
    badge_id: str
    title: str
    description: str


@dataclass
class ProgressionSystem:
    level: int = 1
    xp: int = 0
    gems: int = 0
    cave_depth: int = 1
    completed_quests: List[str] = field(default_factory=list)
    earned_badges: List[KnowledgeBadge] = field(default_factory=list)

    # ---- XP / level math ----------------------------------------------------
    @staticmethod
    def xp_required_for_level(level: int) -> int:
        """How much XP is needed to go from `level` to `level + 1`."""
        return int(config.XP_PER_LEVEL_BASE *
                   (config.XP_PER_LEVEL_GROWTH ** (level - 1)))

    @property
    def xp_to_next_level(self) -> int:
        return self.xp_required_for_level(self.level)

    @property
    def xp_progress_fraction(self) -> float:
        return min(1.0, self.xp / max(1, self.xp_to_next_level))

    # ---- rewards ------------------------------------------------------------
    def grant_xp(self, base_xp: int, explorer_class: str = "Sage") -> int:
        """Add XP, respecting class bonuses. Returns how many levels gained."""
        bonus = config.EXPLORER_CLASSES.get(explorer_class, {}).get("xp_bonus", 1.0)
        gained = int(base_xp * bonus)
        self.xp += gained
        levels_gained = 0
        while self.xp >= self.xp_to_next_level:
            self.xp -= self.xp_to_next_level
            self.level += 1
            levels_gained += 1
        return levels_gained

    def grant_gems(self, amount: int) -> None:
        self.gems = max(0, self.gems + amount)

    def grant_badge(self, badge: KnowledgeBadge) -> bool:
        """Award a badge if not already earned. Returns True if new."""
        if any(b.badge_id == badge.badge_id for b in self.earned_badges):
            return False
        self.earned_badges.append(badge)
        return True

    def complete_quest(self, quest_id: str) -> bool:
        if quest_id in self.completed_quests:
            return False
        self.completed_quests.append(quest_id)
        return True

    def descend(self, levels: int = 1) -> None:
        self.cave_depth += levels

    # ---- serialisation ------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "xp": self.xp,
            "gems": self.gems,
            "cave_depth": self.cave_depth,
            "completed_quests": list(self.completed_quests),
            "earned_badges": [
                {"badge_id": b.badge_id, "title": b.title,
                 "description": b.description}
                for b in self.earned_badges
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProgressionSystem":
        return cls(
            level=data.get("level", 1),
            xp=data.get("xp", 0),
            gems=data.get("gems", 0),
            cave_depth=data.get("cave_depth", 1),
            completed_quests=list(data.get("completed_quests", [])),
            earned_badges=[KnowledgeBadge(**b)
                           for b in data.get("earned_badges", [])],
        )

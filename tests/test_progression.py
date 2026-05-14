"""Basic tests for the progression system. Run with: pytest tests/"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from questcave.systems.progression import ProgressionSystem, KnowledgeBadge


def test_grant_xp_levels_up():
    p = ProgressionSystem()
    levels_gained = p.grant_xp(100, explorer_class="Warrior")  # no bonus
    assert levels_gained == 1
    assert p.level == 2
    assert p.xp == 0


def test_grant_xp_partial():
    p = ProgressionSystem()
    p.grant_xp(50, explorer_class="Warrior")  # no bonus
    assert p.level == 1
    assert p.xp == 50


def test_explorer_xp_bonus():
    p = ProgressionSystem()
    p.grant_xp(100, explorer_class="Sage")  # 10% bonus -> 110 XP
    assert p.level == 2
    assert p.xp == 10


def test_complete_quest_idempotent():
    p = ProgressionSystem()
    assert p.complete_quest("Q1") is True
    assert p.complete_quest("Q1") is False
    assert p.completed_quests == ["Q1"]


def test_grant_badge_idempotent():
    p = ProgressionSystem()
    badge = KnowledgeBadge("B1", "Test", "desc")
    assert p.grant_badge(badge) is True
    assert p.grant_badge(badge) is False
    assert len(p.earned_badges) == 1


def test_round_trip_serialisation():
    p = ProgressionSystem(level=5, xp=42, gems=100, cave_depth=3,
                          completed_quests=["A", "B"])
    p.grant_badge(KnowledgeBadge("BX", "X", "x"))
    d = p.to_dict()
    p2 = ProgressionSystem.from_dict(d)
    assert p2.level == 5
    assert p2.xp == 42
    assert p2.gems == 100
    assert p2.cave_depth == 3
    assert p2.completed_quests == ["A", "B"]
    assert len(p2.earned_badges) == 1
    assert p2.earned_badges[0].badge_id == "BX"

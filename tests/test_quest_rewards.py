"""Regression tests for the quest-finish reward grant.

Bug v0.2.0: clicking during the reward overlay called _finish_success
multiple times, which called _on_quest_finish multiple times, which
granted XP / gems / cave depth on every call. A 30-second click-spam
could push a player to level 20+ and depth 2000+.

Fix: ChallengeScene._finish_success / _give_up early-out if already
called; CaveExploreScene._on_quest_finish early-outs if the quest is
already in completed_quests.
"""
import os
import sys
from pathlib import Path

# Run pygame headless
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pygame
pygame.init()
pygame.display.set_mode((1280, 720))

from questcave.core.game import Game
from questcave.scenes.cave_explore import CaveExploreScene
from questcave.scenes.challenge_scene import ChallengeScene
from questcave.systems.quests import load_quests


def _setup():
    g = Game()
    g.scene_manager.replace(CaveExploreScene(g, None, "Sage"))
    explore = g.scene_manager.current
    quest = load_quests()[0]
    ch = ChallengeScene(g, quest, explore.progression, "Sage",
                        return_scene=explore,
                        on_finish=explore._on_quest_finish)
    g.scene_manager.push(ch)
    return g, explore, ch, quest


def test_on_quest_finish_is_idempotent_per_quest():
    """Calling _on_quest_finish twice for the same quest only rewards once."""
    g, explore, ch, quest = _setup()
    explore._on_quest_finish(quest, True)
    xp_after_first = explore.progression.xp
    gems_after_first = explore.progression.gems
    depth_after_first = explore.progression.cave_depth

    # 50 more calls should change nothing.
    for _ in range(50):
        explore._on_quest_finish(quest, True)

    assert explore.progression.xp == xp_after_first
    assert explore.progression.gems == gems_after_first
    assert explore.progression.cave_depth == depth_after_first


def test_finish_success_is_idempotent():
    """Calling _finish_success many times only triggers on_finish once."""
    g, explore, ch, quest = _setup()
    ch.challenge.completed = True
    ch._begin_reward_animation()
    start_depth = explore.progression.cave_depth

    for _ in range(100):
        ch._finish_success()

    # Should have advanced depth by exactly 1, not 100.
    assert explore.progression.cave_depth == start_depth + 1
    assert explore.progression.gems == quest.reward.gems


def test_give_up_then_finish_success_does_nothing():
    """If you've already given up, finishing later shouldn't grant rewards."""
    g, explore, ch, quest = _setup()
    start_depth = explore.progression.cave_depth
    ch._give_up()
    ch._finish_success()
    assert explore.progression.cave_depth == start_depth
    assert explore.progression.xp == 0
    assert quest.quest_id not in explore.progression.completed_quests

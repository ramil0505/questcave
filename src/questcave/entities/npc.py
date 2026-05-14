"""NPCs the player can talk to.

Each NPC has a position, an interaction radius, and a dialogue tree key
that maps into data/dialogue.json. Subclass for special behaviour.
"""
from __future__ import annotations

import pygame
from typing import Optional, Callable

from .. import config


class NPC(pygame.sprite.Sprite):
    def __init__(self, name: str, pos: tuple,
                 colour: tuple = config.GOLD,
                 dialogue_key: str = "default",
                 size: int = 36) -> None:
        super().__init__()
        self.name = name
        self.dialogue_key = dialogue_key
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self._render(colour, size)
        self.rect = self.image.get_rect(center=pos)
        self.colour = colour
        # Hook for behaviour beyond plain dialogue
        self.on_interact: Optional[Callable[["NPC"], None]] = None

    def _render(self, colour: tuple, size: int) -> None:
        self.image.fill((0, 0, 0, 0))
        # Soft glow halo
        pygame.draw.circle(self.image, (*colour, 60),
                           (size // 2, size // 2), size // 2)
        # Body
        pygame.draw.circle(self.image, colour,
                           (size // 2, size // 2), size // 2 - 4)
        # Inner highlight
        pygame.draw.circle(self.image, (255, 255, 255),
                           (size // 2 - 4, size // 2 - 4), 3)

    def distance_to(self, point: tuple) -> float:
        dx = self.rect.centerx - point[0]
        dy = self.rect.centery - point[1]
        return (dx * dx + dy * dy) ** 0.5

    def is_within_interact_range(self, point: tuple) -> bool:
        return self.distance_to(point) <= config.PLAYER_INTERACT_RADIUS


class CaveGuardian(NPC):
    """The mentor NPC. Hands out quests."""

    def __init__(self, pos: tuple) -> None:
        super().__init__(name="Cave Guardian",
                         pos=pos,
                         colour=config.GOLD,
                         dialogue_key="guardian_intro",
                         size=44)

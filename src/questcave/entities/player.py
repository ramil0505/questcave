"""The player character.

Rendered as a coloured rounded square with a small directional indicator —
swap to a sprite by setting self.image inside __init__.
"""
from __future__ import annotations

import pygame
from typing import Tuple

from .. import config


class Player(pygame.sprite.Sprite):
    def __init__(self, name: str = "Adventurer",
                 explorer_class: str = "Sage",
                 pos: Tuple[int, int] = (config.WINDOW_WIDTH // 2,
                                         config.WINDOW_HEIGHT // 2)) -> None:
        super().__init__()
        self.name = name
        self.explorer_class = explorer_class
        klass = config.EXPLORER_CLASSES.get(explorer_class,
                                            config.EXPLORER_CLASSES["Sage"])
        self.colour = klass["colour"]

        # Visual
        self.image = pygame.Surface((config.PLAYER_SIZE, config.PLAYER_SIZE),
                                    pygame.SRCALPHA)
        self._render_sprite()
        self.rect = self.image.get_rect(center=pos)
        self.facing = pygame.Vector2(0, 1)        # facing down by default
        self.position = pygame.Vector2(self.rect.center)

    def _render_sprite(self) -> None:
        """Draw the placeholder body. Replace with sprite load later."""
        self.image.fill((0, 0, 0, 0))
        # Outline
        pygame.draw.rect(self.image, (15, 15, 15),
                         self.image.get_rect(), border_radius=8)
        # Body
        pygame.draw.rect(self.image, self.colour,
                         self.image.get_rect().inflate(-4, -4),
                         border_radius=6)
        # Eye spot to suggest facing
        eye_centre = (config.PLAYER_SIZE - 10, config.PLAYER_SIZE // 2)
        pygame.draw.circle(self.image, (255, 255, 255), eye_centre, 3)

    # --- movement ---------------------------------------------------------
    def handle_input(self, dt: float, keys: pygame.key.ScancodeWrapper) -> None:
        direction = pygame.Vector2(0, 0)
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            direction.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            direction.x += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            direction.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            direction.y += 1
        if direction.length_squared() > 0:
            direction = direction.normalize()
            self.facing = direction
        self.position += direction * config.PLAYER_SPEED * dt

    def update_after_collision(self) -> None:
        self.rect.center = (int(self.position.x), int(self.position.y))

    def clamp_to_bounds(self, bounds: pygame.Rect) -> None:
        self.rect.clamp_ip(bounds)
        self.position.update(self.rect.center)

    # --- stats container --------------------------------------------------
    def to_dict(self) -> dict:
        return {"name": self.name, "explorer_class": self.explorer_class}

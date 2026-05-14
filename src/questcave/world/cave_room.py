"""A single explorable cave room — modernised look.

Features:
- Gradient floor that darkens with depth
- Animated flickering torches (positions are stable; the glow flickers)
- Cracked-stone-look tile shading
- Vignette at the edges for atmosphere
- Optional ambient dust particle emission point
"""
from __future__ import annotations

import math
import random
import pygame
from typing import List, Tuple

from .. import config


class CaveRoom:
    def __init__(self, name: str, depth: int = 1) -> None:
        self.name = name
        self.depth = depth
        self.bounds = pygame.Rect(0, 80, config.WINDOW_WIDTH,
                                  config.WINDOW_HEIGHT - 80)
        # We'll allow the room to grow with the window
        self._tiles_cache_size = None
        self._floor_tiles: List[Tuple[pygame.Rect, Tuple[int, int, int]]] = []
        self.torch_positions: List[Tuple[int, int]] = []
        self._regen_decor()

    # ---- decoration generation -----------------------------------------
    def _regen_decor(self) -> None:
        rng = random.Random(self.depth * 9973 + 17)
        # Base floor colour shifts subtly as we go deeper (cooler/darker)
        depth_shift = min(15, self.depth * 1)
        base = (max(0, config.CAVE_FLOOR[0] - depth_shift),
                max(0, config.CAVE_FLOOR[1] - depth_shift),
                max(0, config.CAVE_FLOOR[2] - depth_shift // 2))
        self._floor_tiles.clear()
        cols = self.bounds.width // config.TILE_SIZE + 1
        rows = self.bounds.height // config.TILE_SIZE + 1
        for r in range(rows):
            for c in range(cols):
                rect = pygame.Rect(
                    self.bounds.left + c * config.TILE_SIZE,
                    self.bounds.top + r * config.TILE_SIZE,
                    config.TILE_SIZE, config.TILE_SIZE,
                )
                shade = rng.randint(-10, 10)
                colour = (max(0, min(255, base[0] + shade)),
                          max(0, min(255, base[1] + shade)),
                          max(0, min(255, base[2] + shade)))
                self._floor_tiles.append((rect, colour))

        # Torches around the perimeter
        self.torch_positions.clear()
        n_torches = 5
        for i in range(n_torches):
            x = self.bounds.left + 80 + i * ((self.bounds.width - 160) // (n_torches - 1))
            self.torch_positions.append((x, self.bounds.top + 24))
        for i in range(n_torches):
            x = self.bounds.left + 80 + i * ((self.bounds.width - 160) // (n_torches - 1))
            self.torch_positions.append((x, self.bounds.bottom - 24))

    def set_bounds(self, rect: pygame.Rect) -> None:
        self.bounds = rect
        self._regen_decor()

    # ---- per-frame ------------------------------------------------------
    def draw(self, surface: pygame.Surface, time_t: float = 0.0) -> None:
        # Background wall colour
        surface.fill(config.CAVE_WALL_DARK)

        # Floor with rounded inset
        floor_rect = self.bounds.inflate(-24, -24)
        pygame.draw.rect(surface, config.CAVE_DARKER, floor_rect,
                         border_radius=14)

        # Tiles within the floor
        for rect, colour in self._floor_tiles:
            if floor_rect.colliderect(rect):
                clip = rect.clip(floor_rect)
                pygame.draw.rect(surface, colour, clip)
                # Subtle grout line
                pygame.draw.rect(surface, (0, 0, 0, 35), clip, width=1)

        # Floor highlight (top edge)
        pygame.draw.line(surface, (80, 100, 116),
                         (floor_rect.left + 6, floor_rect.top + 1),
                         (floor_rect.right - 6, floor_rect.top + 1), 1)

        # Torches
        for tx, ty in self.torch_positions:
            self._draw_torch(surface, tx, ty, time_t)

        # Vignette (radial darkening at edges) - drawn last
        self._draw_vignette(surface, floor_rect)

        # Depth marker, bottom-right - more polished
        self._draw_depth_marker(surface)

    def _draw_torch(self, surface, x, y, time_t) -> None:
        flicker = math.sin(time_t * 12 + x * 0.13)
        radius = 70 + int(8 * flicker)
        # Layered glow
        for r, a in [(radius, 18), (int(radius * 0.65), 35),
                     (int(radius * 0.35), 70)]:
            glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*config.GOLD, a), (r, r), r)
            surface.blit(glow, (x - r, y - r))
        # Bracket
        pygame.draw.rect(surface, (30, 22, 14),
                         (x - 3, y + 4, 6, 14), border_radius=2)
        # Flame
        h = 14 + int(3 * flicker)
        pygame.draw.polygon(surface, (255, 220, 90),
                            [(x, y - h), (x - 5, y - 1), (x + 5, y - 1)])
        pygame.draw.polygon(surface, (255, 250, 180),
                            [(x, y - h + 5), (x - 3, y - 1), (x + 3, y - 1)])

    def _draw_vignette(self, surface, rect) -> None:
        # Soft darkening at the edges of the room
        vig = pygame.Surface(rect.size, pygame.SRCALPHA)
        for i in range(8):
            alpha = 8 - i
            if alpha < 1:
                continue
            inset = i * 6
            r = pygame.Rect(inset, inset,
                            rect.width - 2 * inset, rect.height - 2 * inset)
            pygame.draw.rect(vig, (0, 0, 0, alpha), r, width=6,
                             border_radius=12)
        surface.blit(vig, rect.topleft)

    def _draw_depth_marker(self, surface) -> None:
        font = pygame.font.Font(None, 20)
        font_small = pygame.font.Font(None, 14)
        # Pill backing
        label = font.render(f"-{self.depth * 12} m", True, config.WHITE)
        sub = font_small.render("DEPTH", True, config.GOLD_BRIGHT)
        pad_x, pad_y = 16, 8
        pill_w = max(label.get_width(), sub.get_width()) + pad_x * 2
        pill_h = label.get_height() + sub.get_height() + pad_y * 2 + 2
        pill = pygame.Rect(0, 0, pill_w, pill_h)
        pill.bottomright = (surface.get_width() - 18,
                            surface.get_height() - 18)
        pygame.draw.rect(surface, (10, 16, 22), pill, border_radius=10)
        pygame.draw.rect(surface, config.GOLD_DEEP, pill, width=1,
                         border_radius=10)
        surface.blit(sub, (pill.centerx - sub.get_width() // 2,
                           pill.y + pad_y))
        surface.blit(label, (pill.centerx - label.get_width() // 2,
                             pill.y + pad_y + sub.get_height() + 2))

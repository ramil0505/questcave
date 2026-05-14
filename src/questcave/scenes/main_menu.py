"""Modern main menu.

Background: parallax cave silhouettes, slow drifting dust motes, animated torches.
Title: pulses with a soft teal glow.
Buttons: hover-scale with glow underneath.
"""
from __future__ import annotations

import math
import pygame
from typing import List

from .. import config
from ..core.scene import Scene
from ..core.save_load import load_game
from ..ui.button import Button
from ..ui.draw import draw_glow, draw_vertical_gradient, render_text_with_shadow
from ..utils.particles import ParticleSystem


class MainMenuScene(Scene):
    def __init__(self, game) -> None:
        super().__init__(game)
        self.t = 0.0
        self.particles = ParticleSystem()
        self.font_title = pygame.font.Font(None, config.FONT_TITLE_SIZE + 30)
        self.font_sub = pygame.font.Font(None, 26)
        self.font_foot = pygame.font.Font(None, 16)
        self._build_layout()

    def _build_layout(self) -> None:
        w = self.game.width
        h = self.game.height
        cx = w // 2
        button_w, button_h = 320, 60
        gap = 16
        start_y = int(h * 0.58)

        save_exists = load_game() is not None
        entries = [("New Game", self._new_game, "primary")]
        if save_exists:
            entries.append(("Continue Adventure", self._continue, "ghost"))
        entries.append(("Stats & Badges", self._stats, "ghost"))
        entries.append(("Quit", self._quit, "subtle"))

        self.buttons: List[Button] = []
        for i, (label, cb, style) in enumerate(entries):
            rect = pygame.Rect(cx - button_w // 2,
                               start_y + i * (button_h + gap),
                               button_w, button_h)
            bg = (config.TEAL if style == "primary"
                  else config.LIGHT_GRAY if style == "ghost"
                  else config.GRAY)
            self.buttons.append(Button(rect, label, cb, bg=bg, style=style,
                                       font_size=24))

    def on_resize(self, w, h) -> None:
        self._build_layout()

    # ---- callbacks ------------------------------------------------------
    def _new_game(self) -> None:
        from .character_select import CharacterSelectScene
        self.switch_to(CharacterSelectScene(self.game))

    def _continue(self) -> None:
        saved = load_game()
        if saved is None:
            self._new_game()
            return
        from .cave_explore import CaveExploreScene
        self.switch_to(CaveExploreScene(self.game, saved))

    def _stats(self) -> None:
        from .stats_view import StatsViewScene
        self.switch_to(StatsViewScene(self.game))

    def _quit(self) -> None:
        self.quit()

    # ---- scene API ------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._quit()
        for b in self.buttons:
            b.handle_event(event)

    def update(self, dt: float) -> None:
        self.t += dt
        mp = pygame.mouse.get_pos()
        for b in self.buttons:
            b.update(dt, mp)
        # Spawn drifting dust in the whole window
        area = pygame.Rect(0, 0, self.game.width, self.game.height)
        if len(self.particles.particles) < 60:
            self.particles.spawn_ambient_dust(area, count=1,
                                              colour=(200, 220, 220))
        # Torch embers from 4 fixed positions
        if int(self.t * 30) % 4 == 0:
            for tx, ty in self._torch_positions():
                self.particles.spawn_torch_ember((tx, ty + 6))
        self.particles.update(dt)

    def _torch_positions(self) -> list:
        w, h = self.game.width, self.game.height
        return [(160, 200), (w - 160, 200),
                (160, h - 180), (w - 160, h - 180)]

    def draw(self, surface: pygame.Surface) -> None:
        w, h = surface.get_size()
        # Vertical gradient background
        draw_vertical_gradient(surface, surface.get_rect(),
                               config.CAVE_DARKER, config.CAVE_DARK)

        # Decorative diagonal "cave depth" silhouettes (parallax-ish)
        for i, ratio in enumerate([0.85, 0.7, 0.55]):
            offset = 14 * math.sin(self.t * 0.3 + i)
            colour_shade = 6 - i * 2
            self._draw_silhouette(surface, ratio, offset, colour_shade)

        # Torches
        for tx, ty in self._torch_positions():
            self._draw_torch(surface, tx, ty)

        # Particles between bg and foreground
        self.particles.draw(surface)

        # Title with pulsing glow
        pulse = 0.5 + 0.5 * math.sin(self.t * 1.4)
        glow_radius = int(180 + 25 * pulse)
        draw_glow(surface, (w // 2, int(h * 0.28)), glow_radius,
                  config.TEAL, max_alpha=int(60 + 25 * pulse), layers=4)

        title = render_text_with_shadow(self.font_title, "QuestCave",
                                        config.WHITE, (0, 0, 0), (2, 4))
        surface.blit(title, (w // 2 - title.get_width() // 2,
                             int(h * 0.18)))

        sub = self.font_sub.render(
            "A serious RPG for learning Requirements Engineering",
            True, config.LIGHT_GRAY)
        surface.blit(sub, (w // 2 - sub.get_width() // 2, int(h * 0.36)))

        # Decorative divider
        pygame.draw.line(surface, config.TEAL_DARK,
                         (w // 2 - 140, int(h * 0.45)),
                         (w // 2 + 140, int(h * 0.45)), 2)
        # Centre diamond on the line
        cx_d, cy_d = w // 2, int(h * 0.45)
        pygame.draw.polygon(surface, config.TEAL,
                            [(cx_d, cy_d - 6), (cx_d + 6, cy_d),
                             (cx_d, cy_d + 6), (cx_d - 6, cy_d)])

        # Buttons
        for b in self.buttons:
            b.draw(surface)

        # Footer
        foot = self.font_foot.render(
            "v0.2.0  ·  Riga Technical University  ·  Press ESC to quit",
            True, config.GRAY)
        surface.blit(foot, (w // 2 - foot.get_width() // 2, h - 30))

    def _draw_silhouette(self, surface, ratio, offset, shade) -> None:
        w, h = surface.get_size()
        floor_y = int(h * ratio)
        peaks = [
            (-40 + offset, h),
            (-40 + offset, floor_y + 40),
            (w * 0.15 + offset, floor_y),
            (w * 0.28 + offset, floor_y + 30),
            (w * 0.42 + offset, floor_y - 10),
            (w * 0.55 + offset, floor_y + 20),
            (w * 0.68 + offset, floor_y - 6),
            (w * 0.82 + offset, floor_y + 12),
            (w + 40 + offset, floor_y + 40),
            (w + 40, h),
        ]
        colour = (max(0, config.CAVE_WALL[0] - shade),
                  max(0, config.CAVE_WALL[1] - shade),
                  max(0, config.CAVE_WALL[2] - shade))
        pygame.draw.polygon(surface, colour, peaks)

    def _draw_torch(self, surface, x, y) -> None:
        # Flame glow
        flicker = math.sin(self.t * 12 + x)
        glow_r = 50 + int(8 * flicker)
        draw_glow(surface, (x, y), glow_r, config.GOLD,
                  max_alpha=55, layers=4)
        # Bracket
        bracket_rect = pygame.Rect(x - 4, y + 6, 8, 22)
        pygame.draw.rect(surface, (40, 30, 20), bracket_rect, border_radius=3)
        # Flame
        flame_h = 18 + int(4 * flicker)
        flame_pts = [(x, y - flame_h), (x - 6, y - 4), (x + 6, y - 4)]
        pygame.draw.polygon(surface, config.GOLD_BRIGHT, flame_pts)
        flame_pts2 = [(x, y - flame_h + 6), (x - 4, y - 4), (x + 4, y - 4)]
        pygame.draw.polygon(surface, (255, 220, 130), flame_pts2)

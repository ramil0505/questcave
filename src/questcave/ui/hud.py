"""Modern in-game HUD.

Top strip with gradient. Animated XP bar that smoothly chases the target
value. Big level-up callout pops in via Tween + ease_out_back. Optional
right-side mini-quest tracker.
"""
from __future__ import annotations

import math
import pygame

from .. import config
from ..systems.progression import ProgressionSystem
from .draw import draw_vertical_gradient, draw_pill, draw_glow


class HUD:
    """Top strip showing level / xp / gems / depth / badges."""

    def __init__(self, progression: ProgressionSystem) -> None:
        self.progression = progression
        self.font_label = pygame.font.Font(None, 16)
        self.font_value = pygame.font.Font(None, 24)
        self.font_big = pygame.font.Font(None, 48)

        # Animated values
        self._xp_displayed = float(progression.xp)
        self._level_displayed = progression.level
        self._levelup_t = 0.0
        self._xp_gain_flash_t = 0.0
        # Track last value so we can detect external changes
        self._last_xp = progression.xp
        self._last_level = progression.level

    # ---- update -----------------------------------------------------------
    def update(self, dt: float) -> None:
        # Detect XP gain (could have come from a level-up too)
        if self.progression.xp != self._last_xp or self.progression.level != self._last_level:
            self._xp_gain_flash_t = 0.6
            if self.progression.level > self._last_level:
                self._levelup_t = 1.6
            self._last_xp = self.progression.xp
            self._last_level = self.progression.level

        # Smoothly chase XP value for the bar
        target = float(self.progression.xp)
        # If we levelled up, we want the bar to wrap; for simplicity snap on level change
        if self._level_displayed != self.progression.level:
            self._level_displayed = self.progression.level
            self._xp_displayed = target
        diff = target - self._xp_displayed
        self._xp_displayed += diff * min(1.0, dt * 4)

        if self._levelup_t > 0:
            self._levelup_t = max(0.0, self._levelup_t - dt)
        if self._xp_gain_flash_t > 0:
            self._xp_gain_flash_t = max(0.0, self._xp_gain_flash_t - dt)

    # ---- draw -------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        w = surface.get_width()
        strip = pygame.Rect(0, 0, w, 64)
        draw_vertical_gradient(surface, strip,
                               config.COLOR_HUD_BG_TOP, config.COLOR_HUD_BG)
        pygame.draw.line(surface, config.TEAL_DARK,
                         (0, strip.bottom), (w, strip.bottom), 2)

        # --- Level pill --------------------------------------------------
        x = 20
        pill = pygame.Rect(x, 14, 78, 36)
        draw_pill(surface, pill, config.GOLD_DEEP,
                  border_colour=config.GOLD, border_width=1)
        lv_label = self.font_label.render("LEVEL", True, (40, 30, 8))
        surface.blit(lv_label, (pill.x + 10, pill.y + 4))
        lv_value = self.font_value.render(
            str(self.progression.level), True, config.WHITE)
        surface.blit(lv_value, (pill.right - lv_value.get_width() - 12,
                                pill.y + 8))

        # --- XP bar -----------------------------------------------------
        x = pill.right + 16
        bar_w, bar_h = 240, 16
        bar_y = 24
        bar_bg = pygame.Rect(x, bar_y + 6, bar_w, bar_h)
        pygame.draw.rect(surface, (30, 40, 48), bar_bg, border_radius=8)
        # Fill
        frac = (self._xp_displayed
                / max(1, self.progression.xp_to_next_level))
        frac = max(0.0, min(1.0, frac))
        fill_w = int(bar_w * frac)
        if fill_w > 0:
            fill_rect = pygame.Rect(x, bar_y + 6, fill_w, bar_h)
            draw_vertical_gradient(surface, fill_rect,
                                   config.TEAL_BRIGHT, config.TEAL_DARK)
            # Inner highlight
            pygame.draw.line(surface, (255, 255, 255, 80),
                             (fill_rect.x + 2, fill_rect.y + 1),
                             (fill_rect.right - 2, fill_rect.y + 1), 1)
        pygame.draw.rect(surface, (60, 80, 92), bar_bg, width=1,
                         border_radius=8)
        # XP gain flash
        if self._xp_gain_flash_t > 0:
            alpha = int(120 * (self._xp_gain_flash_t / 0.6))
            flash = pygame.Surface(bar_bg.size, pygame.SRCALPHA)
            pygame.draw.rect(flash, (255, 255, 255, alpha),
                             flash.get_rect(), border_radius=8)
            surface.blit(flash, bar_bg.topleft)

        xp_label = self.font_label.render(
            f"{int(self._xp_displayed)} / {self.progression.xp_to_next_level} XP",
            True, config.LIGHT_GRAY)
        surface.blit(xp_label, (x, bar_y - 8))

        # --- Gems --------------------------------------------------------
        x = bar_bg.right + 24
        self._draw_stat_chip(surface, (x, 14),
                             icon_colour=config.PURPLE,
                             label="GEMS",
                             value=str(self.progression.gems))

        # --- Depth -------------------------------------------------------
        x += 130
        self._draw_stat_chip(surface, (x, 14),
                             icon_colour=config.TEAL,
                             label="DEPTH",
                             value=str(self.progression.cave_depth))

        # --- Badges ------------------------------------------------------
        x += 130
        self._draw_stat_chip(surface, (x, 14),
                             icon_colour=config.CORAL,
                             label="BADGES",
                             value=str(len(self.progression.earned_badges)))

        # --- Controls hint, right side ---------------------------------
        hint = self.font_label.render(
            "WASD move    E talk    TAB stats    ESC pause",
            True, config.GRAY)
        surface.blit(hint, (w - hint.get_width() - 16, 24))

        # --- Level-up callout ------------------------------------------
        if self._levelup_t > 0:
            self._draw_levelup(surface)

    def _draw_stat_chip(self, surface, pos, icon_colour, label, value) -> None:
        x, y = pos
        chip = pygame.Rect(x, y, 116, 36)
        pygame.draw.rect(surface, (20, 28, 36), chip, border_radius=8)
        pygame.draw.rect(surface, (45, 55, 65), chip, width=1, border_radius=8)
        # Coloured dot
        pygame.draw.circle(surface, icon_colour, (chip.x + 14, chip.centery), 6)
        # Label/value
        lbl = self.font_label.render(label, True, config.LIGHT_GRAY)
        val = self.font_value.render(value, True, config.WHITE)
        surface.blit(lbl, (chip.x + 28, chip.y + 4))
        surface.blit(val, (chip.x + 28, chip.y + 16))

    def _draw_levelup(self, surface) -> None:
        # ease_out_back-like pop: spend the first 0.4s scaling in,
        # then hold, then fade.
        t = 1.6 - self._levelup_t
        if t < 0.4:
            scale = 0.3 + 0.7 * (t / 0.4)
            alpha = int(220 * (t / 0.4))
        elif t < 1.2:
            scale = 1.0
            alpha = 220
        else:
            frac = max(0.0, (1.6 - t) / 0.4)
            scale = 1.0
            alpha = int(220 * frac)
        scale = max(0.1, min(1.2, scale))

        text = self.font_big.render("LEVEL UP!", True, config.GOLD_BRIGHT)
        scaled = pygame.transform.smoothscale(
            text, (int(text.get_width() * scale),
                   int(text.get_height() * scale)))
        # Apply alpha
        scaled_alpha = pygame.Surface(scaled.get_size(), pygame.SRCALPHA)
        scaled_alpha.blit(scaled, (0, 0))
        scaled_alpha.set_alpha(alpha)
        w = surface.get_width()
        # Glow behind
        cx = w // 2
        cy = 130
        draw_glow(surface, (cx, cy),
                  int(180 * scale), config.GOLD,
                  max_alpha=int(60 * (alpha / 220)), layers=4)
        surface.blit(scaled_alpha,
                     (cx - scaled_alpha.get_width() // 2,
                      cy - scaled_alpha.get_height() // 2))

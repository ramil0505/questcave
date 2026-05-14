"""Modern character select with hover/selection animations.

Each class card lifts on hover and glows brightly when selected.
Bottom strip explains the selected class's perks in detail.
"""
from __future__ import annotations

import math
import pygame
from typing import Dict, List, Optional

from .. import config
from ..core.scene import Scene
from ..ui.button import Button
from ..ui.draw import draw_panel, draw_glow, draw_vertical_gradient, render_text_with_shadow
from ..utils.particles import ParticleSystem


class CharacterSelectScene(Scene):
    def __init__(self, game) -> None:
        super().__init__(game)
        self.selected: Optional[str] = None
        self.t = 0.0
        self.particles = ParticleSystem()

        self.font_title = pygame.font.Font(None, config.FONT_HEADING_SIZE + 12)
        self.font_blurb = pygame.font.Font(None, 18)
        self.font_class = pygame.font.Font(None, 30)
        self.font_icon = pygame.font.Font(None, 52)

        self._hover_t: Dict[str, float] = {c: 0.0 for c in config.EXPLORER_CLASSES}
        self._select_t: Dict[str, float] = {c: 0.0 for c in config.EXPLORER_CLASSES}
        self._build_layout()

    def _build_layout(self) -> None:
        w, h = self.game.width, self.game.height
        classes = list(config.EXPLORER_CLASSES.keys())
        card_w, card_h = 280, 380
        total_w = len(classes) * card_w + (len(classes) - 1) * 32
        start_x = (w - total_w) // 2
        self.card_rects: Dict[str, pygame.Rect] = {}
        for i, c in enumerate(classes):
            self.card_rects[c] = pygame.Rect(start_x + i * (card_w + 32),
                                             170, card_w, card_h)

        self.confirm = Button(
            pygame.Rect(w // 2 - 140, h - 80, 280, 56),
            "Begin Adventure", self._begin,
            bg=config.TEAL, style="primary", font_size=24,
        )
        self.back = Button(
            pygame.Rect(40, h - 80, 140, 56),
            "Back", self._back, style="subtle", font_size=22,
        )

    def on_resize(self, w, h) -> None:
        self._build_layout()

    # ---- callbacks ------------------------------------------------------
    def _begin(self) -> None:
        if self.selected is None:
            return
        from .cave_explore import CaveExploreScene
        self.switch_to(CaveExploreScene(self.game, None, self.selected))

    def _back(self) -> None:
        from .main_menu import MainMenuScene
        self.switch_to(MainMenuScene(self.game))

    # ---- scene API ------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._back()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for name, rect in self.card_rects.items():
                if rect.collidepoint(event.pos):
                    self.selected = name
                    break
        self.confirm.handle_event(event)
        self.back.handle_event(event)

    def update(self, dt: float) -> None:
        self.t += dt
        mp = pygame.mouse.get_pos()
        self.confirm.update(dt, mp)
        self.confirm.disabled = self.selected is None
        self.back.update(dt, mp)

        for name, rect in self.card_rects.items():
            hovered = rect.collidepoint(mp)
            target = 1.0 if hovered else 0.0
            self._hover_t[name] += (target - self._hover_t[name]) * min(1.0, dt * 8)
            sel_target = 1.0 if self.selected == name else 0.0
            self._select_t[name] += (sel_target - self._select_t[name]) * min(1.0, dt * 6)

        # Ambient particles around the selected class card
        if self.selected:
            rect = self.card_rects[self.selected]
            if int(self.t * 12) % 2 == 0:
                klass = config.EXPLORER_CLASSES[self.selected]
                self.particles.spawn_sparkle_burst(
                    (rect.centerx + (self.t * 50 % rect.width - rect.width / 2),
                     rect.bottom - 10),
                    count=1, colour=klass["colour"])
        self.particles.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        w, h = surface.get_size()
        draw_vertical_gradient(surface, surface.get_rect(),
                               config.CAVE_DARKER, config.CAVE_DARK)

        title = render_text_with_shadow(self.font_title,
                                        "Choose your Explorer", config.WHITE)
        surface.blit(title, (w // 2 - title.get_width() // 2, 70))

        hint = pygame.font.Font(None, 20).render(
            "Each class shapes how you learn. Click a card to select.",
            True, config.LIGHT_GRAY)
        surface.blit(hint, (w // 2 - hint.get_width() // 2, 120))

        for name, rect in self.card_rects.items():
            self._draw_class_card(surface, name, rect)

        self.particles.draw(surface)
        self.confirm.draw(surface)
        self.back.draw(surface)

        if self.selected is None:
            note = pygame.font.Font(None, 18).render(
                "Pick an explorer class to continue.", True, config.LIGHT_GRAY)
            surface.blit(note, (w // 2 - note.get_width() // 2, h - 100))

    def _draw_class_card(self, surface, name, base_rect) -> None:
        klass = config.EXPLORER_CLASSES[name]
        h_t = self._hover_t[name]
        s_t = self._select_t[name]

        # Lift on hover
        lift = -int(10 * h_t)
        rect = base_rect.move(0, lift)

        # Glow if selected
        if s_t > 0.05:
            draw_glow(surface, rect.center, int(rect.width * 0.7),
                      klass["colour"], max_alpha=int(80 * s_t), layers=4)

        # Panel
        accent = config.TEAL if s_t < 0.1 else klass["colour"]
        draw_panel(surface, rect,
                   top=(40, 54, 64), bottom=(24, 34, 42),
                   border=accent, border_width=2 + int(2 * s_t), radius=14)

        # Avatar circle with class icon
        avatar_y = rect.y + 80
        pulse = 0.5 + 0.5 * math.sin(self.t * 2 + hash(name))
        ring_r = 56 + int(4 * pulse * s_t)
        pygame.draw.circle(surface, (10, 16, 22),
                           (rect.centerx, avatar_y), ring_r + 6)
        pygame.draw.circle(surface, klass["colour"],
                           (rect.centerx, avatar_y), ring_r)
        pygame.draw.circle(surface, (255, 255, 255, 40),
                           (rect.centerx, avatar_y), ring_r, 2)
        # Icon letter
        icon_surf = self.font_icon.render(klass["icon"], True, config.WHITE)
        surface.blit(icon_surf, (rect.centerx - icon_surf.get_width() // 2,
                                 avatar_y - icon_surf.get_height() // 2))

        # Class name
        label = self.font_class.render(name, True, config.WHITE)
        surface.blit(label,
                     (rect.centerx - label.get_width() // 2, avatar_y + 80))

        # Decorative line
        pygame.draw.line(surface, accent,
                         (rect.x + 30, avatar_y + 130),
                         (rect.right - 30, avatar_y + 130), 1)

        # Blurb
        self._wrap_text(surface, klass["blurb"],
                        rect.inflate(-30, -30), top=avatar_y + 150)

        # Selected pill
        if s_t > 0.5:
            pill_rect = pygame.Rect(0, 0, 110, 26)
            pill_rect.midbottom = (rect.centerx, rect.bottom - 14)
            pygame.draw.rect(surface, klass["colour"], pill_rect,
                             border_radius=13)
            sel_font = pygame.font.Font(None, 18)
            sel_label = sel_font.render("SELECTED", True, (20, 20, 20))
            surface.blit(sel_label, (pill_rect.centerx - sel_label.get_width() // 2,
                                     pill_rect.centery - sel_label.get_height() // 2))

    def _wrap_text(self, surface, text, rect, top) -> None:
        words = text.split(" ")
        lines: List[str] = []
        cur = ""
        for w in words:
            attempt = (cur + " " + w).strip()
            if self.font_blurb.size(attempt)[0] <= rect.width:
                cur = attempt
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        y = top
        for ln in lines:
            ls = self.font_blurb.render(ln, True, config.LIGHT_GRAY)
            surface.blit(ls,
                         (rect.centerx - ls.get_width() // 2, y))
            y += 22

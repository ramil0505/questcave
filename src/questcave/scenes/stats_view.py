"""Stats / badges view.

Shows the player their level, XP, gem count, cave depth, list of earned
badges with descriptions, and completed quests. Loads from save if no
ProgressionSystem is passed in.
"""
from __future__ import annotations

import pygame
from typing import List, Optional

from .. import config
from ..core.scene import Scene
from ..core.save_load import load_game
from ..systems.progression import ProgressionSystem
from ..ui.button import Button
from ..ui.draw import draw_panel, draw_vertical_gradient, draw_pill, render_text_with_shadow


class StatsViewScene(Scene):
    def __init__(self, game,
                 progression: Optional[ProgressionSystem] = None) -> None:
        super().__init__(game)
        if progression is None:
            saved = load_game()
            if saved:
                progression = ProgressionSystem.from_dict(saved)
            else:
                progression = ProgressionSystem()
        self.progression = progression

        self.font_title = pygame.font.Font(None, 44)
        self.font_h = pygame.font.Font(None, 24)
        self.font_b = pygame.font.Font(None, 20)
        self.font_s = pygame.font.Font(None, 16)
        self.font_huge = pygame.font.Font(None, 60)
        self.scroll_y = 0
        self._build_layout()

    def _build_layout(self) -> None:
        w, h = self.game.size
        self.back = Button(
            pygame.Rect(20, h - 70, 130, 48),
            "Back", self._back, style="subtle", font_size=22,
        )

    def on_resize(self, w, h) -> None:
        self._build_layout()

    # ---- callbacks -----------------------------------------------------
    def _back(self) -> None:
        # Pop ourselves
        self.done = True

    # ---- scene API -----------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_ESCAPE, pygame.K_TAB):
            self._back()
        self.back.handle_event(event)
        # Scrollwheel for badges list
        if event.type == pygame.MOUSEWHEEL:
            self.scroll_y = max(0, self.scroll_y - event.y * 30)

    def update(self, dt: float) -> None:
        self.back.update(dt, pygame.mouse.get_pos())

    def draw(self, surface: pygame.Surface) -> None:
        w, h = surface.get_size()
        draw_vertical_gradient(surface, surface.get_rect(),
                               config.CAVE_DARKER, config.CAVE_DARK)

        # Title
        title = render_text_with_shadow(self.font_title, "Stats & Badges",
                                        config.WHITE)
        surface.blit(title, (40, 30))
        sub = self.font_b.render(
            f"Adventurer  ·  {self.progression.level} Levels  ·  "
            f"{len(self.progression.earned_badges)} Badges  ·  "
            f"Cave Depth {self.progression.cave_depth}",
            True, config.LIGHT_GRAY)
        surface.blit(sub, (40, 80))

        # Big stat row
        self._draw_stat_row(surface)

        # Badges section
        badges_y = 280
        h_label = self.font_h.render("Knowledge Badges", True,
                                     config.TEAL_BRIGHT)
        surface.blit(h_label, (40, badges_y))
        # Divider
        pygame.draw.line(surface, config.TEAL_DARK,
                         (40, badges_y + 32), (w - 40, badges_y + 32), 1)

        # Badge grid
        self._draw_badges(surface, top=badges_y + 50)

        # Completed quests, bottom right summary
        cq_y = h - 200
        cq_label = self.font_h.render(
            f"Completed Quests: {len(self.progression.completed_quests)}",
            True, config.GOLD_BRIGHT)
        surface.blit(cq_label, (40, cq_y))
        for i, qid in enumerate(self.progression.completed_quests[:5]):
            txt = self.font_s.render(f"· {qid}", True, config.LIGHT_GRAY)
            surface.blit(txt, (60, cq_y + 30 + i * 20))

        self.back.draw(surface)

    def _draw_stat_row(self, surface) -> None:
        w = surface.get_width()
        stats = [
            ("LEVEL", str(self.progression.level), config.GOLD),
            ("EXPERIENCE",
             f"{self.progression.xp} / {self.progression.xp_to_next_level}",
             config.TEAL),
            ("GEMS", str(self.progression.gems), config.PURPLE),
            ("DEPTH", str(self.progression.cave_depth), config.CORAL),
        ]
        card_w = (w - 80 - 3 * 16) // 4
        for i, (label, value, colour) in enumerate(stats):
            rect = pygame.Rect(40 + i * (card_w + 16), 130, card_w, 130)
            draw_panel(surface, rect,
                       top=(36, 46, 56), bottom=(22, 30, 38),
                       border=colour, border_width=1, radius=12)
            # Tag pill
            pill = pygame.Rect(rect.x + 14, rect.y + 14, 96, 22)
            draw_pill(surface, pill, colour,
                      border_colour=colour, border_width=0)
            lbl = self.font_s.render(label, True, (20, 20, 25))
            surface.blit(lbl,
                         (pill.centerx - lbl.get_width() // 2,
                          pill.centery - lbl.get_height() // 2))
            # Big value
            val = self.font_huge.render(value, True, config.WHITE)
            # Scale down if too wide
            if val.get_width() > rect.width - 20:
                ratio = (rect.width - 20) / val.get_width()
                val = pygame.transform.smoothscale(
                    val, (int(val.get_width() * ratio),
                          int(val.get_height() * ratio)))
            surface.blit(val,
                         (rect.centerx - val.get_width() // 2,
                          rect.y + 50))

    def _draw_badges(self, surface, top) -> None:
        badges = self.progression.earned_badges
        if not badges:
            txt = self.font_b.render(
                "No badges earned yet — complete a quest to earn your first.",
                True, config.GRAY)
            surface.blit(txt, (60, top))
            return
        cols = 3
        card_w, card_h = 360, 100
        gap = 16
        for i, badge in enumerate(badges):
            row, col = i // cols, i % cols
            rect = pygame.Rect(40 + col * (card_w + gap),
                               top + row * (card_h + gap) - self.scroll_y,
                               card_w, card_h)
            if rect.bottom < top or rect.top > surface.get_height() - 100:
                continue
            draw_panel(surface, rect,
                       top=(36, 46, 56), bottom=(22, 30, 38),
                       border=config.GOLD, border_width=1, radius=10)
            # Badge medal (circle with star)
            cx, cy = rect.x + 50, rect.y + rect.height // 2
            pygame.draw.circle(surface, config.GOLD_DEEP, (cx, cy), 32)
            pygame.draw.circle(surface, config.GOLD, (cx, cy), 28)
            pygame.draw.circle(surface, config.GOLD_BRIGHT, (cx, cy), 24, 2)
            # Star
            self._draw_star(surface, (cx, cy), 12, config.WHITE)
            # Title and desc
            title = self.font_b.render(badge.title, True, config.WHITE)
            surface.blit(title, (rect.x + 96, rect.y + 22))
            desc = self.font_s.render(badge.description, True, config.LIGHT_GRAY)
            surface.blit(desc, (rect.x + 96, rect.y + 50))
            bid = self.font_s.render(badge.badge_id, True, config.GRAY)
            surface.blit(bid, (rect.x + 96, rect.y + 70))

    def _draw_star(self, surface, centre, radius, colour) -> None:
        import math
        pts = []
        for i in range(10):
            angle = -math.pi / 2 + i * math.pi / 5
            r = radius if i % 2 == 0 else radius * 0.45
            pts.append((centre[0] + math.cos(angle) * r,
                        centre[1] + math.sin(angle) * r))
        pygame.draw.polygon(surface, colour, pts)

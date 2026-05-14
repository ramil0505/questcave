"""Card-Matching Challenge with modern animations.

Improvements vs v0.1:
- Cards lift visibly when grabbed (shadow, scale-up)
- Wrong drop: red flash + bounce-back via easing
- Correct drop: green flash + sparkle burst + locked card glow
- Subtle drag hint pulse on first card (fixing usability finding)
- Slots have a soft inner shadow when empty, gold glow when correct match lands
"""
from __future__ import annotations

import math
import random
import pygame
from typing import Any, Dict, List, Optional, Tuple

from .. import config
from .base import BaseChallenge
from ..utils.easing import ease_out_back, ease_out_cubic
from ..utils.tween import Tween, TweenGroup
from ..utils.particles import ParticleSystem
from ..ui.draw import draw_panel, draw_glow, draw_vertical_gradient


class _Card:
    """A draggable requirement card."""

    def __init__(self, text: str, home_pos: Tuple[int, int],
                 pair_id: int) -> None:
        self.text = text
        self.pair_id = pair_id
        self.rect = pygame.Rect(home_pos[0], home_pos[1],
                                config.CARD_WIDTH, config.CARD_HEIGHT)
        self.home_pos = home_pos
        self.dragging = False
        self.drag_offset = (0, 0)
        self.locked = False
        self.flash_t = 0.0
        self.flash_colour: Tuple[int, int, int] = config.TEAL
        # If snapping home after wrong drop, animate via these
        self.snap_back_x: Optional[Tween] = None
        self.snap_back_y: Optional[Tween] = None

    def begin_drag(self, mouse_pos):
        self.dragging = True
        self.drag_offset = (self.rect.x - mouse_pos[0],
                            self.rect.y - mouse_pos[1])
        # Cancel any in-flight snap-back
        self.snap_back_x = None
        self.snap_back_y = None

    def drag_to(self, mouse_pos):
        self.rect.x = mouse_pos[0] + self.drag_offset[0]
        self.rect.y = mouse_pos[1] + self.drag_offset[1]

    def end_drag(self):
        self.dragging = False

    def update(self, dt):
        if self.flash_t > 0:
            self.flash_t = max(0.0, self.flash_t - dt)
        if self.snap_back_x is not None:
            self.snap_back_x.update(dt)
            self.snap_back_y.update(dt)
            self.rect.x = int(self.snap_back_x.value)
            self.rect.y = int(self.snap_back_y.value)
            if self.snap_back_x.done and self.snap_back_y.done:
                self.snap_back_x = None
                self.snap_back_y = None


class _Slot:
    def __init__(self, text: str, pos: Tuple[int, int], pair_id: int) -> None:
        self.text = text
        self.pair_id = pair_id
        self.rect = pygame.Rect(pos[0], pos[1],
                                config.CARD_WIDTH, config.CARD_HEIGHT)
        self.filled = False
        self.flash_t = 0.0


class CardMatchingChallenge(BaseChallenge):
    NAME = "card_matching"

    def __init__(self, data: Dict[str, Any]) -> None:
        super().__init__(data)
        self._title = data.get("title", "Match the Requirements")
        self._prompt = data.get(
            "prompt", "Drag each requirement onto the matching solution.")

        pairs: List[Dict[str, str]] = data.get("pairs", [])
        if not pairs:
            pairs = [
                {"requirement": "The system shall respond within 2 seconds.",
                 "solution": "Performance (non-functional)",
                 "explanation": "Response time is a quality attribute."},
                {"requirement": "Users can log in via email and password.",
                 "solution": "Functional",
                 "explanation": "A behaviour the system must provide."},
            ]
        self.pair_explanations = {i: p.get("explanation", "")
                                  for i, p in enumerate(pairs)}
        self.n_pairs = len(pairs)

        self._layout_cards(pairs)
        self.held: Optional[_Card] = None
        self.tweens = TweenGroup()
        self.particles = ParticleSystem()
        self.t = 0.0
        self._hint_used = False

        self.font_title = pygame.font.Font(None, config.FONT_HEADING_SIZE)
        self.font_prompt = pygame.font.Font(None, 22)
        self.font_card = pygame.font.Font(None, 19)
        self.font_feedback = pygame.font.Font(None, 22)
        self.font_label = pygame.font.Font(None, 18)

    def _layout_cards(self, pairs):
        rng = random.Random()
        req_indices = list(range(len(pairs)))
        rng.shuffle(req_indices)
        sol_indices = list(range(len(pairs)))
        rng.shuffle(sol_indices)

        top = 230
        col_left = 90
        col_right = config.WINDOW_WIDTH - 90 - config.CARD_WIDTH

        self.cards: List[_Card] = []
        for visual_row, idx in enumerate(req_indices):
            y = top + visual_row * (config.CARD_HEIGHT + config.CARD_MARGIN)
            self.cards.append(_Card(
                text=pairs[idx]["requirement"],
                home_pos=(col_left, y),
                pair_id=idx,
            ))

        self.slots: List[_Slot] = []
        for visual_row, idx in enumerate(sol_indices):
            y = top + visual_row * (config.CARD_HEIGHT + config.CARD_MARGIN)
            self.slots.append(_Slot(
                text=pairs[idx]["solution"],
                pos=(col_right, y),
                pair_id=idx,
            ))

    # ---- BaseChallenge ---------------------------------------------------
    def title(self) -> str:
        return self._title

    def prompt(self) -> str:
        return self._prompt

    # ---- input -----------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if self.completed:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for card in reversed(self.cards):
                if card.locked:
                    continue
                if card.rect.collidepoint(mx, my):
                    card.begin_drag((mx, my))
                    self.held = card
                    self._hint_used = True   # they've grabbed at least once
                    break

        elif event.type == pygame.MOUSEMOTION and self.held is not None:
            self.held.drag_to(event.pos)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.held is not None:
                self._drop_held()

    def _drop_held(self) -> None:
        assert self.held is not None
        card = self.held
        card.end_drag()
        self.held = None
        self.attempts += 1

        for slot in self.slots:
            if slot.filled:
                continue
            if card.rect.colliderect(slot.rect):
                if slot.pair_id == card.pair_id:
                    # Correct: snap exactly onto slot
                    card.rect.topleft = slot.rect.topleft
                    card.locked = True
                    slot.filled = True
                    card.flash_t = 0.6
                    card.flash_colour = config.GREEN
                    slot.flash_t = 0.6
                    expl = self.pair_explanations.get(card.pair_id, "")
                    self.feedback_text = f"Correct! {expl}"
                    # Sparkle burst at slot
                    self.particles.spawn_sparkle_burst(slot.rect.center,
                                                       count=20)
                    self._check_completion()
                    return
                else:
                    # Wrong: bounce back home
                    card.flash_t = 0.45
                    card.flash_colour = config.RED
                    self._snap_back(card)
                    self.feedback_text = "Not quite. Try a different pairing."
                    return
        # No slot - just snap home
        self._snap_back(card)

    def _snap_back(self, card: _Card) -> None:
        sx, sy = card.rect.topleft
        ex, ey = card.home_pos
        card.snap_back_x = Tween(sx, ex, duration=0.4, ease=ease_out_back)
        card.snap_back_y = Tween(sy, ey, duration=0.4, ease=ease_out_back)

    def _check_completion(self) -> None:
        if all(c.locked for c in self.cards):
            self.completed = True
            self.feedback_text = "All matched! Quest complete."

    # ---- per-frame -------------------------------------------------------
    def update(self, dt: float) -> None:
        self.t += dt
        for card in self.cards:
            card.update(dt)
        for slot in self.slots:
            if slot.flash_t > 0:
                slot.flash_t = max(0.0, slot.flash_t - dt)
        self.tweens.update(dt)
        self.particles.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        # Header card
        header_rect = pygame.Rect(40, 70, surface.get_width() - 80, 130)
        draw_panel(surface, header_rect,
                   top=(28, 42, 52), bottom=(20, 30, 38),
                   border=config.TEAL_DARK, border_width=1, radius=12)
        title = self.font_title.render(self._title, True, config.WHITE)
        surface.blit(title, (header_rect.x + 24, header_rect.y + 20))
        prompt = self.font_prompt.render(self._prompt, True, config.LIGHT_GRAY)
        surface.blit(prompt, (header_rect.x + 24, header_rect.y + 60))

        # Progress pill, top-right of header
        matched = sum(1 for c in self.cards if c.locked)
        prog_text = f"{matched} / {self.n_pairs}"
        prog_font = pygame.font.Font(None, 28)
        prog_surf = prog_font.render(prog_text, True, config.GOLD)
        prog_pill = pygame.Rect(0, 0,
                                prog_surf.get_width() + 36,
                                40)
        prog_pill.topright = (header_rect.right - 16, header_rect.y + 16)
        pygame.draw.rect(surface, (12, 18, 24), prog_pill, border_radius=20)
        pygame.draw.rect(surface, config.GOLD_DEEP, prog_pill, width=1,
                         border_radius=20)
        surface.blit(prog_surf,
                     (prog_pill.centerx - prog_surf.get_width() // 2,
                      prog_pill.centery - prog_surf.get_height() // 2))
        # Sub label
        plabel = self.font_label.render("MATCHED", True, config.LIGHT_GRAY)
        surface.blit(plabel, (prog_pill.x - plabel.get_width() - 10,
                              prog_pill.centery - plabel.get_height() // 2))

        # Column labels
        col_label_font = pygame.font.Font(None, 20)
        req_label = col_label_font.render("REQUIREMENT CARDS",
                                          True, config.TEAL_BRIGHT)
        sol_label = col_label_font.render("SOLUTION SLOTS",
                                          True, config.GOLD_BRIGHT)
        surface.blit(req_label, (90, 205))
        surface.blit(sol_label,
                     (surface.get_width() - 90 - config.CARD_WIDTH, 205))

        # Slots
        for slot in self.slots:
            self._draw_slot(surface, slot)
        # Cards (held drawn last)
        held = self.held
        for card in self.cards:
            if card is not held:
                self._draw_card(surface, card)
        if held is not None:
            self._draw_card(surface, held, lifted=True)

        # First-time drag hint (pulsing arrow next to first unlocked card)
        if not self._hint_used:
            first = next((c for c in self.cards if not c.locked), None)
            if first is not None:
                pulse = 0.5 + 0.5 * math.sin(self.t * 4)
                hint_x = first.rect.right + 12 + int(8 * pulse)
                hint_y = first.rect.centery
                pygame.draw.polygon(surface, config.GOLD,
                                    [(hint_x, hint_y - 8),
                                     (hint_x + 14, hint_y),
                                     (hint_x, hint_y + 8)])
                hint_text = pygame.font.Font(None, 18).render(
                    "drag", True, config.GOLD_BRIGHT)
                surface.blit(hint_text, (hint_x + 18, hint_y - 8))

        # Particles
        self.particles.draw(surface)

        # Feedback strip
        if self.feedback_text:
            is_good = ("Correct" in self.feedback_text
                       or "complete" in self.feedback_text)
            colour = config.GREEN_BRIGHT if is_good else config.CORAL
            fb_rect = pygame.Rect(40, surface.get_height() - 90,
                                  surface.get_width() - 80, 50)
            pygame.draw.rect(surface, (16, 22, 28), fb_rect, border_radius=10)
            pygame.draw.rect(surface, colour, fb_rect, width=2,
                             border_radius=10)
            fb_surf = self.font_feedback.render(self.feedback_text, True,
                                                colour)
            surface.blit(fb_surf,
                         (fb_rect.x + 20,
                          fb_rect.centery - fb_surf.get_height() // 2))

        # Attempt count
        att = self.font_label.render(f"Attempts: {self.attempts}",
                                     True, config.LIGHT_GRAY)
        surface.blit(att, (40, surface.get_height() - 28))

    # ---- visuals --------------------------------------------------------
    def _draw_card(self, surface, card: _Card, lifted: bool = False) -> None:
        rect = card.rect
        # Shadow (bigger when lifted)
        sh_w = rect.width + (16 if lifted else 8)
        sh_h = rect.height + (12 if lifted else 6)
        shadow = pygame.Surface((sh_w, sh_h), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 130 if lifted else 60),
                         shadow.get_rect(), border_radius=10)
        surface.blit(shadow,
                     (rect.x - (sh_w - rect.width) // 2,
                      rect.y + (4 if lifted else 2)))

        # Body gradient
        if card.locked:
            top, bottom = (60, 180, 110), (30, 130, 80)
        elif card.flash_t > 0:
            base = card.flash_colour
            top = (min(255, base[0] + 40),
                   min(255, base[1] + 40),
                   min(255, base[2] + 40))
            bottom = base
        else:
            top = (90, 220, 200)
            bottom = (30, 150, 140)

        body = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(body, (255, 255, 255), body.get_rect(),
                         border_radius=10)
        grad = pygame.Surface(rect.size)
        draw_vertical_gradient(grad, grad.get_rect(), top, bottom)
        body.blit(grad, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(body, rect.topleft)

        # Inner highlight line
        pygame.draw.line(surface, (255, 255, 255, 80),
                         (rect.x + 6, rect.y + 2),
                         (rect.right - 6, rect.y + 2), 1)
        # Outer border
        border = (0, 0, 0)
        if lifted:
            border = config.WHITE
        pygame.draw.rect(surface, border, rect, width=2, border_radius=10)

        # Lock icon for matched cards
        if card.locked:
            self._draw_lock_icon(surface, (rect.right - 22, rect.y + 8))

        self._draw_card_text(surface, rect, card.text, config.WHITE)

    def _draw_slot(self, surface, slot: _Slot) -> None:
        rect = slot.rect
        if slot.filled:
            # Subtle gold halo for satisfied slot
            if slot.flash_t > 0:
                glow_r = int(40 + 20 * (slot.flash_t / 0.6))
                draw_glow(surface, rect.center, glow_r, config.GOLD,
                          max_alpha=int(80 * (slot.flash_t / 0.6)), layers=3)
            top, bottom = (50, 80, 60), (30, 60, 45)
            border = config.GREEN
        else:
            top, bottom = (40, 50, 60), (24, 32, 42)
            border = config.GOLD_DEEP

        body = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(body, (255, 255, 255), body.get_rect(),
                         border_radius=10)
        grad = pygame.Surface(rect.size)
        draw_vertical_gradient(grad, grad.get_rect(), top, bottom)
        body.blit(grad, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(body, rect.topleft)

        # Dashed border if empty (suggests "drop here")
        if not slot.filled:
            self._draw_dashed_rect(surface, rect, config.GOLD_DEEP,
                                   dash_len=8, gap_len=6, radius=10, width=2)
        else:
            pygame.draw.rect(surface, border, rect, width=2, border_radius=10)

        self._draw_card_text(surface, rect, slot.text, config.WHITE)

    def _draw_dashed_rect(self, surface, rect, colour, dash_len=8, gap_len=6,
                          radius=10, width=2):
        # Simple top/bottom/left/right dashed lines (no rounded corner dashes)
        # Top
        x = rect.x + radius
        while x < rect.right - radius:
            pygame.draw.line(surface, colour, (x, rect.y),
                             (min(x + dash_len, rect.right - radius), rect.y),
                             width)
            x += dash_len + gap_len
        # Bottom
        x = rect.x + radius
        while x < rect.right - radius:
            pygame.draw.line(surface, colour, (x, rect.bottom - 1),
                             (min(x + dash_len, rect.right - radius), rect.bottom - 1),
                             width)
            x += dash_len + gap_len
        # Left
        y = rect.y + radius
        while y < rect.bottom - radius:
            pygame.draw.line(surface, colour, (rect.x, y),
                             (rect.x, min(y + dash_len, rect.bottom - radius)),
                             width)
            y += dash_len + gap_len
        # Right
        y = rect.y + radius
        while y < rect.bottom - radius:
            pygame.draw.line(surface, colour, (rect.right - 1, y),
                             (rect.right - 1, min(y + dash_len, rect.bottom - radius)),
                             width)
            y += dash_len + gap_len

    def _draw_lock_icon(self, surface, topleft) -> None:
        x, y = topleft
        # Shackle
        pygame.draw.arc(surface, config.WHITE,
                        (x + 2, y + 1, 10, 10), 3.14, 0, 2)
        # Body
        body = pygame.Rect(x, y + 6, 14, 10)
        pygame.draw.rect(surface, config.WHITE, body, border_radius=2)
        pygame.draw.circle(surface, (40, 100, 80),
                           (body.centerx, body.centery + 1), 1)

    def _draw_card_text(self, surface, rect, text, colour) -> None:
        words = text.split(" ")
        lines: List[str] = []
        current = ""
        max_width = rect.width - 24
        for word in words:
            attempt = (current + " " + word).strip()
            if self.font_card.size(attempt)[0] <= max_width:
                current = attempt
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        total_h = len(lines) * 22
        y = rect.y + (rect.height - total_h) // 2
        for line in lines:
            line_surf = self.font_card.render(line, True, colour)
            # Drop shadow
            shadow_surf = self.font_card.render(line, True, (0, 0, 0))
            shadow_surf.set_alpha(120)
            surface.blit(shadow_surf,
                         (rect.x + (rect.width - line_surf.get_width()) // 2 + 1,
                          y + 1))
            surface.blit(line_surf,
                         (rect.x + (rect.width - line_surf.get_width()) // 2, y))
            y += 22

"""Dialogue box with typewriter effect and animated entry.

Lines are revealed character-by-character. Press Space to skip to the end
of the current line; press again to advance.
"""
from __future__ import annotations

import pygame
from typing import List

from .. import config
from .draw import draw_panel, render_text_with_shadow


class DialogueBox:
    def __init__(self, speaker: str, lines: List[str],
                 chars_per_second: float = 50.0) -> None:
        self.speaker = speaker
        self.lines = lines
        self.index = 0
        self.active = True
        self.finished = False
        self.chars_per_second = chars_per_second
        self._revealed_chars = 0.0
        self._panel_t = 0.0

        self.font_speaker = pygame.font.Font(None, 24)
        self.font_text = pygame.font.Font(None, 22)
        self.font_hint = pygame.font.Font(None, 16)

    @property
    def current_line(self) -> str:
        if self.index < len(self.lines):
            return self.lines[self.index]
        return ""

    @property
    def fully_revealed(self) -> bool:
        return int(self._revealed_chars) >= len(self.current_line)

    # ---- input -----------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if not self.active:
            return
        advance = False
        if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_SPACE, pygame.K_RETURN, pygame.K_e):
            advance = True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            advance = True

        if advance:
            if not self.fully_revealed:
                # First click reveals all
                self._revealed_chars = len(self.current_line)
            else:
                # Second click advances
                self.index += 1
                self._revealed_chars = 0.0
                if self.index >= len(self.lines):
                    self.active = False
                    self.finished = True

    # ---- update ----------------------------------------------------------
    def update(self, dt: float) -> None:
        if not self.active:
            return
        # Animate panel rising in
        self._panel_t = min(1.0, self._panel_t + dt * 4)
        # Reveal characters
        if not self.fully_revealed:
            self._revealed_chars += dt * self.chars_per_second

    # ---- draw ------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        if not self.active:
            return

        w, h = surface.get_size()
        # Dim
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        surface.blit(overlay, (0, 0))

        # Panel - slides up as _panel_t goes 0->1
        target_y = h - 220
        start_y = h
        y = int(start_y + (target_y - start_y) * self._panel_t)
        box_rect = pygame.Rect(40, y, w - 80, 180)
        draw_panel(surface, box_rect,
                   top=(28, 40, 50), bottom=(18, 26, 34),
                   border=config.TEAL, border_width=2, radius=14)

        # Speaker name tag
        tag_rect = pygame.Rect(box_rect.x + 24, box_rect.y - 18, 240, 32)
        pygame.draw.rect(surface, config.TEAL_DARK, tag_rect, border_radius=10)
        pygame.draw.rect(surface, config.TEAL_BRIGHT, tag_rect, width=2,
                         border_radius=10)
        sp = self.font_speaker.render(self.speaker, True, config.WHITE)
        surface.blit(sp, (tag_rect.x + 14, tag_rect.y + 6))

        # Current line (typewriter-revealed, word-wrapped)
        revealed = self.current_line[:int(self._revealed_chars)]
        self._draw_wrapped(surface, revealed,
                           box_rect.inflate(-48, -64))

        # Blinking cursor when still revealing
        if not self.fully_revealed and pygame.time.get_ticks() % 700 < 400:
            cursor = self.font_text.render("|", True, config.TEAL_BRIGHT)
            # crude: just stick it at the end of the text in the box
            surface.blit(cursor,
                         (box_rect.x + 30 + (len(revealed) % 80) * 8,
                          box_rect.y + 70))

        # Hint
        hint_text = ("[Space] continue" if self.fully_revealed
                     else "[Space] skip")
        hint = self.font_hint.render(
            f"{hint_text}   ({self.index + 1}/{len(self.lines)})",
            True, config.LIGHT_GRAY)
        surface.blit(hint, (box_rect.right - hint.get_width() - 20,
                            box_rect.bottom - 26))

    def _draw_wrapped(self, surface, text, rect) -> None:
        words = text.split(" ")
        lines: List[str] = []
        current = ""
        for w in words:
            attempt = (current + " " + w).strip()
            if self.font_text.size(attempt)[0] <= rect.width:
                current = attempt
            else:
                if current:
                    lines.append(current)
                current = w
        if current:
            lines.append(current)
        y = rect.y
        for ln in lines:
            surface.blit(self.font_text.render(ln, True, config.WHITE),
                         (rect.x, y))
            y += 26

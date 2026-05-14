"""Pause menu pushed on top of the active scene.

Renders the previous scene first (frozen), then a darkened overlay with
Resume / Settings / Stats / Return-to-Menu / Quit buttons.
"""
from __future__ import annotations

import pygame
from typing import List

from .. import config
from ..core.scene import Scene
from ..ui.button import Button
from ..ui.draw import draw_panel, render_text_with_shadow


class PauseMenuScene(Scene):
    def __init__(self, game, paused_scene: Scene) -> None:
        super().__init__(game)
        self.paused_scene = paused_scene
        self.font_title = pygame.font.Font(None, 50)
        self.font_label = pygame.font.Font(None, 16)
        # Snapshot the underlying scene by drawing it once on enter
        self._snapshot: pygame.Surface = None
        self._build_layout()

    def on_enter(self) -> None:
        # Render the paused scene to a snapshot we'll redraw each frame
        snap = pygame.Surface(self.game.size).convert()
        self.paused_scene.draw(snap)
        self._snapshot = snap

    def _build_layout(self) -> None:
        w, h = self.game.size
        cx = w // 2
        button_w, button_h = 280, 52
        gap = 14
        start_y = h // 2 - 60

        entries = [
            ("Resume",         self._resume,       "primary"),
            ("Stats & Badges", self._stats,        "ghost"),
            ("Return to Menu", self._return_menu,  "ghost"),
            ("Quit Game",      self._quit,         "subtle"),
        ]
        self.buttons: List[Button] = []
        for i, (label, cb, style) in enumerate(entries):
            rect = pygame.Rect(cx - button_w // 2,
                               start_y + i * (button_h + gap),
                               button_w, button_h)
            bg = config.TEAL if style == "primary" else config.LIGHT_GRAY
            self.buttons.append(Button(rect, label, cb, bg=bg, style=style,
                                       font_size=22))

    def on_resize(self, w, h) -> None:
        self._build_layout()
        snap = pygame.Surface((w, h)).convert()
        self.paused_scene.draw(snap)
        self._snapshot = snap

    # ---- callbacks ----------------------------------------------------
    def _resume(self) -> None:
        # Pop ourselves off the stack
        self.done = True

    def _stats(self) -> None:
        from .stats_view import StatsViewScene
        # Find a progression on the paused scene if possible
        prog = getattr(self.paused_scene, "progression", None)
        self.game.scene_manager.push(StatsViewScene(self.game, prog))

    def _return_menu(self) -> None:
        from .main_menu import MainMenuScene
        # Replace the entire stack with the main menu
        self.game.scene_manager.replace(MainMenuScene(self.game))

    def _quit(self) -> None:
        self.quit()

    # ---- scene API ----------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._resume()
            return
        for b in self.buttons:
            b.handle_event(event)

    def update(self, dt: float) -> None:
        mp = pygame.mouse.get_pos()
        for b in self.buttons:
            b.update(dt, mp)

    def draw(self, surface: pygame.Surface) -> None:
        # Background = the paused scene snapshot
        if self._snapshot is not None:
            surface.blit(self._snapshot, (0, 0))
        # Darkening overlay
        w, h = surface.get_size()
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        surface.blit(overlay, (0, 0))

        # Title
        title = render_text_with_shadow(self.font_title, "Paused",
                                        config.WHITE)
        surface.blit(title, (w // 2 - title.get_width() // 2,
                             h // 2 - 180))
        hint = self.font_label.render("Press ESC to resume", True,
                                      config.LIGHT_GRAY)
        surface.blit(hint, (w // 2 - hint.get_width() // 2,
                            h // 2 - 130))

        for b in self.buttons:
            b.draw(surface)

"""The main Game object — initialises Pygame, runs the loop, owns the SceneManager."""
from __future__ import annotations

import sys
import pygame

from .. import config
from .scene_manager import SceneManager


class Game:
    """Top-level game object. Construct once, call run()."""

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(config.WINDOW_TITLE)
        flags = pygame.RESIZABLE if config.ALLOW_RESIZE else 0
        self.screen = pygame.display.set_mode(
            (config.WINDOW_WIDTH, config.WINDOW_HEIGHT), flags
        )
        self.clock = pygame.time.Clock()
        self.running = True
        self.scene_manager = SceneManager()
        self.last_dt = 0.0

        from ..scenes.main_menu import MainMenuScene
        self.scene_manager.push(MainMenuScene(self))

    # ---- public helpers -------------------------------------------------
    @property
    def size(self):
        return self.screen.get_size()

    @property
    def width(self):
        return self.screen.get_width()

    @property
    def height(self):
        return self.screen.get_height()

    def _handle_resize(self, event: pygame.event.Event) -> None:
        new_w = max(config.WINDOW_MIN_WIDTH, event.w)
        new_h = max(config.WINDOW_MIN_HEIGHT, event.h)
        self.screen = pygame.display.set_mode(
            (new_w, new_h),
            pygame.RESIZABLE if config.ALLOW_RESIZE else 0
        )
        # Notify the current scene if it cares.
        scene = self.scene_manager.current
        if scene is not None and hasattr(scene, "on_resize"):
            scene.on_resize(new_w, new_h)

    # ---- main loop ------------------------------------------------------
    def run(self) -> None:
        try:
            while self.running and not self.scene_manager.is_empty:
                dt = self.clock.tick(config.FPS) / 1000.0
                # Clamp giant dt spikes (e.g. when window is being dragged)
                self.last_dt = min(dt, 0.1)

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.VIDEORESIZE:
                        self._handle_resize(event)
                    else:
                        self.scene_manager.handle_event(event)

                self.scene_manager.update(self.last_dt)
                self.scene_manager.draw(self.screen)
                pygame.display.flip()
        finally:
            pygame.quit()
            sys.exit(0)

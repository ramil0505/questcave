"""Base class for any screen/state in the game.

A Scene owns its own update / draw / input handling. The Game's SceneManager
swaps between Scenes (e.g. MainMenu -> CaveExplore -> CardMatching -> CaveExplore).
"""
from __future__ import annotations

import pygame
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .game import Game


class Scene(ABC):
    """Abstract base scene. Subclass and implement the three methods."""

    def __init__(self, game: "Game") -> None:
        self.game = game
        self.done = False                 # Set True to signal the SceneManager to pop us
        self.next_scene: Optional[Scene] = None  # If set, replace current scene with this

    # --- lifecycle hooks --------------------------------------------------
    def on_enter(self) -> None:
        """Called once when this scene becomes active."""

    def on_exit(self) -> None:
        """Called once when this scene is left."""

    # --- per-frame --------------------------------------------------------
    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        """Process a single pygame event."""

    @abstractmethod
    def update(self, dt: float) -> None:
        """Advance game state. dt = seconds since last frame."""

    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None:
        """Render the scene to the given surface."""

    # --- helpers ----------------------------------------------------------
    def switch_to(self, scene: "Scene") -> None:
        """Replace this scene with another at the end of the frame."""
        self.next_scene = scene
        self.done = True

    def quit(self) -> None:
        self.game.running = False

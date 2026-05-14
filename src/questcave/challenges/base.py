"""Base class for any RE learning challenge.

Subclass and implement the four abstract methods. The Game's ChallengeScene
wraps the challenge, draws a back-button, and calls into these methods.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

import pygame


class BaseChallenge(ABC):
    """One playable RE learning interaction."""

    def __init__(self, data: Dict[str, Any]) -> None:
        self.data = data
        self.completed: bool = False         # set True when player solves it
        self.failed: bool = False            # set True if player gives up
        self.feedback_text: str = ""         # shown in HUD area
        self.attempts: int = 0

    @abstractmethod
    def title(self) -> str:
        """Short title shown at the top of the challenge screen."""

    @abstractmethod
    def prompt(self) -> str:
        """One-line instruction. Keep it short, players ignore long text."""

    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        ...

    @abstractmethod
    def update(self, dt: float) -> None:
        ...

    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None:
        ...

    # ---- optional ------------------------------------------------------------
    def reset(self) -> None:
        """Restart the challenge from scratch."""
        self.completed = False
        self.failed = False
        self.feedback_text = ""
        self.attempts = 0

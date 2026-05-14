"""Screen-wide effects: camera shake, full-screen flash, fade transitions."""
from __future__ import annotations

import random
from typing import Tuple

import pygame

from .. import config


class ScreenShake:
    """Apply a small random offset to a draw call for `duration` seconds."""

    def __init__(self) -> None:
        self.remaining = 0.0
        self.intensity = 0.0

    def trigger(self, duration: float = 0.25, intensity: float = 8.0) -> None:
        self.remaining = max(self.remaining, duration)
        self.intensity = max(self.intensity, intensity)

    def update(self, dt: float) -> None:
        if self.remaining > 0:
            self.remaining = max(0.0, self.remaining - dt)
            if self.remaining == 0:
                self.intensity = 0.0

    @property
    def offset(self) -> Tuple[int, int]:
        if self.remaining <= 0:
            return (0, 0)
        return (random.randint(-int(self.intensity), int(self.intensity)),
                random.randint(-int(self.intensity), int(self.intensity)))


class ScreenFlash:
    """Full-screen colour flash that fades out."""

    def __init__(self) -> None:
        self.t = 0.0
        self.duration = 0.0
        self.colour = (255, 255, 255)
        self.max_alpha = 180

    def trigger(self, colour: Tuple[int, int, int] = (255, 255, 255),
                duration: float = 0.35, max_alpha: int = 180) -> None:
        self.colour = colour
        self.duration = duration
        self.t = duration
        self.max_alpha = max_alpha

    def update(self, dt: float) -> None:
        if self.t > 0:
            self.t = max(0.0, self.t - dt)

    def draw(self, surface: pygame.Surface) -> None:
        if self.t <= 0:
            return
        frac = self.t / self.duration            # 1 -> 0
        alpha = int(self.max_alpha * frac)
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((*self.colour, alpha))
        surface.blit(overlay, (0, 0))


class FadeTransition:
    """Fades the screen to a solid colour and back. Useful between scenes."""

    def __init__(self) -> None:
        self.t = 0.0
        self.duration = 0.0
        self.fading_in = True                    # in = from opaque to clear
        self.colour = (0, 0, 0)

    def start_fade_in(self, duration: float = 0.4,
                      colour: Tuple[int, int, int] = (0, 0, 0)) -> None:
        self.duration = duration
        self.t = duration
        self.fading_in = True
        self.colour = colour

    def start_fade_out(self, duration: float = 0.4,
                       colour: Tuple[int, int, int] = (0, 0, 0)) -> None:
        self.duration = duration
        self.t = 0.0
        self.fading_in = False
        self.colour = colour

    def update(self, dt: float) -> None:
        if self.fading_in:
            self.t = max(0.0, self.t - dt)
        else:
            self.t = min(self.duration, self.t + dt)

    def draw(self, surface: pygame.Surface) -> None:
        if self.duration <= 0:
            return
        frac = self.t / self.duration if self.fading_in else self.t / self.duration
        alpha = int(255 * frac)
        if alpha <= 0:
            return
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((*self.colour, alpha))
        surface.blit(overlay, (0, 0))

    @property
    def covered(self) -> bool:
        """True when the screen is fully covered (useful to swap scenes)."""
        return not self.fading_in and self.t >= self.duration

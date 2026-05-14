"""Lightweight tween manager.

Animate any numeric value from A to B over a duration, with an easing curve.
Optional on_complete callback fires when the tween finishes.

Example:
    tween = Tween(start=0, end=1, duration=0.4, ease=ease_out_back)
    # each frame:
    tween.update(dt)
    alpha = tween.value
    if tween.done: ...
"""
from __future__ import annotations

from typing import Callable, Optional, List

from .easing import linear


class Tween:
    """A single value animation."""

    def __init__(self, start: float, end: float, duration: float,
                 ease: Callable[[float], float] = linear,
                 on_complete: Optional[Callable[[], None]] = None,
                 delay: float = 0.0) -> None:
        self.start = start
        self.end = end
        self.duration = max(0.0001, duration)
        self.ease = ease
        self.on_complete = on_complete
        self.delay = delay

        self.elapsed = 0.0
        self.done = False
        self._fired_complete = False

    @property
    def value(self) -> float:
        if self.elapsed < self.delay:
            return self.start
        local_t = (self.elapsed - self.delay) / self.duration
        if local_t >= 1.0:
            return self.end
        eased = self.ease(local_t)
        return self.start + (self.end - self.start) * eased

    def update(self, dt: float) -> None:
        if self.done:
            return
        self.elapsed += dt
        if self.elapsed >= self.delay + self.duration:
            self.done = True
            if not self._fired_complete and self.on_complete:
                self._fired_complete = True
                self.on_complete()

    def reset(self) -> None:
        self.elapsed = 0.0
        self.done = False
        self._fired_complete = False


class TweenGroup:
    """Manages many tweens at once. Auto-prunes finished ones."""

    def __init__(self) -> None:
        self._tweens: List[Tween] = []

    def add(self, tween: Tween) -> Tween:
        self._tweens.append(tween)
        return tween

    def update(self, dt: float) -> None:
        for t in self._tweens:
            t.update(dt)
        self._tweens = [t for t in self._tweens if not t.done]

    def clear(self) -> None:
        self._tweens.clear()

"""Stack-based scene manager.

Why a stack? When the player enters a Challenge, we *push* the challenge scene
on top of the exploration scene; when the challenge ends, we *pop* back to
exactly the exploration state where they left off — no save/restore plumbing.
"""
from __future__ import annotations

from typing import List, Optional
import pygame

from .scene import Scene


class SceneManager:
    def __init__(self) -> None:
        self._stack: List[Scene] = []

    # ---- stack operations ---------------------------------------------------
    def push(self, scene: Scene) -> None:
        if self._stack:
            self._stack[-1].on_exit()
        self._stack.append(scene)
        scene.on_enter()

    def pop(self) -> Optional[Scene]:
        if not self._stack:
            return None
        top = self._stack.pop()
        top.on_exit()
        if self._stack:
            self._stack[-1].on_enter()
        return top

    def replace(self, scene: Scene) -> None:
        """Pop everything, push the new scene."""
        while self._stack:
            self.pop()
        self.push(scene)

    @property
    def current(self) -> Optional[Scene]:
        return self._stack[-1] if self._stack else None

    @property
    def is_empty(self) -> bool:
        return not self._stack

    # ---- per-frame ----------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if self.current:
            self.current.handle_event(event)

    def update(self, dt: float) -> None:
        scene = self.current
        if scene is None:
            return
        scene.update(dt)
        if scene.done:
            next_scene = scene.next_scene
            self.pop()
            if next_scene is not None:
                self.push(next_scene)

    def draw(self, surface: pygame.Surface) -> None:
        if self.current:
            self.current.draw(surface)

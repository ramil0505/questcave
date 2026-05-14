"""Modern button widget with hover scaling, glow, and smooth transitions."""
from __future__ import annotations

import pygame
from typing import Callable, Tuple, Optional

from .. import config
from .draw import draw_glow, draw_vertical_gradient


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


class Button:
    def __init__(self, rect: pygame.Rect, label: str,
                 on_click: Callable[[], None],
                 bg: Tuple[int, int, int] = config.TEAL,
                 bg_hover: Optional[Tuple[int, int, int]] = None,
                 text_colour: Tuple[int, int, int] = config.WHITE,
                 font_size: int = 22,
                 icon: Optional[str] = None,
                 style: str = "primary") -> None:
        """
        style:
            'primary'   - solid colour with gradient + glow on hover
            'ghost'     - outlined, transparent
            'subtle'    - dark grey
        """
        self.rect = rect
        self.base_rect = rect.copy()
        self.label = label
        self.on_click = on_click
        self.bg = bg
        self.bg_hover = bg_hover or self._auto_hover(bg)
        self.text_colour = text_colour
        self.font = pygame.font.Font(None, font_size)
        self.icon = icon
        self.style = style

        self.hover_t = 0.0           # 0=resting, 1=fully hovered
        self.press_t = 0.0           # 0=resting, 1=pressed (pulse on click)
        self.disabled = False

    @staticmethod
    def _auto_hover(c: Tuple[int, int, int]) -> Tuple[int, int, int]:
        return (min(255, c[0] + 30), min(255, c[1] + 30), min(255, c[2] + 30))

    # ---- events ----------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if self.disabled:
            return
        if event.type == pygame.MOUSEMOTION:
            self.hovered_now = self.rect.collidepoint(event.pos)
        elif (event.type == pygame.MOUSEBUTTONDOWN
              and event.button == 1
              and self.rect.collidepoint(event.pos)):
            self.press_t = 1.0
            self.on_click()

    # ---- per-frame -------------------------------------------------------
    def update(self, dt: float, mouse_pos: Tuple[int, int]) -> None:
        target = 1.0 if (not self.disabled and
                         self.rect.collidepoint(mouse_pos)) else 0.0
        # Smooth ease toward target
        speed = 8.0
        self.hover_t = _lerp(self.hover_t, target, min(1.0, dt * speed))
        # Press pulse decays quickly
        self.press_t = max(0.0, self.press_t - dt * 4.0)

    # ---- draw ------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        # Scale based on hover/press - subtle pop
        scale = 1.0 + 0.04 * self.hover_t - 0.03 * self.press_t
        w = int(self.base_rect.width * scale)
        h = int(self.base_rect.height * scale)
        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = self.base_rect.center

        # Soft glow on hover
        if self.hover_t > 0.05 and self.style == "primary":
            glow_radius = int(self.rect.width * 0.7)
            draw_glow(surface, self.rect.center, glow_radius,
                      self.bg_hover, max_alpha=int(70 * self.hover_t), layers=4)

        # Body
        if self.style == "ghost":
            self._draw_ghost(surface)
        elif self.style == "subtle":
            self._draw_subtle(surface)
        else:
            self._draw_primary(surface)

        # Label
        full_label = (f"{self.icon}  {self.label}"
                      if self.icon else self.label)
        label_surf = self.font.render(full_label, True, self.text_colour)
        surface.blit(label_surf,
                     (self.rect.centerx - label_surf.get_width() // 2,
                      self.rect.centery - label_surf.get_height() // 2))

    def _draw_primary(self, surface) -> None:
        body = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        # Round mask
        pygame.draw.rect(body, (255, 255, 255), body.get_rect(),
                         border_radius=10)
        # Gradient
        bottom = self.bg
        top = self.bg_hover if self.hover_t > 0.5 else self.bg
        # Lerp between resting and hovered gradient
        top_lerp = (
            int(_lerp(self.bg[0], self.bg_hover[0], self.hover_t)),
            int(_lerp(self.bg[1], self.bg_hover[1], self.hover_t)),
            int(_lerp(self.bg[2], self.bg_hover[2], self.hover_t)),
        )
        bottom_lerp = (
            max(0, top_lerp[0] - 30),
            max(0, top_lerp[1] - 30),
            max(0, top_lerp[2] - 30),
        )
        grad = pygame.Surface(self.rect.size)
        draw_vertical_gradient(grad, grad.get_rect(), top_lerp, bottom_lerp)
        body.blit(grad, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(body, self.rect.topleft)
        # Subtle border
        pygame.draw.rect(surface, (255, 255, 255, 30), self.rect,
                         width=1, border_radius=10)

    def _draw_ghost(self, surface) -> None:
        # Slight fill on hover
        if self.hover_t > 0:
            fill = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            pygame.draw.rect(fill, (*self.bg, int(30 * self.hover_t)),
                             fill.get_rect(), border_radius=10)
            surface.blit(fill, self.rect.topleft)
        pygame.draw.rect(surface, self.bg, self.rect, width=2,
                         border_radius=10)

    def _draw_subtle(self, surface) -> None:
        bg = config.DARKER_GRAY if self.hover_t < 0.5 else config.DARK_GRAY
        pygame.draw.rect(surface, bg, self.rect, border_radius=10)
        pygame.draw.rect(surface, config.GRAY, self.rect, width=1,
                         border_radius=10)

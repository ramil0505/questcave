"""Reusable drawing helpers: gradient panels, glows, rounded rects with shadow.

Pulling these out keeps the rest of the UI code clean and the visual language
consistent across menus, HUD, dialogue, and cards.
"""
from __future__ import annotations

from typing import Tuple

import pygame

from .. import config


def draw_vertical_gradient(surface: pygame.Surface, rect: pygame.Rect,
                           top_colour: Tuple[int, int, int],
                           bottom_colour: Tuple[int, int, int]) -> None:
    """Cheap top->bottom gradient. Draws one row per pixel."""
    if rect.height <= 0 or rect.width <= 0:
        return
    grad = pygame.Surface((1, rect.height))
    for y in range(rect.height):
        t = y / max(1, rect.height - 1)
        r = int(top_colour[0] + (bottom_colour[0] - top_colour[0]) * t)
        g = int(top_colour[1] + (bottom_colour[1] - top_colour[1]) * t)
        b = int(top_colour[2] + (bottom_colour[2] - top_colour[2]) * t)
        grad.set_at((0, y), (r, g, b))
    grad = pygame.transform.scale(grad, (rect.width, rect.height))
    surface.blit(grad, rect.topleft)


def draw_panel(surface: pygame.Surface, rect: pygame.Rect,
               top: Tuple[int, int, int] = config.COLOR_PANEL_TOP,
               bottom: Tuple[int, int, int] = config.COLOR_PANEL,
               border: Tuple[int, int, int] = config.COLOR_PANEL_BORDER,
               border_width: int = 2,
               radius: int = 12,
               shadow: bool = True) -> None:
    """Gradient panel with optional drop shadow and rounded border."""
    if shadow:
        shadow_surf = pygame.Surface(
            (rect.width + 12, rect.height + 12), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 120),
                         shadow_surf.get_rect(), border_radius=radius + 2)
        surface.blit(shadow_surf, (rect.x - 6, rect.y - 3))

    # Body via mask: draw rounded rect, then a gradient clipped to it.
    body = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(body, (255, 255, 255), body.get_rect(),
                     border_radius=radius)
    grad = pygame.Surface(rect.size)
    grad_rect = grad.get_rect()
    draw_vertical_gradient(grad, grad_rect, top, bottom)
    body.blit(grad, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(body, rect.topleft)

    if border_width > 0:
        pygame.draw.rect(surface, border, rect, width=border_width,
                         border_radius=radius)


def draw_glow(surface: pygame.Surface, centre: Tuple[int, int],
              radius: int, colour: Tuple[int, int, int],
              max_alpha: int = 90, layers: int = 4) -> None:
    """Soft radial glow at a point. Used for buttons, torches, highlights."""
    for i in range(layers, 0, -1):
        r = int(radius * (i / layers))
        a = int(max_alpha * (1 - i / (layers + 1)))
        glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*colour, a), (r, r), r)
        surface.blit(glow, (centre[0] - r, centre[1] - r))


def draw_pill(surface: pygame.Surface, rect: pygame.Rect,
              colour: Tuple[int, int, int],
              border_colour: Tuple[int, int, int] = None,
              border_width: int = 0) -> None:
    """Fully-rounded pill shape (good for tags, badges)."""
    radius = rect.height // 2
    pygame.draw.rect(surface, colour, rect, border_radius=radius)
    if border_colour and border_width:
        pygame.draw.rect(surface, border_colour, rect,
                         width=border_width, border_radius=radius)


def render_text_with_shadow(font: pygame.font.Font, text: str,
                            colour: Tuple[int, int, int],
                            shadow_colour: Tuple[int, int, int] = (0, 0, 0),
                            offset: Tuple[int, int] = (1, 2)) -> pygame.Surface:
    """Pre-rendered text with a soft drop-shadow."""
    main = font.render(text, True, colour)
    shadow = font.render(text, True, shadow_colour)
    w = main.get_width() + abs(offset[0])
    h = main.get_height() + abs(offset[1])
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.blit(shadow, offset)
    surf.blit(main, (0, 0))
    return surf

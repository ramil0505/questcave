"""Particle system for ambient atmosphere and reward feedback.

Three usage patterns covered:
  * ambient (long-lived, repopulating, e.g. dust motes in a cave)
  * burst (one-shot at a point, e.g. sparkle on correct match)
  * confetti (rain falling from above, used on quest complete)

ParticleSystem owns a flat list. Spawn methods append; update advances/prunes;
draw blits with alpha based on remaining life.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import List, Tuple

import pygame


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    gx: float                 # gravity / drift x
    gy: float
    life: float
    max_life: float
    size: float
    colour: Tuple[int, int, int]
    fade: bool = True
    shrink: bool = False
    spin: float = 0.0         # only used for rect/square confetti
    spin_speed: float = 0.0


class ParticleSystem:
    def __init__(self) -> None:
        self.particles: List[Particle] = []

    # ---- spawn methods ----------------------------------------------------
    def spawn_ambient_dust(self, area: pygame.Rect, count: int = 1,
                           colour: Tuple[int, int, int] = (180, 200, 200)) -> None:
        """Slow floating dust motes. Call each frame to keep the cave atmospheric."""
        for _ in range(count):
            self.particles.append(Particle(
                x=random.uniform(area.left, area.right),
                y=random.uniform(area.top, area.bottom),
                vx=random.uniform(-10, 10),
                vy=random.uniform(-15, -5),
                gx=0, gy=0,
                life=random.uniform(3.0, 6.0),
                max_life=6.0,
                size=random.uniform(1.5, 3.0),
                colour=colour,
                fade=True,
            ))

    def spawn_sparkle_burst(self, pos: Tuple[float, float], count: int = 18,
                            colour: Tuple[int, int, int] = (244, 196, 48)) -> None:
        """Bright spark explosion at a point — use on correct match / pickup."""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(80, 220)
            self.particles.append(Particle(
                x=pos[0], y=pos[1],
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                gx=0, gy=180,                 # gravity pulls down
                life=random.uniform(0.4, 0.9),
                max_life=0.9,
                size=random.uniform(2.5, 5.0),
                colour=colour,
                fade=True,
                shrink=True,
            ))

    def spawn_footstep(self, pos: Tuple[float, float]) -> None:
        """Tiny puff under the player's feet."""
        for _ in range(2):
            self.particles.append(Particle(
                x=pos[0] + random.uniform(-6, 6),
                y=pos[1] + random.uniform(-2, 4),
                vx=random.uniform(-8, 8),
                vy=random.uniform(-12, -2),
                gx=0, gy=10,
                life=0.5,
                max_life=0.5,
                size=random.uniform(2, 4),
                colour=(100, 110, 110),
                fade=True,
                shrink=True,
            ))

    def spawn_confetti(self, area: pygame.Rect, count: int = 60) -> None:
        """Coloured rectangles rain from above. Use on quest complete."""
        palette = [(244, 196, 48), (42, 174, 143), (212, 101, 74),
                   (107, 76, 138), (116, 176, 87), (59, 122, 140)]
        for _ in range(count):
            self.particles.append(Particle(
                x=random.uniform(area.left, area.right),
                y=random.uniform(area.top - 40, area.top),
                vx=random.uniform(-40, 40),
                vy=random.uniform(80, 180),
                gx=0, gy=120,
                life=random.uniform(1.5, 2.6),
                max_life=2.6,
                size=random.uniform(6, 11),
                colour=random.choice(palette),
                fade=True,
                spin=random.uniform(0, 360),
                spin_speed=random.uniform(-360, 360),
            ))

    def spawn_torch_ember(self, pos: Tuple[float, float]) -> None:
        """Rising orange embers from a torch position."""
        self.particles.append(Particle(
            x=pos[0] + random.uniform(-3, 3),
            y=pos[1],
            vx=random.uniform(-6, 6),
            vy=random.uniform(-50, -30),
            gx=0, gy=0,
            life=random.uniform(0.6, 1.2),
            max_life=1.2,
            size=random.uniform(1.5, 3.0),
            colour=random.choice([(244, 196, 48), (255, 140, 60), (240, 100, 50)]),
            fade=True,
            shrink=True,
        ))

    # ---- update + draw ----------------------------------------------------
    def update(self, dt: float) -> None:
        for p in self.particles:
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vx += p.gx * dt
            p.vy += p.gy * dt
            p.life -= dt
            if p.spin_speed:
                p.spin += p.spin_speed * dt
        self.particles = [p for p in self.particles if p.life > 0]

    def draw(self, surface: pygame.Surface) -> None:
        for p in self.particles:
            life_frac = max(0.0, min(1.0, p.life / p.max_life))
            alpha = int(255 * life_frac) if p.fade else 255
            size = p.size * (life_frac if p.shrink else 1.0)
            if size < 0.5:
                continue
            if p.spin_speed:
                # Rotated rectangle confetti
                surf = pygame.Surface((int(size * 2), int(size * 1.2)),
                                      pygame.SRCALPHA)
                pygame.draw.rect(surf, (*p.colour, alpha),
                                 surf.get_rect(), border_radius=2)
                rotated = pygame.transform.rotate(surf, p.spin)
                rect = rotated.get_rect(center=(int(p.x), int(p.y)))
                surface.blit(rotated, rect)
            else:
                radius = max(1, int(size))
                surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (*p.colour, alpha),
                                   (radius, radius), radius)
                surface.blit(surf, (int(p.x) - radius, int(p.y) - radius))

    def clear(self) -> None:
        self.particles.clear()

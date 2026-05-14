"""Wrapper scene for any BaseChallenge.

Adds:
- Top bar with quest title and back/give-up button
- Reward overlay with confetti, screen flash, big number animation
- Smooth fade-in transition
"""
from __future__ import annotations

import pygame
from typing import Callable

from .. import config
from ..core.scene import Scene
from ..challenges.registry import create_challenge
from ..systems.quests import Quest
from ..systems.progression import ProgressionSystem
from ..ui.button import Button
from ..ui.draw import draw_panel, draw_glow, draw_vertical_gradient, render_text_with_shadow
from ..utils.particles import ParticleSystem
from ..utils.effects import ScreenFlash, FadeTransition
from ..utils.tween import Tween
from ..utils.easing import ease_out_back, ease_out_cubic


class ChallengeScene(Scene):
    def __init__(self, game, quest: Quest, progression: ProgressionSystem,
                 explorer_class: str, return_scene: Scene,
                 on_finish: Callable[[Quest, bool], None]) -> None:
        super().__init__(game)
        self.quest = quest
        self.progression = progression
        self.explorer_class = explorer_class
        self.return_scene = return_scene
        self.on_finish = on_finish

        self.challenge = create_challenge(quest.challenge_type,
                                          quest.challenge_data)
        self.error_text = (None if self.challenge
                           else f"Unknown challenge: {quest.challenge_type}")

        self.back_button = Button(
            pygame.Rect(20, 18, 130, 40),
            "Give Up", self._give_up, style="subtle", font_size=20,
        )

        # Reward overlay state
        self.reward_active = False
        self.reward_timer = 0.0
        self.reward_duration = 3.0
        self.reward_particles = ParticleSystem()
        self.flash = ScreenFlash()
        self.fade = FadeTransition()
        self.fade.start_fade_in(duration=0.4)
        # Tween for the reward panel scale-in
        self.reward_panel_t: Tween = None
        # Guard against on_finish being called multiple times (e.g. if the
        # player click-spams during the reward overlay).
        self._finished = False

        self.font_topic = pygame.font.Font(None, 22)
        self.font_big = pygame.font.Font(None, 56)
        self.font_h = pygame.font.Font(None, 32)
        self.font_b = pygame.font.Font(None, 24)
        self.font_s = pygame.font.Font(None, 18)

    def on_resize(self, w, h) -> None:
        pass  # challenge scenes are layout-based, no per-resize work needed

    # ---- callbacks -----------------------------------------------------
    def _give_up(self) -> None:
        if self._finished:
            return
        self._finished = True
        self.on_finish(self.quest, False)
        self.switch_to(self.return_scene)

    def _finish_success(self) -> None:
        if self._finished:
            return
        self._finished = True
        self.on_finish(self.quest, True)
        self.switch_to(self.return_scene)

    # ---- scene API -----------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._give_up()
            return
        if self.reward_active:
            # Allow skipping the reward animation by clicking
            if (event.type == pygame.MOUSEBUTTONDOWN
                    or event.type == pygame.KEYDOWN):
                if self.reward_timer > 0.6:
                    self._finish_success()
            return
        self.back_button.handle_event(event)
        if self.challenge is not None and not self.challenge.completed:
            self.challenge.handle_event(event)

    def update(self, dt: float) -> None:
        mp = pygame.mouse.get_pos()
        self.back_button.update(dt, mp)
        self.flash.update(dt)
        self.fade.update(dt)

        if self.reward_active:
            self.reward_timer += dt
            self.reward_particles.update(dt)
            if self.reward_panel_t:
                self.reward_panel_t.update(dt)
            # Auto-finish at the end of the reward duration
            if self.reward_timer >= self.reward_duration:
                self._finish_success()
            return

        if self.challenge is None:
            return
        self.challenge.update(dt)
        if self.challenge.completed and not self.reward_active:
            self._begin_reward_animation()

    def _begin_reward_animation(self) -> None:
        self.reward_active = True
        self.reward_timer = 0.0
        # Burst of confetti from the top
        w, h = self.game.size
        self.reward_particles.spawn_confetti(
            pygame.Rect(0, -20, w, 40), count=80)
        # Bright white flash
        self.flash.trigger((255, 240, 200), duration=0.45, max_alpha=180)
        # Panel scale tween
        self.reward_panel_t = Tween(0.0, 1.0, duration=0.5,
                                    ease=ease_out_back)

    def draw(self, surface: pygame.Surface) -> None:
        # Background gradient
        draw_vertical_gradient(surface, surface.get_rect(),
                               config.CAVE_DARKER, config.CAVE_DARK)

        # Top bar with title and reward info
        self._draw_top_bar(surface)

        # Challenge body
        if self.error_text:
            font = pygame.font.Font(None, 28)
            err = font.render(self.error_text, True, config.CORAL)
            surface.blit(err,
                         (surface.get_width() // 2 - err.get_width() // 2,
                          surface.get_height() // 2))
        elif self.challenge is not None:
            self.challenge.draw(surface)

        # Back button on top
        self.back_button.draw(surface)

        if self.reward_active:
            self._draw_reward_overlay(surface)

        # Effects last
        self.flash.draw(surface)
        self.fade.draw(surface)

    # ---- pieces --------------------------------------------------------
    def _draw_top_bar(self, surface) -> None:
        # Quest topic chip
        topic_text = f"{self.quest.re_topic}"
        chip = self.font_topic.render(topic_text, True, config.GOLD_BRIGHT)
        chip_rect = pygame.Rect(0, 0, chip.get_width() + 28, 32)
        chip_rect.center = (surface.get_width() // 2, 36)
        pygame.draw.rect(surface, config.GOLD_DEEP, chip_rect, border_radius=16)
        surface.blit(chip, (chip_rect.centerx - chip.get_width() // 2,
                            chip_rect.centery - chip.get_height() // 2))

        # Reward indicator on the right
        rw = f"+{self.quest.reward.xp} XP   +{self.quest.reward.gems} Gems"
        rw_surf = self.font_topic.render(rw, True, config.LIGHT_GRAY)
        surface.blit(rw_surf,
                     (surface.get_width() - rw_surf.get_width() - 22, 30))

    def _draw_reward_overlay(self, surface) -> None:
        w, h = surface.get_size()
        # Dim
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        # Confetti
        self.reward_particles.draw(surface)

        # Reward panel - scales in
        scale = self.reward_panel_t.value if self.reward_panel_t else 1.0
        pw, ph = int(620 * scale), int(300 * scale)
        panel = pygame.Rect(0, 0, pw, ph)
        panel.center = (w // 2, h // 2)

        # Glow behind
        draw_glow(surface, panel.center, int(panel.width * 0.55),
                  config.GOLD, max_alpha=int(90 * scale), layers=4)

        if scale < 0.2:
            return  # Too small to bother drawing details

        draw_panel(surface, panel,
                   top=(38, 48, 58), bottom=(20, 28, 36),
                   border=config.GOLD, border_width=3, radius=18)

        # Title
        title = render_text_with_shadow(self.font_big, "Quest Complete!",
                                        config.GOLD_BRIGHT)
        surface.blit(title,
                     (panel.centerx - title.get_width() // 2,
                      panel.y + 28))

        # Rewards
        y = panel.y + 110
        rewards = [
            (f"+{self.quest.reward.xp}", "Experience", config.TEAL),
            (f"+{self.quest.reward.gems}", "Gems", config.PURPLE),
        ]
        if self.quest.reward.badge_id:
            rewards.append(("New", "Badge unlocked", config.CORAL))
        # Layout horizontally
        col_w = panel.width // len(rewards)
        for i, (big, label, colour) in enumerate(rewards):
            cx = panel.x + col_w // 2 + i * col_w
            big_surf = self.font_big.render(big, True, colour)
            surface.blit(big_surf, (cx - big_surf.get_width() // 2, y))
            lbl_surf = self.font_b.render(label, True, config.LIGHT_GRAY)
            surface.blit(lbl_surf,
                         (cx - lbl_surf.get_width() // 2, y + 48))

        # Hint
        if self.reward_timer > 0.8:
            hint = self.font_s.render(
                "Click to continue   ·   Auto-returns shortly",
                True, config.GRAY)
            surface.blit(hint,
                         (panel.centerx - hint.get_width() // 2,
                          panel.bottom - 26))

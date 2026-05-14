"""Cave exploration scene - the main gameplay loop.

Modern upgrades:
- Player leaves footstep dust when moving
- Ambient dust motes drift through the cave
- NPC has a gentle idle bob animation
- Interact prompt pulses above the NPC when in range
- Smooth pause-menu integration (TAB = stats, ESC = pause)
- Screen shake when level-up happens
"""
from __future__ import annotations

import math
import pygame
from typing import List, Optional

from .. import config
from ..core.scene import Scene
from ..core.save_load import save_game
from ..entities.player import Player
from ..entities.npc import NPC, CaveGuardian
from ..world.cave_room import CaveRoom
from ..systems.progression import ProgressionSystem
from ..systems.quests import Quest, load_quests
from ..systems.dialogue import get_dialogue
from ..ui.hud import HUD
from ..ui.dialogue_box import DialogueBox
from ..utils.particles import ParticleSystem
from ..utils.effects import ScreenShake


class CaveExploreScene(Scene):
    def __init__(self, game,
                 saved_state: Optional[dict] = None,
                 explorer_class: str = "Sage") -> None:
        super().__init__(game)

        if saved_state:
            self.player = Player(
                name=saved_state.get("name", "Adventurer"),
                explorer_class=saved_state.get("explorer_class", "Sage"),
            )
            self.progression = ProgressionSystem.from_dict(saved_state)
        else:
            self.player = Player(explorer_class=explorer_class)
            self.progression = ProgressionSystem()

        self.t = 0.0
        self.room = CaveRoom(name="Entrance Hall",
                             depth=self.progression.cave_depth)
        self._sync_room_bounds()

        # Guardian on the right of the room
        gx = self.game.width - 180
        gy = self.game.height // 2
        self.guardian = CaveGuardian(pos=(gx, gy))
        self.npcs: List[NPC] = [self.guardian]
        self.guardian.on_interact = self._guardian_interact

        # UI
        self.hud = HUD(self.progression)
        self.dialogue: Optional[DialogueBox] = None
        self.pending_quest: Optional[Quest] = None
        self.toast: Optional[str] = None
        self.toast_t = 0.0

        # FX
        self.particles = ParticleSystem()
        self.shake = ScreenShake()
        self._footstep_cooldown = 0.0
        self._last_player_pos = pygame.Vector2(self.player.rect.center)
        self._last_known_level = self.progression.level

        self.quest_cursor = 0

    def _sync_room_bounds(self) -> None:
        """Match the room to the current window minus HUD strip."""
        self.room.set_bounds(pygame.Rect(
            0, 80, self.game.width, self.game.height - 80))

    def on_resize(self, w, h) -> None:
        self._sync_room_bounds()
        # Reposition guardian
        self.guardian.rect.center = (w - 180, h // 2)

    # ---- interaction helpers -------------------------------------------
    def _guardian_interact(self, npc: NPC) -> None:
        quests = [q for q in load_quests()
                  if q.quest_id not in self.progression.completed_quests]
        if not quests:
            self.dialogue = DialogueBox(
                "Cave Guardian",
                get_dialogue("guardian_exhausted"))
            self.pending_quest = None
            return

        if self.quest_cursor >= len(quests):
            self.quest_cursor = 0
        quest = quests[self.quest_cursor]
        self.quest_cursor += 1

        intro_key = ("guardian_intro" if self.progression.level == 1
                     and not self.progression.completed_quests
                     else "guardian_returning")
        intro_lines = list(get_dialogue(intro_key)) + [
            f"Your task: {quest.title}.",
            quest.description,
            "Are you ready? Press Space to begin.",
        ]
        self.dialogue = DialogueBox("Cave Guardian", intro_lines)
        self.pending_quest = quest

    def _launch_pending_quest(self) -> None:
        if self.pending_quest is None:
            return
        from .challenge_scene import ChallengeScene
        scene = ChallengeScene(self.game, self.pending_quest,
                               self.progression,
                               self.player.explorer_class,
                               return_scene=self,
                               on_finish=self._on_quest_finish)
        self.pending_quest = None
        self.switch_to(scene)

    def _on_quest_finish(self, quest: Quest, success: bool) -> None:
        if not success:
            return
        # complete_quest returns False if this quest is already in
        # completed_quests, which means we've already given the rewards.
        # Without this guard, repeated calls (e.g. if the player click-spams
        # during the reward overlay) would multiply XP / gems / depth.
        first_time = self.progression.complete_quest(quest.quest_id)
        if not first_time:
            return
        self.progression.grant_xp(quest.reward.xp,
                                  self.player.explorer_class)
        self.progression.grant_gems(quest.reward.gems)
        if quest.reward.badge_id:
            from ..systems.progression import KnowledgeBadge
            self.progression.grant_badge(KnowledgeBadge(
                badge_id=quest.reward.badge_id,
                title=quest.title,
                description=quest.re_topic,
            ))
        self.progression.descend(1)
        self.room = CaveRoom("Deeper Hall",
                             depth=self.progression.cave_depth)
        self._sync_room_bounds()
        self._show_toast(
            f"+{quest.reward.xp} XP   +{quest.reward.gems} gems   "
            f"Cave depth -> {self.progression.cave_depth}")
        self._save()
        if self.progression.level > self._last_known_level:
            self.shake.trigger(duration=0.4, intensity=6)
            self._last_known_level = self.progression.level

    def _show_toast(self, text: str, duration: float = 3.5) -> None:
        self.toast = text
        self.toast_t = duration

    def _save(self) -> None:
        state = {**self.player.to_dict(), **self.progression.to_dict()}
        save_game(state)

    # ---- scene API ------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if self.dialogue and self.dialogue.active:
            self.dialogue.handle_event(event)
            if self.dialogue.finished:
                self.dialogue = None
                self._launch_pending_quest()
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._save()
                from .pause_menu import PauseMenuScene
                self.game.scene_manager.push(PauseMenuScene(self.game, self))
            elif event.key == pygame.K_TAB:
                from .stats_view import StatsViewScene
                self.game.scene_manager.push(
                    StatsViewScene(self.game, self.progression))
            elif event.key in (pygame.K_e, pygame.K_SPACE):
                self._try_interact()

    def _try_interact(self) -> None:
        for npc in self.npcs:
            if npc.is_within_interact_range(self.player.rect.center):
                if npc.on_interact is not None:
                    npc.on_interact(npc)
                break

    def update(self, dt: float) -> None:
        self.t += dt
        self.hud.update(dt)
        self.shake.update(dt)

        if self.dialogue and self.dialogue.active:
            self.dialogue.update(dt)
            return

        keys = pygame.key.get_pressed()
        self.player.handle_input(dt, keys)
        self.player.update_after_collision()
        self.player.clamp_to_bounds(self.room.bounds)

        # Footstep particles when actually moving
        cur = pygame.Vector2(self.player.rect.center)
        moved = (cur - self._last_player_pos).length()
        self._last_player_pos = cur
        self._footstep_cooldown -= dt
        if moved > 1 and self._footstep_cooldown <= 0:
            self.particles.spawn_footstep(
                (self.player.rect.centerx,
                 self.player.rect.bottom - 4))
            self._footstep_cooldown = 0.15

        # Ambient dust motes (sparse)
        if len(self.particles.particles) < 30:
            self.particles.spawn_ambient_dust(
                self.room.bounds, count=1,
                colour=(160, 180, 180))

        # Torch embers occasionally
        if int(self.t * 20) % 3 == 0:
            for tx, ty in self.room.torch_positions[:3]:
                self.particles.spawn_torch_ember((tx, ty))

        self.particles.update(dt)

        # Toast fade
        if self.toast_t > 0:
            self.toast_t -= dt
            if self.toast_t <= 0:
                self.toast = None

    def draw(self, surface: pygame.Surface) -> None:
        # Render world to an offscreen surface so we can apply shake easily
        ox, oy = self.shake.offset
        canvas = surface

        # World
        self.room.draw(canvas, time_t=self.t)
        self.particles.draw(canvas)

        # Entities (sort by y for poor-man's depth)
        sprites = [*self.npcs, self.player]
        sprites.sort(key=lambda s: s.rect.bottom)
        for sp in sprites:
            # Gentle bob on NPCs
            if isinstance(sp, NPC):
                bob = int(math.sin(self.t * 2 + sp.rect.x) * 3)
                canvas.blit(sp.image,
                            (sp.rect.x + ox, sp.rect.y + bob + oy))
            else:
                canvas.blit(sp.image, (sp.rect.x + ox, sp.rect.y + oy))

        # Interact prompt
        for npc in self.npcs:
            if npc.is_within_interact_range(self.player.rect.center):
                self._draw_interact_prompt(canvas, npc)

        # HUD always on top
        self.hud.draw(canvas)

        if self.dialogue:
            self.dialogue.draw(canvas)

        if self.toast:
            self._draw_toast(canvas)

    # ---- ui helpers -----------------------------------------------------
    def _draw_interact_prompt(self, surface, npc) -> None:
        pulse = 0.5 + 0.5 * math.sin(self.t * 5)
        font = pygame.font.Font(None, 22)
        label = font.render(f"[E] Talk to {npc.name}", True, config.WHITE)
        pad = 16
        bg = pygame.Rect(0, 0, label.get_width() + pad * 2,
                         label.get_height() + 12)
        bg.midbottom = (npc.rect.centerx,
                        npc.rect.top - 12 - int(4 * pulse))
        # Background pill
        pygame.draw.rect(surface, (10, 16, 22), bg, border_radius=8)
        pygame.draw.rect(surface, config.TEAL, bg, width=2, border_radius=8)
        surface.blit(label, (bg.x + pad, bg.y + 6))
        # Small arrow under the pill pointing to NPC
        pygame.draw.polygon(surface, config.TEAL,
                            [(bg.centerx - 6, bg.bottom),
                             (bg.centerx + 6, bg.bottom),
                             (bg.centerx, bg.bottom + 6)])

    def _draw_toast(self, surface) -> None:
        font = pygame.font.Font(None, 24)
        label = font.render(self.toast, True, config.WHITE)
        bg = pygame.Rect(0, 0, label.get_width() + 40, label.get_height() + 22)
        bg.midtop = (surface.get_width() // 2, 78)
        # Alpha for fade in/out
        alpha = min(255, int(255 * min(1.0, self.toast_t / 0.6)))
        ts = pygame.Surface(bg.size, pygame.SRCALPHA)
        pygame.draw.rect(ts, (*config.TEAL_DEEP, alpha),
                         ts.get_rect(), border_radius=10)
        pygame.draw.rect(ts, (*config.TEAL, alpha),
                         ts.get_rect(), width=2, border_radius=10)
        surface.blit(ts, bg.topleft)
        label.set_alpha(alpha)
        surface.blit(label, (bg.x + 20, bg.y + 10))

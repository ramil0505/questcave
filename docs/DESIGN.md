# QuestCave - Architecture & Design

## Why this design?

The project intentionally separates three concerns:

1. **Engine plumbing** (`core/`) — game loop, scene stack, save/load. Knows nothing about RE or the cave theme. Replace Pygame with another engine and this layer stays largely the same.
2. **Gameplay systems** (`systems/`, `entities/`, `world/`) — what *the game* is. Player, NPCs, XP, quests, dialogue. Talks to engine via the Scene API.
3. **Learning content** (`challenges/`, `data/*.json`) — the RE part. Adding a new RE topic or new mini-game type touches only this layer.

This means a designer can add a new quest by editing `data/quests.json` without writing Python, and a developer can add a new mini-game type by writing one new file in `challenges/` and registering it.

## Scene stack

The scene manager is a **stack**, not a single slot. When the player enters a challenge from exploration, the challenge is *pushed on top*. When the challenge ends, it's popped and exploration resumes from exactly where it left off — no save / load gymnastics needed.

```
[ MainMenu ]
[ CharacterSelect ] - new game
[ CaveExplore     ] - main gameplay
[ CaveExplore | Challenge ] - during a challenge (Challenge on top)
```

## Challenge plug-in pattern

Every learning interaction is a `BaseChallenge` subclass that implements `handle_event / update / draw` and flips `self.completed = True` when solved. The registry (`challenges/registry.py`) maps a string name to a class. Quest data references the string. To add a new type:

```python
# 1. Create src/questcave/challenges/classify_reqs.py
from .base import BaseChallenge
class ClassifyReqsChallenge(BaseChallenge):
    NAME = "classify_reqs"
    def title(self): return "Classify the Requirements"
    def prompt(self): return "Click each card and assign a category."
    def handle_event(self, event): ...
    def update(self, dt):       ...
    def draw(self, surface):    ...

# 2. Register it in challenges/registry.py
from .classify_reqs import ClassifyReqsChallenge
REGISTRY[ClassifyReqsChallenge.NAME] = ClassifyReqsChallenge

# 3. Add quests in data/quests.json with "challenge_type": "classify_reqs"
```

## Save format

JSON, currently at `saves/savegame.json`. Schema is versioned (`SAVE_VERSION` in `core/save_load.py`). When you bump the schema, write a migration that handles old versions and produce v2 data.

## Where to extend next

In rough priority order, based on the planned scope and the formative usability test findings:

| Extension | File | Effort |
|-----------|------|--------|
| Classification mini-game (drop cards into category buckets) | new `challenges/classify_reqs.py` | low |
| MoSCoW prioritisation as ranked list, not card matching | new `challenges/moscow_rank.py` | medium |
| Ambiguity-hunt (click on the vague word in a sentence) | new `challenges/ambiguity_hunt.py` | medium |
| Multi-room cave with locked doors gated by badges earned | `world/cave_map.py` (new) + `CaveExploreScene` | medium |
| Pet companion that follows the player and reacts to wins | new `entities/pet.py` | low |
| Daily streak system with cave-decay loss aversion | new `systems/streak.py` | medium |
| Sound and music | `assets/sounds/` + a thin `audio.py` mixer | low |
| Sprite art replacing placeholder coloured rectangles | `assets/images/` + load in `Player.__init__` | low (with art) |
| Guild / co-op layer | networking layer, separate sprint | high |

## Mapping to the project lectures

The architecture deliberately mirrors the class model produced in Lecture-9 / Task 9 (Player, Cave Guardian, Quest, Cave Room, RE Challenge, Requirement Card, Solution Card, Reward, Knowledge Badge). Each of those classes has a code home:

| Class diagram entity | Where it lives |
|----------------------|----------------|
| Player | `entities/player.py` + `systems/progression.py` |
| Cave Guardian | `entities/npc.py::CaveGuardian` |
| Cave Room | `world/cave_room.py` |
| Quest | `systems/quests.py::Quest` + `data/quests.json` |
| RE Challenge | `challenges/base.py::BaseChallenge` |
| Requirement Card | `challenges/card_matching.py::DraggableCard` |
| Solution Card | `challenges/card_matching.py::SolutionSlot` |
| Reward | `systems/quests.py::QuestReward` |
| Knowledge Badge | `systems/progression.py::KnowledgeBadge` |

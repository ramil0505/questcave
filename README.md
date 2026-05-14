# QuestCave

A 2D top-down RPG serious game for learning **Requirements Engineering** (RE). Built with Python + Pygame.

Players descend into a procedurally-themed cave, meet a Cave Guardian mentor, accept quests, and solve interactive RE challenges (card matching, requirement classification, MoSCoW prioritisation) embedded directly in the game mechanics — not as multiple-choice quizzes. Progress earns XP, knowledge badges, and unlocks deeper cave levels.

This repository is the **playable MVP and architectural skeleton**. The vertical slice (main menu → cave exploration → meet Guardian → card-matching challenge → reward) works end-to-end. Additional challenge types, rooms, and content are added by dropping JSON data files and implementing new `Challenge` subclasses.

## Quick start

```bash
# 1. Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the game
python main.py
```

Tested on Python 3.10+ with Pygame 2.5+.

## Controls

| Input              | Action                                      |
|--------------------|---------------------------------------------|
| WASD or arrow keys | Move the player                             |
| E or Space         | Interact with nearby NPC / object           |
| Tab                | Open inventory / badge collection           |
| Esc                | Pause / open menu                           |
| Mouse drag         | Drag requirement cards in challenges        |
| Mouse click        | Click buttons, advance dialogue             |

## Project layout

```
questcave/
├── main.py                     Entry point — runs Game()
├── requirements.txt
├── README.md
├── data/                       JSON content (quests, cards, dialogue)
│   ├── quests.json
│   ├── cards.json
│   └── dialogue.json
├── assets/                     Sprites, fonts, sounds
└── src/questcave/
    ├── config.py               Constants (window, colours, paths)
    ├── core/                   Engine: game loop, scenes, save/load
    ├── entities/               Player, NPCs, pet companion
    ├── world/                  Cave rooms and map
    ├── systems/                Quests, progression (XP/levels), dialogue, badges
    ├── challenges/             RE learning mini-games (one per file)
    ├── ui/                     HUD, dialogue box, buttons
    ├── scenes/                 Main menu, exploration, challenge scenes
    └── utils/                  Helpers
```

## Architecture in one paragraph

`Game` owns the main loop and a `SceneManager` that swaps between `Scene` subclasses (menu, exploration, challenge). Each `Scene` handles its own input/update/draw. The `Player` and NPCs are Pygame Sprites that live inside a `CaveRoom`. When the player interacts with the Cave Guardian, a `Quest` is offered; accepting it launches a `Challenge` scene. Challenges are pluggable: each subclasses `BaseChallenge` and implements `update`, `draw`, and `check_solution`. The first one implemented is `CardMatchingChallenge`, which renders requirement cards the player can drag onto matching solution slots. Solving a challenge calls back into `ProgressionSystem` to award XP, possibly a `KnowledgeBadge`, and update the player's `cave_depth`.

## Adding new challenges

1. Create `src/questcave/challenges/your_challenge.py` subclassing `BaseChallenge`.
2. Implement `handle_event`, `update`, `draw`, and set `self.completed = True` on success.
3. Register it in `challenges/registry.py` so quest definitions can reference it by name.
4. Add a quest in `data/quests.json` that calls `"challenge_type": "your_challenge"`.

## Adding content without code

Edit `data/quests.json` to define new quests. Edit `data/cards.json` to add requirement cards. The game loads them at startup.

## Roadmap

The implemented MVP is the foundation. Items below are stubbed or pending — search `# TODO` in the code for extension points.

- [x] Game loop, scene manager, save/load
- [x] Player movement, collision, HUD
- [x] NPC dialogue system
- [x] Card-matching challenge
- [x] XP, level, and knowledge badges
- [ ] Classification challenge (functional vs non-functional)
- [ ] MoSCoW prioritisation challenge
- [ ] Ambiguity-hunt challenge
- [ ] Multi-room cave with progression gating
- [ ] Pet companion mechanic
- [ ] Guild / co-op layer
- [ ] Daily streak system with cave decay
- [ ] Sound and music

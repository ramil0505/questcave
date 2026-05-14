<div align="center">

# QuestCave

### A serious 2D RPG for learning Requirements Engineering

*Descend into the cave. Solve real RE challenges. Earn XP, gems, and Knowledge Badges.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Pygame](https://img.shields.io/badge/Pygame-2.5%2B-green.svg)](https://www.pygame.org/)
[![License](https://img.shields.io/badge/License-Academic-orange.svg)](#license)
[![Status](https://img.shields.io/badge/Status-Playable%20MVP-brightgreen.svg)](#)

<!-- HERO IMAGE — replace with screenshots/01_main_menu.png -->
<img src="screenshots/01_main_menu.png" alt="QuestCave main menu" width="800"/>

</div>

---

## About

**QuestCave** is a serious RPG built in Python + Pygame that teaches Requirements Engineering through actual gameplay — not multiple-choice quizzes. You play an explorer descending into an ancient cave, where a wise Cave Guardian gives you quests. Each quest is a hands-on interactive challenge: drag requirement cards onto solution slots, classify functional vs non-functional requirements, prioritise backlogs using MoSCoW, and more.

Built as a coursework project for **Riga Technical University**.

> **Note**: QuestCave is a learning game — the RE content is the point. Mechanics like drag-and-drop, XP, and cave depth exist to make the learning *stick*, not just decorate a quiz.

---

## Highlights

- **Real game mechanics, not quizzes.** Physically drag cards. Wrong drops bounce back; correct ones lock with a sparkle burst.
- **Three explorer classes** — Sage (+10% XP), Warrior (balanced), Rogue (extra gems).
- **Animated cave exploration** with flickering torches, ambient dust particles, footstep effects, NPC idle bobbing.
- **Three RE topics built-in**: Functional vs Non-functional, Stakeholder identification, MoSCoW prioritisation.
- **Modern UI**: gradient panels, glowing buttons with hover-scale, typewriter dialogue, confetti reward animations, screen shake on level-up.
- **Persistent progression** — XP, levels, gems, cave depth, Knowledge Badges. Auto-saves between sessions.
- **Pause menu and stats view** — see your badges, completed quests, and progress.
- **Responsive window** — resize freely; the cave room and HUD adapt.
- **Extensible by design** — add new RE challenges in one file; add new quests as JSON.

---

## Screenshots

<!-- Replace these with real screenshots after pushing. -->
<!-- Recommended size: 800–1200px wide, .png format -->

### Main menu — animated cave atmosphere
<img src="screenshots/01_main_menu.png" alt="Main menu" width="800"/>

### Choose your explorer class
<img src="screenshots/02_character_select.png" alt="Character select" width="800"/>

### Explore the cave with a modern HUD
<img src="screenshots/03_cave_explore.png" alt="Cave exploration" width="800"/>

### Drag-and-drop RE challenges
<img src="screenshots/04_challenge.png" alt="Card matching challenge" width="800"/>

### Quest complete — confetti and rewards
<img src="screenshots/05_reward.png" alt="Reward overlay" width="800"/>

### Track your progress and Knowledge Badges
<img src="screenshots/06_stats.png" alt="Stats and badges view" width="800"/>

---

## Quick start

### Prerequisites
- **Python 3.10 or newer** ([python.org](https://www.python.org/downloads/) — during install, tick **"Add Python to PATH"**)
- **Windows / macOS / Linux** — Pygame supports all three

### Installation (Windows PowerShell)

```powershell
# 1. Clone the repository
git clone https://github.com/YOUR-USERNAME/questcave.git
cd questcave

# 2. Create a virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the game
python main.py
```

### Installation (macOS / Linux)

```bash
git clone https://github.com/YOUR-USERNAME/questcave.git
cd questcave
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

---

## How to play

| Input              | Action                                       |
|--------------------|----------------------------------------------|
| **WASD** / Arrows  | Move the player                              |
| **E** / Space      | Interact with the Cave Guardian              |
| **Mouse drag**     | Drag requirement cards in challenges         |
| **Tab**            | Open stats and badges view                   |
| **Esc**            | Pause menu / return to title                 |
| **Mouse click**    | Activate buttons; advance dialogue           |

**Goal**: Talk to the Cave Guardian, accept a quest, solve the RE challenge it presents, and earn rewards. Each completed quest takes you one level deeper into the cave.

---

## Project structure

```
questcave/
├── main.py                       Entry point — run this
├── requirements.txt              pygame only
├── README.md
├── .gitignore
├── data/                         Game content (no code required to extend)
│   ├── quests.json               3 RE quests with rewards
│   └── dialogue.json             NPC dialogue trees
├── docs/
│   └── DESIGN.md                 Architecture and extension guide
├── assets/                       Sprites, fonts, sounds (drop assets here)
├── tests/                        Unit and regression tests
│   ├── test_progression.py
│   └── test_quest_rewards.py
└── src/questcave/
    ├── config.py                 All constants — palette, sizes, paths
    ├── core/                     Game loop, scenes, save/load
    ├── entities/                 Player, NPCs, Cave Guardian
    ├── world/                    Cave rooms, map
    ├── systems/                  Progression, quests, dialogue, badges
    ├── challenges/               RE learning mini-games
    │   └── card_matching.py      The drag-and-drop matching mechanic
    ├── ui/                       HUD, buttons, dialogue box, panels
    ├── scenes/                   Menu, character select, explore, challenge
    └── utils/                    Easing, tweens, particles, screen effects
```

---

## Tech stack

- **Python 3.10+**
- **Pygame 2.5+** — 2D rendering, input, audio (audio currently silent)
- **JSON** — quest definitions, dialogue, save game
- **pytest** — automated tests (run with `python -m pytest tests/ -v`)

No other dependencies. The whole project is one `pip install` from running.

---

## Adding your own content

### Add a quest without writing code

Edit `data/quests.json`. Each quest specifies which challenge type to launch and what data to feed it. Example:

```json
{
  "quest_id": "Q004_my_quest",
  "title": "My new quest",
  "re_topic": "Stakeholder analysis",
  "description": "Tell the story shown to the player here.",
  "challenge_type": "card_matching",
  "challenge_data": {
    "pairs": [
      { "requirement": "...", "solution": "...", "explanation": "..." }
    ]
  },
  "reward": { "xp": 100, "gems": 15, "badge_id": "BADGE_NEW" }
}
```

### Add a new challenge type

1. Create `src/questcave/challenges/your_challenge.py` subclassing `BaseChallenge`
2. Implement `handle_event`, `update`, `draw`, set `self.completed = True` on success
3. Register it in `src/questcave/challenges/registry.py`
4. Reference it from a quest in `data/quests.json` via `challenge_type`

See `docs/DESIGN.md` for the full pattern with examples.

---

## Roadmap

- [x] Game loop, scene manager, save/load
- [x] Player movement, collision, HUD with animated XP bar
- [x] NPC dialogue with typewriter effect
- [x] Drag-and-drop card matching challenge
- [x] XP, levels, gems, knowledge badges
- [x] Reward animation with confetti and screen flash
- [x] Pause menu and stats view
- [x] Resizable window
- [ ] Classification challenge (functional vs non-functional bins)
- [ ] MoSCoW prioritisation as a ranked list
- [ ] Ambiguity-hunt challenge (click vague words in a sentence)
- [ ] Multi-room cave with locked doors gated by badges
- [ ] Daily streak with cave-decay loss aversion
- [ ] Sound effects and ambient music
- [ ] Sprite art replacing placeholder shapes
- [ ] Leaderboard scene (see Figma reference)

---

## Tests

```powershell
python -m pytest tests/ -v
```

9 tests covering progression math, quest reward idempotency, and the spam-click reward bug.

---

## Credits

- **Game design & code**: Bahram and the QuestCave Team
- **Built for**: Requirements Engineering coursework, Riga Technical University, 2026
- **Engine**: [Pygame](https://www.pygame.org/)
- **Inspiration**: Octalysis gamification framework, Hero's Journey narrative arc

---

## License

This project is built as academic coursework. Code may be reused for educational purposes. Please credit the author and Riga Technical University.

---

<div align="center">

**Found a bug or have a quest idea?** Open an issue or pull request.

*Made for learning. Played for fun.*

</div>

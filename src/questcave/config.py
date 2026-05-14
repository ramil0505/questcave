"""Game-wide constants. Tweak here, don't sprinkle magic numbers in the code."""
from pathlib import Path

# --- Window ------------------------------------------------------------------
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_MIN_WIDTH = 960
WINDOW_MIN_HEIGHT = 540
WINDOW_TITLE = "QuestCave"
FPS = 60
ALLOW_RESIZE = True

# --- Paths -------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
DATA_DIR = PROJECT_ROOT / "data"
SAVE_DIR = PROJECT_ROOT / "saves"
SAVE_DIR.mkdir(exist_ok=True)
SAVE_FILE = SAVE_DIR / "savegame.json"
SETTINGS_FILE = SAVE_DIR / "settings.json"

# --- Modern colour palette ---------------------------------------------------
BLACK = (8, 10, 14)
CAVE_DARK = (16, 24, 32)
CAVE_DARKER = (10, 16, 22)
CAVE_FLOOR = (44, 58, 68)
CAVE_FLOOR_LIGHT = (54, 70, 82)
CAVE_WALL = (24, 36, 44)
CAVE_WALL_DARK = (14, 22, 28)
CAVE_GLOW = (90, 200, 180)

TEAL = (45, 212, 191)
TEAL_BRIGHT = (94, 234, 212)
TEAL_DARK = (15, 118, 110)
TEAL_DEEP = (8, 80, 76)

GOLD = (251, 191, 36)
GOLD_BRIGHT = (253, 224, 71)
GOLD_DEEP = (180, 130, 20)
PURPLE = (167, 139, 250)
PURPLE_DEEP = (109, 40, 217)
CORAL = (251, 113, 90)
RED = (239, 68, 68)
GREEN = (34, 197, 94)
GREEN_BRIGHT = (74, 222, 128)
BLUE = (96, 165, 250)

WHITE = (245, 247, 250)
OFF_WHITE = (220, 224, 228)
LIGHT_GRAY = (180, 188, 196)
GRAY = (110, 120, 130)
DARK_GRAY = (50, 58, 66)
DARKER_GRAY = (32, 38, 44)

COLOR_BG = CAVE_DARK
COLOR_TEXT = WHITE
COLOR_TEXT_MUTED = LIGHT_GRAY
COLOR_ACCENT = TEAL
COLOR_HUD_BG = (12, 18, 24)
COLOR_HUD_BG_TOP = (18, 28, 36)
COLOR_XP_BAR = TEAL
COLOR_HEALTH_BAR = CORAL
COLOR_PANEL = (24, 34, 42)
COLOR_PANEL_TOP = (32, 44, 54)
COLOR_PANEL_BORDER = (60, 80, 92)

# --- Player ------------------------------------------------------------------
PLAYER_SPEED = 240
PLAYER_SIZE = 36
PLAYER_INTERACT_RADIUS = 70

XP_PER_LEVEL_BASE = 100
XP_PER_LEVEL_GROWTH = 1.4

EXPLORER_CLASSES = {
    "Sage":    {"colour": (118, 168, 220), "xp_bonus": 1.10,
                "blurb": "Analytical mind. +10% XP from challenges.",
                "icon": "S"},
    "Warrior": {"colour": (220, 118, 118), "xp_bonus": 1.00,
                "blurb": "Steady and bold. Standard XP rate.",
                "icon": "W"},
    "Rogue":   {"colour": (170, 200, 100), "xp_bonus": 1.00,
                "blurb": "Crafty. Earns extra gems on success.",
                "icon": "R"},
}

# --- Cave ---------------------------------------------------------------------
TILE_SIZE = 48
ROOM_COLS = 24
ROOM_ROWS = 13

# --- Challenge ----------------------------------------------------------------
CARD_WIDTH = 280
CARD_HEIGHT = 80
CARD_MARGIN = 16

# --- Fonts -------------------------------------------------------------------
FONT_DEFAULT = None
FONT_TITLE_SIZE = 64
FONT_HEADING_SIZE = 34
FONT_SUBHEADING_SIZE = 24
FONT_BODY_SIZE = 20
FONT_SMALL_SIZE = 14

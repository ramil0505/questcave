"""QuestCave entry point.

Run with: python main.py
"""
import sys
from pathlib import Path

# Make `src` importable so we can use `from questcave...` everywhere.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from questcave.core.game import Game


def main() -> None:
    Game().run()


if __name__ == "__main__":
    main()

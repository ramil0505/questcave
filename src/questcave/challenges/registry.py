"""Maps challenge_type strings (from quests.json) to challenge classes.

Add new challenges here so quest data can reference them by name.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Type

from .base import BaseChallenge
from .card_matching import CardMatchingChallenge


REGISTRY: Dict[str, Type[BaseChallenge]] = {
    CardMatchingChallenge.NAME: CardMatchingChallenge,
    # TODO: register classification, prioritisation, ambiguity_hunt as you add them.
}


def create_challenge(challenge_type: str,
                     data: Dict[str, Any]) -> Optional[BaseChallenge]:
    cls = REGISTRY.get(challenge_type)
    if cls is None:
        return None
    return cls(data)

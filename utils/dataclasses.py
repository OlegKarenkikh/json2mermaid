# utils/dataclasses.py v5.2
"""Data classes for intent classification"""

from dataclasses import dataclass
from typing import Optional, List

@dataclass
class IntentClassification:
    """Classification result for an intent"""
    intent_id: str
    intent_type: str
    subtype: Optional[str] = None
    confidence: float = 1.0
    reasons: List[str] = None
    
    def __post_init__(self):
        if self.reasons is None:
            self.reasons = []

@dataclass
class Transition:
    """Transition between intents"""
    source_id: str
    target_id: str
    transition_type: str  # redirect, button, etc.
    condition: Optional[str] = None

@dataclass
class SlotInfo:
    """Slot information"""
    slot_id: str
    slot_type: str
    required: bool = False
    default_value: Optional[str] = None

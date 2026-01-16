# utils/analyzers.py v5.2
"""Intent analysis - 4-pass system"""

from typing import Dict, List, Any
from collections import defaultdict
from .dataclasses import IntentClassification, Transition

def first_pass(intents: List[Dict]) -> Dict[str, Any]:
    """
    First pass: Basic classification
    Classify intents by record_type and basic patterns
    """
    print("\n[1/4] First pass: Basic classification...")
    
    classifications = {}
    transitions = []
    
    for intent in intents:
        intent_id = intent.get('intent_id', 'unknown')
        record_type = str(intent.get('record_type', '')).lower()
        title = str(intent.get('title', '')).lower()
        
        # Basic classification
        if 'main' in record_type or 'regexp_main' in record_type:
            intent_type = 'main_intent'
        elif 'match' in record_type:
            intent_type = 'match_intent'
        elif 'viber' in record_type or 'telegram' in record_type:
            intent_type = 'messenger_intent'
        elif 'fallback' in title or 'error' in title:
            intent_type = 'fallback_intent'
        else:
            intent_type = 'dialog_intent'
        
        classifications[intent_id] = IntentClassification(
            intent_id=intent_id,
            intent_type=intent_type
        )
        
        # Extract redirects
        for answer in intent.get('answers', []):
            for button in answer.get('buttons', []):
                action = button.get('action', {})
                if action.get('type') == 'REDIRECT_TO_INTENT':
                    target_id = action.get('intent_id', '')
                    if target_id:
                        transitions.append(Transition(
                            source_id=intent_id,
                            target_id=target_id,
                            transition_type='button_redirect'
                        ))
    
    print(f"   Classified {len(classifications)} intents")
    print(f"   Found {len(transitions)} transitions")
    
    return {
        'classifications': classifications,
        'transitions': transitions
    }

def second_pass(intents: List[Dict], all_data: Dict) -> Dict:
    """
    Second pass: Subtype classification
    Identify domain-specific subtypes
    """
    print("\n[2/4] Second pass: Subtype classification...")
    
    classifications = all_data['classifications']
    subtype_keywords = {
        'insurance': ['осаго', 'каско', 'дмс', 'полис', 'страх'],
        'loyalty': ['бонус', 'скидка', 'программа лояльности'],
        'personal_cabinet': ['личный кабинет', 'lk', 'профиль'],
        'mobile_app': ['приложение', 'app', 'мобильн'],
        'payment': ['оплат', 'платеж', 'payment']
    }
    
    for intent in intents:
        intent_id = intent.get('intent_id', '')
        title = str(intent.get('title', '')).lower()
        topics = [str(t).lower() for t in intent.get('topics', [])]
        combined = f"{title} {' '.join(topics)}"
        
        # Find matching subtype
        for subtype, keywords in subtype_keywords.items():
            if any(kw in combined for kw in keywords):
                if intent_id in classifications:
                    classifications[intent_id].subtype = subtype
                    break
    
    subtypes_found = sum(1 for c in classifications.values() if c.subtype)
    print(f"   Assigned {subtypes_found} subtypes")
    
    return all_data

def third_pass(intents: List[Dict], all_data: Dict) -> Dict:
    """
    Third pass: Extract slots and entities
    """
    print("\n[3/4] Third pass: Slot extraction...")
    
    slots_by_intent = defaultdict(list)
    
    for intent in intents:
        intent_id = intent.get('intent_id', '')
        slot_ids = intent.get('slot_ids', [])
        
        if slot_ids and isinstance(slot_ids, list):
            slots_by_intent[intent_id] = slot_ids
    
    all_data['slots'] = dict(slots_by_intent)
    print(f"   Extracted slots from {len(slots_by_intent)} intents")
    
    return all_data

def fourth_pass(intents: List[Dict], all_data: Dict) -> Dict:
    """
    Fourth pass: Calculate statistics
    """
    print("\n[4/4] Fourth pass: Statistics...")
    
    stats = {
        'total_intents': len(intents),
        'total_transitions': len(all_data['transitions']),
        'intents_with_slots': len(all_data.get('slots', {})),
        'type_distribution': defaultdict(int),
        'subtype_distribution': defaultdict(int)
    }
    
    for classification in all_data['classifications'].values():
        stats['type_distribution'][classification.intent_type] += 1
        if classification.subtype:
            stats['subtype_distribution'][classification.subtype] += 1
    
    all_data['statistics'] = dict(stats)
    print(f"   Statistics calculated")
    
    return all_data

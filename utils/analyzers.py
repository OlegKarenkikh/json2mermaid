# utils/analyzers.py v5.3
"""Интент анализ - 4-проходная система"""

from typing import Dict, List, Any
from collections import defaultdict
from .dataclasses import IntentClassification, Transition

def _safe_list(value: Any, default: List = None) -> List:
    """
    Безопасное преобразование в список
    Обрабатывает NaN, None, float и другие невалидные значения
    """
    if default is None:
        default = []
    
    # Проверяем на NaN (float)
    if isinstance(value, float):
        import math
        if math.isnan(value):
            return default
    
    # Проверяем на None
    if value is None:
        return default
    
    # Если уже список
    if isinstance(value, list):
        return value
    
    # Все остальное - возвращаем default
    return default

def _extract_transitions(intent: Dict) -> List[Transition]:
    """
    Извлечение всех типов переходов из интента
    """
    transitions = []
    intent_id = intent.get('intent_id', 'unknown')
    
    # 1. Прямой redirect_to
    redirect_to = intent.get('redirect_to')
    if redirect_to and isinstance(redirect_to, str):
        transitions.append(Transition(
            source_id=intent_id,
            target_id=redirect_to,
            transition_type='direct_redirect'
        ))
    
    # 2. Fallback intent
    fallback_intent = intent.get('fallback_intent')
    if fallback_intent and isinstance(fallback_intent, str):
        transitions.append(Transition(
            source_id=intent_id,
            target_id=fallback_intent,
            transition_type='fallback'
        ))
    
    # 3. Переходы из answers
    answers = _safe_list(intent.get('answers', []))
    for answer in answers:
        if not isinstance(answer, dict):
            continue
        
        # 3a. Answer-level redirect
        answer_redirect = answer.get('redirect_to')
        if answer_redirect and isinstance(answer_redirect, str):
            transitions.append(Transition(
                source_id=intent_id,
                target_id=answer_redirect,
                transition_type='answer_redirect'
            ))
        
        # 3b. Переходы из кнопок
        buttons = _safe_list(answer.get('buttons', []))
        for button in buttons:
            if not isinstance(button, dict):
                continue
            
            action = button.get('action', {})
            if not isinstance(action, dict):
                continue
            
            action_type = action.get('type', '')
            
            # REDIRECT_TO_INTENT
            if action_type == 'REDIRECT_TO_INTENT':
                target_id = action.get('intent_id', '')
                if target_id:
                    transitions.append(Transition(
                        source_id=intent_id,
                        target_id=target_id,
                        transition_type='button_redirect'
                    ))
            
            # URL with redirect parameter
            elif action_type == 'URL':
                url = action.get('url', '')
                # Можно добавить парсинг intent_id из URL
                pass
    
    # 4. Условные переходы из slot_fillers
    slot_fillers = _safe_list(intent.get('slot_fillers', []))
    for filler in slot_fillers:
        if not isinstance(filler, dict):
            continue
        
        # Условия
        conditions = _safe_list(filler.get('conditions', []))
        for condition in conditions:
            if not isinstance(condition, dict):
                continue
            
            # then_redirect
            then_redirect = condition.get('then_redirect')
            if then_redirect and isinstance(then_redirect, str):
                transitions.append(Transition(
                    source_id=intent_id,
                    target_id=then_redirect,
                    transition_type='conditional_redirect'
                ))
            
            # else_redirect
            else_redirect = condition.get('else_redirect')
            if else_redirect and isinstance(else_redirect, str):
                transitions.append(Transition(
                    source_id=intent_id,
                    target_id=else_redirect,
                    transition_type='conditional_redirect'
                ))
    
    # 5. Intent matching (для match-интентов)
    matched_intent = intent.get('matched_intent_id')
    if matched_intent and isinstance(matched_intent, str):
        transitions.append(Transition(
            source_id=intent_id,
            target_id=matched_intent,
            transition_type='intent_match'
        ))
    
    return transitions

def first_pass(intents: List[Dict]) -> Dict[str, Any]:
    """
    First pass: Basic classification
    Classify intents by record_type and basic patterns
    """
    print("\n[1/4] First pass: Basic classification...")
    
    classifications = {}
    all_transitions = []
    
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
        
        # Извлечение всех переходов
        intent_transitions = _extract_transitions(intent)
        all_transitions.extend(intent_transitions)
    
    # Удаление дубликатов
    unique_transitions = []
    seen = set()
    for t in all_transitions:
        key = (t.source_id, t.target_id, t.transition_type)
        if key not in seen:
            seen.add(key)
            unique_transitions.append(t)
    
    print(f"   Classified {len(classifications)} intents")
    print(f"   Found {len(unique_transitions)} unique transitions")
    if len(all_transitions) != len(unique_transitions):
        print(f"   (удалено {len(all_transitions) - len(unique_transitions)} дубликатов)")
    
    # Статистика по типам переходов
    transition_types = defaultdict(int)
    for t in unique_transitions:
        transition_types[t.transition_type] += 1
    
    if transition_types:
        print(f"   Типы переходов:")
        for ttype, count in sorted(transition_types.items(), key=lambda x: -x[1]):
            print(f"      {ttype}: {count}")
    
    return {
        'classifications': classifications,
        'transitions': unique_transitions
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
        
        # Безопасно получаем topics (может быть NaN/float)
        topics_raw = intent.get('topics', [])
        topics = [str(t).lower() for t in _safe_list(topics_raw)]
        
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
        slot_ids_raw = intent.get('slot_ids', [])
        slot_ids = _safe_list(slot_ids_raw)
        
        if slot_ids:
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

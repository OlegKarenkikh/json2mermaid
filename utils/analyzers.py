# utils/analyzers.py v5.4
"""Интент анализ - 4-проходная система с расширенным извлечением переходов"""

import re
from typing import Dict, List, Any, Optional
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

def _extract_redirect_from_text(answer_text: str) -> List[str]:
    """
    Извлекает различные команды редиректа из текста ответа.
    Поддерживаемые форматы:
    - REDIRECT_TO_INTENT <intent_id>
    - GOTO <intent_id>
    - JUMP_TO <intent_id>
    - /goto <intent_id>
    """
    if not answer_text:
        return []
    
    redirects = []
    
    # REDIRECT_TO_INTENT command
    pattern1 = r'REDIRECT_TO_INTENT\s+(\S+)'
    redirects.extend(re.findall(pattern1, answer_text))
    
    # GOTO command
    pattern2 = r'(?:^|\s)GOTO\s+(\S+)'
    redirects.extend(re.findall(pattern2, answer_text, re.IGNORECASE))
    
    # JUMP_TO command
    pattern3 = r'JUMP_TO\s+(\S+)'
    redirects.extend(re.findall(pattern3, answer_text, re.IGNORECASE))
    
    # /goto command (slash command)
    pattern4 = r'/goto\s+(\S+)'
    redirects.extend(re.findall(pattern4, answer_text, re.IGNORECASE))
    
    # CALL_INTENT
    pattern5 = r'CALL_INTENT\s+(\S+)'
    redirects.extend(re.findall(pattern5, answer_text, re.IGNORECASE))
    
    return redirects


def _extract_buttons_from_markdown(answer_text: str) -> List[Dict[str, str]]:
    """
    Извлекает кнопки из markdown формата в тексте ответа
    Формат: [Текст кнопки](type:action action:intent_id)
    """
    if not answer_text:
        return []
    
    buttons = []
    # Паттерн для markdown кнопок: [текст](type:action action:action_id)
    pattern = r'\[([^\]]+)\]\(type:action\s+action:([^\)]+)\)'
    matches = re.findall(pattern, answer_text)
    
    for text, action_id in matches:
        buttons.append({
            'text': text.strip(),
            'action_id': action_id.strip()
        })
    
    return buttons


def _format_slot_condition(slots: List[Dict]) -> str:
    """
    Форматирует условие слотов для отображения
    """
    if not slots:
        return ""
    
    conditions = []
    for slot in slots:
        slot_id = slot.get('slot_id', '')
        values = slot.get('values', [])
        if slot_id and values:
            val_str = ','.join(str(v) for v in values[:2])
            if len(values) > 2:
                val_str += '...'
            conditions.append(f"{slot_id}={val_str}")
    
    return ' AND '.join(conditions) if conditions else ""


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
        
        answer_text = answer.get('answer', '')
        slots = _safe_list(answer.get('slots', []))
        slot_condition = _format_slot_condition(slots)
        
        # 3a. Answer-level redirect
        answer_redirect = answer.get('redirect_to')
        if answer_redirect and isinstance(answer_redirect, str):
            transitions.append(Transition(
                source_id=intent_id,
                target_id=answer_redirect,
                transition_type='answer_redirect',
                condition=slot_condition if slot_condition else None
            ))
        
        # 3b. REDIRECT_TO_INTENT из текста ответа (НОВОЕ!)
        text_redirects = _extract_redirect_from_text(answer_text)
        for target in text_redirects:
            transitions.append(Transition(
                source_id=intent_id,
                target_id=target,
                transition_type='text_redirect',
                condition=slot_condition if slot_condition else None
            ))
        
        # 3c. Кнопки из markdown в тексте ответа (НОВОЕ!)
        markdown_buttons = _extract_buttons_from_markdown(answer_text)
        for btn in markdown_buttons:
            transitions.append(Transition(
                source_id=intent_id,
                target_id=btn['action_id'],
                transition_type='button_action',
                condition=f"button: {btn['text']}"
            ))
        
        # 3d. Переходы из кнопок (структурированные данные)
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
        
        # 3e. Actions из ответа (НОВОЕ!)
        actions = _safe_list(answer.get('actions', []))
        for action in actions:
            if not isinstance(action, dict):
                continue
            
            action_id = action.get('action_id', '')
            action_text = action.get('action_text', '')
            if action_id:
                # Actions - это потенциальные переходы к другим интентам
                transitions.append(Transition(
                    source_id=intent_id,
                    target_id=action_id,
                    transition_type='action_redirect',
                    condition=f"action: {action_text}" if action_text else None
                ))
    
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


def _safe_str(value: Any, default: str = '') -> str:
    """
    Безопасное преобразование в строку.
    Обрабатывает NaN, None, float и другие невалидные значения.
    """
    if value is None:
        return default
    
    # Проверяем на NaN (float)
    if isinstance(value, float):
        import math
        if math.isnan(value):
            return default
        return str(value)
    
    # Для строк - просто возвращаем
    if isinstance(value, str):
        return value
    
    # Все остальное - преобразуем в строку
    try:
        return str(value)
    except Exception:
        return default


def build_intent_mappings(intents: List[Dict]) -> Dict[str, Dict]:
    """
    Строит маппинги для разрешения связей между интентами.
    
    Returns:
        {
            'by_intent_id': {intent_id: intent},
            'by_symbol_code': {symbol_code: intent},
            'by_action_id': {action_id: intent},
            'symbol_to_intent': {symbol_code: intent_id},
            'action_to_intent': {action_id: intent_id},
        }
    """
    mappings = {
        'by_intent_id': {},
        'by_symbol_code': {},
        'symbol_to_intent': {},
        'action_to_intent': {},
        'all_intent_ids': set(),
        'all_symbol_codes': set(),
    }
    
    for intent in intents:
        intent_id = _safe_str(intent.get('intent_id'), '')
        symbol_code = _safe_str(intent.get('symbol_code'), '')
        
        if intent_id:
            mappings['by_intent_id'][intent_id] = intent
            mappings['all_intent_ids'].add(intent_id)
        
        if symbol_code:
            mappings['by_symbol_code'][symbol_code] = intent
            mappings['all_symbol_codes'].add(symbol_code)
            if intent_id:
                mappings['symbol_to_intent'][symbol_code] = intent_id
        
        # Также собираем action_id -> intent_id маппинг
        # (action_id из кнопок может ссылаться на symbol_code или intent_id)
        answers = _safe_list(intent.get('answers', []))
        for answer in answers:
            if not isinstance(answer, dict):
                continue
            actions = _safe_list(answer.get('actions', []))
            for action in actions:
                if isinstance(action, dict):
                    action_id = action.get('action_id', '')
                    if action_id and intent_id:
                        # Если action_id совпадает с symbol_code этого интента
                        if action_id == symbol_code:
                            mappings['action_to_intent'][action_id] = intent_id
    
    return mappings


def resolve_target_id(target: str, mappings: Dict) -> str:
    """
    Разрешает идентификатор цели в intent_id.
    Проверяет: intent_id -> symbol_code -> action_id
    """
    if not target:
        return target
    
    # Если это уже intent_id
    if target in mappings.get('all_intent_ids', set()):
        return target
    
    # Если это symbol_code
    if target in mappings.get('symbol_to_intent', {}):
        return mappings['symbol_to_intent'][target]
    
    # Если это action_id
    if target in mappings.get('action_to_intent', {}):
        return mappings['action_to_intent'][target]
    
    # Не найдено - возвращаем как есть (внешняя цель)
    return target


def extract_detailed_flow(intent: Dict) -> Dict[str, Any]:
    """
    Извлекает полную логику обработки интента включая:
    - Условия входа (regex)
    - Ветвления по слотам
    - Все возможные переходы
    """
    intent_id = _safe_str(intent.get('intent_id'), 'unknown')
    title = _safe_str(intent.get('title'), '')
    
    flow = {
        'intent_id': intent_id,
        'title': title,
        'record_type': _safe_str(intent.get('record_type'), ''),
        'entry_conditions': [],
        'branches': [],
        'transitions': []
    }
    
    # 1. Условия входа (regex из inputs)
    inputs = _safe_list(intent.get('inputs', []))
    for inp in inputs:
        if not isinstance(inp, dict):
            continue
        questions = _safe_list(inp.get('questions', []))
        for q in questions:
            if isinstance(q, dict):
                sentence = q.get('sentence', '')
                if sentence:
                    flow['entry_conditions'].append({
                        'type': 'regex' if sentence.startswith('/') else 'text',
                        'pattern': sentence
                    })
    
    # 2. Ветвления по ответам
    answers = _safe_list(intent.get('answers', []))
    for idx, answer in enumerate(answers):
        if not isinstance(answer, dict):
            continue
        
        answer_text = answer.get('answer', '')
        slots = _safe_list(answer.get('slots', []))
        
        branch = {
            'answer_id': answer.get('id', f'answer_{idx}'),
            'slot_conditions': [],
            'actions': [],
            'redirects': [],
            'buttons': []
        }
        
        # Условия слотов
        for slot in slots:
            if isinstance(slot, dict):
                branch['slot_conditions'].append({
                    'slot_id': slot.get('slot_id', ''),
                    'values': slot.get('values', [])
                })
        
        # Команды в тексте ответа
        if answer_text:
            # SET_SLOT_VALUE
            set_slots = re.findall(r'SET_SLOT_VALUE_(\S+)\s+(\S+)', answer_text)
            for slot_name, value in set_slots:
                branch['actions'].append({
                    'type': 'set_slot',
                    'slot': slot_name,
                    'value': value
                })
            
            # DELETE_SLOT_VALUE
            del_slots = re.findall(r'DELETE_SLOT_VALUE_(\S+)', answer_text)
            for slot_name in del_slots:
                branch['actions'].append({
                    'type': 'delete_slot',
                    'slot': slot_name
                })
            
            # REDIRECT_TO_INTENT
            redirects = _extract_redirect_from_text(answer_text)
            for r in redirects:
                branch['redirects'].append(r)
            
            # Кнопки из markdown
            buttons = _extract_buttons_from_markdown(answer_text)
            branch['buttons'] = buttons
        
        # Actions из ответа
        actions_list = _safe_list(answer.get('actions', []))
        for act in actions_list:
            if isinstance(act, dict):
                branch['buttons'].append({
                    'text': act.get('action_text', ''),
                    'action_id': act.get('action_id', '')
                })
        
        flow['branches'].append(branch)
    
    # 3. Все переходы
    flow['transitions'] = _extract_transitions(intent)
    
    return flow

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

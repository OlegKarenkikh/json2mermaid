#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Диагностика извлечения переходов из JSON файла.
Показывает какие переходы найдены и каких не хватает.
"""

import json
import sys
import os
import re
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def analyze_intent_structure(intent: dict, idx: int) -> dict:
    """Анализирует структуру одного интента."""
    result = {
        'index': idx,
        'intent_id': intent.get('intent_id', 'N/A'),
        'title': str(intent.get('title', ''))[:50],
        'record_type': intent.get('record_type', 'N/A'),
        'has_inputs': bool(intent.get('inputs')),
        'has_answers': bool(intent.get('answers')),
        'transitions_found': [],
        'potential_issues': []
    }
    
    # Проверяем redirect_to на уровне интента
    if intent.get('redirect_to'):
        result['transitions_found'].append(('direct_redirect', intent['redirect_to']))
    
    # Проверяем fallback_intent
    if intent.get('fallback_intent'):
        result['transitions_found'].append(('fallback', intent['fallback_intent']))
    
    # Анализируем answers
    answers = intent.get('answers', [])
    if not isinstance(answers, list):
        result['potential_issues'].append(f'answers is not a list: {type(answers)}')
        return result
    
    for ans_idx, answer in enumerate(answers):
        if not isinstance(answer, dict):
            result['potential_issues'].append(f'answer[{ans_idx}] is not a dict: {type(answer)}')
            continue
        
        answer_text = answer.get('answer', '')
        
        # 1. REDIRECT_TO_INTENT в тексте
        redirects = re.findall(r'REDIRECT_TO_INTENT\s+(\S+)', str(answer_text))
        for r in redirects:
            slots = answer.get('slots', [])
            slot_info = _format_slots(slots) if slots else ''
            result['transitions_found'].append(('text_redirect', r, slot_info))
        
        # 2. Кнопки в markdown
        buttons_md = re.findall(r'\[([^\]]+)\]\(type:action\s+action:([^\)]+)\)', str(answer_text))
        for text, action_id in buttons_md:
            result['transitions_found'].append(('button_markdown', action_id, text))
        
        # 3. actions массив
        actions = answer.get('actions', [])
        if isinstance(actions, list):
            for act in actions:
                if isinstance(act, dict):
                    action_id = act.get('action_id', '')
                    action_text = act.get('action_text', '')
                    if action_id:
                        result['transitions_found'].append(('action_array', action_id, action_text))
        
        # 4. buttons массив (структурированный)
        buttons = answer.get('buttons', [])
        if isinstance(buttons, list):
            for btn in buttons:
                if isinstance(btn, dict):
                    action = btn.get('action', {})
                    if isinstance(action, dict):
                        if action.get('type') == 'REDIRECT_TO_INTENT':
                            target = action.get('intent_id', '')
                            if target:
                                result['transitions_found'].append(('button_struct', target))
        
        # 5. redirect_to на уровне answer
        if answer.get('redirect_to'):
            result['transitions_found'].append(('answer_redirect', answer['redirect_to']))
    
    # Проверяем slot_fillers
    slot_fillers = intent.get('slot_fillers', [])
    if isinstance(slot_fillers, list):
        for filler in slot_fillers:
            if isinstance(filler, dict):
                conditions = filler.get('conditions', [])
                if isinstance(conditions, list):
                    for cond in conditions:
                        if isinstance(cond, dict):
                            if cond.get('then_redirect'):
                                result['transitions_found'].append(('slot_then', cond['then_redirect']))
                            if cond.get('else_redirect'):
                                result['transitions_found'].append(('slot_else', cond['else_redirect']))
    
    return result


def _format_slots(slots):
    """Форматирует условия слотов."""
    if not slots:
        return ''
    parts = []
    for s in slots[:2]:
        if isinstance(s, dict):
            slot_id = s.get('slot_id', '')
            values = s.get('values', [])
            if slot_id and values:
                parts.append(f"{slot_id}={values[0]}")
    return ' & '.join(parts)


def main():
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'intent_data.jsonl'
    
    print("=" * 80)
    print("🔍 ДИАГНОСТИКА ИЗВЛЕЧЕНИЯ ПЕРЕХОДОВ")
    print("=" * 80)
    print(f"Файл: {input_file}")
    print()
    
    if not os.path.exists(input_file):
        print(f"❌ Файл не найден: {input_file}")
        return 1
    
    # Загружаем данные
    intents = []
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            # Пробуем как JSON массив
            try:
                data = json.load(f)
                if isinstance(data, list):
                    intents = data
                elif isinstance(data, dict) and 'intents' in data:
                    intents = data['intents']
            except:
                # Пробуем как JSONL
                f.seek(0)
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        try:
                            obj = json.loads(line)
                            if isinstance(obj, dict):
                                intents.append(obj)
                        except:
                            pass
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        return 1
    
    print(f"✅ Загружено интентов: {len(intents)}")
    print()
    
    # Собираем все intent_id
    all_intent_ids = set()
    for intent in intents:
        iid = intent.get('intent_id', '')
        if iid:
            all_intent_ids.add(iid)
    
    print(f"📋 Уникальных intent_id: {len(all_intent_ids)}")
    print()
    
    # Анализируем каждый интент
    total_transitions = 0
    transition_types = defaultdict(int)
    internal_targets = set()
    external_targets = set()
    intents_with_transitions = 0
    intents_without_transitions = 0
    
    # Показываем примеры
    examples_with = []
    examples_without = []
    
    for idx, intent in enumerate(intents):
        analysis = analyze_intent_structure(intent, idx)
        
        if analysis['transitions_found']:
            intents_with_transitions += 1
            if len(examples_with) < 3:
                examples_with.append(analysis)
            
            for trans in analysis['transitions_found']:
                trans_type = trans[0]
                target = trans[1]
                transition_types[trans_type] += 1
                total_transitions += 1
                
                if target in all_intent_ids:
                    internal_targets.add(target)
                else:
                    external_targets.add(target)
        else:
            intents_without_transitions += 1
            if len(examples_without) < 3:
                examples_without.append(analysis)
        
        if analysis['potential_issues']:
            print(f"⚠️  Интент #{idx} ({analysis['intent_id'][:30]}...): {analysis['potential_issues']}")
    
    # Статистика
    print()
    print("=" * 80)
    print("📊 СТАТИСТИКА ПЕРЕХОДОВ")
    print("=" * 80)
    print(f"Всего переходов найдено: {total_transitions}")
    print(f"Интентов с переходами: {intents_with_transitions}")
    print(f"Интентов БЕЗ переходов: {intents_without_transitions}")
    print()
    
    print("📈 По типам переходов:")
    for trans_type, count in sorted(transition_types.items(), key=lambda x: -x[1]):
        print(f"   {trans_type}: {count}")
    
    print()
    print(f"🎯 Внутренние цели (есть в файле): {len(internal_targets)}")
    print(f"🔗 Внешние цели (НЕТ в файле): {len(external_targets)}")
    
    if external_targets:
        print("\n   Примеры внешних целей:")
        for ext in list(external_targets)[:10]:
            print(f"      - {ext}")
        if len(external_targets) > 10:
            print(f"      ... и ещё {len(external_targets) - 10}")
    
    # Примеры
    print()
    print("=" * 80)
    print("📝 ПРИМЕРЫ ИНТЕНТОВ С ПЕРЕХОДАМИ")
    print("=" * 80)
    for ex in examples_with:
        print(f"\n#{ex['index']} {ex['intent_id'][:40]}...")
        print(f"   Тип: {ex['record_type']}")
        print(f"   Переходы ({len(ex['transitions_found'])}):")
        for t in ex['transitions_found'][:5]:
            print(f"      - {t}")
        if len(ex['transitions_found']) > 5:
            print(f"      ... и ещё {len(ex['transitions_found']) - 5}")
    
    print()
    print("=" * 80)
    print("📝 ПРИМЕРЫ ИНТЕНТОВ БЕЗ ПЕРЕХОДОВ")
    print("=" * 80)
    for ex in examples_without[:3]:
        print(f"\n#{ex['index']} {ex['intent_id'][:40]}...")
        print(f"   Тип: {ex['record_type']}")
        print(f"   Title: {ex['title']}")
        print(f"   has_inputs: {ex['has_inputs']}, has_answers: {ex['has_answers']}")
    
    # Рекомендации
    print()
    print("=" * 80)
    print("💡 РЕКОМЕНДАЦИИ")
    print("=" * 80)
    
    if total_transitions == 0:
        print("❌ Переходы не найдены!")
        print("   Возможные причины:")
        print("   1. Другой формат данных - покажите пример вашего JSON")
        print("   2. Переходы задаются по-другому (не REDIRECT_TO_INTENT)")
        print("   3. Связи через symbol_code или другие поля")
    elif len(external_targets) > len(internal_targets):
        print("⚠️  Большинство целей - внешние (не в этом файле)")
        print("   Это нормально если у вас только часть интентов")
        print("   Диаграмма покажет связи, но целевые узлы будут жёлтыми")
    else:
        print("✅ Переходы найдены корректно")
        print(f"   Связность: {len(internal_targets)}/{len(all_intent_ids)} интентов связаны")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

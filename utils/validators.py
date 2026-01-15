# utils/validators.py v5.1
"""Comprehensive validation module with NaN handling"""

from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict
import json
import math

def is_nan_value(value: Any) -> bool:
    """Check if value is NaN (float, string 'NaN', None)"""
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, str) and value.upper() in ('NAN', 'NONE', 'NULL', ''):
        return True
    return False

def validate_intent_ids(intents: List[Dict]) -> Dict[str, Any]:
    """Validate uniqueness of intent_ids"""
    intent_ids = [i.get('intent_id') for i in intents if i.get('intent_id')]
    id_counts = defaultdict(int)
    for iid in intent_ids:
        id_counts[iid] += 1
    
    duplicates = {k: v for k, v in id_counts.items() if v > 1}
    result = {
        'total': len(intent_ids),
        'unique': len(id_counts),
        'duplicates': duplicates,
        'duplicate_count': len(duplicates),
        'is_valid': len(duplicates) == 0
    }
    
    if duplicates:
        print(f"❌ Дубликаты intent_id: {len(duplicates)}")
        for intent_id, count in list(duplicates.items())[:5]:
            print(f"   - {intent_id}: {count} раз")
    else:
        print(f"✅ Все intent_id уникальны ({len(intent_ids)})")
    
    return result

def validate_titles(intents: List[Dict]) -> Dict[str, Any]:
    """Validate title uniqueness and detect duplicates"""
    title_to_ids = defaultdict(list)
    
    for intent in intents:
        title = intent.get('title', '')
        intent_id = intent.get('intent_id', '')
        if title and not is_nan_value(title):
            title_to_ids[title].append(intent_id)
    
    duplicates = {title: ids for title, ids in title_to_ids.items() if len(ids) > 1}
    
    result = {
        'total_titles': len(title_to_ids),
        'duplicate_titles': duplicates,
        'duplicate_count': len(duplicates),
        'is_valid': len(duplicates) == 0
    }
    
    if duplicates:
        print(f"⚠️  Дубликаты title: {len(duplicates)}")
        for title, ids in list(duplicates.items())[:3]:
            print(f"   - '{title[:50]}...': {len(ids)} интентов")
    else:
        print(f"✅ Все title уникальны")
    
    return result

def validate_nan_fields(intents: List[Dict]) -> Dict[str, Any]:
    """Detect NaN values across all fields"""
    nan_stats = defaultdict(int)
    critical_fields = ['record_type', 'intent_settings', 'routing_params', 'answers', 'inputs']
    
    for intent in intents:
        intent_id = intent.get('intent_id', 'unknown')
        
        for field in critical_fields:
            value = intent.get(field)
            if is_nan_value(value):
                nan_stats[field] += 1
        
        # Check nested NaN in routing_params
        routing = intent.get('routing_params', {})
        if isinstance(routing, dict):
            for key in ['callcenters', 'languages', 'usergroups', 'skills']:
                if is_nan_value(routing.get(key)):
                    nan_stats[f'routing_params.{key}'] += 1
    
    total = len(intents)
    result = {
        'total_intents': total,
        'nan_by_field': dict(nan_stats),
        'nan_percentage': {k: round(v/total*100, 2) for k, v in nan_stats.items()},
        'is_valid': len(nan_stats) == 0
    }
    
    if nan_stats:
        print(f"⚠️  Обнаружены NaN значения:")
        for field, count in sorted(nan_stats.items(), key=lambda x: -x[1])[:5]:
            pct = round(count/total*100, 1)
            print(f"   - {field}: {count} ({pct}%)")
    else:
        print(f"✅ NaN значения отсутствуют")
    
    return result

def validate_empty_content(intents: List[Dict]) -> Dict[str, Any]:
    """Validate that intents have answers and inputs"""
    empty_answers = []
    empty_inputs = []
    
    for intent in intents:
        intent_id = intent.get('intent_id', 'unknown')
        
        answers = intent.get('answers', [])
        if not answers or len(answers) == 0:
            empty_answers.append(intent_id)
        
        inputs = intent.get('inputs', [])
        if not inputs or len(inputs) == 0:
            empty_inputs.append(intent_id)
    
    result = {
        'empty_answers': empty_answers,
        'empty_answers_count': len(empty_answers),
        'empty_inputs': empty_inputs,
        'empty_inputs_count': len(empty_inputs),
        'is_valid': len(empty_answers) == 0 and len(empty_inputs) == 0
    }
    
    if empty_answers:
        print(f"❌ Интенты без ответов: {len(empty_answers)}")
        for iid in empty_answers[:3]:
            print(f"   - {iid}")
    
    if empty_inputs:
        print(f"⚠️  Интенты без inputs: {len(empty_inputs)}")
    
    if not empty_answers and not empty_inputs:
        print(f"✅ Все интенты имеют answers и inputs")
    
    return result

def validate_redirects(intents: List[Dict]) -> Dict[str, Any]:
    """Validate REDIRECT_TO_INTENT targets exist"""
    import re
    
    all_ids = {i.get('intent_id') for i in intents}
    broken_redirects = []
    redirect_map = defaultdict(list)  # source -> [targets]
    
    for intent in intents:
        intent_id = intent.get('intent_id', 'unknown')
        
        for answer in intent.get('answers', []):
            answer_text = answer.get('answer', '')
            if isinstance(answer_text, str):
                matches = re.findall(r'REDIRECT_TO_INTENT\s+(\S+)', answer_text)
                for target in matches:
                    redirect_map[intent_id].append(target)
                    if target not in all_ids:
                        broken_redirects.append((intent_id, target))
    
    result = {
        'total_redirects': sum(len(v) for v in redirect_map.values()),
        'broken_redirects': broken_redirects,
        'broken_count': len(broken_redirects),
        'redirect_map': dict(redirect_map),
        'is_valid': len(broken_redirects) == 0
    }
    
    if broken_redirects:
        print(f"❌ Несуществующие redirect targets: {len(broken_redirects)}")
        for src, tgt in broken_redirects[:3]:
            print(f"   - {src} -> {tgt}")
    else:
        print(f"✅ Все redirects валидны")
    
    return result

def detect_circular_redirects(redirect_map: Dict[str, List[str]]) -> List[List[str]]:
    """Detect circular redirect chains"""
    cycles = []
    
    def dfs(node: str, path: List[str], visited: Set[str]) -> None:
        if node in path:
            cycle_start = path.index(node)
            cycle = path[cycle_start:] + [node]
            if cycle not in cycles:
                cycles.append(cycle)
            return
        
        if node in visited:
            return
        
        visited.add(node)
        path.append(node)
        
        for target in redirect_map.get(node, []):
            dfs(target, path.copy(), visited)
    
    for start_node in redirect_map.keys():
        dfs(start_node, [], set())
    
    return cycles

def run_all_validations(intents: List[Dict], all_data: Dict) -> Dict[str, Any]:
    """Run comprehensive validation suite"""
    print("\n" + "="*80)
    print("🔍 ВАЛИДАЦИЯ ДАННЫХ v5.1")
    print("="*80)
    
    results = {}
    
    # 1. Intent ID validation
    print("\n[1/6] Проверка intent_id...")
    results['intent_ids'] = validate_intent_ids(intents)
    
    # 2. Title validation
    print("\n[2/6] Проверка title...")
    results['titles'] = validate_titles(intents)
    
    # 3. NaN detection
    print("\n[3/6] Проверка NaN значений...")
    results['nan_fields'] = validate_nan_fields(intents)
    
    # 4. Empty content
    print("\n[4/6] Проверка пустых answers/inputs...")
    results['empty_content'] = validate_empty_content(intents)
    
    # 5. Redirects
    print("\n[5/6] Проверка redirects...")
    results['redirects'] = validate_redirects(intents)
    
    # 6. Circular redirects
    print("\n[6/6] Поиск циклических redirects...")
    redirect_map = results['redirects'].get('redirect_map', {})
    cycles = detect_circular_redirects(redirect_map)
    results['circular_redirects'] = {
        'cycles': cycles,
        'cycle_count': len(cycles),
        'is_valid': len(cycles) == 0
    }
    
    if cycles:
        print(f"⚠️  Обнаружены циклы: {len(cycles)}")
        for cycle in cycles[:3]:
            print(f"   - {' -> '.join(cycle)}")
    else:
        print(f"✅ Циклических redirects не обнаружено")
    
    # Summary
    error_count = sum([
        results['intent_ids']['duplicate_count'],
        results['redirects']['broken_count'],
        results['empty_content']['empty_answers_count']
    ])
    
    warning_count = sum([
        results['titles']['duplicate_count'],
        len(results['nan_fields']['nan_by_field']),
        results['circular_redirects']['cycle_count'],
        results['empty_content']['empty_inputs_count']
    ])
    
    results['summary'] = {
        'total_intents': len(intents),
        'error_count': error_count,
        'warning_count': warning_count,
        'is_valid': error_count == 0,
        'has_warnings': warning_count > 0
    }
    
    print("\n" + "="*80)
    print(f"📊 ИТОГИ ВАЛИДАЦИИ:")
    print(f"   Ошибок: {error_count}")
    print(f"   Предупреждений: {warning_count}")
    print("="*80 + "\n")
    
    return results

def save_validation_report(results: Dict[str, Any], output_dir: str):
    """Save detailed validation report"""
    import os
    from datetime import datetime
    
    report = {
        'validation_timestamp': datetime.now().isoformat(),
        'version': '5.1',
        'summary': results.get('summary', {}),
        'details': {
            'intent_ids': results.get('intent_ids', {}),
            'titles': results.get('titles', {}),
            'nan_fields': results.get('nan_fields', {}),
            'empty_content': results.get('empty_content', {}),
            'redirects': results.get('redirects', {}),
            'circular_redirects': results.get('circular_redirects', {})
        }
    }
    
    filepath = os.path.join(output_dir, 'validation_report.json')
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Отчёт валидации: {filepath}")

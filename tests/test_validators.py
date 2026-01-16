import pytest
from utils.validators import (
    validate_intent_ids,
    validate_titles,
    validate_nan_fields,
    validate_empty_content,
    validate_redirects,
    detect_circular_redirects,
    run_all_validations
)

def test_validate_intent_ids():
    intents = [
        {"intent_id": "1"},
        {"intent_id": "2"},
        {"intent_id": "1"} # Duplicate
    ]
    result = validate_intent_ids(intents)
    assert result['is_valid'] is False
    assert result['duplicate_count'] == 1
    assert "1" in result['duplicates']

def test_validate_titles():
    intents = [
        {"intent_id": "1", "title": "Title A"},
        {"intent_id": "2", "title": "Title B"},
        {"intent_id": "3", "title": "Title A"} # Duplicate
    ]
    result = validate_titles(intents)
    assert result['is_valid'] is False
    assert result['duplicate_count'] == 1
    assert "Title A" in result['duplicate_titles']

def test_validate_nan_fields():
    intents = [
        {"intent_id": "1", "record_type": "NaN"}, # NaN
        {"intent_id": "2", "record_type": "main"}
    ]
    result = validate_nan_fields(intents)
    assert result['is_valid'] is False
    assert result['nan_by_field']['record_type'] == 1

def test_validate_empty_content():
    intents = [
        {"intent_id": "1", "answers": [], "inputs": [{"questions": []}]}, # Empty answers
        {"intent_id": "2", "answers": [{"answer": "ok"}], "inputs": []}, # Empty inputs
        {"intent_id": "3", "answers": [{"answer": "ok"}], "inputs": [{"questions": []}]} # OK
    ]
    result = validate_empty_content(intents)
    assert result['is_valid'] is False
    assert "1" in result['empty_answers']
    assert "2" in result['empty_inputs']

def test_validate_redirects():
    intents = [
        {"intent_id": "1", "answers": [{"answer": "REDIRECT_TO_INTENT 2"}]}, # Valid
        {"intent_id": "2", "answers": [{"answer": "ok"}]},
        {"intent_id": "3", "answers": [{"answer": "REDIRECT_TO_INTENT 99"}]} # Broken
    ]
    result = validate_redirects(intents)
    assert result['is_valid'] is False
    assert result['broken_count'] == 1
    assert ("3", "99") in result['broken_redirects']

def test_detect_circular_redirects():
    redirect_map = {
        "1": ["2"],
        "2": ["3"],
        "3": ["1"], # Cycle: 1 -> 2 -> 3 -> 1
        "4": ["5"]
    }
    cycles = detect_circular_redirects(redirect_map)
    
    # После исправления алгоритма возвращается только 1 уникальный цикл
    # (без дубликатов с разных стартовых узлов)
    assert len(cycles) == 1
    
    # Проверяем что цикл содержит правильные узлы
    cycle = cycles[0]
    cycle_nodes = set(cycle[:-1])  # Убираем последний элемент (дубликат первого)
    assert cycle_nodes == {"1", "2", "3"}
    
    # Цикл должен заканчиваться тем же узлом, с которого начался
    assert cycle[0] == cycle[-1]


def test_detect_multiple_cycles():
    """Тест на обнаружение нескольких независимых циклов"""
    redirect_map = {
        "a": ["b"],
        "b": ["a"],  # Цикл 1: a -> b -> a
        "x": ["y"],
        "y": ["z"],
        "z": ["x"],  # Цикл 2: x -> y -> z -> x
    }
    cycles = detect_circular_redirects(redirect_map)
    
    assert len(cycles) == 2
    
    # Собираем узлы каждого цикла
    cycle_node_sets = [set(c[:-1]) for c in cycles]
    assert {"a", "b"} in cycle_node_sets
    assert {"x", "y", "z"} in cycle_node_sets

def test_run_all_validations(capsys):
    intents = [
        {"intent_id": "1", "title": "T1", "record_type": "main", "answers": [{"answer": "ok"}], "inputs": [{"questions": []}]},
        {"intent_id": "1", "title": "T2", "record_type": "main", "answers": [{"answer": "ok"}], "inputs": [{"questions": []}]} # Duplicate ID
    ]
    results = run_all_validations(intents, {})
    assert results['summary']['is_valid'] is False
    assert results['intent_ids']['is_valid'] is False

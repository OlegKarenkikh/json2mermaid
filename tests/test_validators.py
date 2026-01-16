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
        {"intent_id": "1", "title": "A"},
        {"intent_id": "1", "title": "B"},
        {"intent_id": "2", "title": "C"}
    ]
    result = validate_intent_ids(intents)
    assert result['is_valid'] is False
    assert result['duplicate_count'] == 1
    assert "1" in result['duplicates']

def test_validate_titles():
    intents = [
        {"intent_id": "1", "title": "Duplicate"},
        {"intent_id": "2", "title": "Duplicate"},
        {"intent_id": "3", "title": "Unique"}
    ]
    result = validate_titles(intents)
    assert result['is_valid'] is False
    assert result['duplicate_count'] == 1
    assert "Duplicate" in result['duplicate_titles']

def test_validate_nan_fields():
    intents = [
        {"intent_id": "1", "record_type": float("nan")},
        {"intent_id": "2", "record_type": "NaN"},
        {"intent_id": "3", "record_type": "valid"}
    ]
    result = validate_nan_fields(intents)
    assert result['is_valid'] is False
    assert result['nan_by_field']['record_type'] == 2

def test_validate_empty_content():
    intents = [
        {"intent_id": "1", "answers": [], "inputs": [{"questions": []}]},
        {"intent_id": "2", "answers": [{"answer": "text"}], "inputs": []},
        {"intent_id": "3", "answers": [{"answer": "text"}], "inputs": [{"questions": []}]}
    ]
    result = validate_empty_content(intents)
    assert result['is_valid'] is False
    assert "1" in result['empty_answers']
    assert "2" in result['empty_inputs']

def test_validate_redirects():
    intents = [
        {"intent_id": "1", "answers": [{"answer": "REDIRECT_TO_INTENT 2"}]},
        {"intent_id": "2", "answers": [{"answer": "REDIRECT_TO_INTENT 3"}]}
    ]
    result = validate_redirects(intents)
    assert result['is_valid'] is False
    assert len(result['broken_redirects']) == 1
    assert result['broken_redirects'][0] == ("2", "3")

def test_detect_circular_redirects():
    redirect_map = {
        "1": ["2"],
        "2": ["3"],
        "3": ["1"]
    }
    cycles = detect_circular_redirects(redirect_map)
    # The current implementation finds the same cycle starting from each node
    # So we expect 3 reported cycles for a loop of length 3
    assert len(cycles) == 3
    # Check that one of them is the expected sequence
    assert ["1", "2", "3", "1"] in cycles or ["2", "3", "1", "2"] in cycles

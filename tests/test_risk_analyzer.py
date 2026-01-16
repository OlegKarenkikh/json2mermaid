import pytest
from utils.risk_analyzer import (
    analyze_intent_risks,
    RiskSeverity,
    RiskType
)

def test_analyze_intent_risks_critical():
    intents = [{"intent_id": "1", "title": "Test"}]
    validation_results = {
        'intent_ids': {'duplicates': {'1': 2}},
        'empty_content': {'empty_answers': ['1']},
        'redirects': {'broken_redirects': [('1', '2')]}
    }

    risks = analyze_intent_risks(intents, validation_results)

    assert "1" in risks
    assert risks["1"].severity == RiskSeverity.CRITICAL
    risk_types = [r[0] for r in risks["1"].risks]
    assert RiskType.DUPLICATE_ID in risk_types
    assert RiskType.EMPTY_ANSWERS in risk_types
    assert RiskType.BROKEN_REDIRECT in risk_types

def test_analyze_intent_risks_high():
    intents = [{"intent_id": "1", "record_type": "NaN"}]
    validation_results = {
        'circular_redirects': {'cycles': [['1', '2', '1']]}
    }

    risks = analyze_intent_risks(intents, validation_results)

    assert "1" in risks
    assert risks["1"].severity == RiskSeverity.HIGH
    risk_types = [r[0] for r in risks["1"].risks]
    assert RiskType.NAN_VALUE in risk_types or RiskType.MISSING_RECORD_TYPE in risk_types
    assert RiskType.CIRCULAR_REDIRECT in risk_types

def test_analyze_intent_risks_medium():
    intents = [{
        "intent_id": "1",
        "title": "Test",
        "record_type": "dialog",
        "intent_settings": {},
        "routing_params": {},
        "topics": []
    }]
    validation_results = {
        'empty_content': {'empty_inputs': ['1']},
        'graph_analysis': {'graph': {'dead_ends': ['1']}}
    }

    risks = analyze_intent_risks(intents, validation_results)

    assert "1" in risks
    assert risks["1"].severity == RiskSeverity.MEDIUM
    risk_types = [r[0] for r in risks["1"].risks]
    assert RiskType.EMPTY_INPUTS in risk_types
    assert RiskType.DEAD_END in risk_types

def test_analyze_intent_risks_low():
    intents = [{
        "intent_id": "1",
        "title": "Test",
        "record_type": "dialog",
        "intent_settings": {},
        "routing_params": {},
        "topics": []
    }]
    validation_results = {
        'titles': {'duplicate_titles': {'Test': ['1', '2']}}
    }

    risks = analyze_intent_risks(intents, validation_results)

    assert "1" in risks
    assert risks["1"].severity == RiskSeverity.LOW
    risk_types = [r[0] for r in risks["1"].risks]
    assert RiskType.DUPLICATE_TITLE in risk_types

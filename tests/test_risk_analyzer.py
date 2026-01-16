import pytest
from utils.risk_analyzer import (
    analyze_intent_risks,
    generate_risk_summary,
    RiskSeverity,
    RiskType
)

# Helper to create intent with default non-NaN optional fields
def create_intent(**kwargs):
    intent = {
        "intent_id": "1",
        "record_type": "main",
        "intent_settings": {},
        "routing_params": {},
        "topics": []
    }
    intent.update(kwargs)
    return intent

def test_analyze_intent_risks_critical():
    intents = [create_intent()]
    validation_results = {
        "intent_ids": {"duplicates": {"1": 2}}, # Critical: Duplicate ID
        "titles": {"duplicate_titles": {}},
        "empty_content": {},
        "redirects": {"broken_redirects": []},
        "circular_redirects": {"cycles": []},
        "graph_analysis": {}
    }

    risks = analyze_intent_risks(intents, validation_results)

    assert "1" in risks
    assert risks["1"].severity == RiskSeverity.CRITICAL
    risk_types = [r[0] for r in risks["1"].risks]
    assert RiskType.DUPLICATE_ID in risk_types

def test_analyze_intent_risks_high():
    intents = [create_intent(record_type="NaN")] # High: NaN record_type
    validation_results = {
        "intent_ids": {"duplicates": {}},
        "titles": {"duplicate_titles": {}},
        "empty_content": {},
        "redirects": {"broken_redirects": []},
        "circular_redirects": {"cycles": []},
        "graph_analysis": {}
    }

    risks = analyze_intent_risks(intents, validation_results)

    assert "1" in risks
    assert risks["1"].severity == RiskSeverity.HIGH
    risk_types = [r[0] for r in risks["1"].risks]
    assert RiskType.MISSING_RECORD_TYPE in risk_types

def test_analyze_intent_risks_medium():
    intents = [create_intent()]
    validation_results = {
        "intent_ids": {"duplicates": {}},
        "titles": {"duplicate_titles": {}},
        "empty_content": {"empty_inputs": ["1"]}, # Medium: Empty inputs
        "redirects": {"broken_redirects": []},
        "circular_redirects": {"cycles": []},
        "graph_analysis": {}
    }

    risks = analyze_intent_risks(intents, validation_results)

    assert "1" in risks
    assert risks["1"].severity == RiskSeverity.MEDIUM
    risk_types = [r[0] for r in risks["1"].risks]
    assert RiskType.EMPTY_INPUTS in risk_types

def test_generate_risk_summary():
    # Mock IntentRisk objects
    class MockRisk:
        def __init__(self, severity, risks_list):
            self.severity = severity
            self.risks = risks_list

    risks = {
        "1": MockRisk(RiskSeverity.CRITICAL, [(RiskType.DUPLICATE_ID, "desc")]),
        "2": MockRisk(RiskSeverity.HIGH, [(RiskType.NAN_VALUE, "desc")]),
        "3": MockRisk(RiskSeverity.INFO, [])
    }

    summary = generate_risk_summary(risks)

    assert summary['total_intents'] == 3
    assert summary['severity_distribution']['critical'] == 1
    assert summary['severity_distribution']['high'] == 1
    # Check risk score calculation
    assert summary['risk_score'] == 0

    # Let's try a better score case
    risks_good = {
        "1": MockRisk(RiskSeverity.INFO, []),
        "2": MockRisk(RiskSeverity.INFO, []),
        "3": MockRisk(RiskSeverity.INFO, []),
        "4": MockRisk(RiskSeverity.INFO, [])
    }
    summary_good = generate_risk_summary(risks_good)
    assert summary_good['risk_score'] == 100

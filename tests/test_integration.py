import os
import json
import pytest
from utils.loaders import load_intents
from utils.validators import run_all_validations, save_validation_report
from utils.risk_analyzer import analyze_intent_risks, export_risk_report
from utils.regex_analyzer import analyze_intent_regex_patterns
from utils.entry_point_analyzer import analyze_entry_points
from utils.freshness_analyzer import analyze_data_freshness

@pytest.fixture
def sample_data(tmp_path):
    content = """
{"intent_id": "1", "title": "Main", "record_type": "cc_regexp_main", "inputs": [{"questions": [{"sentence": "hello"}]}], "answers": [{"answer": "REDIRECT_TO_INTENT 2"}]}
{"intent_id": "2", "title": "Sub", "record_type": "dialog", "inputs": [], "answers": [{"answer": "Hi"}]}
{"intent_id": "3", "title": "Broken", "record_type": "dialog", "inputs": [], "answers": [{"answer": "REDIRECT_TO_INTENT 999"}]}
"""
    p = tmp_path / "data.jsonl"
    p.write_text(content.strip(), encoding='utf-8')
    return str(p)

def test_full_pipeline(sample_data, tmp_path):
    # 1. Load
    intents, metadata = load_intents(sample_data)
    assert len(intents) == 3

    # 2. Validation
    validation_results = run_all_validations(intents, {})
    assert validation_results['summary']['is_valid'] is False # Because of broken redirect in intent 3

    # Save validation report
    save_validation_report(validation_results, str(tmp_path))
    assert (tmp_path / "validation_report.json").exists()

    # 3. Risk Analysis
    risks = analyze_intent_risks(intents, validation_results)
    assert "3" in risks

    # Save risk report
    export_risk_report(risks, str(tmp_path / "risk_analysis.json"))
    assert (tmp_path / "risk_analysis.json").exists()

    # 4. Quality Metrics
    regex_metrics = analyze_intent_regex_patterns(intents)
    assert regex_metrics['total_patterns'] == 1

    entry_metrics = analyze_entry_points(intents)
    assert entry_metrics['unique_types'] >= 1

    freshness_metrics = analyze_data_freshness(intents)
    assert freshness_metrics['has_version_data'] is False # No version in sample

    # Verify content of generated reports
    with open(tmp_path / "risk_analysis.json", 'r', encoding='utf-8') as f:
        risk_report = json.load(f)
        assert risk_report['summary']['total_intents'] > 0

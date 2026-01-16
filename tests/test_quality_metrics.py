import pytest
from datetime import datetime, timedelta
from utils.regex_analyzer import analyze_regex_pattern, RegexComplexity
from utils.entry_point_analyzer import analyze_entry_points
from utils.freshness_analyzer import analyze_data_freshness, convert_ticks_to_datetime

def test_analyze_regex_pattern():
    # Simple
    simple = analyze_regex_pattern("abc")
    assert simple['complexity'] == RegexComplexity.SIMPLE

    # Moderate
    moderate = analyze_regex_pattern("a|b|c")  # 3 alternatives
    assert moderate['complexity'] == RegexComplexity.MODERATE

    # Complex
    complex_pattern = "a|b|c|d|e|f"  # 6 alternatives
    result = analyze_regex_pattern(complex_pattern)
    assert result['complexity'] == RegexComplexity.COMPLEX

def test_analyze_entry_points():
    intents = [
        {
            "intent_id": "main",
            "record_type": "cc_regexp_main",
            "inputs": [{"questions": ["hi"]}]
        },
        {
            "intent_id": "match",
            "record_type": "cc_match",
            "inputs": [{"questions": ["hi"]}]
        },
        {
            "intent_id": "other",
            "record_type": "other",
            "inputs": [] # No inputs, ignored
        }
    ]

    result = analyze_entry_points(intents)
    assert result['unique_types'] == 2
    assert result['diversity_score'] == 50

def test_analyze_data_freshness():
    # .NET ticks for 2025-01-01
    # 621355968000000000 + 1735689600 * 10000000 = 638712960000000000
    date = datetime(2025, 1, 1)
    ticks = 638712960000000000

    # We use the same conversion function to avoid timezone mismatches in testing
    # verifying that the function is self-consistent
    expected_dt = convert_ticks_to_datetime(ticks)

    intents = [{"version": ticks}]

    # Reference date is 10 days after expected_dt
    ref_date = expected_dt + timedelta(days=10)
    result = analyze_data_freshness(intents, reference_date=ref_date)

    assert result['has_version_data'] is True
    assert result['updated_last_month'] == 1
    assert result['activity_score'] == 100

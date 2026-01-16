import pytest
from datetime import datetime, timedelta
from utils.regex_analyzer import analyze_intent_regex_patterns, RegexComplexity
from utils.entry_point_analyzer import analyze_entry_points, EntryPointType
from utils.freshness_analyzer import analyze_data_freshness

# --- Regex Analyzer Tests ---

def test_regex_analyzer_simple():
    intents = [{
        "intent_id": "1",
        "inputs": [{"questions": [{"sentence": "hello"}]}]
    }]
    result = analyze_intent_regex_patterns(intents)
    assert result['total_patterns'] == 1
    assert result['complexity_distribution'][RegexComplexity.SIMPLE] == 1
    assert result['complex_count'] == 0

def test_regex_analyzer_complex():
    # > 100 chars
    pattern = "a" * 101
    intents = [{
        "intent_id": "1",
        "inputs": [{"questions": [{"sentence": pattern}]}]
    }]
    result = analyze_intent_regex_patterns(intents)
    assert result['complex_count'] == 1
    assert result['top_complex_patterns'][0]['intent_id'] == "1"

def test_regex_analyzer_alternatives():
    # > 10 alternatives
    pattern = "a|b|c|d|e|f|g|h|i|j|k"
    intents = [{
        "intent_id": "1",
        "inputs": [{"questions": [{"sentence": pattern}]}]
    }]
    result = analyze_intent_regex_patterns(intents)
    # Should be VERY_COMPLEX because > 10 alternatives
    assert result['complexity_distribution'][RegexComplexity.VERY_COMPLEX] == 1


# --- Entry Point Analyzer Tests ---

def test_entry_point_analyzer():
    intents = [
        {"intent_id": "1", "record_type": "cc_regexp_main", "inputs": [{"questions": ["q"]}]},
        {"intent_id": "2", "record_type": "cc_match", "inputs": [{"questions": ["q"]}]},
        {"intent_id": "3", "record_type": "internal", "inputs": []} # No inputs -> not an entry point
    ]
    result = analyze_entry_points(intents)

    assert result['total_entry_points'] == 2
    assert result['unique_types'] == 2 # cc_regexp_main and cc_match
    assert result['diversity_score'] == 50 # 2 * 25 = 50

# --- Freshness Analyzer Tests ---

def datetime_to_ticks(dt):
    TICKS_TO_UNIX_EPOCH = 621355968000000000
    TICKS_PER_SECOND = 10000000
    return int(dt.timestamp() * TICKS_PER_SECOND + TICKS_TO_UNIX_EPOCH)

def test_freshness_analyzer():
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    month_ago = now - timedelta(days=20)
    old = now - timedelta(days=60)

    intents = [
        {"version": datetime_to_ticks(yesterday)}, # Last day
        {"version": datetime_to_ticks(month_ago)}, # Last month
        {"version": datetime_to_ticks(old)} # Old
    ]

    result = analyze_data_freshness(intents, reference_date=now)

    assert result['has_version_data'] is True
    assert result['total_intents'] == 3
    assert result['updated_last_day'] == 1
    assert result['updated_last_month'] == 2 # yesterday + month_ago
    # ratio = 2/3 = 66.6% -> score ~ 66
    assert 60 <= result['activity_score'] <= 70
    assert result['freshness'] == 'fresh'

def test_freshness_analyzer_no_data():
    intents = [{"intent_id": "1"}] # No version
    result = analyze_data_freshness(intents)
    assert result['has_version_data'] is False

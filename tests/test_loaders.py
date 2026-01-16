import os
import json
import pytest
from utils.loaders import load_intents

@pytest.fixture
def temp_file(tmp_path):
    def _create_file(content, filename="test_data.jsonl"):
        p = tmp_path / filename
        p.write_text(content, encoding='utf-8')
        return str(p)
    return _create_file

def test_load_standard_jsonl(temp_file):
    content = """{"intent_id": "1", "title": "Test 1"}
{"intent_id": "2", "title": "Test 2"}"""
    filepath = temp_file(content)
    intents, metadata = load_intents(filepath)

    assert len(intents) == 2
    assert intents[0]['intent_id'] == "1"
    assert intents[1]['intent_id'] == "2"
    assert metadata['parsing_stats']['success'] == 2

def test_load_extra_data(temp_file):
    content = """{"intent_id": "1", "title": "Test 1"} {"intent_id": "2", "title": "Test 2"}
{"intent_id": "3", "title": "Test 3"}"""
    filepath = temp_file(content)
    intents, metadata = load_intents(filepath)

    assert len(intents) == 3
    assert intents[0]['intent_id'] == "1"
    assert intents[1]['intent_id'] == "2"
    assert intents[2]['intent_id'] == "3"
    assert metadata['parsing_stats']['fixed_extra_data'] > 0

def test_load_comments_and_empty_lines(temp_file):
    content = """
# This is a comment
{"intent_id": "1", "title": "Test 1"}

// Another comment
{"intent_id": "2", "title": "Test 2"}
"""
    filepath = temp_file(content)
    intents, metadata = load_intents(filepath)

    assert len(intents) == 2
    assert metadata['parsing_stats']['skipped_empty'] > 0

def test_load_invalid_json(temp_file):
    content = """{"intent_id": "1", "title": "Test 1"}
invalid json
{"intent_id": "2", "title": "Test 2"}"""
    filepath = temp_file(content)
    intents, metadata = load_intents(filepath)

    assert len(intents) == 2
    assert metadata['parsing_stats']['skipped_invalid'] == 1

def test_load_json_array(temp_file):
    content = """[
{"intent_id": "1", "title": "Test 1"},
{"intent_id": "2", "title": "Test 2"}
]"""
    filepath = temp_file(content)
    intents, metadata = load_intents(filepath)

    assert len(intents) == 2
    assert intents[0]['intent_id'] == "1"

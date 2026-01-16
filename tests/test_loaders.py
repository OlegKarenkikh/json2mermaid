import os
import json
import pytest
from utils.loaders import load_intents

def create_jsonl_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def test_load_valid_jsonl(tmp_path):
    filepath = tmp_path / "valid.jsonl"
    content = '{"intent_id": "1", "title": "Test 1"}\n{"intent_id": "2", "title": "Test 2"}'
    create_jsonl_file(filepath, content)

    intents, metadata = load_intents(str(filepath))

    assert len(intents) == 2
    assert intents[0]['intent_id'] == "1"
    assert intents[1]['intent_id'] == "2"
    assert metadata['parsing_stats']['success'] == 2

def test_load_extra_data(tmp_path):
    filepath = tmp_path / "extra.jsonl"
    content = '{"id": "1"} {"id": "2"}\n{"id": "3"}'
    create_jsonl_file(filepath, content)

    intents, metadata = load_intents(str(filepath))

    assert len(intents) == 3
    # Note: Implementation counts "success" for standard loads and "fixed_extra_data" for raw_decode
    # Line 1 fails standard load -> robust parsing extracts 2 items (fixed)
    # Line 2 succeeds standard load (success)
    # Total loaded = 3
    assert metadata['total_loaded'] == 3
    assert metadata['parsing_stats']['fixed_extra_data'] == 2
    assert metadata['parsing_stats']['success'] == 1

def test_load_json_array(tmp_path):
    filepath = tmp_path / "array.json"
    content = '[{"id": "1"}, {"id": "2"}]'
    create_jsonl_file(filepath, content)

    intents, metadata = load_intents(str(filepath))

    assert len(intents) == 2
    assert metadata['parsing_stats']['success'] == 2

def test_load_invalid_json(tmp_path):
    filepath = tmp_path / "invalid.jsonl"
    content = '{"id": "1"}\nINVALID_JSON\n{"id": "2"}'
    create_jsonl_file(filepath, content)

    intents, metadata = load_intents(str(filepath))

    assert len(intents) == 2
    assert metadata['parsing_stats']['skipped_invalid'] == 1
    assert metadata['parsing_stats']['success'] == 2

def test_load_empty_lines_and_comments(tmp_path):
    filepath = tmp_path / "comments.jsonl"
    content = '# Comment\n\n{"id": "1"}\n// Another comment'
    create_jsonl_file(filepath, content)

    intents, metadata = load_intents(str(filepath))

    assert len(intents) == 1
    assert metadata['parsing_stats']['skipped_empty'] == 3 # 1 empty + 2 comments
    assert metadata['parsing_stats']['success'] == 1

def test_file_not_found():
    intents, metadata = load_intents("non_existent_file.jsonl")
    assert intents == []
    assert metadata == {}

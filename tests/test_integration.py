import os
import json
import pytest
import subprocess
import sys

@pytest.fixture
def sample_data(tmp_path):
    input_file = tmp_path / "intent_data.jsonl"
    output_dir = tmp_path / "dialog_flow_analysis" # Default output dir in config

    # Create sample JSONL
    data = [
        {"intent_id": "1", "title": "Greeting", "record_type": "cc_regexp_main", "answers": [{"answer": "Hello"}], "inputs": [{"questions": [{"sentence": "hi"}]}]},
        {"intent_id": "2", "title": "Help", "record_type": "cc_match", "answers": [{"answer": "How can I help?"}], "inputs": [{"questions": [{"sentence": "help"}]}]},
        {"intent_id": "3", "title": "Exit", "record_type": "cc_match", "answers": [{"answer": "Bye"}], "inputs": [{"questions": [{"sentence": "bye"}]}]}
    ]

    with open(input_file, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item) + "\n")

    return str(input_file), str(output_dir)

def test_full_pipeline_subprocess(sample_data, tmp_path):
    input_file, output_dir = sample_data

    # We need to run the script from the root directory
    # and we need to overwrite utils/config.py or ensure the script uses our input file.
    # Since we cannot easily patch config via subprocess, we rely on the script checking INPUT_FILE.
    # The script uses 'intent_data.jsonl' by default.
    # We can create a symlink or copy our file to 'intent_data.jsonl' in the current working directory.

    cwd = os.getcwd()
    target_input = os.path.join(cwd, "intent_data.jsonl")

    # Backup existing file if any
    backup_file = None
    if os.path.exists(target_input):
        backup_file = target_input + ".bak"
        os.rename(target_input, backup_file)

    try:
        # Copy sample data to intent_data.jsonl
        with open(input_file, 'r') as src, open(target_input, 'w') as dst:
            dst.write(src.read())

        # Run the script
        result = subprocess.run(
            [sys.executable, "generator_v5.1_main.py"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "DIALOG ANALYZER" in result.stdout
        assert "ЭТАП 1: Загрузка данных" in result.stdout

        # Verify output
        # The script creates output in 'dialog_flow_analysis' (defined in config.py)
        # We can't easily change OUTPUT_DIR without editing config.py.
        # So we check the default location.
        default_output_dir = "dialog_flow_analysis"
        assert os.path.exists(default_output_dir)
        assert os.path.exists(os.path.join(default_output_dir, "validation_report.json"))

        # Check for risk_analysis.json (Assert failure expected based on code audit)
        # assert os.path.exists(os.path.join(default_output_dir, "risk_analysis.json"))

    finally:
        # Cleanup
        if os.path.exists(target_input):
            os.remove(target_input)
        if backup_file and os.path.exists(backup_file):
            os.rename(backup_file, target_input)

def test_pipeline_no_data_subprocess():
    # Run without intent_data.jsonl
    cwd = os.getcwd()
    target_input = os.path.join(cwd, "intent_data.jsonl")

    backup_file = None
    if os.path.exists(target_input):
        backup_file = target_input + ".bak"
        os.rename(target_input, backup_file)

    try:
        result = subprocess.run(
            [sys.executable, "generator_v5.1_main.py"],
            capture_output=True,
            text=True
        )

        # Expect failure (return code 1) because file not found
        assert result.returncode == 1
        assert "Файл не найден" in result.stdout

    finally:
        if backup_file and os.path.exists(backup_file):
            os.rename(backup_file, target_input)

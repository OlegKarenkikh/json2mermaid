# utils/config.py v5.2
"""Configuration settings for Dialog Analyzer"""

import os

# Input/Output settings
INPUT_FILE = "intent_data.jsonl"
OUTPUT_DIR = "dialog_flow_analysis"
MAX_LINES = None  # None = read all lines

# Analysis settings
ENABLE_VALIDATION = True
STOP_ON_VALIDATION_ERRORS = False
CLASSIFY_SUBTYPES = True
FILTER_EXPIRED = True  # Filter out expired intents

# Export settings
EXPORT_CSV = True
EXPORT_JSON = True
EXPORT_DIAGRAMS = True  # Генерация Mermaid диаграмм включена!

# Diagram settings (if EXPORT_DIAGRAMS = True)
DIAGRAM_FORMAT = "svg"  # svg, png, pdf
MAX_NODES_PER_DIAGRAM = 50
INCLUDE_LEGEND = True

# Validation thresholds
MAX_TITLE_LENGTH = 200
MAX_ANSWERS_PER_INTENT = 10
MAX_REGEX_LENGTH = 300

# Risk analysis settings
RISK_SCORE_WEIGHTS = {
    'critical': 25,  # Points to deduct per critical issue
    'high': 10,
    'medium': 5,
    'low': 2,
    'info': 0
}

# Quality metrics settings
QUALITY_THRESHOLDS = {
    'regex_complexity_warning': 10,  # % of complex patterns
    'regex_complexity_critical': 20,
    'entry_point_diversity_min': 2,  # Minimum types
    'freshness_warning_days': 60,
    'freshness_critical_days': 180
}

# Logging
VERBOSE = True
DEBUG = False

# Create output directory if it doesn't exist
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

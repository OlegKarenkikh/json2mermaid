# utils/loaders.py v5.2
"""Data loading utilities"""

import json
from typing import List, Dict, Tuple, Any
from datetime import datetime

def convert_ticks_to_datetime(ticks: int):
    """Convert .NET ticks to datetime"""
    if not ticks or ticks <= 0:
        return None
    try:
        TICKS_TO_UNIX_EPOCH = 621355968000000000
        TICKS_PER_SECOND = 10000000
        unix_seconds = (ticks - TICKS_TO_UNIX_EPOCH) / TICKS_PER_SECOND
        return datetime.fromtimestamp(unix_seconds)
    except (ValueError, OverflowError):
        return None

def is_expired(intent: Dict) -> bool:
    """Check if intent is expired"""
    expire = intent.get('expire', 0)
    if expire <= 0:
        return False
    
    expire_date = convert_ticks_to_datetime(expire)
    if expire_date is None:
        return False
    
    return expire_date < datetime.now()

def load_intents(filepath: str, max_lines: int = None) -> Tuple[List[Dict], Dict[str, Any]]:
    """
    Load intents from JSONL file
    
    Returns:
        (intents, metadata)
    """
    intents = []
    metadata = {
        'total_loaded': 0,
        'filtered_expired': 0,
        'final_count': 0,
        'version_statistics': {
            'with_version': 0,
            'with_expire': 0,
            'active': 0,
            'expired': 0
        }
    }
    
    print(f"📂 Loading data from: {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if max_lines and line_num > max_lines:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                try:
                    intent = json.loads(line)
                    metadata['total_loaded'] += 1
                    
                    # Version statistics
                    if intent.get('version', 0) > 0:
                        metadata['version_statistics']['with_version'] += 1
                    
                    if intent.get('expire', 0) > 0:
                        metadata['version_statistics']['with_expire'] += 1
                        
                        if is_expired(intent):
                            metadata['version_statistics']['expired'] += 1
                            metadata['filtered_expired'] += 1
                            continue  # Skip expired
                        else:
                            metadata['version_statistics']['active'] += 1
                    
                    intents.append(intent)
                    
                except json.JSONDecodeError as e:
                    print(f"⚠️  Line {line_num}: JSON decode error - {e}")
                    continue
        
        metadata['final_count'] = len(intents)
        print(f"✅ Loaded {metadata['final_count']} intents")
        
        if metadata['filtered_expired'] > 0:
            print(f"ℹ️  Filtered {metadata['filtered_expired']} expired intents")
        
        return intents, metadata
        
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        return [], metadata
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return [], metadata

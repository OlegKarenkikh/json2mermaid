# utils/entry_point_analyzer.py v5.1
"""Entry point diversity and classification analysis"""

from typing import Dict, List, Any
from collections import defaultdict

class EntryPointType:
    """Types of entry points in dialog system"""
    MAIN = "cc_regexp_main"              # Main regex-based entry
    MATCH = "cc_match"                    # Match-based entry  
    MESSENGER = "cc_viber_telegram"       # Messenger-specific entry
    SYSTEM = "system"                     # System/internal entry
    FALLBACK = "fallback"                 # Fallback/error handler
    CUSTOM = "custom"                     # Custom entry point

ENTRY_POINT_PATTERNS = {
    EntryPointType.MAIN: ['cc_regexp_main', 'main_intent', 'entry_main'],
    EntryPointType.MATCH: ['cc_match', 'match_intent'],
    EntryPointType.MESSENGER: ['viber', 'telegram', 'whatsapp', 'messenger'],
    EntryPointType.SYSTEM: ['system_', 'internal_'],
    EntryPointType.FALLBACK: ['fallback', 'error_', 'catch_all']
}

def classify_entry_point(intent: Dict) -> str:
    """Classify intent as entry point type"""
    record_type = str(intent.get('record_type', '')).lower()
    symbol_code = str(intent.get('symbol_code', '')).lower()
    intent_id = str(intent.get('intent_id', '')).lower()
    
    combined = f"{record_type} {symbol_code} {intent_id}"
    
    for ep_type, patterns in ENTRY_POINT_PATTERNS.items():
        for pattern in patterns:
            if pattern in combined:
                return ep_type
    
    return EntryPointType.CUSTOM

def analyze_entry_points(intents: List[Dict]) -> Dict[str, Any]:
    """Analyze entry point diversity and distribution"""
    print("\n🚪 Анализ точек входа...")
    
    entry_points = []
    type_distribution = defaultdict(int)
    
    for intent in intents:
        intent_id = intent.get('intent_id', '')
        record_type = intent.get('record_type', '')
        
        # Check if it's an entry point
        has_inputs = len(intent.get('inputs', [])) > 0
        is_entry = any([
            'main' in str(record_type).lower(),
            'regexp_main' in str(record_type).lower(),
            record_type in ['cc_match', 'cc_viber_telegram']
        ])
        
        if has_inputs and is_entry:
            ep_type = classify_entry_point(intent)
            entry_points.append({
                'intent_id': intent_id,
                'type': ep_type,
                'record_type': record_type,
                'title': intent.get('title', '')[:50]
            })
            type_distribution[ep_type] += 1
    
    # Calculate diversity score (0-100)
    unique_types = len(type_distribution)
    diversity_score = min(100, unique_types * 25)  # Max 4 types = 100
    
    # Print summary
    print(f"   Всего точек входа: {len(entry_points)}")
    print(f"   Уникальных типов: {unique_types}")
    print(f"   Diversity Score: {diversity_score}/100")
    
    if type_distribution:
        print(f"\n   Распределение:")
        for ep_type, count in sorted(type_distribution.items(), key=lambda x: -x[1]):
            print(f"      {ep_type}: {count}")
    
    return {
        'total_entry_points': len(entry_points),
        'type_distribution': dict(type_distribution),
        'unique_types': unique_types,
        'diversity_score': diversity_score,
        'entry_points': entry_points,
        'has_multiple_channels': unique_types > 1
    }

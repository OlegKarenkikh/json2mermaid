# utils/regex_analyzer.py v5.1
"""Regex pattern analysis and complexity detection"""

import re
from typing import Dict, List, Any
from collections import defaultdict

class RegexComplexity:
    """Complexity levels for regex patterns"""
    SIMPLE = "simple"              # < 30 chars, 0-2 alternatives
    MODERATE = "moderate"          # 30-100 chars, 3-5 alternatives  
    COMPLEX = "complex"            # 100-200 chars, 6-10 alternatives
    VERY_COMPLEX = "very_complex"  # > 200 chars or > 10 alternatives

def analyze_regex_pattern(pattern: str) -> Dict[str, Any]:
    """Analyze single regex pattern complexity"""
    if not pattern:
        return {'length': 0, 'complexity': RegexComplexity.SIMPLE, 'issues': [], 'score': 0}
    
    # Remove flags from pattern
    clean_pattern = re.sub(r'/[gimsuyx]*$', '', pattern).strip('/')
    length = len(clean_pattern)
    
    # Count alternatives (| operator)
    alternatives = clean_pattern.count('|') + 1
    
    # Count special constructs
    issues = []
    lookaheads = len(re.findall(r'\(\?[=!]', clean_pattern))
    lookbehinds = len(re.findall(r'\(\?<[=!]', clean_pattern))
    nested_groups = clean_pattern.count('((')
    character_classes = clean_pattern.count('[')
    
    if lookaheads > 0:
        issues.append(f"Contains {lookaheads} lookahead(s)")
    if lookbehinds > 0:
        issues.append(f"Contains {lookbehinds} lookbehind(s)")
    if nested_groups > 2:
        issues.append(f"Deep nesting ({nested_groups} levels)")
    if character_classes > 5:
        issues.append(f"Many character classes ({character_classes})")
    if alternatives > 10:
        issues.append(f"Too many alternatives ({alternatives})")
    
    # Determine complexity
    if length > 200 or alternatives > 10:
        complexity = RegexComplexity.VERY_COMPLEX
    elif length > 100 or alternatives > 5:
        complexity = RegexComplexity.COMPLEX
    elif length > 30 or alternatives > 2:
        complexity = RegexComplexity.MODERATE
    else:
        complexity = RegexComplexity.SIMPLE
    
    # Calculate score (higher = more complex)
    score = length + alternatives * 10 + len(issues) * 20
    
    return {
        'length': length,
        'alternatives': alternatives,
        'complexity': complexity,
        'issues': issues,
        'score': score
    }

def analyze_intent_regex_patterns(intents: List[Dict]) -> Dict[str, Any]:
    """Analyze regex patterns across all intents"""
    print("\n🔍 Анализ сложности regex паттернов...")
    
    complexity_dist = defaultdict(int)
    complex_patterns = []
    total_patterns = 0
    
    for intent in intents:
        intent_id = intent.get('intent_id', 'unknown')
        
        for input_obj in intent.get('inputs', []):
            for question in input_obj.get('questions', []):
                sentence = question.get('sentence', '')
                if not sentence:
                    continue
                
                total_patterns += 1
                analysis = analyze_regex_pattern(sentence)
                complexity_dist[analysis['complexity']] += 1
                
                # Track complex patterns
                if analysis['complexity'] in [RegexComplexity.COMPLEX, RegexComplexity.VERY_COMPLEX]:
                    complex_patterns.append({
                        'intent_id': intent_id,
                        'pattern': sentence[:100] + ('...' if len(sentence) > 100 else ''),
                        'length': analysis['length'],
                        'alternatives': analysis['alternatives'],
                        'issues': analysis['issues'],
                        'score': analysis['score']
                    })
    
    # Sort by score (most complex first)
    complex_patterns.sort(key=lambda x: x['score'], reverse=True)
    
    complex_count = len(complex_patterns)
    complex_pct = round(complex_count / total_patterns * 100, 1) if total_patterns > 0 else 0
    
    # Print summary
    print(f"   Всего паттернов: {total_patterns}")
    print(f"   Сложных (>100 символов): {complex_count} ({complex_pct}%)")
    
    if complex_patterns:
        print(f"\n   ТОП-3 самых сложных:")
        for i, pattern in enumerate(complex_patterns[:3], 1):
            print(f"   {i}. {pattern['intent_id']} - {pattern['length']} символов, {pattern['alternatives']} альтернатив")
    
    return {
        'total_patterns': total_patterns,
        'complexity_distribution': dict(complexity_dist),
        'complex_count': complex_count,
        'complex_percentage': complex_pct,
        'top_complex_patterns': complex_patterns[:10]
    }

def get_regex_risk_level(complexity: str) -> str:
    """Map regex complexity to risk level"""
    mapping = {
        RegexComplexity.SIMPLE: 'info',
        RegexComplexity.MODERATE: 'low',
        RegexComplexity.COMPLEX: 'medium',
        RegexComplexity.VERY_COMPLEX: 'high'
    }
    return mapping.get(complexity, 'info')

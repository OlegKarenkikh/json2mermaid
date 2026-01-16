# utils/risk_analyzer.py v5.1
"""Risk analysis and visual indication system"""

from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict
from enum import Enum

class RiskSeverity(Enum):
    """Risk severity levels"""
    CRITICAL = "critical"  # Блокирует работу сценария
    HIGH = "high"         # Может привести к ошибкам
    MEDIUM = "medium"     # Потенциальные проблемы
    LOW = "low"           # Минорные замечания
    INFO = "info"         # Информационные

class RiskType(Enum):
    """Types of risks in dialog intents"""
    NAN_VALUE = "nan_value"
    EMPTY_ANSWERS = "empty_answers"
    EMPTY_INPUTS = "empty_inputs"
    BROKEN_REDIRECT = "broken_redirect"
    CIRCULAR_REDIRECT = "circular_redirect"
    DUPLICATE_ID = "duplicate_id"
    DUPLICATE_TITLE = "duplicate_title"
    ISOLATED_SUBGRAPH = "isolated_subgraph"
    DEAD_END = "dead_end"
    COMPLEX_REGEX = "complex_regex"
    MISSING_RECORD_TYPE = "missing_record_type"

# Risk color scheme for visualization
RISK_COLORS = {
    RiskSeverity.CRITICAL: "#FF4444",  # Красный
    RiskSeverity.HIGH: "#FF8844",      # Оранжевый
    RiskSeverity.MEDIUM: "#FFCC44",    # Желтый
    RiskSeverity.LOW: "#88CCFF",       # Голубой
    RiskSeverity.INFO: "#CCCCCC",      # Серый
}

# Helper functions for NaN detection
def _is_nan_or_empty(value: Any) -> bool:
    """
    Проверяет, является ли значение NaN, None или пустым.
    Используется для обязательных полей.
    """
    if value is None:
        return True
    if isinstance(value, float):
        import math
        if math.isnan(value):
            return True
    if isinstance(value, str):
        if value.upper() in ('NAN', 'NONE', 'NULL', ''):
            return True
    return False

def _is_explicit_nan(value: Any) -> bool:
    """
    Проверяет, является ли значение явным NaN (float nan или строка 'NaN').
    Используется для опциональных полей - None для них допустим.
    """
    if value is None:
        return False  # None допустим для опциональных полей
    if isinstance(value, float):
        import math
        if math.isnan(value):
            return True
    if isinstance(value, str):
        if value.upper() == 'NAN':
            return True
    return False

# Risk severity mapping
RISK_SEVERITY_MAP = {
    RiskType.DUPLICATE_ID: RiskSeverity.CRITICAL,
    RiskType.BROKEN_REDIRECT: RiskSeverity.CRITICAL,
    RiskType.EMPTY_ANSWERS: RiskSeverity.CRITICAL,
    RiskType.CIRCULAR_REDIRECT: RiskSeverity.HIGH,
    RiskType.NAN_VALUE: RiskSeverity.HIGH,
    RiskType.MISSING_RECORD_TYPE: RiskSeverity.HIGH,
    RiskType.EMPTY_INPUTS: RiskSeverity.MEDIUM,
    RiskType.DEAD_END: RiskSeverity.MEDIUM,
    RiskType.DUPLICATE_TITLE: RiskSeverity.LOW,
    RiskType.COMPLEX_REGEX: RiskSeverity.LOW,
    RiskType.ISOLATED_SUBGRAPH: RiskSeverity.INFO,
}

class IntentRisk:
    """Risk information for a single intent"""
    def __init__(self, intent_id: str):
        self.intent_id = intent_id
        self.risks: List[Tuple[RiskType, str]] = []  # (type, description)
        self.severity = RiskSeverity.INFO
    
    def add_risk(self, risk_type: RiskType, description: str):
        """Add a risk to this intent"""
        self.risks.append((risk_type, description))
        # Update severity to highest risk
        risk_severity = RISK_SEVERITY_MAP.get(risk_type, RiskSeverity.INFO)
        if self._compare_severity(risk_severity, self.severity) > 0:
            self.severity = risk_severity
    
    def _compare_severity(self, s1: RiskSeverity, s2: RiskSeverity) -> int:
        """Compare two severities (-1, 0, 1)"""
        order = [RiskSeverity.INFO, RiskSeverity.LOW, RiskSeverity.MEDIUM, 
                 RiskSeverity.HIGH, RiskSeverity.CRITICAL]
        return order.index(s1) - order.index(s2)
    
    def get_color(self) -> str:
        """Get color for this intent based on highest severity"""
        return RISK_COLORS.get(self.severity, "#FFFFFF")
    
    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary"""
        return {
            'intent_id': self.intent_id,
            'severity': self.severity.value,
            'color': self.get_color(),
            'risk_count': len(self.risks),
            'risks': [
                {'type': rt.value, 'description': desc}
                for rt, desc in self.risks
            ]
        }

def analyze_intent_risks(intents: List[Dict], validation_results: Dict) -> Dict[str, IntentRisk]:
    """Analyze risks for all intents based on validation results"""
    risks = {}
    
    # Initialize risk objects
    for intent in intents:
        intent_id = intent.get('intent_id', 'unknown')
        risks[intent_id] = IntentRisk(intent_id)
    
    # 1. Duplicate IDs
    duplicates = validation_results.get('intent_ids', {}).get('duplicates', {})
    for intent_id in duplicates.keys():
        if intent_id in risks:
            risks[intent_id].add_risk(
                RiskType.DUPLICATE_ID,
                f"Duplicate intent_id found {duplicates[intent_id]} times"
            )
    
    # 2. Duplicate titles
    dup_titles = validation_results.get('titles', {}).get('duplicate_titles', {})
    for title, intent_ids in dup_titles.items():
        for intent_id in intent_ids:
            if intent_id in risks:
                risks[intent_id].add_risk(
                    RiskType.DUPLICATE_TITLE,
                    f"Title '{title[:30]}...' used by {len(intent_ids)} intents"
                )
    
    # 3. NaN values
    # Определяем обязательные и опциональные поля
    required_fields = ['record_type']  # Обязательные поля
    optional_fields = ['intent_settings', 'routing_params', 'topics']  # Опциональные поля
    
    for intent in intents:
        intent_id = intent.get('intent_id', 'unknown')
        
        # Проверяем обязательное поле record_type
        record_type = intent.get('record_type')
        if _is_nan_or_empty(record_type):
            risks[intent_id].add_risk(
                RiskType.MISSING_RECORD_TYPE,
                "record_type is NaN or missing (обязательное поле)"
            )
        
        # Проверяем опциональные поля на явные NaN значения (но не на None)
        # None для опциональных полей - это нормально
        nan_fields = []
        for field in optional_fields:
            value = intent.get(field)
            # Проверяем только явные NaN (float nan или строка 'NaN'), но не None
            if _is_explicit_nan(value):
                nan_fields.append(field)
        
        if nan_fields:
            risks[intent_id].add_risk(
                RiskType.NAN_VALUE,
                f"Явные NaN значения в: {', '.join(nan_fields)}"
            )
    
    # 4. Empty answers/inputs
    empty_content = validation_results.get('empty_content', {})
    for intent_id in empty_content.get('empty_answers', []):
        if intent_id in risks:
            risks[intent_id].add_risk(
                RiskType.EMPTY_ANSWERS,
                "Intent has no answers - dialog will fail"
            )
    
    for intent_id in empty_content.get('empty_inputs', []):
        if intent_id in risks:
            risks[intent_id].add_risk(
                RiskType.EMPTY_INPUTS,
                "Intent has no inputs - cannot be triggered"
            )
    
    # 5. Broken redirects
    broken_redirects = validation_results.get('redirects', {}).get('broken_redirects', [])
    for source_id, target_id in broken_redirects:
        if source_id in risks:
            risks[source_id].add_risk(
                RiskType.BROKEN_REDIRECT,
                f"Redirects to non-existent intent: {target_id}"
            )
    
    # 6. Circular redirects
    cycles = validation_results.get('circular_redirects', {}).get('cycles', [])
    for cycle in cycles:
        for intent_id in cycle[:-1]:  # Last is duplicate of first
            if intent_id in risks:
                risks[intent_id].add_risk(
                    RiskType.CIRCULAR_REDIRECT,
                    f"Part of circular redirect: {' → '.join(cycle)}"
                )
    
    # 7. Dead ends (from graph analysis)
    graph_analysis = validation_results.get('graph_analysis', {})
    dead_ends = graph_analysis.get('graph', {}).get('dead_ends', [])
    for intent_id in dead_ends:
        if intent_id in risks:
            risks[intent_id].add_risk(
                RiskType.DEAD_END,
                "Intent has no outgoing transitions - dialog ends here"
            )
    
    # 8. Isolated subgraphs
    isolated = graph_analysis.get('isolated_subgraphs', [])
    for component in isolated:
        for intent_id in component:
            if intent_id in risks:
                risks[intent_id].add_risk(
                    RiskType.ISOLATED_SUBGRAPH,
                    f"Part of isolated subgraph ({len(component)} nodes)"
                )
    
    return risks

def generate_risk_summary(risks: Dict[str, IntentRisk]) -> Dict[str, Any]:
    """Generate summary statistics for risks"""
    severity_counts = defaultdict(int)
    risk_type_counts = defaultdict(int)
    
    for intent_risk in risks.values():
        severity_counts[intent_risk.severity.value] += 1
        for risk_type, _ in intent_risk.risks:
            risk_type_counts[risk_type.value] += 1
    
    # Calculate risk score (0-100)
    total_intents = len(risks)
    critical_count = severity_counts.get(RiskSeverity.CRITICAL.value, 0)
    high_count = severity_counts.get(RiskSeverity.HIGH.value, 0)
    
    risk_score = 100
    if total_intents > 0:
        risk_score = max(0, 100 - (
            (critical_count * 25 + high_count * 10) * 100 // total_intents
        ))
    
    return {
        'total_intents': total_intents,
        'risk_score': risk_score,
        'severity_distribution': dict(severity_counts),
        'risk_type_distribution': dict(risk_type_counts),
        'critical_intents': [iid for iid, risk in risks.items() 
                            if risk.severity == RiskSeverity.CRITICAL],
        'high_risk_intents': [iid for iid, risk in risks.items() 
                             if risk.severity == RiskSeverity.HIGH]
    }

def generate_risk_legend() -> str:
    """Generate visual legend for risk colors"""
    legend = ["\n" + "="*80]
    legend.append("📊 ЛЕГЕНДА РИСКОВ")
    legend.append("="*80)
    
    descriptions = {
        RiskSeverity.CRITICAL: "Блокирует работу сценария",
        RiskSeverity.HIGH: "Может привести к ошибкам в runtime",
        RiskSeverity.MEDIUM: "Потенциальные проблемы",
        RiskSeverity.LOW: "Минорные замечания",
        RiskSeverity.INFO: "Информационные уведомления"
    }
    
    for severity in [RiskSeverity.CRITICAL, RiskSeverity.HIGH, 
                     RiskSeverity.MEDIUM, RiskSeverity.LOW, RiskSeverity.INFO]:
        color = RISK_COLORS[severity]
        desc = descriptions[severity]
        legend.append(f"  {severity.value.upper():10s} [{color}] - {desc}")
    
    legend.append("="*80 + "\n")
    return "\n".join(legend)

def export_risk_report(risks: Dict[str, IntentRisk], output_path: str):
    """Export detailed risk report to JSON"""
    import json
    from datetime import datetime
    
    report = {
        'report_timestamp': datetime.now().isoformat(),
        'report_type': 'risk_analysis',
        'version': '5.1',
        'summary': generate_risk_summary(risks),
        'intents': {
            intent_id: risk.to_dict()
            for intent_id, risk in risks.items()
            if len(risk.risks) > 0  # Only export intents with risks
        },
        'risk_legend': {
            severity.value: {
                'color': RISK_COLORS[severity],
                'level': i
            }
            for i, severity in enumerate([RiskSeverity.CRITICAL, RiskSeverity.HIGH,
                                         RiskSeverity.MEDIUM, RiskSeverity.LOW, 
                                         RiskSeverity.INFO])
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Отчёт о рисках: {output_path}")

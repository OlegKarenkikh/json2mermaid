# utils/visual_config.py v5.1
"""Visual configuration for risk-aware diagrams"""

from typing import Dict
from .risk_analyzer import RiskSeverity, RISK_COLORS

# Graphviz node styles based on risk
GRAPHVIZ_RISK_STYLES = {
    RiskSeverity.CRITICAL: {
        'fillcolor': RISK_COLORS[RiskSeverity.CRITICAL],
        'fontcolor': 'white',
        'penwidth': '3',
        'style': 'filled,bold'
    },
    RiskSeverity.HIGH: {
        'fillcolor': RISK_COLORS[RiskSeverity.HIGH],
        'fontcolor': 'black',
        'penwidth': '2',
        'style': 'filled'
    },
    RiskSeverity.MEDIUM: {
        'fillcolor': RISK_COLORS[RiskSeverity.MEDIUM],
        'fontcolor': 'black',
        'penwidth': '1.5',
        'style': 'filled'
    },
    RiskSeverity.LOW: {
        'fillcolor': RISK_COLORS[RiskSeverity.LOW],
        'fontcolor': 'black',
        'penwidth': '1',
        'style': 'filled,dashed'
    },
    RiskSeverity.INFO: {
        'fillcolor': RISK_COLORS[RiskSeverity.INFO],
        'fontcolor': 'black',
        'penwidth': '1',
        'style': 'filled,dotted'
    }
}

# Mermaid styles for risk indication
MERMAID_RISK_STYLES = {
    RiskSeverity.CRITICAL: f"fill:{RISK_COLORS[RiskSeverity.CRITICAL]},stroke:#AA0000,stroke-width:3px,color:#fff",
    RiskSeverity.HIGH: f"fill:{RISK_COLORS[RiskSeverity.HIGH]},stroke:#CC4400,stroke-width:2px",
    RiskSeverity.MEDIUM: f"fill:{RISK_COLORS[RiskSeverity.MEDIUM]},stroke:#886600,stroke-width:1px",
    RiskSeverity.LOW: f"fill:{RISK_COLORS[RiskSeverity.LOW]},stroke:#0066AA,stroke-width:1px,stroke-dasharray:5",
    RiskSeverity.INFO: f"fill:{RISK_COLORS[RiskSeverity.INFO]},stroke:#666666,stroke-width:1px,stroke-dasharray:2"
}

def get_node_style(severity: RiskSeverity, format: str = 'graphviz') -> Dict[str, str]:
    """Get visual style for node based on risk severity"""
    if format == 'graphviz':
        return GRAPHVIZ_RISK_STYLES.get(severity, GRAPHVIZ_RISK_STYLES[RiskSeverity.INFO])
    elif format == 'mermaid':
        return {'style': MERMAID_RISK_STYLES.get(severity, MERMAID_RISK_STYLES[RiskSeverity.INFO])}
    return {}

def generate_legend_graphviz() -> str:
    """Generate Graphviz legend subgraph"""
    legend = ['  subgraph cluster_legend {']
    legend.append('    label="Risk Legend";')
    legend.append('    style=filled;')
    legend.append('    color=lightgrey;')
    legend.append('    node [shape=box];')
    
    for severity in [RiskSeverity.CRITICAL, RiskSeverity.HIGH, 
                     RiskSeverity.MEDIUM, RiskSeverity.LOW, RiskSeverity.INFO]:
        style = GRAPHVIZ_RISK_STYLES[severity]
        node_name = f"legend_{severity.value}"
        legend.append(f'    {node_name} [label="{severity.value.upper()}", '
                     f'fillcolor="{style["fillcolor"]}", '
                     f'fontcolor="{style["fontcolor"]}", '
                     f'style="{style["style"]}"];')
    
    legend.append('  }')
    return '\n'.join(legend)

def generate_legend_mermaid() -> str:
    """Generate Mermaid legend"""
    legend = ['  subgraph Legend']
    
    for severity in [RiskSeverity.CRITICAL, RiskSeverity.HIGH,
                     RiskSeverity.MEDIUM, RiskSeverity.LOW, RiskSeverity.INFO]:
        node_id = f"L{severity.value}"
        legend.append(f'    {node_id}["{severity.value.upper()}"]')
    
    legend.append('  end')
    legend.append('')
    
    # Add styles
    for severity in [RiskSeverity.CRITICAL, RiskSeverity.HIGH,
                     RiskSeverity.MEDIUM, RiskSeverity.LOW, RiskSeverity.INFO]:
        node_id = f"L{severity.value}"
        style = MERMAID_RISK_STYLES[severity]
        legend.append(f'  style {node_id} {style}')
    
    return '\n'.join(legend)

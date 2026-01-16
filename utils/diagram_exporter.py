# utils/diagram_exporter.py v5.2
"""Diagram export utilities (Mermaid) with risk-based styling."""

from typing import Dict, Iterable, Optional, Tuple

from .risk_analyzer import RiskSeverity, IntentRisk
from .visual_config import get_node_style, generate_legend_mermaid


def _sanitize_node_id(intent_id: str) -> str:
    """Sanitize node id for Mermaid."""
    return intent_id.replace("-", "_").replace(".", "_")


def export_mermaid_graph(
    intents: Iterable[Dict],
    transitions: Iterable[Tuple[str, str]],
    intent_risks: Optional[Dict[str, IntentRisk]],
    output_path: str,
    include_legend: bool = True,
) -> None:
    """Export dialog graph as Mermaid diagram with risk styles."""
    lines = ["flowchart TD"]

    intent_list = list(intents)
    intent_ids = {intent.get("intent_id") for intent in intent_list}

    # Nodes
    for intent in intent_list:
        intent_id = intent.get("intent_id", "unknown")
        node_id = _sanitize_node_id(intent_id)
        title = str(intent.get("title", "")).strip()
        label = f"{intent_id}\\n{title}" if title else intent_id
        lines.append(f'  {node_id}["{label}"]')

    # Edges
    for source, target in transitions:
        if source in intent_ids and target in intent_ids:
            src_id = _sanitize_node_id(source)
            tgt_id = _sanitize_node_id(target)
            lines.append(f"  {src_id} --> {tgt_id}")

    # Styles
    for intent in intent_list:
        intent_id = intent.get("intent_id", "unknown")
        node_id = _sanitize_node_id(intent_id)
        severity = RiskSeverity.INFO
        if intent_risks and intent_id in intent_risks:
            severity = intent_risks[intent_id].severity
        style = get_node_style(severity, format="mermaid")["style"]
        lines.append(f"  style {node_id} {style}")

    if include_legend:
        lines.append("")
        lines.append(generate_legend_mermaid())

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

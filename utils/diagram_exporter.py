# utils/diagram_exporter.py v5.3
"""Утилиты экспорта диаграмм (Mermaid) с риск-стилями."""

from typing import Dict, Iterable, Optional, Tuple, List
import re

from .risk_analyzer import RiskSeverity, IntentRisk
from .visual_config import get_node_style, generate_legend_mermaid
from .dataclasses import Transition


def _sanitize_node_id(intent_id: str) -> str:
    """Очистка node id для Mermaid."""
    return intent_id.replace("-", "_").replace(".", "_")


def _sanitize_label(text: str) -> str:
    """
    Очистка текста для Mermaid label.
    Экранирует спецсимволы и кавычки.
    """
    if not text:
        return ""
    
    # Замена двойных кавычек на одинарные
    text = text.replace('"', "'")
    
    # Удаление опасных символов для Mermaid
    dangerous_chars = r'[\[\]{}()<>\\|]'
    text = re.sub(dangerous_chars, '', text)
    
    # Ограничение длины
    if len(text) > 60:
        text = text[:57] + "..."
    
    return text.strip()


def _get_arrow_style(transition_type: str) -> Tuple[str, str]:
    """
    Получить стиль стрелки для типа перехода.
    Возвращает: (arrow_syntax, label)
    """
    styles = {
        'button_redirect': ('-->', ''),
        'direct_redirect': ('==>', 'direct'),
        'conditional_redirect': ('-.->', 'if/else'),
        'fallback': ('-..->', 'fallback'),
        'answer_redirect': ('-->', 'answer'),
        'intent_match': ('-->', 'match'),
    }
    
    return styles.get(transition_type, ('-->', ''))


def export_mermaid_graph(
    intents: Iterable[Dict],
    transitions: Iterable[Transition],
    intent_risks: Optional[Dict[str, IntentRisk]],
    output_path: str,
    include_legend: bool = True,
    max_nodes: int = 1000,
) -> None:
    """Экспорт диалогового графа в Mermaid с риск-стилями."""
    lines = ["flowchart TD"]

    intent_list = list(intents)[:max_nodes]
    intent_ids = {intent.get("intent_id") for intent in intent_list}
    
    # Информация о ограничении
    if len(list(intents)) > max_nodes:
        lines.append(f"  %% Showing first {max_nodes} of {len(list(intents))} intents")

    # Nodes
    for intent in intent_list:
        intent_id = intent.get("intent_id", "unknown")
        node_id = _sanitize_node_id(intent_id)
        title = str(intent.get("title", "")).strip()
        
        # Очистка текста
        clean_id = _sanitize_label(intent_id)
        clean_title = _sanitize_label(title)
        
        # Формирование label
        if clean_title and len(clean_title) > 3:
            label = f"{clean_title}"
        else:
            label = clean_id
        
        lines.append(f'  {node_id}["{label}"]')

    # Edges with styles
    transition_list = [t for t in transitions if t.source_id in intent_ids and t.target_id in intent_ids]
    
    # Группировка по типам
    for transition in transition_list[:5000]:  # Ограничение для больших графов
        src_id = _sanitize_node_id(transition.source_id)
        tgt_id = _sanitize_node_id(transition.target_id)
        arrow, label = _get_arrow_style(transition.transition_type)
        
        if label:
            lines.append(f"  {src_id} {arrow}|{label}| {tgt_id}")
        else:
            lines.append(f"  {src_id} {arrow} {tgt_id}")

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
        lines.append("%% Legend")
        lines.append(generate_legend_mermaid())
        lines.append("")
        lines.append("%% Transition Types:")
        lines.append("%% --> button redirect")
        lines.append("%% ==> direct redirect")
        lines.append("%% -.-> conditional (if/else)")
        lines.append("%% -..-> fallback")
    
    # Статистика
    lines.append("")
    lines.append(f"%% Total nodes: {len(intent_list)}")
    lines.append(f"%% Total edges: {len(transition_list)}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    print(f"\n📊 Статистика диаграммы:")
    print(f"   Узлов: {len(intent_list)}")
    print(f"   Рёбер: {len(transition_list)}")
    if len(list(intents)) > max_nodes:
        print(f"   ⚠️  Показаны первые {max_nodes} из {len(list(intents))} интентов")

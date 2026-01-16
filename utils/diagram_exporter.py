# utils/diagram_exporter.py v5.4
"""Утилиты экспорта диаграмм (Mermaid) с риск-стилями и полной логикой."""

from typing import Dict, Iterable, Optional, Tuple, List, Any
import re

from .risk_analyzer import RiskSeverity, IntentRisk
from .visual_config import get_node_style, generate_legend_mermaid
from .dataclasses import Transition


def _sanitize_node_id(intent_id: str) -> str:
    """Очистка node id для Mermaid."""
    # Заменяем все неалфавитные символы на _
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', intent_id)
    # Убеждаемся что не начинается с цифры
    if sanitized and sanitized[0].isdigit():
        sanitized = 'n_' + sanitized
    return sanitized


def _sanitize_label(text: str, max_len: int = 60) -> str:
    """
    Очистка текста для Mermaid label.
    Экранирует спецсимволы и кавычки.
    """
    if not text:
        return ""
    
    # Замена двойных кавычек на одинарные
    text = text.replace('"', "'")
    
    # Удаление опасных символов для Mermaid
    dangerous_chars = r'[\[\]{}()<>\\|#&;]'
    text = re.sub(dangerous_chars, '', text)
    
    # Заменяем переносы строк на пробелы
    text = text.replace('\n', ' ').replace('\r', '')
    
    # Убираем множественные пробелы
    text = re.sub(r'\s+', ' ', text)
    
    # Ограничение длины
    if len(text) > max_len:
        text = text[:max_len-3] + "..."
    
    return text.strip()


def _get_arrow_style(transition_type: str) -> Tuple[str, str]:
    """
    Получить стиль стрелки для типа перехода.
    Возвращает: (arrow_syntax, label)
    """
    styles = {
        'button_redirect': ('-->', 'btn'),
        'button_action': ('-->', 'action'),
        'action_redirect': ('-->', 'action'),
        'direct_redirect': ('==>', 'direct'),
        'conditional_redirect': ('-.->', 'if/else'),
        'text_redirect': ('==>', 'redirect'),
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


def _extract_slot_condition_label(slots: List[Dict]) -> str:
    """Форматирует условие слотов для отображения на диаграмме."""
    if not slots:
        return ""
    
    conditions = []
    for slot in slots:
        slot_id = slot.get('slot_id', '')
        values = slot.get('values', [])
        if slot_id and values:
            # Сокращаем имя слота если слишком длинное
            short_id = slot_id[-20:] if len(slot_id) > 20 else slot_id
            val_str = str(values[0])[:15] if values else ''
            conditions.append(f"{short_id}={val_str}")
    
    result = ' & '.join(conditions[:2])
    if len(conditions) > 2:
        result += '...'
    return result


def export_detailed_flow_diagram(
    intents: Iterable[Dict],
    output_path: str,
    show_slot_conditions: bool = True,
    show_buttons: bool = True,
    show_regex: bool = True,
) -> None:
    """
    Экспорт детальной диаграммы с полной логикой обработки обращения.
    
    Показывает:
    - Входные условия (regex)
    - Ветвления по слотам
    - Все переходы с условиями
    - Кнопки и действия
    """
    from .analyzers import extract_detailed_flow
    
    lines = ["flowchart TD"]
    lines.append("    %% Detailed Dialog Flow Diagram")
    lines.append("")
    
    intent_list = list(intents)
    all_node_ids = set()
    external_targets = set()
    edge_count = 0
    
    # Сначала собираем все intent_id
    for intent in intent_list:
        intent_id = intent.get('intent_id', '')
        if intent_id:
            all_node_ids.add(intent_id)
    
    for intent in intent_list:
        flow = extract_detailed_flow(intent)
        intent_id = flow['intent_id']
        node_id = _sanitize_node_id(intent_id)
        title = _sanitize_label(flow['title'], 50)
        record_type = flow.get('record_type', '')
        
        # Определяем форму узла в зависимости от типа
        if 'main' in record_type.lower() or 'regexp' in record_type.lower():
            # Главный интент - прямоугольник с закругленными углами
            node_shape = f'{node_id}(["{title}"])'
        else:
            # Обычный интент
            node_shape = f'{node_id}["{title}"]'
        
        lines.append(f"    %% Intent: {intent_id}")
        lines.append(f"    {node_shape}")
        
        # Входные условия (regex) - как узел-условие
        if show_regex and flow['entry_conditions']:
            for idx, cond in enumerate(flow['entry_conditions'][:1]):  # Показываем только первый
                if cond['type'] == 'regex':
                    regex_node_id = f"{node_id}_regex"
                    # Сокращаем regex для отображения
                    pattern = cond['pattern']
                    if len(pattern) > 40:
                        pattern = pattern[:37] + "..."
                    pattern = _sanitize_label(pattern, 40)
                    lines.append(f"    {regex_node_id}{{{{\"{pattern}\"}}}}")
                    lines.append(f"    {regex_node_id} --> {node_id}")
                    edge_count += 1
        
        # Ветвления по ответам
        branches = flow.get('branches', [])
        
        # Если есть ветвления с условиями слотов
        branches_with_slots = [b for b in branches if b.get('slot_conditions')]
        branches_without_slots = [b for b in branches if not b.get('slot_conditions')]
        
        if show_slot_conditions and branches_with_slots:
            # Создаём узел-решение для ветвления
            decision_node_id = f"{node_id}_decision"
            lines.append(f"    {decision_node_id}{{{{\"Проверка условий\"}}}}")
            lines.append(f"    {node_id} --> {decision_node_id}")
            edge_count += 1
            
            for branch_idx, branch in enumerate(branches_with_slots):
                slot_label = _extract_slot_condition_label(branch['slot_conditions'])
                slot_label = _sanitize_label(slot_label, 30)
                
                # Переходы из этой ветки
                for redirect in branch.get('redirects', []):
                    target_node_id = _sanitize_node_id(redirect)
                    if redirect not in all_node_ids:
                        external_targets.add(redirect)
                    lines.append(f"    {decision_node_id} -->|{slot_label}| {target_node_id}")
                    edge_count += 1
        
        # Кнопки (из веток без условий слотов - это основной ответ с кнопками)
        if show_buttons:
            for branch in branches_without_slots:
                buttons = branch.get('buttons', [])
                if buttons:
                    # Дедупликация кнопок по action_id
                    unique_buttons = {}
                    for btn in buttons:
                        action_id = btn.get('action_id', '')
                        if action_id and action_id not in unique_buttons:
                            unique_buttons[action_id] = btn
                    
                    buttons = list(unique_buttons.values())
                    if not buttons:
                        continue
                    
                    # Создаём узел с кнопками
                    buttons_node_id = f"{node_id}_buttons"
                    btn_texts = [_sanitize_label(b.get('text', ''), 15) for b in buttons[:4]]
                    if len(buttons) > 4:
                        btn_texts.append('...')
                    btn_label = ' / '.join(btn_texts)
                    lines.append(f"    {buttons_node_id}[/\"{btn_label}\"/]")
                    lines.append(f"    {node_id} --> {buttons_node_id}")
                    edge_count += 1
                    
                    # Переходы из кнопок
                    for btn in buttons:
                        action_id = btn.get('action_id', '')
                        btn_text = _sanitize_label(btn.get('text', ''), 15)
                        if action_id:
                            target_node_id = _sanitize_node_id(action_id)
                            if action_id not in all_node_ids:
                                external_targets.add(action_id)
                            lines.append(f"    {buttons_node_id} -->|{btn_text}| {target_node_id}")
                            edge_count += 1
        
        lines.append("")
    
    # Добавляем внешние целевые узлы (интенты которых нет в файле)
    if external_targets:
        lines.append("    %% External target intents (not in current file)")
        for ext_id in external_targets:
            ext_node_id = _sanitize_node_id(ext_id)
            short_id = _sanitize_label(ext_id, 30)
            lines.append(f"    {ext_node_id}((\"{short_id}\"))")
        lines.append("")
    
    # Стили
    lines.append("    %% Styles")
    for intent in intent_list:
        intent_id = intent.get('intent_id', '')
        node_id = _sanitize_node_id(intent_id)
        record_type = intent.get('record_type', '')
        
        if 'main' in record_type.lower() or 'regexp' in record_type.lower():
            lines.append(f"    style {node_id} fill:#4CAF50,stroke:#2E7D32,color:#fff")
        else:
            lines.append(f"    style {node_id} fill:#2196F3,stroke:#1565C0,color:#fff")
    
    # Стиль для внешних узлов
    for ext_id in external_targets:
        ext_node_id = _sanitize_node_id(ext_id)
        lines.append(f"    style {ext_node_id} fill:#FFC107,stroke:#F57C00,color:#000")
    
    # Легенда
    lines.append("")
    lines.append("    %% Legend:")
    lines.append("    %% Green rounded = Main intent (entry point)")
    lines.append("    %% Blue rectangle = Dialog intent")
    lines.append("    %% Yellow circle = External intent (target)")
    lines.append("    %% Diamond = Decision/condition node")
    lines.append("    %% Parallelogram = Buttons/actions")
    lines.append("")
    lines.append(f"    %% Total intents: {len(intent_list)}")
    lines.append(f"    %% External targets: {len(external_targets)}")
    lines.append(f"    %% Total edges: {edge_count}")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    print(f"\n📊 Детальная диаграмма создана:")
    print(f"   Интентов: {len(intent_list)}")
    print(f"   Внешних целей: {len(external_targets)}")
    print(f"   Рёбер: {edge_count}")
    print(f"   Файл: {output_path}")


def export_intent_flow_diagram(
    intent: Dict,
    output_path: str,
) -> None:
    """
    Экспорт диаграммы для одного интента с полной логикой обработки.
    
    Показывает все ветвления, условия и переходы внутри одного интента.
    """
    from .analyzers import extract_detailed_flow
    
    flow = extract_detailed_flow(intent)
    intent_id = flow['intent_id']
    title = _sanitize_label(flow['title'], 60)
    
    lines = ["flowchart TD"]
    lines.append(f"    %% Intent Flow: {intent_id}")
    lines.append(f"    %% Title: {title}")
    lines.append("")
    
    main_node_id = _sanitize_node_id(intent_id)
    
    # Главный узел интента
    lines.append(f"    {main_node_id}([\"🎯 {title}\"])")
    lines.append(f"    style {main_node_id} fill:#4CAF50,stroke:#2E7D32,color:#fff")
    lines.append("")
    
    # Входные условия (regex)
    entry_conditions = flow.get('entry_conditions', [])
    if entry_conditions:
        lines.append("    %% Entry Conditions")
        entry_node_id = f"{main_node_id}_entry"
        lines.append(f"    {entry_node_id}{{{{\"📝 Условие входа\"}}}}")
        
        for idx, cond in enumerate(entry_conditions):
            cond_node_id = f"{entry_node_id}_{idx}"
            pattern = _sanitize_label(cond['pattern'][:50], 50)
            if cond['type'] == 'regex':
                lines.append(f"    {cond_node_id}[\"`RegExp: {pattern}`\"]")
            else:
                lines.append(f"    {cond_node_id}[\"`Text: {pattern}`\"]")
            lines.append(f"    {cond_node_id} --> {entry_node_id}")
        
        lines.append(f"    {entry_node_id} --> {main_node_id}")
        lines.append("")
    
    # Обработка ответов/ветвлений
    branches = flow.get('branches', [])
    
    # Разделяем ветки: с условиями слотов и без
    conditional_branches = [b for b in branches if b.get('slot_conditions')]
    default_branches = [b for b in branches if not b.get('slot_conditions')]
    
    # Отслеживаем уже добавленные целевые узлы для дедупликации
    processed_targets = set()
    
    # Ветка по умолчанию (без условий) - обычно с кнопками
    for idx, branch in enumerate(default_branches):
        buttons = branch.get('buttons', [])
        redirects = branch.get('redirects', [])
        
        if buttons:
            # Дедупликация кнопок по action_id
            unique_buttons = {}
            for btn in buttons:
                action_id = btn.get('action_id', '')
                if action_id and action_id not in unique_buttons:
                    unique_buttons[action_id] = btn
            buttons = list(unique_buttons.values())
            
            if buttons:
                buttons_node_id = f"{main_node_id}_btns_{idx}"
                lines.append("    %% Default branch with buttons")
                lines.append(f"    {buttons_node_id}[/\"🔘 Выбор действия\"/]")
                lines.append(f"    {main_node_id} -->|\"без условий\"| {buttons_node_id}")
                lines.append(f"    style {buttons_node_id} fill:#E3F2FD,stroke:#1976D2")
                
                for btn in buttons:
                    btn_text = _sanitize_label(btn.get('text', ''), 20)
                    action_id = btn.get('action_id', '')
                    if action_id:
                        btn_target_id = _sanitize_node_id(action_id)
                        if action_id not in processed_targets:
                            lines.append(f"    {btn_target_id}((\"{_sanitize_label(action_id, 25)}\"))")
                            lines.append(f"    style {btn_target_id} fill:#FFC107,stroke:#F57C00")
                            processed_targets.add(action_id)
                        lines.append(f"    {buttons_node_id} -->|\"{btn_text}\"| {btn_target_id}")
                
                lines.append("")
        
        if redirects:
            for r in redirects:
                if r not in processed_targets:
                    r_node_id = _sanitize_node_id(r)
                    lines.append(f"    {r_node_id}((\"{_sanitize_label(r, 25)}\"))")
                    lines.append(f"    {main_node_id} --> {r_node_id}")
                    lines.append(f"    style {r_node_id} fill:#FFC107,stroke:#F57C00")
                    processed_targets.add(r)
    
    # Условные ветки (с проверкой слотов)
    if conditional_branches:
        lines.append("    %% Conditional branches")
        decision_node_id = f"{main_node_id}_check"
        lines.append(f"    {decision_node_id}{{{{\"⚙️ Проверка слотов\"}}}}")
        lines.append(f"    {main_node_id} --> {decision_node_id}")
        lines.append(f"    style {decision_node_id} fill:#FFF3E0,stroke:#E65100")
        lines.append("")
        
        for branch_idx, branch in enumerate(conditional_branches):
            slot_conds = branch.get('slot_conditions', [])
            redirects = branch.get('redirects', [])
            actions = branch.get('actions', [])
            
            # Форматируем условие - показываем полнее
            cond_parts = []
            for sc in slot_conds[:3]:
                slot_id = sc.get('slot_id', '')
                # Сокращаем только если очень длинный
                if len(slot_id) > 20:
                    slot_id = slot_id[-18:]
                values = sc.get('values', [])
                val = str(values[0])[:12] if values else '?'
                cond_parts.append(f"{slot_id}={val}")
            cond_label = _sanitize_label(' & '.join(cond_parts), 45)
            
            if redirects:
                for redirect in redirects:
                    target_node_id = _sanitize_node_id(redirect)
                    if redirect not in processed_targets:
                        lines.append(f"    {target_node_id}((\"{_sanitize_label(redirect, 25)}\"))")
                        lines.append(f"    style {target_node_id} fill:#FFC107,stroke:#F57C00")
                        processed_targets.add(redirect)
                    lines.append(f"    {decision_node_id} -->|\"{cond_label}\"| {target_node_id}")
            
            # Показываем действия (SET_SLOT, DELETE_SLOT)
            if actions:
                actions_node_id = f"{main_node_id}_act_{branch_idx}"
                action_labels = []
                for act in actions[:2]:
                    if act['type'] == 'set_slot':
                        action_labels.append(f"SET {act['slot']}")
                    elif act['type'] == 'delete_slot':
                        action_labels.append(f"DEL {act['slot']}")
                
                if action_labels:
                    act_label = _sanitize_label(', '.join(action_labels), 30)
                    lines.append(f"    {actions_node_id}[[\"{act_label}\"]]")
                    lines.append(f"    style {actions_node_id} fill:#E8F5E9,stroke:#43A047")
        
        lines.append("")
    
    # Статистика
    lines.append("")
    lines.append(f"    %% Statistics:")
    lines.append(f"    %% Entry conditions: {len(entry_conditions)}")
    lines.append(f"    %% Conditional branches: {len(conditional_branches)}")
    lines.append(f"    %% Default branches: {len(default_branches)}")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    print(f"\n📊 Диаграмма интента создана: {output_path}")

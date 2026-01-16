# utils/multi_format_exporter.py v1.0
"""
Multi-format diagram export for large dialog flows.
Supports: Graphviz DOT, GraphML, JSON (Cytoscape/D3.js), SVG/PNG.
"""

import json
import os
import subprocess
import math
from typing import Dict, List, Any, Optional, Iterable, Set, Tuple
from xml.etree import ElementTree as ET
from collections import defaultdict

from .dataclasses import Transition


def _safe_str(value: Any, default: str = '') -> str:
    """Безопасное преобразование в строку."""
    if value is None:
        return default
    if isinstance(value, float):
        if math.isnan(value):
            return default
        return str(value)
    if isinstance(value, str):
        return value
    try:
        return str(value)
    except Exception:
        return default


def _escape_dot_string(text: str) -> str:
    """Экранирование строки для Graphviz DOT."""
    if not text:
        return ""
    text = text.replace('\\', '\\\\')
    text = text.replace('"', '\\"')
    text = text.replace('\n', '\\n')
    text = text.replace('\r', '')
    return text


def _escape_xml(text: str) -> str:
    """Экранирование строки для XML."""
    if not text:
        return ""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&apos;')
    return text


def _truncate(text: str, max_len: int = 50) -> str:
    """Сокращение текста до указанной длины."""
    if not text:
        return ""
    if len(text) > max_len:
        return text[:max_len-3] + "..."
    return text


def _get_node_color(record_type: str, is_external: bool = False) -> Tuple[str, str]:
    """Получить цвета для узла (fill, border)."""
    if is_external:
        return "#FFC107", "#F57C00"  # Yellow for external
    
    record_type_lower = record_type.lower() if record_type else ""
    if 'main' in record_type_lower or 'regexp' in record_type_lower:
        return "#4CAF50", "#2E7D32"  # Green for main
    elif 'match' in record_type_lower:
        return "#2196F3", "#1565C0"  # Blue for match
    elif 'fallback' in record_type_lower or 'error' in record_type_lower:
        return "#F44336", "#C62828"  # Red for fallback
    else:
        return "#9E9E9E", "#616161"  # Gray for others


def _get_edge_style(transition_type: str) -> Tuple[str, str]:
    """Получить стиль ребра (style, color)."""
    styles = {
        'button_redirect': ('solid', '#1976D2'),
        'button_action': ('solid', '#1976D2'),
        'action_redirect': ('solid', '#1976D2'),
        'direct_redirect': ('bold', '#4CAF50'),
        'text_redirect': ('bold', '#4CAF50'),
        'conditional_redirect': ('dashed', '#FF9800'),
        'fallback': ('dotted', '#F44336'),
        'answer_redirect': ('solid', '#9C27B0'),
        'intent_match': ('solid', '#607D8B'),
    }
    return styles.get(transition_type, ('solid', '#757575'))


# =============================================================================
# GRAPHVIZ DOT EXPORT
# =============================================================================

def export_graphviz_dot(
    intents: Iterable[Dict],
    transitions: Iterable[Transition],
    output_path: str,
    graph_name: str = "DialogFlow",
    rankdir: str = "TB",  # TB, LR, BT, RL
    max_label_len: int = 40,
    cluster_by_type: bool = True,
) -> str:
    """
    Экспорт в формат Graphviz DOT.
    Поддерживает большие графы (тысячи узлов).
    
    Args:
        intents: Список интентов
        transitions: Список переходов
        output_path: Путь для сохранения .dot файла
        graph_name: Название графа
        rankdir: Направление графа (TB=сверху-вниз, LR=слева-направо)
        max_label_len: Максимальная длина метки
        cluster_by_type: Группировать по типам в subgraphs
    
    Returns:
        Путь к созданному файлу
    """
    lines = []
    lines.append(f'digraph "{graph_name}" {{')
    lines.append(f'    rankdir={rankdir};')
    lines.append('    node [shape=box, style="rounded,filled", fontname="Arial", fontsize=10];')
    lines.append('    edge [fontname="Arial", fontsize=8];')
    lines.append('    graph [fontname="Arial", splines=true, overlap=false];')
    lines.append('')
    
    intent_list = list(intents)
    transition_list = list(transitions)
    
    # Собираем все intent_id
    all_intent_ids = set()
    intent_by_id = {}
    for intent in intent_list:
        intent_id = _safe_str(intent.get('intent_id'), '')
        if intent_id:
            all_intent_ids.add(intent_id)
            intent_by_id[intent_id] = intent
    
    # Находим внешние цели
    external_targets = set()
    for t in transition_list:
        if t.target_id and t.target_id not in all_intent_ids:
            external_targets.add(t.target_id)
    
    # Группировка по типам
    if cluster_by_type:
        intents_by_type = defaultdict(list)
        for intent in intent_list:
            record_type = _safe_str(intent.get('record_type'), 'other')
            intents_by_type[record_type].append(intent)
        
        cluster_idx = 0
        for record_type, type_intents in intents_by_type.items():
            lines.append(f'    subgraph cluster_{cluster_idx} {{')
            lines.append(f'        label="{_escape_dot_string(record_type)}";')
            lines.append('        style=rounded;')
            lines.append('        color="#BDBDBD";')
            lines.append('')
            
            for intent in type_intents:
                intent_id = _safe_str(intent.get('intent_id'), '')
                title = _safe_str(intent.get('title'), intent_id)
                title = _truncate(title, max_label_len)
                
                fill_color, border_color = _get_node_color(record_type)
                node_id = _make_dot_node_id(intent_id)
                
                lines.append(f'        {node_id} [')
                lines.append(f'            label="{_escape_dot_string(title)}"')
                lines.append(f'            fillcolor="{fill_color}"')
                lines.append(f'            color="{border_color}"')
                lines.append(f'            tooltip="{_escape_dot_string(intent_id)}"')
                lines.append('        ];')
            
            lines.append('    }')
            lines.append('')
            cluster_idx += 1
    else:
        # Без кластеризации
        for intent in intent_list:
            intent_id = _safe_str(intent.get('intent_id'), '')
            title = _safe_str(intent.get('title'), intent_id)
            title = _truncate(title, max_label_len)
            record_type = _safe_str(intent.get('record_type'), '')
            
            fill_color, border_color = _get_node_color(record_type)
            node_id = _make_dot_node_id(intent_id)
            
            lines.append(f'    {node_id} [')
            lines.append(f'        label="{_escape_dot_string(title)}"')
            lines.append(f'        fillcolor="{fill_color}"')
            lines.append(f'        color="{border_color}"')
            lines.append(f'        tooltip="{_escape_dot_string(intent_id)}"')
            lines.append('    ];')
        lines.append('')
    
    # Внешние узлы
    if external_targets:
        lines.append('    // External targets')
        for ext_id in external_targets:
            node_id = _make_dot_node_id(ext_id)
            fill_color, border_color = _get_node_color('', is_external=True)
            short_label = _truncate(ext_id, max_label_len)
            
            lines.append(f'    {node_id} [')
            lines.append(f'        label="{_escape_dot_string(short_label)}"')
            lines.append(f'        fillcolor="{fill_color}"')
            lines.append(f'        color="{border_color}"')
            lines.append('        shape=ellipse')
            lines.append(f'        tooltip="{_escape_dot_string(ext_id)}"')
            lines.append('    ];')
        lines.append('')
    
    # Рёбра
    lines.append('    // Edges')
    for t in transition_list:
        src_id = _make_dot_node_id(t.source_id)
        tgt_id = _make_dot_node_id(t.target_id)
        style, color = _get_edge_style(t.transition_type)
        
        edge_attrs = [f'color="{color}"']
        
        if style == 'dashed':
            edge_attrs.append('style=dashed')
        elif style == 'dotted':
            edge_attrs.append('style=dotted')
        elif style == 'bold':
            edge_attrs.append('penwidth=2')
        
        if t.condition:
            label = _truncate(t.condition, 25)
            edge_attrs.append(f'label="{_escape_dot_string(label)}"')
        
        attrs_str = ', '.join(edge_attrs)
        lines.append(f'    {src_id} -> {tgt_id} [{attrs_str}];')
    
    lines.append('')
    lines.append('    // Legend')
    lines.append('    subgraph cluster_legend {')
    lines.append('        label="Legend";')
    lines.append('        style=rounded;')
    lines.append('        legend_main [label="Main Intent" fillcolor="#4CAF50" color="#2E7D32"];')
    lines.append('        legend_match [label="Match Intent" fillcolor="#2196F3" color="#1565C0"];')
    lines.append('        legend_external [label="External Target" fillcolor="#FFC107" color="#F57C00" shape=ellipse];')
    lines.append('    }')
    
    lines.append('}')
    
    # Запись файла
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"\n📊 Graphviz DOT диаграмма создана:")
    print(f"   Узлов: {len(intent_list) + len(external_targets)}")
    print(f"   Рёбер: {len(transition_list)}")
    print(f"   Файл: {output_path}")
    
    return output_path


def _make_dot_node_id(intent_id: str) -> str:
    """Создание валидного ID узла для DOT."""
    if not intent_id:
        return "unknown"
    # Заменяем недопустимые символы
    safe_id = ''.join(c if c.isalnum() or c == '_' else '_' for c in intent_id)
    if safe_id and safe_id[0].isdigit():
        safe_id = 'n_' + safe_id
    return safe_id if safe_id else "unknown"


# =============================================================================
# GRAPHVIZ RENDER (SVG/PNG)
# =============================================================================

def render_graphviz(
    dot_path: str,
    output_format: str = "svg",
    layout_engine: str = "dot",
    timeout_seconds: int = 60,
) -> Optional[str]:
    """
    Рендеринг DOT файла в SVG/PNG через Graphviz.
    
    Args:
        dot_path: Путь к .dot файлу
        output_format: Формат вывода (svg, png, pdf)
        layout_engine: Движок раскладки (dot, neato, fdp, sfdp, circo, twopi)
            - dot: иерархический (по умолчанию)
            - neato: spring model (для небольших графов)
            - fdp: force-directed (хорош для кластеров)
            - sfdp: масштабируемый force-directed (для больших графов!)
            - circo: круговая раскладка
            - twopi: радиальная раскладка
        timeout_seconds: Таймаут в секундах (по умолчанию 60)
    
    Returns:
        Путь к созданному файлу или None при ошибке
    """
    output_path = dot_path.rsplit('.', 1)[0] + '.' + output_format
    
    try:
        # Проверяем наличие Graphviz
        result = subprocess.run(
            [layout_engine, '-V'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        print(f"   Рендеринг {output_format.upper()} через {layout_engine} (таймаут {timeout_seconds}с)...")
        
        # Рендерим
        cmd = [layout_engine, f'-T{output_format}', dot_path, '-o', output_path]
        
        # Для больших графов добавляем оптимизации
        if layout_engine == 'sfdp':
            # sfdp оптимизации для больших графов
            cmd.extend([
                '-Goverlap=prism',      # Алгоритм удаления перекрытий
                '-Gsplines=false',       # Отключаем сплайны (быстрее)
                '-Gsep=+5',              # Минимальное расстояние
                '-Gnodesep=0.1',         # Расстояние между узлами
            ])
        elif layout_engine == 'fdp':
            cmd.extend([
                '-Goverlap=false',
                '-Gsplines=false',       # Отключаем сплайны для скорости
            ])
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=timeout_seconds
        )
        
        if result.returncode == 0:
            print(f"   ✅ Graphviz {output_format.upper()} создан: {output_path}")
            return output_path
        else:
            print(f"   ⚠️  Ошибка Graphviz: {result.stderr[:200]}")
            return None
            
    except FileNotFoundError:
        print(f"   ⚠️  Graphviz ({layout_engine}) не установлен")
        print(f"      Установите: apt install graphviz (Linux) / brew install graphviz (Mac)")
        return None
    except subprocess.TimeoutExpired:
        print(f"   ⚠️  Таймаут {timeout_seconds}с при рендеринге")
        print(f"      Граф слишком большой для автоматического рендеринга")
        print(f"      Используйте Gephi для просмотра .gexf файла")
        # Убиваем зависший процесс
        try:
            subprocess.run(['pkill', '-f', layout_engine], capture_output=True, timeout=5)
        except:
            pass
        return None
    except Exception as e:
        print(f"   ⚠️  Ошибка рендеринга: {e}")
        return None


# =============================================================================
# GRAPHML EXPORT (for yEd, Gephi, Cytoscape)
# =============================================================================

def export_graphml(
    intents: Iterable[Dict],
    transitions: Iterable[Transition],
    output_path: str,
) -> str:
    """
    Экспорт в формат GraphML.
    Поддерживается: yEd, Gephi, Cytoscape, NetworkX.
    """
    intent_list = list(intents)
    transition_list = list(transitions)
    
    # Собираем все intent_id
    all_intent_ids = set()
    for intent in intent_list:
        intent_id = _safe_str(intent.get('intent_id'), '')
        if intent_id:
            all_intent_ids.add(intent_id)
    
    # Находим внешние цели
    external_targets = set()
    for t in transition_list:
        if t.target_id and t.target_id not in all_intent_ids:
            external_targets.add(t.target_id)
    
    # Создаём XML
    graphml = ET.Element('graphml')
    graphml.set('xmlns', 'http://graphml.graphdrawing.org/xmlns')
    graphml.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    
    # Определяем атрибуты
    keys = [
        ('d0', 'node', 'title', 'string'),
        ('d1', 'node', 'record_type', 'string'),
        ('d2', 'node', 'is_external', 'boolean'),
        ('d3', 'node', 'color', 'string'),
        ('d4', 'edge', 'transition_type', 'string'),
        ('d5', 'edge', 'condition', 'string'),
        ('d6', 'edge', 'color', 'string'),
    ]
    
    for key_id, key_for, attr_name, attr_type in keys:
        key_elem = ET.SubElement(graphml, 'key')
        key_elem.set('id', key_id)
        key_elem.set('for', key_for)
        key_elem.set('attr.name', attr_name)
        key_elem.set('attr.type', attr_type)
    
    # Создаём граф
    graph = ET.SubElement(graphml, 'graph')
    graph.set('id', 'G')
    graph.set('edgedefault', 'directed')
    
    # Узлы
    for intent in intent_list:
        intent_id = _safe_str(intent.get('intent_id'), '')
        if not intent_id:
            continue
            
        title = _safe_str(intent.get('title'), intent_id)
        record_type = _safe_str(intent.get('record_type'), '')
        fill_color, _ = _get_node_color(record_type)
        
        node = ET.SubElement(graph, 'node')
        node.set('id', intent_id)
        
        data0 = ET.SubElement(node, 'data')
        data0.set('key', 'd0')
        data0.text = title
        
        data1 = ET.SubElement(node, 'data')
        data1.set('key', 'd1')
        data1.text = record_type
        
        data2 = ET.SubElement(node, 'data')
        data2.set('key', 'd2')
        data2.text = 'false'
        
        data3 = ET.SubElement(node, 'data')
        data3.set('key', 'd3')
        data3.text = fill_color
    
    # Внешние узлы
    for ext_id in external_targets:
        fill_color, _ = _get_node_color('', is_external=True)
        
        node = ET.SubElement(graph, 'node')
        node.set('id', ext_id)
        
        data0 = ET.SubElement(node, 'data')
        data0.set('key', 'd0')
        data0.text = ext_id
        
        data1 = ET.SubElement(node, 'data')
        data1.set('key', 'd1')
        data1.text = 'external'
        
        data2 = ET.SubElement(node, 'data')
        data2.set('key', 'd2')
        data2.text = 'true'
        
        data3 = ET.SubElement(node, 'data')
        data3.set('key', 'd3')
        data3.text = fill_color
    
    # Рёбра
    edge_idx = 0
    for t in transition_list:
        _, edge_color = _get_edge_style(t.transition_type)
        
        edge = ET.SubElement(graph, 'edge')
        edge.set('id', f'e{edge_idx}')
        edge.set('source', t.source_id)
        edge.set('target', t.target_id)
        
        data4 = ET.SubElement(edge, 'data')
        data4.set('key', 'd4')
        data4.text = t.transition_type
        
        if t.condition:
            data5 = ET.SubElement(edge, 'data')
            data5.set('key', 'd5')
            data5.text = t.condition
        
        data6 = ET.SubElement(edge, 'data')
        data6.set('key', 'd6')
        data6.text = edge_color
        
        edge_idx += 1
    
    # Запись файла
    tree = ET.ElementTree(graphml)
    ET.indent(tree, space="  ")
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    
    print(f"\n📊 GraphML диаграмма создана:")
    print(f"   Узлов: {len(intent_list) + len(external_targets)}")
    print(f"   Рёбер: {len(transition_list)}")
    print(f"   Файл: {output_path}")
    print(f"   Открыть: yEd, Gephi, Cytoscape")
    
    return output_path


# =============================================================================
# JSON EXPORT (for D3.js, Cytoscape.js, vis.js)
# =============================================================================

def export_json_graph(
    intents: Iterable[Dict],
    transitions: Iterable[Transition],
    output_path: str,
    format_type: str = "cytoscape",  # "cytoscape", "d3", "visjs"
) -> str:
    """
    Экспорт в JSON формат для веб-визуализации.
    
    Форматы:
        - cytoscape: Cytoscape.js формат
        - d3: D3.js force-directed формат
        - visjs: vis.js network формат
    """
    intent_list = list(intents)
    transition_list = list(transitions)
    
    # Собираем все intent_id
    all_intent_ids = set()
    for intent in intent_list:
        intent_id = _safe_str(intent.get('intent_id'), '')
        if intent_id:
            all_intent_ids.add(intent_id)
    
    # Находим внешние цели
    external_targets = set()
    for t in transition_list:
        if t.target_id and t.target_id not in all_intent_ids:
            external_targets.add(t.target_id)
    
    if format_type == "cytoscape":
        data = _export_cytoscape_json(intent_list, transition_list, external_targets)
    elif format_type == "d3":
        data = _export_d3_json(intent_list, transition_list, external_targets)
    elif format_type == "visjs":
        data = _export_visjs_json(intent_list, transition_list, external_targets)
    else:
        raise ValueError(f"Unknown format_type: {format_type}")
    
    # Запись файла
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 JSON ({format_type}) диаграмма создана:")
    print(f"   Узлов: {len(intent_list) + len(external_targets)}")
    print(f"   Рёбер: {len(transition_list)}")
    print(f"   Файл: {output_path}")
    
    return output_path


def _export_cytoscape_json(
    intents: List[Dict],
    transitions: List[Transition],
    external_targets: Set[str],
) -> Dict:
    """Формат Cytoscape.js."""
    elements = []
    
    # Узлы
    for intent in intents:
        intent_id = _safe_str(intent.get('intent_id'), '')
        if not intent_id:
            continue
            
        title = _safe_str(intent.get('title'), intent_id)
        record_type = _safe_str(intent.get('record_type'), '')
        fill_color, border_color = _get_node_color(record_type)
        
        elements.append({
            "data": {
                "id": intent_id,
                "label": _truncate(title, 40),
                "title": title,
                "record_type": record_type,
                "is_external": False,
                "color": fill_color,
                "borderColor": border_color,
            }
        })
    
    # Внешние узлы
    for ext_id in external_targets:
        fill_color, border_color = _get_node_color('', is_external=True)
        elements.append({
            "data": {
                "id": ext_id,
                "label": _truncate(ext_id, 30),
                "title": ext_id,
                "record_type": "external",
                "is_external": True,
                "color": fill_color,
                "borderColor": border_color,
            }
        })
    
    # Рёбра
    for idx, t in enumerate(transitions):
        _, edge_color = _get_edge_style(t.transition_type)
        elements.append({
            "data": {
                "id": f"e{idx}",
                "source": t.source_id,
                "target": t.target_id,
                "transition_type": t.transition_type,
                "condition": t.condition or "",
                "color": edge_color,
            }
        })
    
    return {"elements": elements}


def _export_d3_json(
    intents: List[Dict],
    transitions: List[Transition],
    external_targets: Set[str],
) -> Dict:
    """Формат D3.js force-directed."""
    nodes = []
    links = []
    node_index = {}
    
    # Узлы
    idx = 0
    for intent in intents:
        intent_id = _safe_str(intent.get('intent_id'), '')
        if not intent_id:
            continue
            
        title = _safe_str(intent.get('title'), intent_id)
        record_type = _safe_str(intent.get('record_type'), '')
        fill_color, _ = _get_node_color(record_type)
        
        nodes.append({
            "id": intent_id,
            "label": _truncate(title, 40),
            "group": record_type,
            "color": fill_color,
            "is_external": False,
        })
        node_index[intent_id] = idx
        idx += 1
    
    # Внешние узлы
    for ext_id in external_targets:
        fill_color, _ = _get_node_color('', is_external=True)
        nodes.append({
            "id": ext_id,
            "label": _truncate(ext_id, 30),
            "group": "external",
            "color": fill_color,
            "is_external": True,
        })
        node_index[ext_id] = idx
        idx += 1
    
    # Рёбра
    for t in transitions:
        if t.source_id in node_index and t.target_id in node_index:
            _, edge_color = _get_edge_style(t.transition_type)
            links.append({
                "source": t.source_id,
                "target": t.target_id,
                "type": t.transition_type,
                "color": edge_color,
            })
    
    return {"nodes": nodes, "links": links}


def _export_visjs_json(
    intents: List[Dict],
    transitions: List[Transition],
    external_targets: Set[str],
) -> Dict:
    """Формат vis.js network."""
    nodes = []
    edges = []
    
    # Узлы
    for intent in intents:
        intent_id = _safe_str(intent.get('intent_id'), '')
        if not intent_id:
            continue
            
        title = _safe_str(intent.get('title'), intent_id)
        record_type = _safe_str(intent.get('record_type'), '')
        fill_color, border_color = _get_node_color(record_type)
        
        nodes.append({
            "id": intent_id,
            "label": _truncate(title, 40),
            "title": title,  # tooltip
            "group": record_type,
            "color": {
                "background": fill_color,
                "border": border_color,
            }
        })
    
    # Внешние узлы
    for ext_id in external_targets:
        fill_color, border_color = _get_node_color('', is_external=True)
        nodes.append({
            "id": ext_id,
            "label": _truncate(ext_id, 30),
            "title": ext_id,
            "group": "external",
            "shape": "ellipse",
            "color": {
                "background": fill_color,
                "border": border_color,
            }
        })
    
    # Рёбра
    for idx, t in enumerate(transitions):
        _, edge_color = _get_edge_style(t.transition_type)
        edges.append({
            "id": f"e{idx}",
            "from": t.source_id,
            "to": t.target_id,
            "label": _truncate(t.condition or "", 20),
            "color": edge_color,
            "arrows": "to",
        })
    
    return {"nodes": nodes, "edges": edges}


# =============================================================================
# GEXF EXPORT (for Gephi)
# =============================================================================

def export_gexf(
    intents: Iterable[Dict],
    transitions: Iterable[Transition],
    output_path: str,
) -> str:
    """
    Экспорт в формат GEXF (Graph Exchange XML Format).
    Оптимизирован для Gephi - лучший инструмент для больших графов.
    """
    intent_list = list(intents)
    transition_list = list(transitions)
    
    # Собираем все intent_id
    all_intent_ids = set()
    for intent in intent_list:
        intent_id = _safe_str(intent.get('intent_id'), '')
        if intent_id:
            all_intent_ids.add(intent_id)
    
    # Находим внешние цели
    external_targets = set()
    for t in transition_list:
        if t.target_id and t.target_id not in all_intent_ids:
            external_targets.add(t.target_id)
    
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<gexf xmlns="http://www.gexf.net/1.2draft" version="1.2">')
    lines.append('  <meta lastmodifieddate="2024-01-01">')
    lines.append('    <creator>json2mermaid</creator>')
    lines.append('    <description>Dialog Flow Graph</description>')
    lines.append('  </meta>')
    lines.append('  <graph mode="static" defaultedgetype="directed">')
    
    # Атрибуты узлов
    lines.append('    <attributes class="node">')
    lines.append('      <attribute id="0" title="record_type" type="string"/>')
    lines.append('      <attribute id="1" title="is_external" type="boolean"/>')
    lines.append('    </attributes>')
    
    # Атрибуты рёбер
    lines.append('    <attributes class="edge">')
    lines.append('      <attribute id="0" title="transition_type" type="string"/>')
    lines.append('      <attribute id="1" title="condition" type="string"/>')
    lines.append('    </attributes>')
    
    # Узлы
    lines.append('    <nodes>')
    for intent in intent_list:
        intent_id = _safe_str(intent.get('intent_id'), '')
        if not intent_id:
            continue
            
        title = _safe_str(intent.get('title'), intent_id)
        record_type = _safe_str(intent.get('record_type'), '')
        fill_color, _ = _get_node_color(record_type)
        
        # Конвертируем цвет в RGB
        r, g, b = int(fill_color[1:3], 16), int(fill_color[3:5], 16), int(fill_color[5:7], 16)
        
        lines.append(f'      <node id="{_escape_xml(intent_id)}" label="{_escape_xml(_truncate(title, 50))}">')
        lines.append(f'        <attvalues>')
        lines.append(f'          <attvalue for="0" value="{_escape_xml(record_type)}"/>')
        lines.append(f'          <attvalue for="1" value="false"/>')
        lines.append(f'        </attvalues>')
        lines.append(f'        <viz:color r="{r}" g="{g}" b="{b}" xmlns:viz="http://www.gexf.net/1.2draft/viz"/>')
        lines.append(f'      </node>')
    
    # Внешние узлы
    for ext_id in external_targets:
        fill_color, _ = _get_node_color('', is_external=True)
        r, g, b = int(fill_color[1:3], 16), int(fill_color[3:5], 16), int(fill_color[5:7], 16)
        
        lines.append(f'      <node id="{_escape_xml(ext_id)}" label="{_escape_xml(_truncate(ext_id, 30))}">')
        lines.append(f'        <attvalues>')
        lines.append(f'          <attvalue for="0" value="external"/>')
        lines.append(f'          <attvalue for="1" value="true"/>')
        lines.append(f'        </attvalues>')
        lines.append(f'        <viz:color r="{r}" g="{g}" b="{b}" xmlns:viz="http://www.gexf.net/1.2draft/viz"/>')
        lines.append(f'      </node>')
    
    lines.append('    </nodes>')
    
    # Рёбра
    lines.append('    <edges>')
    for idx, t in enumerate(transitions):
        lines.append(f'      <edge id="{idx}" source="{_escape_xml(t.source_id)}" target="{_escape_xml(t.target_id)}">')
        lines.append(f'        <attvalues>')
        lines.append(f'          <attvalue for="0" value="{_escape_xml(t.transition_type)}"/>')
        if t.condition:
            lines.append(f'          <attvalue for="1" value="{_escape_xml(t.condition)}"/>')
        lines.append(f'        </attvalues>')
        lines.append(f'      </edge>')
    lines.append('    </edges>')
    
    lines.append('  </graph>')
    lines.append('</gexf>')
    
    # Запись файла
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"\n📊 GEXF диаграмма создана (для Gephi):")
    print(f"   Узлов: {len(intent_list) + len(external_targets)}")
    print(f"   Рёбер: {len(transition_list)}")
    print(f"   Файл: {output_path}")
    print(f"   Открыть: Gephi (https://gephi.org/)")
    
    return output_path


# =============================================================================
# EXPORT ALL FORMATS
# =============================================================================

def export_all_formats(
    intents: Iterable[Dict],
    transitions: Iterable[Transition],
    output_dir: str,
    base_name: str = "dialog_flow",
    render_images: bool = True,
    max_nodes_for_render: int = 300,
    render_timeout: int = 60,
) -> Dict[str, str]:
    """
    Экспорт во все поддерживаемые форматы.
    
    Args:
        intents: Список интентов
        transitions: Список переходов
        output_dir: Директория для сохранения
        base_name: Базовое имя файлов
        render_images: Рендерить SVG/PNG через Graphviz
        max_nodes_for_render: Максимум узлов для автоматического рендеринга (default: 300)
        render_timeout: Таймаут рендеринга в секундах (default: 60)
    
    Returns:
        Словарь {формат: путь_к_файлу}
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Конвертируем в списки один раз
    intent_list = list(intents)
    transition_list = list(transitions)
    node_count = len(intent_list)
    
    # Подсчитываем внешние цели
    all_intent_ids = {_safe_str(i.get('intent_id'), '') for i in intent_list}
    external_count = len({t.target_id for t in transition_list if t.target_id not in all_intent_ids})
    total_nodes = node_count + external_count
    
    results = {}
    
    print("\n" + "=" * 80)
    print("🖌️  Генерация диаграмм в нескольких форматах")
    print("=" * 80)
    print(f"   Интентов: {node_count}, Внешних целей: {external_count}, Всего узлов: {total_nodes}")
    print(f"   Рёбер: {len(transition_list)}")
    
    # 1. Graphviz DOT (всегда создаём - это быстро)
    dot_path = os.path.join(output_dir, f"{base_name}.dot")
    results['dot'] = export_graphviz_dot(intent_list, transition_list, dot_path)
    
    # 2. Render SVG/PNG (только для небольших графов)
    if render_images and total_nodes <= max_nodes_for_render:
        print(f"\n📷 Автоматический рендеринг изображений ({total_nodes} узлов <= {max_nodes_for_render})...")
        
        # Выбор движка в зависимости от размера
        if total_nodes > 200:
            engine = 'sfdp'  # Scalable force-directed
        elif total_nodes > 50:
            engine = 'fdp'   # Force-directed
        else:
            engine = 'dot'   # Hierarchical
        
        svg_path = render_graphviz(dot_path, 'svg', engine, render_timeout)
        if svg_path:
            results['svg'] = svg_path
        
        # PNG только для маленьких графов (большие PNG огромные)
        if total_nodes <= 100:
            png_path = render_graphviz(dot_path, 'png', engine, render_timeout)
            if png_path:
                results['png'] = png_path
    elif render_images:
        print(f"\n⏭️  Пропуск автоматического рендеринга ({total_nodes} узлов > {max_nodes_for_render})")
        print(f"   Используйте Gephi или yEd для просмотра больших графов")
    
    # 3. GraphML (для yEd)
    graphml_path = os.path.join(output_dir, f"{base_name}.graphml")
    results['graphml'] = export_graphml(intent_list, transition_list, graphml_path)
    
    # 4. GEXF (для Gephi - лучший для больших графов)
    gexf_path = os.path.join(output_dir, f"{base_name}.gexf")
    results['gexf'] = export_gexf(intent_list, transition_list, gexf_path)
    
    # 5. JSON форматы (для веб-визуализации)
    cytoscape_path = os.path.join(output_dir, f"{base_name}_cytoscape.json")
    results['cytoscape'] = export_json_graph(intent_list, transition_list, cytoscape_path, 'cytoscape')
    
    d3_path = os.path.join(output_dir, f"{base_name}_d3.json")
    results['d3'] = export_json_graph(intent_list, transition_list, d3_path, 'd3')
    
    visjs_path = os.path.join(output_dir, f"{base_name}_visjs.json")
    results['visjs'] = export_json_graph(intent_list, transition_list, visjs_path, 'visjs')
    
    # Итоги
    print("\n" + "=" * 80)
    print("📊 Созданные файлы:")
    print("=" * 80)
    for fmt, path in results.items():
        if path:
            size_kb = os.path.getsize(path) / 1024
            print(f"   {fmt.upper():12s}: {path} ({size_kb:.1f} KB)")
    
    print("\n💡 Рекомендации по просмотру:")
    if total_nodes < 100:
        print("   ✅ Граф небольшой - можно открыть SVG в браузере")
    elif total_nodes < 1000:
        print("   📊 Средний граф - рекомендуется yEd + GraphML")
        print("      Скачать: https://www.yworks.com/products/yed/download")
    else:
        print("   🔥 Большой граф - используйте Gephi + GEXF")
        print("      Скачать: https://gephi.org/users/download/")
        print("      Gephi поддерживает графы с миллионами узлов!")
    
    print("\n   Веб-визуализация: используйте JSON файлы с Cytoscape.js / vis.js / D3.js")
    
    return results

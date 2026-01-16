# utils/graph_analyzer.py v5.1
"""Graph analysis module for dialog flow structure"""

from typing import Dict, List, Set, Tuple, Any, Optional, Iterable
from collections import defaultdict, deque

def build_graph(
    intents: List[Dict],
    redirect_map: Dict[str, List[str]],
    transitions: Optional[Iterable[Tuple[str, str]]] = None,
) -> Dict[str, Any]:
    """Build directed graph from intents and redirects"""
    graph = {
        'nodes': set(),
        'edges': [],
        'entry_points': [],
        'dead_ends': [],
        'node_info': {}
    }
    
    # Collect all nodes
    for intent in intents:
        intent_id = intent.get('intent_id')
        record_type = intent.get('record_type', '')
        
        graph['nodes'].add(intent_id)
        graph['node_info'][intent_id] = {
            'record_type': record_type,
            'title': intent.get('title', ''),
            'has_inputs': len(intent.get('inputs', [])) > 0,
            'has_answers': len(intent.get('answers', [])) > 0
        }
        
        # Entry points are main intents with inputs
        if record_type == 'cc_regexp_main' and len(intent.get('inputs', [])) > 0:
            graph['entry_points'].append(intent_id)
    
    edge_set = set()

    # Build edges from redirect_map
    for source, targets in redirect_map.items():
        for target in targets:
            if target in graph['nodes']:
                edge_set.add((source, target))

    # Add edges from extracted transitions
    if transitions:
        for source, target in transitions:
            if source in graph['nodes'] and target in graph['nodes']:
                edge_set.add((source, target))

    graph['edges'] = list(edge_set)
    
    # Find dead ends (nodes with no outgoing edges)
    nodes_with_outgoing = {src for src, _ in graph['edges']}
    graph['dead_ends'] = [node for node in graph['nodes'] if node not in nodes_with_outgoing]
    
    return graph

def calculate_graph_depth(graph: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate maximum and average depth from entry points"""
    entry_points = graph['entry_points']
    edges = graph['edges']
    
    # Build adjacency list
    adj = defaultdict(list)
    for src, tgt in edges:
        adj[src].append(tgt)
    
    depths = []
    
    for entry in entry_points:
        # BFS to find maximum depth from this entry point
        queue = deque([(entry, 0)])
        visited = {entry}
        max_depth = 0
        
        while queue:
            node, depth = queue.popleft()
            max_depth = max(max_depth, depth)
            
            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1))
        
        depths.append(max_depth)
    
    return {
        'max_depth': max(depths) if depths else 0,
        'min_depth': min(depths) if depths else 0,
        'avg_depth': round(sum(depths) / len(depths), 2) if depths else 0,
        'depths_by_entry': dict(zip(entry_points, depths))
    }

def find_isolated_subgraphs(graph: Dict[str, Any]) -> List[Set[str]]:
    """Find disconnected components in the graph"""
    nodes = graph['nodes']
    edges = graph['edges']
    
    # Build undirected adjacency list
    adj = defaultdict(set)
    for src, tgt in edges:
        adj[src].add(tgt)
        adj[tgt].add(src)
    
    visited = set()
    components = []
    
    def dfs(node: str, component: Set[str]):
        visited.add(node)
        component.add(node)
        for neighbor in adj.get(node, []):
            if neighbor not in visited:
                dfs(neighbor, component)
    
    for node in nodes:
        if node not in visited:
            component = set()
            dfs(node, component)
            components.append(component)
    
    return components

def analyze_graph_structure(
    intents: List[Dict],
    redirect_map: Dict[str, List[str]],
    transitions: Optional[Iterable[Tuple[str, str]]] = None,
) -> Dict[str, Any]:
    """Comprehensive graph structure analysis"""
    print("\n" + "="*80)
    print("📊 АНАЛИЗ СТРУКТУРЫ ГРАФА")
    print("="*80)
    
    # Build graph
    graph = build_graph(intents, redirect_map, transitions)
    
    print(f"\n[1/3] Базовая структура:")
    print(f"   Узлов: {len(graph['nodes'])}")
    print(f"   Рёбер: {len(graph['edges'])}")
    print(f"   Точек входа: {len(graph['entry_points'])}")
    print(f"   Тупиков: {len(graph['dead_ends'])}")
    
    # Calculate depth
    print(f"\n[2/3] Глубина диалогов:")
    depth_info = calculate_graph_depth(graph)
    print(f"   Максимальная: {depth_info['max_depth']}")
    print(f"   Средняя: {depth_info['avg_depth']}")
    print(f"   Минимальная: {depth_info['min_depth']}")
    
    # Find isolated subgraphs
    print(f"\n[3/3] Связность графа:")
    components = find_isolated_subgraphs(graph)
    isolated = [c for c in components if len(c) > 1 and not any(node in graph['entry_points'] for node in c)]
    
    if isolated:
        print(f"⚠️  Изолированных подграфов: {len(isolated)}")
        for i, comp in enumerate(isolated[:3], 1):
            print(f"   {i}. Размер: {len(comp)} узлов")
    else:
        print(f"✅ Все интенты связаны с точками входа")
    
    print("="*80 + "\n")
    
    return {
        'graph': graph,
        'depth': depth_info,
        'components': components,
        'isolated_subgraphs': isolated,
        'is_connected': len(isolated) == 0
    }

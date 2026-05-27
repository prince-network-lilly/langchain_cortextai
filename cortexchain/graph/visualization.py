"""Graph visualization — ASCII representation of StateGraph structure."""

from typing import Dict, List, Set
from cortexchain.graph.state_graph import END


def visualize_graph(graph) -> str:
    """Generate an ASCII visualization of a StateGraph or CompiledGraph.

    Returns a string like:
        [START] --> classify
        classify --> {router}
          --> positive --> respond_positive
          --> negative --> respond_negative
        respond_positive --> [END]
        respond_negative --> [END]
    """
    nodes = getattr(graph, "nodes", {})
    edges = getattr(graph, "edges", {})
    conditional_edges = getattr(graph, "conditional_edges", {})
    entry = getattr(graph, "entry_point", None)

    lines = []
    lines.append("=" * 50)
    lines.append("  GRAPH VISUALIZATION")
    lines.append("=" * 50)
    lines.append("")

    # Entry point
    if entry:
        lines.append(f"  [START] --> [{entry}]")

    # Process each node
    visited: Set[str] = set()
    if entry:
        _trace_node(entry, edges, conditional_edges, nodes, lines, visited)

    # Catch any unvisited nodes
    for node in nodes:
        if node not in visited:
            _trace_node(node, edges, conditional_edges, nodes, lines, visited)

    lines.append("")
    lines.append("=" * 50)
    lines.append(f"  Nodes: {len(nodes)} | Edges: {len(edges)} | Conditional: {len(conditional_edges)}")
    lines.append("=" * 50)

    return "\n".join(lines)


def _trace_node(
    node: str,
    edges: Dict,
    conditional_edges: Dict,
    nodes: Dict,
    lines: List[str],
    visited: Set[str],
) -> None:
    if node in visited:
        return
    visited.add(node)

    if node in conditional_edges:
        cond = conditional_edges[node]
        mapping = cond.get("mapping", {})
        lines.append(f"  [{node}] --?--> (conditional)")
        if mapping:
            for condition_val, target in mapping.items():
                target_display = "[END]" if target == END else f"[{target}]"
                lines.append(f"    | {condition_val} --> {target_display}")
        else:
            lines.append(f"    | (dynamic routing)")
    elif node in edges:
        target = edges[node]
        target_display = "[END]" if target == END else f"[{target}]"
        lines.append(f"  [{node}] --> {target_display}")
    else:
        lines.append(f"  [{node}] --> (no outgoing edge)")

    # Follow fixed edges
    if node in edges and edges[node] != END:
        _trace_node(edges[node], edges, conditional_edges, nodes, lines, visited)

    # Follow conditional edges
    if node in conditional_edges:
        mapping = conditional_edges[node].get("mapping", {})
        for target in mapping.values():
            if target != END:
                _trace_node(target, edges, conditional_edges, nodes, lines, visited)


def print_graph(graph) -> None:
    """Print the graph visualization to stdout."""
    print(visualize_graph(graph))

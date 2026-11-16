import networkx as nx
import plotly.graph_objects as go
from typing import List, Dict, Any, Optional

NODE_COLORS = {
    "Student": "#2563EB",     # Blue
    "Professor": "#4F46E5",   # Indigo
    "Course": "#059669",      # Green
    "Department": "#D97706",  # Amber
    "Entity": "#64748B"       # Slate
}


def render_knowledge_graph(
    nodes_data: List[Dict[str, Any]],
    edges_data: List[Dict[str, Any]],
    highlight_node: Optional[str] = None,
    height: int = 650
) -> go.Figure:
    G = nx.DiGraph()

    for n in nodes_data:
        G.add_node(
            n["id"],
            label=n.get("label", n["id"]),
            ntype=n.get("type", "Entity"),
            unary=n.get("unary_predicates", [])
        )

    for e in edges_data:
        G.add_edge(
            e["source"],
            e["target"],
            predicate=e.get("predicate", ""),
            is_inferred=e.get("is_inferred", False)
        )

    if len(G.nodes) == 0:
        fig = go.Figure()
        fig.add_annotation(text="No nodes or facts to display.", showarrow=False, font=dict(size=14))
        fig.update_layout(height=height)
        return fig

    # Layout with stable seed
    pos = nx.spring_layout(G, k=0.9, iterations=60, seed=42)

    # Edge traces (base facts vs inferred facts)
    base_edge_x, base_edge_y = [], []
    inf_edge_x, inf_edge_y = [], []
    middle_node_x, middle_node_y, edge_hover_text = [], [], []

    for u, v, data in G.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        is_inf = data.get("is_inferred", False)
        pred = data.get("predicate", "")

        if is_inf:
            inf_edge_x.extend([x0, x1, None])
            inf_edge_y.extend([y0, y1, None])
        else:
            base_edge_x.extend([x0, x1, None])
            base_edge_y.extend([y0, y1, None])

        # Middle point for edge labels
        middle_node_x.append((x0 + x1) / 2)
        middle_node_y.append((y0 + y1) / 2)
        inf_badge = " [Inferred]" if is_inf else " [Base]"
        edge_hover_text.append(f"{u} ➔ {pred} ➔ {v}{inf_badge}")

    base_edge_trace = go.Scatter(
        x=base_edge_x, y=base_edge_y,
        line=dict(width=1.5, color="#94A3B8"),
        hoverinfo='none',
        mode='lines',
        name='Base Relationship'
    )

    inf_edge_trace = go.Scatter(
        x=inf_edge_x, y=inf_edge_y,
        line=dict(width=1.8, color="#10B981", dash='dash'),
        hoverinfo='none',
        mode='lines',
        name='Inferred Relationship'
    )

    edge_label_trace = go.Scatter(
        x=middle_node_x, y=middle_node_y,
        mode='markers',
        hoverinfo='text',
        hovertext=edge_hover_text,
        marker=dict(size=8, color='rgba(0,0,0,0)'),
        showlegend=False
    )

    # Node traces
    node_x, node_y, node_colors, node_sizes, node_text, node_hover = [], [], [], [], [], []

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        ntype = G.nodes[node].get("ntype", "Entity")
        unary = G.nodes[node].get("unary", [])

        # Color & highlight
        color = NODE_COLORS.get(ntype, "#64748B")
        is_highlighted = highlight_node and highlight_node.lower() == str(node).lower()

        if is_highlighted:
            node_sizes.append(36)
            node_colors.append("#DC2626")  # Red highlight
        else:
            node_sizes.append(26)
            node_colors.append(color)

        node_text.append(node)
        unary_str = f"<br>Predicates: {', '.join(unary)}" if unary else ""
        node_hover.append(f"<b>{node}</b><br>Type: {ntype}{unary_str}")

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        hovertext=node_hover,
        text=node_text,
        textposition="top center",
        marker=dict(
            color=node_colors,
            size=node_sizes,
            line=dict(width=2, color='#FFFFFF')
        ),
        name='Entities'
    )

    fig = go.Figure(data=[base_edge_trace, inf_edge_trace, edge_label_trace, node_trace])

    fig.update_layout(
        showlegend=True,
        hovermode='closest',
        margin=dict(b=10, l=10, r=10, t=25),
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig

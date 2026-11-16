import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import streamlit as st
from frontend.api_client import api
from frontend.components.ui import (
    render_section_header, render_backend_down_banner
)
from frontend.components.graph import render_knowledge_graph

RELATIONSHIPS = [
    "Enrolled", "Teaches", "BelongsTo", "OfferedBy",
    "Studies", "HeadOf", "Prerequisite", "AssociatedWith"
]


def render_knowledge_graph_page():
    render_section_header(
        "Interactive Knowledge Graph",
        "Visual topological network of college entities and First-Order Logic relationships powered by NetworkX and Plotly"
    )

    health = api.check_health()
    if not health.get("success"):
        render_backend_down_banner(api.base_url)
        return

    c_filt1, c_filt2, c_filt3 = st.columns([3, 2, 2])
    with c_filt1:
        selected_preds = st.multiselect(
            "Filter Predicates / Edge Types",
            RELATIONSHIPS,
            default=["Enrolled", "Teaches", "BelongsTo", "OfferedBy", "HeadOf", "Prerequisite"],
            key="graph_pred_filter"
        )
    with c_filt2:
        search_node = st.text_input("🎯 Highlight Entity Node", "", placeholder="e.g. Ravi, Meena, AI, CSE", key="graph_search_node")
    with c_filt3:
        include_inferred = st.checkbox("Include Inferred Relationships (Dashed)", value=True, key="graph_inc_inf")

    pred_query = ",".join(selected_preds) if selected_preds else ""
    with st.spinner("Constructing topological graph..."):
        resp = api.get_knowledge_graph(predicates=pred_query, include_inferred=include_inferred)

        if resp.get("success"):
            data = resp["data"]
            nodes = data.get("nodes", [])
            edges = data.get("edges", [])

            # Metrics
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Total Nodes", len(nodes))
            with m2:
                st.metric("Total Edges", len(edges))
            with m3:
                base_edges = sum(1 for e in edges if not e.get("is_inferred"))
                st.metric("Base Edges", base_edges)
            with m4:
                inf_edges = sum(1 for e in edges if e.get("is_inferred"))
                st.metric("Inferred Edges", inf_edges)

            # Render Graph
            fig = render_knowledge_graph(
                nodes_data=nodes,
                edges_data=edges,
                highlight_node=search_node.strip() if search_node else None,
                height=700
            )
            st.plotly_chart(fig, use_container_width=True)

            # Legend card
            st.markdown("""
            <div style="background:white; border:1px solid #E2E8F0; border-radius:12px; padding:16px; margin-top:10px;">
                <h4 style="margin-top:0;">Entity Color Legend:</h4>
                <div style="display:flex; gap:20px; flex-wrap:wrap;">
                    <div><span style="display:inline-block; width:14px; height:14px; border-radius:50%; background:#2563EB; margin-right:6px;"></span><strong>Student</strong> (e.g. Ravi, Rahul)</div>
                    <div><span style="display:inline-block; width:14px; height:14px; border-radius:50%; background:#4F46E5; margin-right:6px;"></span><strong>Professor</strong> (e.g. Meena, Kiran)</div>
                    <div><span style="display:inline-block; width:14px; height:14px; border-radius:50%; background:#059669; margin-right:6px;"></span><strong>Course</strong> (e.g. AI, DSA)</div>
                    <div><span style="display:inline-block; width:14px; height:14px; border-radius:50%; background:#D97706; margin-right:6px;"></span><strong>Department</strong> (e.g. CSE, ISE)</div>
                    <div><span style="display:inline-block; width:14px; height:14px; border-radius:50%; background:#64748B; margin-right:6px;"></span><strong>General Entity</strong></div>
                </div>
                <div style="margin-top:10px; font-size:0.85rem; color:#64748B;">
                    <strong>Edge Styles:</strong> Solid grey line = Base fact | Dashed green line = Derived by FOL inference engine
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error(resp.get("error", {}).get("message", "Failed to load graph."))


if __name__ == "__main__":
    render_knowledge_graph_page()


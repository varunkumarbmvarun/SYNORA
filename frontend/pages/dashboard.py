import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import streamlit as st
from frontend.api_client import api
from frontend.components.ui import (
    render_section_header, render_metric_card, render_status_pill, render_backend_down_banner
)
from frontend.components.charts import (
    create_facts_by_predicate_chart, create_base_vs_inferred_chart,
    create_students_per_dept_chart, create_courses_per_prof_chart
)
from frontend.components.graph import render_knowledge_graph


def render_dashboard():
    render_section_header(
        "College FOL Knowledge Base Dashboard",
        "Real-time overview of college entities, First-Order Logic facts, rules, and inference metrics"
    )

    resp = api.get_dashboard_stats()
    if not resp.get("success"):
        render_backend_down_banner(api.base_url)
        return

    data = resp["data"]

    # 7 Metric Cards
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    with c1:
        render_metric_card("Students", data.get("students_count", 0), "Enrolled", "🎓", "#2563EB")
    with c2:
        render_metric_card("Professors", data.get("professors_count", 0), "Faculty", "👨‍🏫", "#4F46E5")
    with c3:
        render_metric_card("Courses", data.get("courses_count", 0), "Offered", "📚", "#059669")
    with c4:
        render_metric_card("Departments", data.get("departments_count", 0), "Academic", "🏛️", "#D97706")
    with c5:
        render_metric_card("Total Facts", data.get("facts_count", 0), "FOL Ground", "📜", "#0F172A")
    with c6:
        render_metric_card("Inferred Facts", data.get("inferred_facts_count", 0), "Derived", "⚡", "#10B981")
    with c7:
        render_metric_card("Rules Active", f"{data.get('enabled_rules_count', 0)}/{data.get('rules_count', 0)}", "FOL Axioms", "⚙️", "#7C3AED")

    st.markdown("<br>", unsafe_allow_html=True)

    # 4 Charts
    col_left, col_right = st.columns(2)
    with col_left:
        fig_pred = create_facts_by_predicate_chart(data.get("facts_by_predicate", {}))
        st.plotly_chart(fig_pred, use_container_width=True)

        fig_dept = create_students_per_dept_chart(data.get("students_per_department", {}))
        st.plotly_chart(fig_dept, use_container_width=True)

    with col_right:
        fig_comp = create_base_vs_inferred_chart(
            data.get("base_facts_count", 0),
            data.get("inferred_facts_count", 0)
        )
        st.plotly_chart(fig_comp, use_container_width=True)

        fig_prof = create_courses_per_prof_chart(data.get("courses_per_professor", {}))
        st.plotly_chart(fig_prof, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Last inference summary & Mini graph preview
    col_inf, col_graph = st.columns([1, 1])

    with col_inf:
        st.subheader("⚡ Last Inference Run")
        last_inf = data.get("last_inference_run")
        if last_inf:
            st.markdown(f"""
            <div style="background:white; border:1px solid #E2E8F0; border-radius:12px; padding:18px;">
                <p><strong>Type:</strong> <span class="pill pill-indigo">{last_inf.get('run_type', '').upper()}</span></p>
                <p><strong>Goal:</strong> <code>{last_inf.get('goal') or 'Full Knowledge Base Forward Fixpoint'}</code></p>
                <p><strong>Iterations:</strong> {last_inf.get('iterations')} | <strong>New Facts:</strong> {last_inf.get('new_facts_count')}</p>
                <p><strong>Execution Time:</strong> {last_inf.get('execution_ms')} ms</p>
                <p style="margin-bottom:0; font-size:0.85rem; color:#64748B;">Timestamp: {last_inf.get('created_at', '')}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No inference runs recorded yet. Head over to the Inference Engine to run forward chaining.")

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📝 Recent Activities")
        activities = data.get("recent_activities", [])
        if activities:
            for act in activities[:6]:
                st.markdown(
                    f"• **{act.get('action')}** on *{act.get('entity')}*: {act.get('detail')} "
                    f"<span style='color:#94A3B8; font-size:0.8rem;'>({act.get('created_at', '')[:19]})</span>",
                    unsafe_allow_html=True
                )
        else:
            st.write("No recent activity.")

    with col_graph:
        st.subheader("🕸️ Knowledge Graph Snapshot")
        graph_resp = api.get_knowledge_graph(include_inferred=True)
        if graph_resp.get("success"):
            g_data = graph_resp["data"]
            fig_g = render_knowledge_graph(g_data.get("nodes", []), g_data.get("edges", []), height=380)
            st.plotly_chart(fig_g, use_container_width=True)
        else:
            st.write("Graph preview unavailable.")

    # Recent queries & facts
    st.markdown("<br>", unsafe_allow_html=True)
    c_q, c_f = st.columns(2)
    with c_q:
        st.subheader("❓ Recent Natural Language Queries")
        queries = data.get("recent_queries", [])
        if queries:
            for q in queries:
                pill = render_status_pill(q.get("truth_value", ""))
                st.markdown(f"""
                <div style="background:white; border:1px solid #E2E8F0; border-radius:10px; padding:12px; margin-bottom:10px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <strong>{q.get('question')}</strong>
                        {pill}
                    </div>
                    <div style="font-size:0.85rem; color:#4F46E5; font-family:monospace; margin-top:4px;">{q.get('logical_query')}</div>
                    <div style="font-size:0.85rem; color:#475569; margin-top:4px;">{q.get('answer')}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.write("No queries asked yet.")

    with c_f:
        st.subheader("📜 Recent Knowledge Base Facts")
        facts = data.get("recent_facts", [])
        if facts:
            for f in facts:
                inf_tag = '<span class="pill pill-green">INFERRED</span>' if f.get("is_inferred") else '<span class="pill pill-indigo">BASE</span>'
                st.markdown(f"""
                <div style="background:white; border:1px solid #E2E8F0; border-radius:10px; padding:10px 14px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
                    <span class="fol-badge">{f.get('fol')}</span>
                    {inf_tag}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.write("No facts recorded.")


if __name__ == "__main__":
    render_dashboard()


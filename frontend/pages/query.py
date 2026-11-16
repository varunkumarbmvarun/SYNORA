import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import streamlit as st
import pandas as pd
from frontend.api_client import api
from frontend.components.ui import (
    render_section_header, render_backend_down_banner, render_status_pill
)
from frontend.pages.inference import render_tree_node

SAMPLE_QUESTIONS = [
    "Who is Varun?",
    "Who teaches AI?",
    "Which students are enrolled in AI?",
    "Which students study AI?",
    "Which professors belong to CSE?",
    "Which courses are offered by CSE?",
    "Who is the head of CSE?",
    "Is Ravi enrolled in AI?",
    "Is Meena a professor?",
    "Is Ravi associated with CSE?",
    "Which courses have prerequisites?",
    "What does Meena teach?",
    "What courses is Ravi studying?",
    "What are the prerequisites of AI?",
    "Who is Ravi's professor?"
]


def render_query_system():
    render_section_header(
        "Natural-Language Query System",
        "Ask questions in natural English; the system normalizes entities, compiles into logical queries, executes SLD backward chaining, and explains the deduction."
    )

    health = api.check_health()
    if not health.get("success"):
        render_backend_down_banner(api.base_url)
        return

    tab_ask, tab_history = st.tabs(["💬 Ask Questions", "📜 Query History"])

    # 1. Ask Tab
    with tab_ask:
        st.markdown("#### Sample Questions (Click to try):")
        cols1 = st.columns(4)
        for i, q in enumerate(SAMPLE_QUESTIONS[:4]):
            with cols1[i]:
                if st.button(q, key=f"sq_{i}"):
                    st.session_state["query_input_text"] = q

        cols2 = st.columns(4)
        for i, q in enumerate(SAMPLE_QUESTIONS[4:8]):
            with cols2[i]:
                if st.button(q, key=f"sq_{i+4}"):
                    st.session_state["query_input_text"] = q

        cols3 = st.columns(4)
        for i, q in enumerate(SAMPLE_QUESTIONS[8:12]):
            with cols3[i]:
                if st.button(q, key=f"sq_{i+8}"):
                    st.session_state["query_input_text"] = q

        cols4 = st.columns(2)
        for i, q in enumerate(SAMPLE_QUESTIONS[12:]):
            with cols4[i]:
                if st.button(q, key=f"sq_{i+12}"):
                    st.session_state["query_input_text"] = q

        st.markdown("<br>", unsafe_allow_html=True)
        default_val = st.session_state.get("query_input_text", "Which students study AI?")
        user_query = st.text_input("Enter your question or direct FOL query:", value=default_val, key="main_query_input")

        if st.button("🚀 Execute Logical Query", type="primary", key="btn_exec_query"):
            if not user_query.strip():
                st.warning("Please type a question.")
            else:
                with st.spinner("Parsing intent and executing logical resolution..."):
                    resp = api.execute_query(user_query.strip())
                    if resp.get("success"):
                        d = resp["data"]
                        truth = d.get("truth_value", "")

                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown(f"""
                        <div style="background:white; border:1px solid #E2E8F0; border-radius:14px; padding:22px; box-shadow:0 2px 10px rgba(0,0,0,0.03);">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <h3 style="margin:0; color:#1E293B;">Logical Query: <code>{d.get('logical_query')}</code></h3>
                                {render_status_pill(truth)}
                            </div>
                            <p style="color:#64748B; margin-top:4px; font-size:0.9rem;">Original: "{d.get('question')}" | Execution: {d.get('execution_ms')} ms</p>
                            <hr style="border:0; border-top:1px solid #F1F5F9; margin:12px 0;">
                            <h4 style="margin:8px 0; color:#0F172A;">Deductive Answer:</h4>
                            <p style="font-size:1.15rem; color:#1E293B; font-weight:600;">{', '.join(d.get('answers', []))}</p>
                            <h4 style="margin:8px 0; color:#0F172A;">Explanation:</h4>
                            <p style="color:#334155; line-height:1.5;">{d.get('explanation')}</p>
                        </div>
                        """, unsafe_allow_html=True)

                        st.markdown("<br>", unsafe_allow_html=True)
                        c_mf, c_rf = st.columns(2)
                        with c_mf:
                            st.markdown("#### 📜 Ground Supporting Facts:")
                            m_facts = d.get("matching_facts", [])
                            if m_facts:
                                for f in m_facts:
                                    st.markdown(f"• <span class='fol-badge'>{f.get('fact')}</span>", unsafe_allow_html=True)
                            else:
                                st.write("No direct ground facts needed or found.")

                        with c_rf:
                            st.markdown("#### ⚙️ Rules Applied:")
                            rules = d.get("rules_applied", [])
                            if rules:
                                for r in rules:
                                    st.markdown(f"• **{r.get('name') or 'Rule ' + str(r.get('id'))}**: `{r.get('text')}`")
                            else:
                                st.write("Direct ground match (no rule chaining required).")

                        st.markdown("<br>", unsafe_allow_html=True)
                        with st.expander("🌳 View Resolution Proof Tree", expanded=True):
                            tree = d.get("proof_tree", {})
                            if tree:
                                render_tree_node(tree)
                            else:
                                st.write("Proof tree unavailable.")
                    else:
                        err = resp.get("error", {})
                        st.error(f"Query Failed: {err.get('message')}")
                        details = err.get("details", {})
                        if details and "suggestions" in details:
                            st.markdown("#### Try asking one of these questions:")
                            for s in details["suggestions"]:
                                st.markdown(f"• `{s}`")

    # 2. History Tab
    with tab_history:
        st.subheader("Query History")
        h_resp = api.get_query_history(limit=50)
        if h_resp.get("success"):
            history = h_resp.get("data", [])
            if history:
                c_clear, _ = st.columns([1, 4])
                with c_clear:
                    if st.button("🗑️ Clear History", key="btn_clear_hist"):
                        api.clear_query_history()
                        st.success("Query history cleared.")
                        st.rerun()

                table_data = []
                for h in history:
                    table_data.append({
                        "ID": h["id"],
                        "Question": h["question"],
                        "Logical Query": h["logical_query"],
                        "Truth Value": h["truth_value"],
                        "Answer": h["answer"],
                        "Timestamp": h.get("created_at", "")[:19]
                    })
                st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
            else:
                st.info("No queries in history.")
        else:
            st.error("Failed to load query history.")


if __name__ == "__main__":
    render_query_system()


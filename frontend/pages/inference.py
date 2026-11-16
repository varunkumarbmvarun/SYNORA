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


def render_tree_node(node: dict, depth: int = 0):
    """Recursively render a proof tree node with clean Streamlit expanders."""
    goal = node.get("goal", "")
    status = node.get("status", "")
    method = node.get("method", "")
    rule_name = node.get("rule_name") or f"Rule {node.get('rule_id')}"
    rule_text = node.get("rule_text", "")
    fact_matched = node.get("fact_matched", "")
    subst = node.get("substitution", {})
    children = node.get("children", [])

    if method == "fact":
        label = f"🌿 Fact Match: {fact_matched} (Proved)"
        st.markdown(f"{'&nbsp;' * (depth * 4)}• **{label}**", unsafe_allow_html=True)
    elif method == "rule":
        label = f"⚙️ {rule_name}: {goal} via [{rule_text}]"
        with st.expander(label, expanded=True):
            if subst:
                st.caption(f"Substitutions: `{subst}`")
            for ch in children:
                render_tree_node(ch, depth + 1)
    elif method == "conjunction":
        with st.expander(f"🧩 Conjunction Proof: {goal}", expanded=True):
            for ch in children:
                render_tree_node(ch, depth + 1)
    else:
        st.markdown(f"{'&nbsp;' * (depth * 4)}❌ **Failed Goal:** `{goal}` [{status}]", unsafe_allow_html=True)


def render_inference():
    render_section_header("FOL Inference Engine", "Execute Forward Chaining to derive new knowledge or Backward Chaining for goal-directed resolution")

    health = api.check_health()
    if not health.get("success"):
        render_backend_down_banner(api.base_url)
        return

    tab_fwd, tab_bwd, tab_hist = st.tabs(["⏩ Forward Chaining", "⏪ Backward Chaining (SLD)", "📜 Run History & Maintenance"])

    # 1. Forward Chaining Tab
    with tab_fwd:
        st.subheader("Forward Chaining Fixpoint Deduction")
        st.markdown(
            "Iteratively applies all enabled FOL rules to base facts until no new knowledge can be derived. "
            "Derived facts are tagged with `is_inferred=True` and linked to their triggering rule."
        )

        c_run, c_clr = st.columns([2, 1])
        with c_run:
            if st.button("🚀 Run Forward Inference Engine", type="primary", key="btn_run_fwd"):
                with st.spinner("Executing Forward Chaining resolution..."):
                    res = api.run_forward_inference()
                    if res.get("success"):
                        data = res["data"]
                        st.success(f"Inference completed in {data['execution_ms']} ms across {data['iterations']} iterations!")

                        m1, m2, m3, m4 = st.columns(4)
                        with m1:
                            st.metric("Base Facts", data["original_fact_count"])
                        with m2:
                            st.metric("New Derived Facts", data["new_facts_count"])
                        with m3:
                            st.metric("Total Facts After", data["total_facts_after"])
                        with m4:
                            st.metric("Iterations to Fixpoint", data["iterations"])

                        # Iteration Steps
                        st.markdown("#### 🔄 Iteration-by-Iteration Breakdown")
                        for step in data.get("steps", []):
                            with st.expander(f"Iteration #{step['iteration']}: {step['facts_derived_count']} facts derived", expanded=True):
                                if step["facts"]:
                                    for f in step["facts"]:
                                        st.markdown(f"• <span class='fol-badge'>{f}</span>", unsafe_allow_html=True)
                                else:
                                    st.write("No new facts derived (fixpoint achieved).")

                        # Newly Inferred Facts Details
                        st.markdown("#### 📜 Newly Inferred Facts & Premises")
                        new_facts = data.get("newly_inferred_facts", [])
                        if new_facts:
                            t_data = []
                            for nf in new_facts:
                                t_data.append({
                                    "Derived Fact": nf["fact"],
                                    "Rule Used": nf.get("rule_name") or f"Rule {nf.get('rule_id')}",
                                    "Premises Matched": ", ".join(nf.get("premises", [])),
                                    "Iteration": nf.get("iteration")
                                })
                            st.dataframe(pd.DataFrame(t_data), use_container_width=True, hide_index=True)
                        else:
                            st.info("No new facts derived; knowledge base was already at fixpoint.")
                    else:
                        st.error(res.get("error", {}).get("message", "Forward inference failed."))

        with c_clr:
            if st.button("🧹 Clear Inferred Facts", key="btn_clr_inf"):
                clr_res = api.clear_inferred_facts()
                if clr_res.get("success"):
                    st.success(f"Cleared {clr_res['data']['deleted_count']} inferred facts!")
                    st.rerun()
                else:
                    st.error("Failed to clear inferred facts.")

    # 2. Backward Chaining Tab
    with tab_bwd:
        st.subheader("Goal-Directed SLD Backward Resolution")
        st.markdown(
            "Resolves a specific goal by backward search through enabled rules down to known ground facts. "
            "Works on the fly without needing forward chaining to run first."
        )

        sample_goals = [
            "Studies(Ravi, AI)",
            "Studies(x, AI)",
            "Teaches(x, AI)",
            "Faculty(Meena)",
            "AssociatedWith(Ravi, CSE)",
            "Studies(Ravi, DBMS)",
            "Studies(Ghost, AI)"
        ]

        st.caption("Quick sample goals:")
        cols = st.columns(len(sample_goals))
        for i, sg in enumerate(sample_goals):
            with cols[i]:
                if st.button(sg, key=f"btn_goal_{i}"):
                    st.session_state["bwd_goal_input"] = sg

        goal_input = st.text_input(
            "Enter Goal Atom",
            value=st.session_state.get("bwd_goal_input", "Studies(Ravi, AI)"),
            key="input_bwd_goal"
        )

        if st.button("🔍 Prove Goal via Backward Chaining", type="primary", key="btn_prove_bwd"):
            with st.spinner("Proving goal..."):
                bwd_res = api.run_backward_inference(goal_input)
                if bwd_res.get("success"):
                    d = bwd_res["data"]
                    truth = d.get("truth_value", "")
                    exec_time = d.get("execution_ms", 0.0)

                    c_tv, c_tm = st.columns([3, 1])
                    with c_tv:
                        st.markdown(f"### Truth Value: {render_status_pill(truth)}", unsafe_allow_html=True)
                    with c_tm:
                        st.caption(f"Execution time: {exec_time} ms")

                    # Variable Bindings
                    bindings = d.get("bindings", [])
                    if bindings:
                        st.markdown("#### 🎯 Variable Solutions / Bindings:")
                        st.dataframe(pd.DataFrame(bindings), use_container_width=True, hide_index=True)

                    # Proof Tree
                    st.markdown("#### 🌳 Resolution Proof Tree:")
                    tree = d.get("proof_tree", {})
                    if tree:
                        render_tree_node(tree)
                    else:
                        st.write("No proof tree available.")
                else:
                    err = bwd_res.get("error", {})
                    st.error(f"Proof Execution Error: {err.get('message')}")

    # 3. History Tab
    with tab_hist:
        st.subheader("Past Inference Runs")
        hist_resp = api.get_inference_results(limit=30)
        if hist_resp.get("success"):
            runs = hist_resp.get("data", [])
            if runs:
                t_runs = []
                for r in runs:
                    t_runs.append({
                        "ID": r["id"],
                        "Type": r["run_type"].upper(),
                        "Goal": r["goal"] or "Forward Fixpoint",
                        "Iterations": r["iterations"],
                        "New Facts": r["new_facts_count"],
                        "Execution (ms)": r["execution_ms"],
                        "Timestamp": r.get("created_at", "")[:19]
                    })
                st.dataframe(pd.DataFrame(t_runs), use_container_width=True, hide_index=True)
            else:
                st.info("No inference history yet.")
        else:
            st.error("Error loading inference history.")


if __name__ == "__main__":
    render_inference()


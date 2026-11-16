import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import streamlit as st
import pandas as pd
from frontend.api_client import api
from frontend.components.ui import (
    render_section_header, render_backend_down_banner
)


def render_fol_rules():
    render_section_header("First-Order Logic Rules", "Manage system axioms and custom inference rules, toggle rule activation, and test dry-runs")

    health = api.check_health()
    if not health.get("success"):
        render_backend_down_banner(api.base_url)
        return

    tab_rules, tab_add, tab_test = st.tabs(["📜 Rule Base", "➕ Add Custom Rule", "🧪 Test Rule (Dry-Run)"])

    # 1. Rules Tab
    with tab_rules:
        resp = api.get_rules()
        if resp.get("success"):
            rules = resp.get("data", [])
            st.caption(f"Total Rules: {len(rules)}")

            for r in rules:
                r_id = r["id"]
                is_custom = r.get("is_custom", False)
                is_enabled = r.get("enabled", True)

                col1, col2, col3 = st.columns([5, 1, 1])
                with col1:
                    custom_badge = '<span class="pill pill-indigo">Custom</span>' if is_custom else '<span class="pill pill-amber">Predefined</span>'
                    st.markdown(
                        f"**#{r_id} {r['name']}** &nbsp; {custom_badge}<br>"
                        f"<span class='fol-badge' style='font-size:1rem;'>{r['rule_text']}</span>",
                        unsafe_allow_html=True
                    )
                with col2:
                    new_state = st.toggle("Enabled", value=is_enabled, key=f"toggle_rule_{r_id}")
                    if new_state != is_enabled:
                        up_res = api.update_rule(r_id, enabled=new_state)
                        if up_res.get("success"):
                            st.success(f"Rule #{r_id} {'enabled' if new_state else 'disabled'}!")
                            st.rerun()
                        else:
                            st.error("Failed to toggle rule.")
                with col3:
                    if is_custom:
                        if st.button("🗑️", key=f"del_rule_{r_id}", help="Delete this custom rule"):
                            del_res = api.delete_rule(r_id)
                            if del_res.get("success"):
                                st.success("Rule deleted!")
                                st.rerun()
                            else:
                                st.error("Failed to delete.")
                    else:
                        st.write("")

                st.markdown("<hr style='margin: 8px 0; border: 0; border-top: 1px solid #F1F5F9;'>", unsafe_allow_html=True)
        else:
            st.error(resp.get("error", {}).get("message", "Error loading rules."))

    # 2. Add Rule Tab
    with tab_add:
        st.subheader("Add a Custom First-Order Logic Rule")
        st.markdown("""
        **Syntax Examples:**
        - Standard Unicode: `∀x ∀y (Enrolled(x,y) → Studies(x,y))`
        - ASCII Arrow: `Enrolled(x,y) -> Studies(x,y)`
        - Multi-premise Conjunction: `Teaches(x,y) & Enrolled(z,y) -> AssociatedWith(z,x)`
        *(Variables must begin with lowercase letters; Constants/Predicates begin with uppercase).*
        """)

        with st.form("add_rule_form"):
            rule_name = st.text_input("Rule Name / Description", placeholder="e.g. Student associated with course professor")
            rule_text = st.text_area("FOL Rule Statement", placeholder="e.g. Teaches(x,y) & Enrolled(z,y) -> AssociatedWith(z,x)")
            is_enabled_chk = st.checkbox("Enable immediately", value=True)

            submit_rule = st.form_submit_button("➕ Save Rule to Engine", type="primary")
            if submit_rule:
                if not rule_name.strip() or not rule_text.strip():
                    st.warning("Please provide a name and rule expression.")
                else:
                    res = api.create_rule(rule_name.strip(), rule_text.strip(), enabled=is_enabled_chk)
                    if res.get("success"):
                        st.success(f"Rule '{rule_name}' successfully parsed, validated, and saved!")
                        st.rerun()
                    else:
                        err = res.get("error", {})
                        st.error(f"Rule Validation Error: {err.get('message')}")

    # 3. Test Rule Tab
    with tab_test:
        st.subheader("🧪 Test Rule Dry-Run")
        st.markdown("Test an FOL rule against the live database without persisting any changes. Discover what substitutions would match and which facts would be derived.")

        test_input = st.text_input(
            "Enter candidate rule text",
            value="Teaches(x,y) & Enrolled(z,y) -> AssociatedWith(z,x)",
            key="input_test_rule"
        )

        if st.button("🚀 Run Dry-Run Analysis", type="primary"):
            with st.spinner("Executing unification & conjunction matching..."):
                t_res = api.test_rule(test_input)
                if t_res.get("success"):
                    d = t_res["data"]
                    st.success(f"Rule parsed successfully: `{d['parsed_rule']}`")

                    c_m1, c_m2 = st.columns(2)
                    with c_m1:
                        st.metric("Total Pattern Matches", d.get("total_matches", 0))
                    with c_m2:
                        st.metric("New Facts Would Derive", d.get("new_facts_count", 0))

                    if d.get("new_facts"):
                        st.markdown("#### ✨ Newly Derived Facts:")
                        for nf in d["new_facts"]:
                            st.markdown(f"• <span class='fol-badge'>{nf}</span>", unsafe_allow_html=True)

                    details = d.get("details", [])
                    if details:
                        st.markdown("#### 🔍 Substitution Details (First 20):")
                        table_data = []
                        for det in details[:20]:
                            table_data.append({
                                "Head Fact": det.get("head"),
                                "Premises Matched": ", ".join(det.get("premises", [])),
                                "Variable Bindings": str(det.get("substitution")),
                                "Already In KB?": "Yes" if det.get("is_already_known") else "New"
                            })
                        st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
                else:
                    err = t_res.get("error", {})
                    st.error(f"Parse/Validation Failure: {err.get('message')}")


if __name__ == "__main__":
    render_fol_rules()


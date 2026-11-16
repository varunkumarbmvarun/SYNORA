import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import json
import pandas as pd
import streamlit as st
from frontend.api_client import api
from frontend.components.ui import (
    render_section_header, render_backend_down_banner
)

PREDICATES = [
    "Student", "Professor", "Course", "Department", "Faculty",
    "Enrolled", "Teaches", "BelongsTo", "OfferedBy",
    "Studies", "HeadOf", "Prerequisite", "AssociatedWith"
]
UNARY_PREDICATES = ["Student", "Professor", "Course", "Department", "Faculty"]


def render_knowledge_base():
    render_section_header("First-Order Logic Knowledge Base", "View, search, add, edit, import and export logical ground facts")

    health = api.check_health()
    if not health.get("success"):
        render_backend_down_banner(api.base_url)
        return

    tab_all, tab_add, tab_manage, tab_import, tab_export = st.tabs([
        "📜 All Facts", "➕ Add Fact", "✏️ Edit / Delete", "📥 Import Facts", "📤 Export Facts"
    ])

    # 1. All Facts Tab
    with tab_all:
        col_f1, col_f2, col_f3, col_f4 = st.columns([2, 2, 2, 1])
        with col_f1:
            search = st.text_input("🔍 Search facts", "", key="kb_search")
        with col_f2:
            pred_filter = st.selectbox("Predicate filter", ["All"] + PREDICATES, key="kb_pred_filter")
        with col_f3:
            inf_filter = st.selectbox("Type filter", ["All", "Base Facts Only", "Inferred Only"], key="kb_inf_filter")
        with col_f4:
            page_size = st.selectbox("Rows", [25, 50, 100], key="kb_page_size")

        predicate = None if pred_filter == "All" else pred_filter
        inferred = None
        if inf_filter == "Base Facts Only":
            inferred = False
        elif inf_filter == "Inferred Only":
            inferred = True

        resp = api.get_facts(
            predicate=predicate,
            search=search,
            inferred=inferred,
            page=1,
            page_size=page_size
        )

        if resp.get("success"):
            data = resp["data"]
            total = data.get("total", 0)
            facts = data.get("facts", [])
            st.caption(f"Showing {len(facts)} of {total} facts")

            if facts:
                df = pd.DataFrame(facts)[["id", "fol", "predicate", "arg1", "arg2", "is_inferred", "source"]]
                df.columns = ["ID", "FOL Representation", "Predicate", "Argument 1", "Argument 2", "Inferred?", "Source"]
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No facts match the selected filters.")
        else:
            st.error(resp.get("error", {}).get("message", "Failed to fetch facts."))

    # 2. Add Fact Tab
    with tab_add:
        st.subheader("Add a New Ground FOL Fact")
        col_a1, col_a2, col_a3 = st.columns([1, 1, 1])

        with col_a1:
            sel_pred = st.selectbox("Predicate", PREDICATES, key="add_fact_pred")
        is_unary = sel_pred in UNARY_PREDICATES

        with col_a2:
            arg1_val = st.text_input("Argument 1 (Subject / Entity)", "", key="add_fact_arg1", help="e.g. Ravi, Meena, AI, CSE")

        with col_a3:
            arg2_val = ""
            if not is_unary:
                arg2_val = st.text_input("Argument 2 (Object / Target)", "", key="add_fact_arg2", help="e.g. AI, CSE, DBMS")

        # Live FOL preview
        arg2_display = f", {arg2_val or 'y'}" if not is_unary else ""
        preview = f"{sel_pred}({arg1_val or 'x'}{arg2_display})"
        st.markdown(f"**FOL Preview:** <span class='fol-badge'>{preview}</span>", unsafe_allow_html=True)

        if st.button("➕ Insert Fact to Knowledge Base", type="primary"):
            if not arg1_val.strip() or (not is_unary and not arg2_val.strip()):
                st.warning("Please provide all required arguments.")
            else:
                res = api.create_fact(sel_pred, arg1_val.strip(), arg2_val.strip() if not is_unary else None)
                if res.get("success"):
                    st.success(f"Fact '{preview}' created successfully!")
                    st.rerun()
                else:
                    st.error(res.get("error", {}).get("message", "Error adding fact."))

    # 3. Edit / Delete Tab
    with tab_manage:
        st.subheader("Manage Existing Fact")
        fact_id_input = st.number_input("Fact ID to edit or delete", min_value=1, step=1, key="manage_fact_id")

        all_resp = api.get_facts(page_size=200)
        found_fact = None
        if all_resp.get("success"):
            for f in all_resp["data"]["facts"]:
                if f["id"] == fact_id_input:
                    found_fact = f
                    break

        if found_fact:
            st.markdown(f"**Selected Fact:** <span class='fol-badge'>{found_fact['fol']}</span>", unsafe_allow_html=True)
            st.write(f"Source: `{found_fact['source']}` | Inferred: `{found_fact['is_inferred']}`")

            c_e1, c_e2, c_e3 = st.columns(3)
            with c_e1:
                e_pred = st.selectbox("Predicate", PREDICATES, index=PREDICATES.index(found_fact["predicate"]) if found_fact["predicate"] in PREDICATES else 0, key="edit_f_pred")
            with c_e2:
                e_arg1 = st.text_input("Argument 1", found_fact["arg1"], key="edit_f_arg1")
            with c_e3:
                e_arg2 = st.text_input("Argument 2", found_fact["arg2"] or "", key="edit_f_arg2", disabled=(e_pred in UNARY_PREDICATES))

            c_b1, c_b2 = st.columns(2)
            with c_b1:
                if st.button("💾 Save Changes", key="btn_save_fact"):
                    up_res = api.update_fact(fact_id_input, e_pred, e_arg1.strip(), e_arg2.strip() if e_pred not in UNARY_PREDICATES else None)
                    if up_res.get("success"):
                        st.success("Fact updated successfully!")
                        st.rerun()
                    else:
                        st.error(up_res.get("error", {}).get("message", "Failed to update."))

            with c_b2:
                confirm_del = st.checkbox("Confirm deletion of this fact", key="chk_del_fact")
                if st.button("🗑️ Delete Fact", type="primary", key="btn_del_fact", disabled=not confirm_del):
                    del_res = api.delete_fact(fact_id_input)
                    if del_res.get("success"):
                        st.success("Fact deleted successfully!")
                        st.rerun()
                    else:
                        st.error(del_res.get("error", {}).get("message", "Failed to delete."))
        else:
            st.info("Enter a valid Fact ID above to inspect, edit, or delete it.")

    # 4. Import Tab
    with tab_import:
        st.subheader("Import Facts into Knowledge Base")

        c_imp1, c_imp2 = st.columns(2)
        with c_imp1:
            st.markdown("#### Option A: Reload Seed Sample Data")
            st.write("Resets the knowledge base to the official sample dataset with CSE departments, professors, courses, enrollments, and 15 FOL rules.")
            confirm_seed = st.checkbox("I understand this resets and reloads the default data", key="chk_seed_reset")
            if st.button("🔄 Reload College Sample Data", disabled=not confirm_seed):
                with st.spinner("Seeding database..."):
                    seed_res = api.seed_sample_data()
                    if seed_res.get("success"):
                        st.success("Sample data and rules successfully loaded!")
                        st.rerun()
                    else:
                        st.error(seed_res.get("error", {}).get("message", "Failed to seed sample data."))

        with c_imp2:
            st.markdown("#### Option B: Upload JSON Facts File")
            st.write("Upload a JSON file containing a list of facts, e.g. `[{\"predicate\": \"Enrolled\", \"arg1\": \"Ravi\", \"arg2\": \"AI\"}]`")
            uploaded_file = st.file_uploader("Upload JSON File", type=["json"], key="upload_kb_json")
            if uploaded_file is not None:
                try:
                    data = json.load(uploaded_file)
                    if isinstance(data, list):
                        if st.button("🚀 Process & Import File"):
                            imp_res = api.import_facts(data)
                            if imp_res.get("success"):
                                st.success(f"Import finished: {imp_res['data']['imported']} imported, {imp_res['data']['skipped']} skipped.")
                                st.rerun()
                            else:
                                st.error(imp_res.get("error", {}).get("message", "Import failed."))
                    else:
                        st.error("JSON file must be an array of objects.")
                except Exception as e:
                    st.error(f"Invalid JSON: {e}")

    # 5. Export Tab
    with tab_export:
        st.subheader("Export Knowledge Base Facts")
        c_ex1, c_ex2 = st.columns(2)
        with c_ex1:
            csv_bytes, err = api.export_report_bytes("facts", "csv")
            if csv_bytes:
                st.download_button(
                    label="📥 Download Facts as CSV",
                    data=csv_bytes,
                    file_name="college_facts.csv",
                    mime="text/csv",
                    type="primary"
                )
            else:
                st.error(f"CSV export error: {err}")

        with c_ex2:
            pdf_bytes, err = api.export_report_bytes("facts", "pdf")
            if pdf_bytes:
                st.download_button(
                    label="📄 Download Facts as PDF",
                    data=pdf_bytes,
                    file_name="college_facts.pdf",
                    mime="application/pdf",
                    type="primary"
                )
            else:
                st.error(f"PDF export error: {err}")


if __name__ == "__main__":
    render_knowledge_base()


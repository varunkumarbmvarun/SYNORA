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


def render_departments():
    render_section_header("Departments Management", "Manage academic departments, department heads, and synchronized First-Order Logic facts")

    health = api.check_health()
    if not health.get("success"):
        render_backend_down_banner(api.base_url)
        return

    profs_resp = api.get_professors()
    professors = profs_resp.get("data", []) if profs_resp.get("success") else []
    prof_map = {p["name"]: p["id"] for p in professors}

    tab_list, tab_add, tab_detail = st.tabs(["🏛️ Department Roster", "➕ Add Department", "🔍 Department Details & Head"])

    # 1. Roster Tab
    with tab_list:
        resp = api.get_departments()
        if resp.get("success"):
            depts = resp.get("data", [])
            st.caption(f"Found {len(depts)} departments")
            if depts:
                table_data = []
                for d in depts:
                    table_data.append({
                        "ID": d["id"],
                        "Code (Constant)": d["code"],
                        "Department Name": d["name"],
                        "Head Professor": d["head_professor_name"] or "None Assigned",
                        "Faculty Count": d["professors_count"],
                        "Students Count": d["students_count"],
                        "Courses Count": d["courses_count"]
                    })
                st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
            else:
                st.info("No departments found.")
        else:
            st.error(resp.get("error", {}).get("message", "Error loading departments."))

    # 2. Add Department Tab
    with tab_add:
        st.subheader("Add a New Department")
        with st.form("add_dept_form"):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Department Name", placeholder="e.g. Mechanical Engineering")
                code = st.text_input("Department Code / FOL Constant", placeholder="e.g. ME", help="Short uppercase code used in FOL atoms, e.g. CSE, ISE")
            with c2:
                head_prof_sel = st.selectbox("Assign Head Professor (Optional)", ["None"] + [p["name"] for p in professors])

            submit_add = st.form_submit_button("➕ Create Department & Sync FOL Facts", type="primary")
            if submit_add:
                if not name.strip() or not code.strip():
                    st.warning("Please fill in Department Name and Code.")
                else:
                    payload = {
                        "name": name.strip(),
                        "code": code.strip().upper(),
                        "head_professor_id": prof_map.get(head_prof_sel) if head_prof_sel != "None" else None
                    }
                    res = api.create_department(payload)
                    if res.get("success"):
                        st.success(f"Department '{name}' ({code.upper()}) created! Created FOL fact Department({code.upper()}).")
                        st.rerun()
                    else:
                        st.error(res.get("error", {}).get("message", "Failed to add department."))

    # 3. Details Tab
    with tab_detail:
        st.subheader("Department Deep Dive & Leadership")
        all_depts_resp = api.get_departments()
        dept_options = {}
        if all_depts_resp.get("success"):
            for d in all_depts_resp["data"]:
                dept_options[f"{d['code']} - {d['name']}"] = d["id"]

        if not dept_options:
            st.info("No departments available.")
            return

        selected_label = st.selectbox("Select Department", list(dept_options.keys()), key="select_dept_dive")
        selected_id = dept_options[selected_label]

        det_resp = api.get_department(selected_id)
        if det_resp.get("success"):
            d_data = det_resp["data"]

            col_info, col_head = st.columns([1, 1])
            with col_info:
                st.markdown(f"""
                <div style="background:white; border:1px solid #E2E8F0; border-radius:12px; padding:18px;">
                    <h3 style="margin-top:0; color:#1E293B;">{d_data['name']} (<span style="color:#D97706;">{d_data['code']}</span>)</h3>
                    <p><strong>Head Professor:</strong> {d_data['head_professor_name'] or 'None Assigned'}</p>
                    <p><strong>Faculty Members:</strong> {len(d_data.get('professors', []))}</p>
                    <p><strong>Enrolled Students:</strong> {len(d_data.get('students', []))}</p>
                    <p><strong>Courses Offered:</strong> {len(d_data.get('courses', []))}</p>
                </div>
                """, unsafe_allow_html=True)

            with col_head:
                st.markdown("#### 👤 Department Head Assignment")
                st.write(f"Current Head: **{d_data['head_professor_name'] or 'None'}**")

                dept_profs = [p["name"] for p in d_data.get("professors", [])]
                c_h1, c_h2 = st.columns([2, 1])
                with c_h1:
                    new_head = st.selectbox("Select Head Professor", dept_profs if dept_profs else ["No faculty in dept"], key="box_new_head")
                with c_h2:
                    if st.button("Set Head", disabled=(not dept_profs)):
                        h_res = api.set_department_head(selected_id, new_head)
                        if h_res.get("success"):
                            st.success(f"Set {new_head} as Head of {d_data['code']}! Updated fact HeadOf({new_head}, {d_data['code']}).")
                            st.rerun()
                        else:
                            st.error(h_res.get("error", {}).get("message", "Failed to set head."))

            # Synchronized FOL Facts for this department
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader(f"🔗 Synchronized FOL Facts for {d_data['code']}")
            related = d_data.get("related_facts", [])
            if related:
                for rf in related:
                    inferred_tag = '<span class="pill pill-green">Inferred</span>' if rf.get('is_inferred') else '<span class="pill pill-indigo">Base</span>'
                    st.markdown(
                        f"• <span class='fol-badge'>{rf.get('fol')}</span> &nbsp; {inferred_tag} &nbsp; "
                        f"<span style='color:#64748B; font-size:0.85rem;'>Source: {rf.get('source')}</span>",
                        unsafe_allow_html=True
                    )
            else:
                st.write("No direct facts recorded.")

            # Danger zone
            st.markdown("<br><hr>", unsafe_allow_html=True)
            st.markdown("#### ⚠️ Danger Zone")
            chk_del = st.checkbox(f"Confirm deletion of department {d_data['code']}", key=f"del_dept_chk_{selected_id}")
            if st.button(f"🗑️ Delete Department {d_data['code']}", type="primary", disabled=not chk_del):
                del_res = api.delete_department(selected_id)
                if del_res.get("success"):
                    st.success(f"Deleted department {d_data['code']} and associated facts.")
                    st.rerun()
                else:
                    st.error(del_res.get("error", {}).get("message", "Delete failed."))


if __name__ == "__main__":
    render_departments()


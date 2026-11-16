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


def render_professors():
    render_section_header("Professors Management", "Manage faculty members, teaching assignments, and synchronized First-Order Logic facts")

    health = api.check_health()
    if not health.get("success"):
        render_backend_down_banner(api.base_url)
        return

    dept_resp = api.get_departments()
    departments = dept_resp.get("data", []) if dept_resp.get("success") else []
    dept_map = {d["code"]: d["id"] for d in departments}

    courses_resp = api.get_courses()
    courses = courses_resp.get("data", []) if courses_resp.get("success") else []

    tab_list, tab_add, tab_detail = st.tabs(["📋 Faculty Roster", "➕ Add Professor", "🔍 Professor Details & Teaching"])

    # 1. Roster Tab
    with tab_list:
        c1, c2 = st.columns([3, 2])
        with c1:
            search = st.text_input("🔍 Search professors", "", key="prof_search")
        with c2:
            dept_filter = st.selectbox("Department filter", ["All"] + [d["code"] for d in departments], key="prof_dept_filter")

        d_filter_val = "" if dept_filter == "All" else dept_filter
        resp = api.get_professors(search=search, department=d_filter_val)

        if resp.get("success"):
            professors = resp.get("data", [])
            st.caption(f"Found {len(professors)} professors")
            if professors:
                table_data = []
                for p in professors:
                    table_data.append({
                        "ID": p["id"],
                        "Code": p["prof_code"],
                        "Name": p["name"],
                        "Email": p["email"],
                        "Specialization": p["specialization"],
                        "Department": p["department_code"],
                        "Courses Taught": ", ".join(p["courses"]) if p["courses"] else "None"
                    })
                st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
            else:
                st.info("No professors found.")
        else:
            st.error(resp.get("error", {}).get("message", "Error loading professors."))

    # 2. Add Professor Tab
    with tab_add:
        st.subheader("Add a New Professor")
        with st.form("add_prof_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name", placeholder="e.g. Ramesh")
                prof_code = st.text_input("Professor Code", placeholder="e.g. PROF04")
                email = st.text_input("Email", placeholder="e.g. ramesh@college.edu")
            with col2:
                specialization = st.text_input("Specialization", placeholder="e.g. Operating Systems")
                dept_code_sel = st.selectbox("Department", [d["code"] for d in departments]) if departments else None

            submit_add = st.form_submit_button("➕ Create Professor & Sync FOL Facts", type="primary")
            if submit_add:
                if not name.strip() or not prof_code.strip() or not email.strip() or not specialization.strip() or not dept_code_sel:
                    st.warning("Please fill in all required fields.")
                else:
                    payload = {
                        "name": name.strip(),
                        "prof_code": prof_code.strip(),
                        "email": email.strip(),
                        "specialization": specialization.strip(),
                        "department_id": dept_map.get(dept_code_sel)
                    }
                    res = api.create_professor(payload)
                    if res.get("success"):
                        st.success(f"Professor '{name}' added successfully! Automatically created FOL facts Professor({name}) and BelongsTo({name}, {dept_code_sel}).")
                        st.rerun()
                    else:
                        st.error(res.get("error", {}).get("message", "Failed to add professor."))

    # 3. Details Tab
    with tab_detail:
        st.subheader("Professor Deep Dive & Teaching")
        all_profs_resp = api.get_professors()
        prof_options = {}
        if all_profs_resp.get("success"):
            for p in all_profs_resp["data"]:
                prof_options[f"{p['name']} ({p['prof_code']}) - {p['department_code']}"] = p["id"]

        if not prof_options:
            st.info("No professors available.")
            return

        selected_label = st.selectbox("Select Professor", list(prof_options.keys()), key="select_prof_dive")
        selected_id = prof_options[selected_label]

        det_resp = api.get_professor(selected_id)
        if det_resp.get("success"):
            p_data = det_resp["data"]

            col_info, col_teaching = st.columns([1, 1])
            with col_info:
                st.markdown(f"""
                <div style="background:white; border:1px solid #E2E8F0; border-radius:12px; padding:18px;">
                    <h3 style="margin-top:0; color:#1E293B;">{p_data['name']}</h3>
                    <p><strong>Code:</strong> {p_data['prof_code']} | <strong>Department:</strong> {p_data['department_name']} ({p_data['department_code']})</p>
                    <p><strong>Email:</strong> {p_data['email']}</p>
                    <p><strong>Specialization:</strong> {p_data['specialization']}</p>
                </div>
                """, unsafe_allow_html=True)

            with col_teaching:
                st.markdown("#### 📖 Courses Taught")
                taught = p_data.get("courses", [])
                if taught:
                    for c_alias in taught:
                        st.markdown(f"• **{c_alias}**")
                else:
                    st.write("Not currently assigned to teach any course.")

                st.markdown("---")
                # Assign action
                c_as1, c_as2 = st.columns([2, 1])
                available_courses = [c["alias"] for c in courses if c["alias"] not in taught]
                with c_as1:
                    to_assign = st.selectbox("Assign course", available_courses if available_courses else ["None"], key="box_to_assign")
                with c_as2:
                    if st.button("Assign", disabled=(not available_courses)):
                        as_res = api.assign_professor_course(selected_id, to_assign)
                        if as_res.get("success"):
                            st.success(f"Assigned {p_data['name']} to teach {to_assign}! Created fact Teaches({p_data['name']}, {to_assign}).")
                            st.rerun()
                        else:
                            st.error(as_res.get("error", {}).get("message", "Assignment failed."))

                # Unassign action
                if taught:
                    c_unas1, c_unas2 = st.columns([2, 1])
                    with c_unas1:
                        to_unassign = st.selectbox("Unassign course", taught, key="box_to_unassign")
                    with c_unas2:
                        if st.button("Unassign", key="btn_unassign"):
                            unas_res = api.unassign_professor_course(selected_id, to_unassign)
                            if unas_res.get("success"):
                                st.success(f"Unassigned {p_data['name']} from {to_unassign}!")
                                st.rerun()
                            else:
                                st.error(unas_res.get("error", {}).get("message", "Unassign failed."))

            # Synchronized FOL Facts for this professor
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader(f"🔗 Synchronized FOL Facts for {p_data['name']}")
            related = p_data.get("related_facts", [])
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
            chk_del = st.checkbox(f"Confirm deletion of professor {p_data['name']}", key=f"del_prof_chk_{selected_id}")
            if st.button(f"🗑️ Delete Professor {p_data['name']}", type="primary", disabled=not chk_del):
                del_res = api.delete_professor(selected_id)
                if del_res.get("success"):
                    st.success(f"Deleted {p_data['name']} and all associated FOL facts.")
                    st.rerun()
                else:
                    st.error(del_res.get("error", {}).get("message", "Delete failed."))


if __name__ == "__main__":
    render_professors()


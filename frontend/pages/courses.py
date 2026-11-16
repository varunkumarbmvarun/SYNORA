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


def render_courses():
    render_section_header("Courses & Curriculum", "Manage academic courses, symbolic aliases, prerequisites, and synchronized First-Order Logic facts")

    health = api.check_health()
    if not health.get("success"):
        render_backend_down_banner(api.base_url)
        return

    dept_resp = api.get_departments()
    departments = dept_resp.get("data", []) if dept_resp.get("success") else []
    dept_map = {d["code"]: d["id"] for d in departments}

    tab_list, tab_add, tab_detail = st.tabs(["📚 Course Catalog", "➕ Add Course", "🔍 Course Details & Prerequisites"])

    # 1. Course Catalog Tab
    with tab_list:
        c1, c2 = st.columns([3, 2])
        with c1:
            search = st.text_input("🔍 Search courses", "", key="course_search")
        with c2:
            dept_filter = st.selectbox("Department filter", ["All"] + [d["code"] for d in departments], key="course_dept_filter")

        d_filter_val = "" if dept_filter == "All" else dept_filter
        resp = api.get_courses(search=search, department=d_filter_val)

        if resp.get("success"):
            courses = resp.get("data", [])
            st.caption(f"Found {len(courses)} courses")
            if courses:
                table_data = []
                for c in courses:
                    table_data.append({
                        "ID": c["id"],
                        "Code": c["course_code"],
                        "Name": c["name"],
                        "Alias (Constant)": c["alias"],
                        "Credits": c["credits"],
                        "Department": c["department_code"],
                        "Instructors": ", ".join(c["professors"]) if c["professors"] else "None",
                        "Enrolled Count": c["students_count"],
                        "Prerequisites": ", ".join(c["prerequisites"]) if c["prerequisites"] else "None"
                    })
                st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
            else:
                st.info("No courses found.")
        else:
            st.error(resp.get("error", {}).get("message", "Error loading courses."))

    # 2. Add Course Tab
    with tab_add:
        st.subheader("Add a New Course")
        with st.form("add_course_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Course Name", placeholder="e.g. Operating Systems")
                course_code = st.text_input("Course Code", placeholder="e.g. CS402")
                alias = st.text_input("Symbolic Alias / FOL Constant", placeholder="e.g. OS", help="Short uppercase code used in FOL atoms, e.g. AI, DSA")
            with col2:
                credits_val = st.number_input("Credits", min_value=1, max_value=6, value=4)
                dept_code_sel = st.selectbox("Department", [d["code"] for d in departments]) if departments else None

            submit_add = st.form_submit_button("➕ Create Course & Sync FOL Facts", type="primary")
            if submit_add:
                if not name.strip() or not course_code.strip() or not alias.strip() or not dept_code_sel:
                    st.warning("Please fill in all required fields.")
                else:
                    payload = {
                        "name": name.strip(),
                        "course_code": course_code.strip(),
                        "alias": alias.strip().upper(),
                        "credits": int(credits_val),
                        "department_id": dept_map.get(dept_code_sel)
                    }
                    res = api.create_course(payload)
                    if res.get("success"):
                        st.success(f"Course '{name}' ({alias.upper()}) created! Created FOL facts Course({alias.upper()}) and OfferedBy({alias.upper()}, {dept_code_sel}).")
                        st.rerun()
                    else:
                        st.error(res.get("error", {}).get("message", "Failed to add course."))

    # 3. Details Tab
    with tab_detail:
        st.subheader("Course Deep Dive & Prerequisites")
        all_courses_resp = api.get_courses()
        course_options = {}
        if all_courses_resp.get("success"):
            for c in all_courses_resp["data"]:
                course_options[f"{c['name']} ({c['alias']}) - {c['department_code']}"] = c["id"]

        if not course_options:
            st.info("No courses available.")
            return

        selected_label = st.selectbox("Select Course", list(course_options.keys()), key="select_course_dive")
        selected_id = course_options[selected_label]

        det_resp = api.get_course(selected_id)
        if det_resp.get("success"):
            c_data = det_resp["data"]

            col_info, col_prereqs = st.columns([1, 1])
            with col_info:
                st.markdown(f"""
                <div style="background:white; border:1px solid #E2E8F0; border-radius:12px; padding:18px;">
                    <h3 style="margin-top:0; color:#1E293B;">{c_data['name']} (<span style="color:#4F46E5;">{c_data['alias']}</span>)</h3>
                    <p><strong>Code:</strong> {c_data['course_code']} | <strong>Credits:</strong> {c_data['credits']}</p>
                    <p><strong>Department:</strong> {c_data['department_name']} ({c_data['department_code']})</p>
                    <p><strong>Instructors:</strong> {', '.join(c_data['professors']) if c_data['professors'] else 'None'}</p>
                    <p><strong>Enrolled Students:</strong> {c_data['students_count']} students</p>
                </div>
                """, unsafe_allow_html=True)

            with col_prereqs:
                st.markdown("#### 🔗 Prerequisites")
                prereqs = c_data.get("prerequisites", [])
                if prereqs:
                    for pr_alias in prereqs:
                        st.markdown(f"• **{pr_alias}** is required before taking **{c_data['alias']}**")
                else:
                    st.write("No prerequisite requirements.")

                st.markdown("---")
                # Add prerequisite
                all_aliases = [c["alias"] for c in all_courses_resp["data"] if c["id"] != selected_id and c["alias"] not in prereqs]
                c_pr1, c_pr2 = st.columns([2, 1])
                with c_pr1:
                    to_add_prereq = st.selectbox("Add prerequisite", all_aliases if all_aliases else ["None"], key="box_to_prereq")
                with c_pr2:
                    if st.button("Add Prereq", disabled=(not all_aliases)):
                        pr_res = api.add_prerequisite(selected_id, to_add_prereq)
                        if pr_res.get("success"):
                            st.success(f"Added prerequisite {to_add_prereq}! Created fact Prerequisite({to_add_prereq}, {c_data['alias']}).")
                            st.rerun()
                        else:
                            st.error(pr_res.get("error", {}).get("message", "Failed to add prerequisite."))

            # Synchronized FOL Facts for this course
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader(f"🔗 Synchronized FOL Facts for {c_data['alias']}")
            related = c_data.get("related_facts", [])
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
            chk_del = st.checkbox(f"Confirm deletion of course {c_data['alias']}", key=f"del_course_chk_{selected_id}")
            if st.button(f"🗑️ Delete Course {c_data['alias']}", type="primary", disabled=not chk_del):
                del_res = api.delete_course(selected_id)
                if del_res.get("success"):
                    st.success(f"Deleted course {c_data['alias']} and associated facts.")
                    st.rerun()
                else:
                    st.error(del_res.get("error", {}).get("message", "Delete failed."))


if __name__ == "__main__":
    render_courses()


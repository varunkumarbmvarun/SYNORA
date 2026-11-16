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


def render_students():
    render_section_header("Students Management", "Manage student entities, course enrollments, and synchronized First-Order Logic facts")

    health = api.check_health()
    if not health.get("success"):
        render_backend_down_banner(api.base_url)
        return

    # Fetch departments for dropdowns
    dept_resp = api.get_departments()
    departments = dept_resp.get("data", []) if dept_resp.get("success") else []
    dept_map = {d["code"]: d["id"] for d in departments}

    courses_resp = api.get_courses()
    courses = courses_resp.get("data", []) if courses_resp.get("success") else []

    tab_list, tab_add, tab_detail = st.tabs(["📋 Student Roster", "➕ Add Student", "🔍 Student Details & Enrollment"])

    # 1. Roster Tab
    with tab_list:
        c1, c2 = st.columns([3, 2])
        with c1:
            search = st.text_input("🔍 Search by name, code or email", "", key="stud_search")
        with c2:
            dept_filter = st.selectbox("Filter by Department", ["All"] + [d["code"] for d in departments], key="stud_dept_filter")

        d_filter_val = "" if dept_filter == "All" else dept_filter
        resp = api.get_students(search=search, department=d_filter_val)

        if resp.get("success"):
            students = resp.get("data", [])
            st.caption(f"Found {len(students)} students")
            if students:
                table_data = []
                for s in students:
                    table_data.append({
                        "ID": s["id"],
                        "Code": s["student_code"],
                        "Name": s["name"],
                        "Email": s["email"],
                        "Semester": s["semester"],
                        "Status": s["status"],
                        "Department": s["department_code"],
                        "Courses Enrolled": ", ".join(s["courses"]) if s["courses"] else "None"
                    })
                st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
            else:
                st.info("No students found.")
        else:
            st.error(resp.get("error", {}).get("message", "Error loading students."))

    # 2. Add Student Tab
    with tab_add:
        st.subheader("Add a New Student")
        with st.form("add_student_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name", placeholder="e.g. Kavya")
                student_code = st.text_input("Student Code / USN", placeholder="e.g. USN06")
                email = st.text_input("Email", placeholder="e.g. kavya@college.edu")
            with col2:
                semester = st.number_input("Semester", min_value=1, max_value=8, value=1)
                dept_code_sel = st.selectbox("Department", [d["code"] for d in departments]) if departments else None
                status = st.selectbox("Status", ["Active", "Inactive", "Graduated"])

            submit_add = st.form_submit_button("➕ Create Student & Sync FOL Facts", type="primary")
            if submit_add:
                if not name.strip() or not student_code.strip() or not email.strip() or not dept_code_sel:
                    st.warning("Please fill in all required fields.")
                else:
                    payload = {
                        "name": name.strip(),
                        "student_code": student_code.strip(),
                        "email": email.strip(),
                        "semester": int(semester),
                        "department_id": dept_map.get(dept_code_sel),
                        "status": status
                    }
                    res = api.create_student(payload)
                    if res.get("success"):
                        st.success(f"Student '{name}' added successfully! Automatically created FOL facts Student({name}) and BelongsTo({name}, {dept_code_sel}).")
                        st.rerun()
                    else:
                        st.error(res.get("error", {}).get("message", "Failed to add student."))

    # 3. Student Details Tab
    with tab_detail:
        st.subheader("Student Deep Dive & FOL Facts")
        all_students_resp = api.get_students()
        student_options = {}
        if all_students_resp.get("success"):
            for s in all_students_resp["data"]:
                student_options[f"{s['name']} ({s['student_code']}) - {s['department_code']}"] = s["id"]

        if not student_options:
            st.info("No students available.")
            return

        selected_label = st.selectbox("Select Student", list(student_options.keys()), key="select_stud_dive")
        selected_id = student_options[selected_label]

        det_resp = api.get_student(selected_id)
        if det_resp.get("success"):
            s_data = det_resp["data"]

            col_info, col_courses = st.columns([1, 1])
            with col_info:
                st.markdown(f"""
                <div style="background:white; border:1px solid #E2E8F0; border-radius:12px; padding:18px;">
                    <h3 style="margin-top:0; color:#1E293B;">{s_data['name']}</h3>
                    <p><strong>Code:</strong> {s_data['student_code']} | <strong>Status:</strong> {render_status_pill(s_data['status'])}</p>
                    <p><strong>Department:</strong> {s_data['department_name']} ({s_data['department_code']})</p>
                    <p><strong>Semester:</strong> {s_data['semester']} | <strong>Email:</strong> {s_data['email']}</p>
                </div>
                """, unsafe_allow_html=True)

            with col_courses:
                st.markdown("#### 📚 Enrolled Courses")
                enrolled = s_data.get("courses", [])
                if enrolled:
                    for c_alias in enrolled:
                        st.markdown(f"• **{c_alias}**")
                else:
                    st.write("Not enrolled in any course.")

                st.markdown("---")
                # Enroll action
                c_en1, c_en2 = st.columns([2, 1])
                available_courses = [c["alias"] for c in courses if c["alias"] not in enrolled]
                with c_en1:
                    to_enroll = st.selectbox("Enroll in course", available_courses if available_courses else ["None"], key="box_to_enroll")
                with c_en2:
                    if st.button("Enroll", disabled=(not available_courses)):
                        en_res = api.enroll_student(selected_id, to_enroll)
                        if en_res.get("success"):
                            st.success(f"Enrolled in {to_enroll}! Added fact Enrolled({s_data['name']}, {to_enroll}).")
                            st.rerun()
                        else:
                            st.error(en_res.get("error", {}).get("message", "Enrollment failed."))

                # Unenroll action
                if enrolled:
                    c_un1, c_un2 = st.columns([2, 1])
                    with c_un1:
                        to_unenroll = st.selectbox("Unenroll from course", enrolled, key="box_to_unenroll")
                    with c_un2:
                        if st.button("Unenroll", key="btn_unenroll"):
                            un_res = api.unenroll_student(selected_id, to_unenroll)
                            if un_res.get("success"):
                                st.success(f"Unenrolled from {to_unenroll}!")
                                st.rerun()
                            else:
                                st.error(un_res.get("error", {}).get("message", "Unenroll failed."))

            # Synchronized FOL Facts for this student
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader(f"🔗 Synchronized FOL Facts for {s_data['name']}")
            related = s_data.get("related_facts", [])
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
            chk_del = st.checkbox(f"Confirm deletion of student {s_data['name']}", key=f"del_stud_chk_{selected_id}")
            if st.button(f"🗑️ Delete Student {s_data['name']}", type="primary", disabled=not chk_del):
                del_res = api.delete_student(selected_id)
                if del_res.get("success"):
                    st.success(f"Deleted {s_data['name']} and all associated FOL facts.")
                    st.rerun()
                else:
                    st.error(del_res.get("error", {}).get("message", "Delete failed."))


if __name__ == "__main__":
    render_students()


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

REPORT_TABS = [
    ("Students", "students"),
    ("Professors", "professors"),
    ("Courses", "courses"),
    ("Departments", "departments"),
    ("Knowledge Base", "facts"),
    ("Inference Runs", "inference"),
    ("Query History", "queries")
]


def render_report_tab(tab_name: str, report_type: str):
    st.subheader(f"{tab_name} Report Export")
    st.write(f"Generate and download official PDF or raw CSV reports for {tab_name.lower()}.")

    c1, c2 = st.columns(2)
    with c1:
        csv_bytes, csv_err = api.export_report_bytes(report_type, "csv")
        if csv_bytes:
            st.download_button(
                label=f"📥 Download {tab_name} as CSV",
                data=csv_bytes,
                file_name=f"{report_type}_report.csv",
                mime="text/csv",
                key=f"dl_csv_{report_type}",
                type="primary"
            )
        else:
            st.error(f"CSV error: {csv_err}")

    with c2:
        pdf_bytes, pdf_err = api.export_report_bytes(report_type, "pdf")
        if pdf_bytes:
            st.download_button(
                label=f"📄 Download {tab_name} as PDF",
                data=pdf_bytes,
                file_name=f"{report_type}_report.pdf",
                mime="application/pdf",
                key=f"dl_pdf_{report_type}",
                type="primary"
            )
        else:
            st.error(f"PDF error: {pdf_err}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### Table Preview")

    # Preview data
    if report_type == "students":
        r = api.get_students()
        if r.get("success") and r.get("data"):
            st.dataframe(pd.DataFrame(r["data"]), use_container_width=True, hide_index=True)
    elif report_type == "professors":
        r = api.get_professors()
        if r.get("success") and r.get("data"):
            st.dataframe(pd.DataFrame(r["data"]), use_container_width=True, hide_index=True)
    elif report_type == "courses":
        r = api.get_courses()
        if r.get("success") and r.get("data"):
            st.dataframe(pd.DataFrame(r["data"]), use_container_width=True, hide_index=True)
    elif report_type == "departments":
        r = api.get_departments()
        if r.get("success") and r.get("data"):
            st.dataframe(pd.DataFrame(r["data"]), use_container_width=True, hide_index=True)
    elif report_type == "facts":
        r = api.get_facts(page_size=100)
        if r.get("success") and r.get("data"):
            st.dataframe(pd.DataFrame(r["data"].get("facts", [])), use_container_width=True, hide_index=True)
    elif report_type == "inference":
        r = api.get_inference_results(limit=50)
        if r.get("success") and r.get("data"):
            st.dataframe(pd.DataFrame(r["data"]), use_container_width=True, hide_index=True)
    elif report_type == "queries":
        r = api.get_query_history(limit=50)
        if r.get("success") and r.get("data"):
            st.dataframe(pd.DataFrame(r["data"]), use_container_width=True, hide_index=True)


def render_reports():
    render_section_header("Reports & Data Exports", "Export college analytics, knowledge base snapshots, and resolution logs in CSV and PDF formats")

    health = api.check_health()
    if not health.get("success"):
        render_backend_down_banner(api.base_url)
        return

    tab_objs = st.tabs([t[0] for t in REPORT_TABS])
    for i, (name, r_type) in enumerate(REPORT_TABS):
        with tab_objs[i]:
            render_report_tab(name, r_type)


if __name__ == "__main__":
    render_reports()


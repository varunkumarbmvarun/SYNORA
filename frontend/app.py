import os
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import streamlit as st

# Configure Page
st.set_page_config(
    page_title="College KB · FOL",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

from frontend.api_client import api
from frontend.components.ui import inject_custom_css, render_status_pill

# Import Page Renderers
from frontend.pages.dashboard import render_dashboard
from frontend.pages.knowledge_base import render_knowledge_base
from frontend.pages.students import render_students
from frontend.pages.professors import render_professors
from frontend.pages.courses import render_courses
from frontend.pages.departments import render_departments
from frontend.pages.fol_rules import render_fol_rules
from frontend.pages.inference import render_inference
from frontend.pages.query import render_query_system
from frontend.pages.knowledge_graph import render_knowledge_graph_page
from frontend.pages.reports import render_reports
from frontend.pages.settings import render_settings

# Inject CSS styling
inject_custom_css()

# Sidebar Navigation
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand-card">
        <div class="brand-logo-badge">🎓</div>
        <div>
            <div class="brand-title">College KB</div>
            <div class="brand-tag">⚡ FOL REASONER v2.0</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    nav_options = [
        "Dashboard",
        "Knowledge Base",
        "Students",
        "Professors",
        "Courses",
        "Departments",
        "FOL Rules",
        "Inference Engine",
        "Query System",
        "Knowledge Graph",
        "Reports",
        "Settings"
    ]
    nav_icons = [
        "grid-1x2-fill",
        "database-fill",
        "mortarboard-fill",
        "person-workspace",
        "book-half",
        "building-fill",
        "sliders2",
        "lightning-charge-fill",
        "chat-dots-fill",
        "diagram-3-fill",
        "bar-chart-fill",
        "gear-wide-connected"
    ]

    selected_page = "Dashboard"
    try:
        from streamlit_option_menu import option_menu
        selected_page = option_menu(
            menu_title=None,
            options=nav_options,
            icons=nav_icons,
            default_index=0,
            styles={
                "container": {
                    "padding": "0",
                    "background-color": "transparent"
                },
                "icon": {
                    "font-size": "15px",
                    "margin-right": "8px"
                },
                "nav-link": {
                    "font-size": "13.5px",
                    "font-weight": "550",
                    "text-align": "left",
                    "margin": "2.5px 0",
                    "padding": "9px 12px",
                    "border-radius": "10px",
                    "color": "#334155",
                    "--hover-color": "#EEF2FF",
                    "transition": "all 0.22s cubic-bezier(0.4, 0, 0.2, 1)"
                },
                "nav-link-selected": {
                    "background": "linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%)",
                    "color": "#FFFFFF !important",
                    "font-weight": "650",
                    "border-radius": "10px",
                    "box-shadow": "0 4px 15px rgba(79, 70, 229, 0.35)",
                    "transition": "all 0.2s ease"
                }
            }
        )
    except Exception:
        selected_page = st.radio("Navigation", nav_options)

    # Backend status check
    health = api.check_health()
    is_connected = health.get("success", False)

    if is_connected:
        st.markdown("""
        <div class="backend-status-card connected">
            <span class="pulsing-dot"></span>
            <div>
                <div class="status-text-title">Backend Connected</div>
                <div class="status-text-sub">Flask REST API · :5000</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="backend-status-card disconnected">
            <span class="pulsing-dot-red"></span>
            <div>
                <div class="status-text-title" style="color: #991B1B;">Backend Offline</div>
                <div class="status-text-sub" style="color: #B91C1C;">Run: python backend/app.py</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    if st.button("⚡ Refresh Status", use_container_width=True):
        st.rerun()


# Page Routing
if selected_page == "Dashboard":
    render_dashboard()
elif selected_page == "Knowledge Base":
    render_knowledge_base()
elif selected_page == "Students":
    render_students()
elif selected_page == "Professors":
    render_professors()
elif selected_page == "Courses":
    render_courses()
elif selected_page == "Departments":
    render_departments()
elif selected_page == "FOL Rules":
    render_fol_rules()
elif selected_page == "Inference Engine":
    render_inference()
elif selected_page == "Query System":
    render_query_system()
elif selected_page == "Knowledge Graph":
    render_knowledge_graph_page()
elif selected_page == "Reports":
    render_reports()
elif selected_page == "Settings":
    render_settings()

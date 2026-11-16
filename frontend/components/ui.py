import streamlit as st
from typing import Optional, Any


def inject_custom_css():
    """Injects high-end, colorful, animated SaaS styling into Streamlit."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif;
        color: #0F172A;
    }

    /* Main Content Background */
    .stApp {
        background: linear-gradient(180deg, #F8FAFC 0%, #F1F5F9 100%);
    }

    /* Sidebar Background Styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%) !important;
        border-right: 1px solid #E2E8F0 !important;
        box-shadow: 4px 0 20px rgba(0, 0, 0, 0.02) !important;
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 1.5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    /* Brand Card in Sidebar */
    .sidebar-brand-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(240, 244, 255, 0.9) 100%);
        border: 1px solid rgba(226, 232, 240, 0.9);
        border-radius: 16px;
        padding: 14px 16px;
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 18px;
        box-shadow: 0 4px 16px rgba(99, 102, 241, 0.08);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .sidebar-brand-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(99, 102, 241, 0.15);
        border-color: rgba(99, 102, 241, 0.3);
    }
    .brand-logo-badge {
        width: 44px;
        height: 44px;
        min-width: 44px;
        border-radius: 12px;
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 50%, #EC4899 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.4rem;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
        animation: floatLogo 3s ease-in-out infinite;
    }
    @keyframes floatLogo {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-3px); }
    }
    .brand-title {
        font-size: 1.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #0F172A 0%, #4338CA 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
        line-height: 1.1;
    }
    .brand-tag {
        display: inline-block;
        font-size: 0.65rem;
        font-weight: 700;
        color: #4F46E5;
        background: #EEF2FF;
        padding: 2px 7px;
        border-radius: 9999px;
        letter-spacing: 0.06em;
        margin-top: 3px;
        border: 1px solid rgba(99, 102, 241, 0.2);
    }

    /* Option Menu Styling Enhancements */
    .nav-link {
        transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1) !important;
        position: relative !important;
    }
    .nav-link:hover {
        transform: translateX(5px) !important;
        background: #EEF2FF !important;
        color: #4338CA !important;
    }
    .nav-link-selected {
        transform: translateX(4px) !important;
    }

    /* Distinct Vibrant Icon Colors in Sidebar */
    .nav-item:nth-child(1) .nav-link:not(.nav-link-selected) i { color: #3B82F6 !important; }
    .nav-item:nth-child(2) .nav-link:not(.nav-link-selected) i { color: #0EA5E9 !important; }
    .nav-item:nth-child(3) .nav-link:not(.nav-link-selected) i { color: #10B981 !important; }
    .nav-item:nth-child(4) .nav-link:not(.nav-link-selected) i { color: #8B5CF6 !important; }
    .nav-item:nth-child(5) .nav-link:not(.nav-link-selected) i { color: #F59E0B !important; }
    .nav-item:nth-child(6) .nav-link:not(.nav-link-selected) i { color: #EC4899 !important; }
    .nav-item:nth-child(7) .nav-link:not(.nav-link-selected) i { color: #6366F1 !important; }
    .nav-item:nth-child(8) .nav-link:not(.nav-link-selected) i { color: #EF4444 !important; }
    .nav-item:nth-child(9) .nav-link:not(.nav-link-selected) i { color: #A855F7 !important; }
    .nav-item:nth-child(10) .nav-link:not(.nav-link-selected) i { color: #14B8A6 !important; }
    .nav-item:nth-child(11) .nav-link:not(.nav-link-selected) i { color: #06B6D4 !important; }
    .nav-item:nth-child(12) .nav-link:not(.nav-link-selected) i { color: #64748B !important; }

    /* Backend Connection Status Card */
    .backend-status-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 10px 14px;
        display: flex;
        align-items: center;
        gap: 10px;
        margin-top: 10px;
        margin-bottom: 8px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
        transition: all 0.2s ease;
    }
    .backend-status-card.connected {
        background: #F0FDF4;
        border-color: #BBF7D0;
    }
    .backend-status-card.disconnected {
        background: #FEF2F2;
        border-color: #FECDD3;
    }
    .pulsing-dot {
        width: 10px;
        height: 10px;
        min-width: 10px;
        border-radius: 50%;
        background: #10B981;
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
        animation: pulseLive 2s infinite;
    }
    .pulsing-dot-red {
        width: 10px;
        height: 10px;
        min-width: 10px;
        border-radius: 50%;
        background: #EF4444;
        box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
        animation: pulseAlert 2s infinite;
    }
    @keyframes pulseLive {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1.05); box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    @keyframes pulseAlert {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
        70% { transform: scale(1.05); box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }
    .status-text-title {
        font-size: 0.82rem;
        font-weight: 700;
        color: #065F46;
        line-height: 1.2;
    }
    .status-text-sub {
        font-size: 0.72rem;
        color: #059669;
    }

    /* Metric Card */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        margin-bottom: 12px;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px -4px rgba(15, 23, 42, 0.08);
        border-color: #CBD5E1;
    }
    .metric-icon-circle {
        width: 36px;
        height: 36px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.15rem;
    }
    .metric-title {
        font-size: 0.78rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .metric-value {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        line-height: 1.1;
        margin-top: 6px;
    }
    .metric-subtitle {
        font-size: 0.78rem;
        color: #94A3B8;
        font-weight: 500;
        margin-top: 4px;
    }

    /* Modern Streamlit Buttons */
    div.stButton > button:first-child {
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        padding: 0.45rem 1.1rem !important;
        transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1) !important;
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08) !important;
        border-color: #CBD5E1 !important;
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: 0 4px 14px rgba(79, 70, 229, 0.35) !important;
    }
    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 22px rgba(79, 70, 229, 0.45) !important;
    }

    /* Modern Streamlit Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px !important;
        background-color: #F1F5F9 !important;
        padding: 5px !important;
        border-radius: 12px !important;
        border: 1px solid #E2E8F0 !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px !important;
        padding: 8px 18px !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        color: #64748B !important;
        border: none !important;
        transition: all 0.2s ease !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #4F46E5 !important;
        background-color: rgba(255, 255, 255, 0.7) !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #4F46E5 !important;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06) !important;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        border-radius: 10px !important;
        font-weight: 600 !important;
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        transition: all 0.2s ease !important;
    }
    .streamlit-expanderHeader:hover {
        border-color: #CBD5E1 !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
    }

    /* Status Pills */
    .pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.74rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }
    .pill-green {
        background-color: #DCFCE7;
        color: #15803D;
        border: 1px solid #BBF7D0;
    }
    .pill-red {
        background-color: #FEE2E2;
        color: #B91C1C;
        border: 1px solid #FECDD3;
    }
    .pill-amber {
        background-color: #FEF3C7;
        color: #B45309;
        border: 1px solid #FDE68A;
    }
    .pill-indigo {
        background-color: #EEF2FF;
        color: #4338CA;
        border: 1px solid #C7D2FE;
    }

    /* FOL Code Badge */
    .fol-badge {
        font-family: 'Courier New', Courier, monospace;
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 3px 8px;
        color: #312E81;
        font-weight: 700;
        font-size: 0.88rem;
    }

    /* Content Box */
    .content-box {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 2px 12px rgba(15, 23, 42, 0.03);
        margin-bottom: 20px;
    }

    /* Backend Error Box */
    .backend-error-box {
        background: #FFF1F2;
        border: 1px solid #FECDD3;
        border-radius: 14px;
        padding: 22px;
        margin: 20px 0;
        color: #9F1239;
        box-shadow: 0 4px 14px rgba(239, 68, 68, 0.08);
    }
    </style>
    """, unsafe_allow_html=True)


def render_metric_card(title: str, value: Any, subtitle: str = "", icon: str = "📌", color: str = "#4F46E5"):
    st.markdown(f"""
    <div class="metric-card" style="border-top: 3px solid {color};">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div class="metric-title">{title}</div>
            <div class="metric-icon-circle" style="background: {color}18; color: {color};">{icon}</div>
        </div>
        <div class="metric-value" style="color: {color};">{value}</div>
        {f'<div class="metric-subtitle">{subtitle}</div>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)


def render_status_pill(status: str) -> str:
    s = status.upper()
    if s in ("TRUE", "ACTIVE", "CONNECTED", "HEALTHY", "PROVED"):
        cls = "pill-green"
    elif s in ("FALSE", "INACTIVE", "DISCONNECTED", "FAILED"):
        cls = "pill-red"
    elif s in ("UNKNOWN", "PENDING", "WARNING"):
        cls = "pill-amber"
    else:
        cls = "pill-indigo"
    return f'<span class="pill {cls}">{status}</span>'


def render_backend_down_banner(base_url: str):
    st.markdown(f"""
    <div class="backend-error-box">
        <h3 style="margin-top:0; color:#BE123C; font-weight:700;">⚠️ Backend Not Reachable</h3>
        <p>The Streamlit frontend could not connect to the Flask REST API at <code>{base_url}</code>.</p>
        <p>Please open a terminal and run:</p>
        <pre style="background:#FFE4E6; padding:10px; border-radius:8px; color:#881337; font-weight:600;">python backend/app.py</pre>
        <p style="margin-bottom:0;">Then click <strong>Refresh</strong> in the sidebar once the backend starts.</p>
    </div>
    """, unsafe_allow_html=True)


def render_section_header(title: str, subtitle: Optional[str] = None):
    st.markdown(f"""
    <div style="margin-bottom: 22px;">
        <h1 style="margin: 0; font-weight: 800; font-size: 1.85rem; letter-spacing: -0.02em; color: #0F172A;">{title}</h1>
        {f'<p style="color: #64748B; margin: 6px 0 0 0; font-size: 0.95rem; font-weight: 450;">{subtitle}</p>' if subtitle else ''}
        <div style="height: 3px; width: 60px; background: linear-gradient(90deg, #4F46E5, #06B6D4); border-radius: 9999px; margin-top: 14px;"></div>
    </div>
    """, unsafe_allow_html=True)

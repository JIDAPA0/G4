import streamlit as st
import streamlit.components.v1 as components


DASHBOARD_URL = "https://math-teacher-workforce-analytics.nuankaew-pratya.chatgpt.site/"


st.set_page_config(
    page_title="แดชบอร์ดกลุ่มวิชาเอกครู",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)


st.markdown(
    """
    <style>
    #MainMenu,
    header,
    footer,
    div[data-testid="stToolbar"],
    div[data-testid="stDecoration"],
    div[data-testid="collapsedControl"] {
        display: none !important;
    }

    .stApp {
        background: #e7e7df;
    }

    .block-container {
        width: 100vw !important;
        max-width: 100vw !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    iframe {
        display: block;
        border: 0 !important;
    }

    .fallback {
        position: fixed;
        right: 18px;
        bottom: 18px;
        z-index: 20;
        border: 1px solid #e3e1d7;
        border-radius: 8px;
        padding: 10px 12px;
        background: #fffef8;
        box-shadow: 0 12px 28px rgba(70, 70, 56, 0.12);
        font-family: Arial, sans-serif;
        font-size: 13px;
        font-weight: 800;
    }

    .fallback a {
        color: #6849ee;
        text-decoration: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


components.iframe(
    DASHBOARD_URL,
    height=1200,
    scrolling=True,
)

st.markdown(
    f"""
    <div class="fallback">
        ถ้าหน้าเว็บไม่แสดงใน Streamlit:
        <a href="{DASHBOARD_URL}" target="_blank" rel="noopener">เปิดแดชบอร์ดต้นฉบับ</a>
    </div>
    """,
    unsafe_allow_html=True,
)

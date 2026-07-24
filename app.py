"""
Mr. AI Smart Classroom — Main Entry Point
Handles: theme injection → auth gate → sidebar routing → page dispatch.
"""
import streamlit as st

# ── Page config (MUST be first Streamlit call) ──────────────────
st.set_page_config(
    page_title="Mr. AI Smart Classroom",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "**Mr. AI Smart Classroom** — AI-Powered Educational Platform\nBuilt with Streamlit + Ollama + ChromaDB",
    },
)

# ── Initialize session state safe defaults ───────────────────────
if "sm_page" not in st.session_state:
    st.session_state["sm_page"] = "books"
if "sm_user" not in st.session_state:
    st.session_state["sm_user"] = {}
if "sm_chat_history" not in st.session_state:
    st.session_state["sm_chat_history"] = []

# ── Auto-Detect Best Installed Ollama Model ─────────────────────
from app.utils.model_detector import get_active_model
st.session_state["active_model"] = get_active_model()

# ── Bootstrap database on first run ─────────────────────────────
from app.database.db import initialize_database
initialize_database()

# ── ALWAYS APPLY THEME AT ENTRY (For both Login & Authenticated app) ──
user  = st.session_state.get("sm_user", {})
theme = user.get("theme", "Light Mode")

from app.themes.styles import apply_theme
apply_theme(theme)

# ── Auth gate ────────────────────────────────────────────────────
from app.authentication.auth import is_authenticated, render_login_page

if not is_authenticated():
    render_login_page()
    st.stop()

# ─────────────────────────────────────────────────────────────────
# AUTHENTICATED APPLICATION
# ─────────────────────────────────────────────────────────────────

# ── Render sidebar → get current page ───────────────────────────
from app.components.sidebar import render_sidebar
current_page = render_sidebar()

# ── Dispatch to page module (wrapped in try-except for visible error tracking)
try:
    if current_page == "books":
        from app.pages.books import render
        render()

    elif current_page == "chat":
        from app.pages.chat import render
        render()

    elif current_page == "quizzes":
        from app.pages.quizzes import render
        render()

    elif current_page == "notes":
        from app.pages.notes import render
        render()

    elif current_page == "flashcards":
        from app.pages.flashcards import render
        render()

    elif current_page == "settings":
        from app.pages.settings import render
        render()

    else:
        st.error(f"Unknown page: {current_page}. Defaulting to Books.")
        st.session_state["sm_page"] = "books"
        from app.pages.books import render
        render()

except Exception as e:
    st.exception(e)

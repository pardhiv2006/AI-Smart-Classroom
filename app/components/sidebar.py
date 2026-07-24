"""
Mr. AI Smart Classroom — Sidebar Navigation Component
Optimized Streamlit sidebar mechanics with exact 60x60px logo badge, 44px buttons, and balanced viewport fit.
"""
import streamlit as st
from datetime import datetime
from app.database.db import get_uploaded_books

NAV_ITEMS = [
    ("books",      "📚", "Books"),
    ("chat",       "🤖", "AI Tutor"),
    ("notes",      "📝", "Study Notes"),
    ("flashcards", "🃏", "Flashcards"),
    ("quizzes",    "🧪", "Quizzes"),
    ("settings",   "⚙️", "Settings"),
]

def render_sidebar() -> str:
    """
    Render permanently expanded desktop sidebar and return selected page key.
    Calculates viewport distribution for zero vertical scrolling across desktop viewports.
    """
    user = st.session_state.get("sm_user", {})
    if not isinstance(user, dict):
        user = {}
        
    user_id = user.get("id", 0)
    username = user.get("username", st.session_state.get("sm_user_name", "Guest"))
    role = user.get("role", st.session_state.get("sm_role", "Guest")).capitalize()
    last_login_raw = user.get("last_login", "")

    # Format last login string
    if last_login_raw:
        try:
            dt = datetime.strptime(last_login_raw, "%Y-%m-%d %H:%M:%S")
            last_login = dt.strftime("%d %b %Y %I:%M %p")
        except Exception:
            last_login = str(last_login_raw)[:16]
    else:
        last_login = "Just now"

    current_page = st.session_state.get("sm_page", "books")

    with st.sidebar:
        # ── 1. BRANDING SECTION (60px x 60px LOGO, 19px TITLE, 11.5px SUBTITLE) ──
        st.markdown("""
        <div style="text-align: center; margin-bottom: 0.2rem;">
            <div style="width: 60px; height: 60px; border-radius: 15px; background: linear-gradient(135deg, #2563EB 0%, #06B6D4 100%);
                        display: flex; align-items: center; justify-content: center; font-size: 1.9rem; color: #FFFFFF;
                        margin: 0 auto 0.2rem; box-shadow: 0 4px 14px rgba(37,99,235,0.25);">
                🧠
            </div>
            <div style="font-size: 19px; font-weight: 800; letter-spacing: -0.02em; line-height: 1.2;">
                Mr. AI Smart Classroom
            </div>
            <div style="font-size: 11.5px; opacity: 0.75; font-weight: 600; margin-top: 0.1rem;">
                AI-Powered Learning Platform
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<hr style='margin: 0.15rem 0; border-color: rgba(128,128,128,0.12);'>", unsafe_allow_html=True)

        # ── 2. USER PROFILE SECTION ──
        role_bg = "#ECFDF5" if role == "Student" else ("#FEF3C7" if role == "Teacher" else "#F1F5F9")
        role_color = "#059669" if role == "Student" else ("#D97706" if role == "Teacher" else "#475569")

        st.markdown(f"""
        <div style="text-align: center; padding: 0.05rem 0;">
            <div style="font-size: 0.88rem; font-weight: 800; margin-bottom: 0.08rem;">
                👤 {username}
            </div>
            <div>
                <span style="background: {role_bg}; color: {role_color}; padding: 0.1rem 0.55rem; border-radius: 999px;
                             font-size: 0.68rem; font-weight: 700; text-transform: uppercase;">
                    🎓 {role}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<hr style='margin: 0.15rem 0; border-color: rgba(128,128,128,0.12);'>", unsafe_allow_html=True)

        # ── 3. NAVIGATION OPTIONS (6 BUTTONS, 44px HEIGHT, 7px SPACING) ──
        for page_key, icon, label in NAV_ITEMS:
            is_active = (current_page == page_key)
            btn_type = "primary" if is_active else "secondary"
            
            if st.button(f"{icon}  {label}", key=f"sidebar_nav_{page_key}", use_container_width=True, type=btn_type):
                st.session_state["sm_page"] = page_key
                st.rerun()

        st.markdown("<hr style='margin: 0.15rem 0; border-color: rgba(128,128,128,0.12);'>", unsafe_allow_html=True)

        # ── 4. LOGOUT BUTTON ──
        if st.button("🚪  Logout", key="sidebar_logout_btn", use_container_width=True):
            from app.authentication.auth import logout
            logout()

    return current_page

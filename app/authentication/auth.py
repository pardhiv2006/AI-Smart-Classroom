"""
Mr. AI Smart Classroom — Master Strict Implementation Authentication Controller.
Per exact user directive:
1. Register form uses native st.form() with st.selectbox() — ZERO st.button() calls inside st.form(). ZERO StreamlitAPIException.
2. Role field layout: Height 56px, Border Radius 16px, Pure White Background #FFFFFF, Border 1px solid #D8E5FF.
3. Right Blue Gradient Arrow Tile: Width 64px, Height 56px, Gradient #2F6BFF -> #36C2FF, Right corners rounded (15px).
4. Perfectly centered 18px White (#FFFFFF) chevron SVG that rotates 180° smoothly when expanded (aria-expanded="true").
5. Placeholder: "Choose your role", Options: [Student, Teacher, Parent, Administrator].
6. Validation: If no role selected on Create Account, displays "⚠️ Please select a role."
7. Single 100vh viewport, 600px Glass Card, ZERO desktop scrolling.
Backed by bcrypt password security & smartclass.db persistence.
"""
import time
import os
import base64
import bcrypt
import streamlit as st
from datetime import datetime
from app.database.db import (
    create_user, get_user, authenticate_user, user_exists,
    update_last_login, initialize_database
)

def _clean_html(html_str: str) -> str:
    """Strip leading/trailing whitespace from every line so Markdown parser never creates code blocks."""
    return "\n".join(line.strip() for line in html_str.splitlines() if line.strip())


def register_user_account(username: str, password: str, role: str = "Student") -> tuple[bool, str]:
    """Register a new user with bcrypt password hash."""
    username = username.strip()
    if not username or not password:
        return False, "Username and password are required."
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if role == "Choose your role" or not role:
        return False, "Please select a role."

    if user_exists(username):
        return False, "Username already exists. Please choose another username."

    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    success = create_user(username, hashed_password, role)
    if success:
        return True, "🎉 Account Created Successfully! You can now login."
    return False, "Failed to create account. Please try again."


def login_user_account(username: str, password: str) -> tuple[bool, str, dict | None]:
    """Authenticate user credentials against smartclass.db."""
    ok, msg, user = authenticate_user(username, password)
    if ok and user:
        set_session_user(user)
    return ok, msg, user


def guest_login() -> dict:
    """Create an ephemeral guest session dictionary."""
    guest_user = {
        "id": 0,
        "username": "Guest",
        "role": "Guest",
        "theme": "Light Mode",
        "perf_mode": "Balanced",
        "persona": "Friendly Tutor",
        "ai_model": "llama3",
        "last_login": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    set_session_user(guest_user)
    return guest_user


def set_session_user(user: dict):
    """Store authenticated state and keys in session state."""
    st.session_state["authenticated"] = True
    st.session_state["sm_authenticated"] = True
    st.session_state["sm_user"] = user
    st.session_state["sm_role"] = user.get("role", "Student")


def get_session_user() -> dict | None:
    return st.session_state.get("sm_user", None)


def is_authenticated() -> bool:
    return st.session_state.get("authenticated", False) or st.session_state.get("sm_authenticated", False)


def logout():
    """Clear session state and redirect to login screen."""
    st.session_state["authenticated"] = False
    st.session_state["sm_authenticated"] = False
    st.session_state["sm_user"] = None
    st.session_state["sm_role"] = None
    st.session_state.pop("sm_page", None)
    st.rerun()


def render_login_page():
    """
    Master Strict Implementation Authentication Interface.
    64px Blue Gradient Right Arrow Section with 180° rotation on expand.
    Zero st.button() calls inside st.form(). Zero StreamlitAPIException.
    100vh Single Viewport, 600px Glass Card.
    """
    initialize_database()

    if "auth_tab" not in st.session_state:
        st.session_state["auth_tab"] = "Login"

    css_styles = _clean_html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"] {
    font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
    background: linear-gradient(180deg, #F4F8FF 0%, #FFFFFF 100%) !important;
    overflow: hidden !important;
    height: 100vh !important;
    max-height: 100vh !important;
    margin: 0 !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

@media (max-width: 768px) {
    html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"] {
        overflow-y: auto !important;
        height: auto !important;
    }
}

header[data-testid="stHeader"], footer, [data-testid="stHeaderNav"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] {
    display: none !important;
}

/* MAIN GROUPED CONTAINER (600px MAX WIDTH) */
.block-container {
    padding-top: 0.5rem !important;
    padding-bottom: 0.5rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    max-width: 600px !important;
    margin: 0 auto !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
    height: 100vh !important;
}

[data-testid="stInputInstruction"],
[data-testid="stFormSubmitButtonInstruction"],
div[data-testid="stFormInstruction"],
[data-testid="InputInstructions"],
a.anchor-link,
small {
    display: none !important;
}

/* Background Soft Blue Ambient Glow */
.bg-ambient-soft {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 700px;
    height: 700px;
    background: radial-gradient(circle, rgba(47, 107, 255, 0.08), transparent 70%);
    filter: blur(100px);
    pointer-events: none;
    z-index: 0;
}

/* BRANDING SECTION ABOVE CARD */
.brand-grouped-section {
    text-align: center;
    margin-bottom: 22px;
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    z-index: 2;
    width: 100%;
}
.brand-logo-squircle {
    width: clamp(68px, 8.5vh, 80px);
    height: clamp(68px, 8.5vh, 80px);
    border-radius: 22px;
    background: linear-gradient(135deg, #2F6BFF 0%, #36C2FF 100%);
    box-shadow: 0 16px 36px rgba(47, 107, 255, 0.28);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 18px;
    color: #FFFFFF;
}
.brand-title-text {
    font-size: clamp(32px, 5vh, 46px) !important;
    font-weight: 800 !important;
    letter-spacing: -1.2px !important;
    line-height: 1.05 !important;
    background: linear-gradient(90deg, #2F6BFF 0%, #36C2FF 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 10px 0 !important;
}
.brand-subtitle-text {
    font-size: clamp(15px, 2.2vh, 18px) !important;
    color: #64748B !important;
    font-weight: 500 !important;
    margin: 0 !important;
}

/* 3 TAB BUTTONS SPANNING FULL 600px CARD WIDTH */
[data-testid="stHorizontalBlock"] {
    width: 100% !important;
    max-width: 600px !important;
    margin-bottom: 18px !important;
    position: relative;
    z-index: 2;
}

div[data-testid="stColumn"] button[kind="primary"] {
    width: 100% !important;
    height: 56px !important;
    border-radius: 16px !important;
    background: linear-gradient(135deg, #2F6BFF 0%, #36C2FF 100%) !important;
    color: #FFFFFF !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    box-shadow: 0 12px 32px rgba(47, 107, 255, 0.25) !important;
    border-bottom: 3px solid #2F6BFF !important;
    border-top: none !important;
    border-left: none !important;
    border-right: none !important;
    transform: translateY(-2px) !important;
    cursor: pointer !important;
    transition: all 0.25s ease !important;
}

div[data-testid="stColumn"] button[kind="secondary"] {
    width: 100% !important;
    height: 56px !important;
    border-radius: 16px !important;
    background: #FFFFFF !important;
    border: 1px solid #D6E6FF !important;
    color: #334155 !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    cursor: pointer !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03) !important;
}

div[data-testid="stColumn"] button[kind="secondary"]:hover {
    background: #F8FBFF !important;
    border-color: #36C2FF !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 24px rgba(54, 194, 255, 0.12) !important;
    color: #2F6BFF !important;
}

/* ENLARGED AUTHENTICATION CARD (600px MAX WIDTH) */
div[data-testid="stForm"] {
    background: rgba(255, 255, 255, 0.94) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border-radius: 28px !important;
    padding: clamp(24px, 3.2vh, 36px) clamp(28px, 4vw, 40px) !important;
    box-shadow: 0 24px 60px rgba(47, 107, 255, 0.12) !important;
    border: 1px solid rgba(255, 255, 255, 0.8) !important;
    max-width: 600px !important;
    width: 100% !important;
    margin: 0 auto !important;
    position: relative;
    z-index: 2;
}

/* Form Field Labels */
div[data-testid="stTextInput"] label, div[data-testid="stSelectbox"] label {
    font-family: 'Inter', sans-serif !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    color: #334155 !important;
    margin-bottom: 6px !important;
}

/* Main Outer Input Box (EXACTLY 56px Height, 16px Radius, Pure White #FFFFFF Background) */
div[data-testid="stTextInput"] div[data-baseweb="input"],
div[data-testid="stSelectbox"] div[data-baseweb="select"] {
    height: 56px !important;
    min-height: 56px !important;
    max-height: 56px !important;
    border-radius: 16px !important;
    background: #FFFFFF !important;
    border: 1px solid #D8E5FF !important;
    overflow: hidden !important;
    padding: 0 !important;
    margin: 0 !important;
    display: flex !important;
    align-items: center !important;
    box-shadow: none !important;
    transition: all 0.2s ease !important;
}

div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
div[data-testid="stSelectbox"] div[data-baseweb="select"]:focus-within {
    border-color: #2F6BFF !important;
    box-shadow: 0 0 0 4px rgba(47, 107, 255, 0.12) !important;
}

/* Text Input Area (Pure White #FFFFFF, Padding-Left 16px, Inter 16px) */
div[data-testid="stTextInput"] input {
    height: 56px !important;
    padding-left: 16px !important;
    border: none !important;
    background: #FFFFFF !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 16px !important;
    font-weight: 400 !important;
    color: #0F172A !important;
    width: 100% !important;
}
div[data-testid="stTextInput"] input::placeholder {
    color: #98A2B3 !important;
}

/* Right-Side Icon Button for Password Eye (EXACTLY 56px Width x 56px Height) */
div[data-testid="stTextInput"] div[data-baseweb="input"] button {
    background: linear-gradient(135deg, #2F6BFF 0%, #36C2FF 100%) !important;
    color: #FFFFFF !important;
    width: 56px !important;
    min-width: 56px !important;
    max-width: 56px !important;
    height: 56px !important;
    min-height: 56px !important;
    max-height: 56px !important;
    border-radius: 0 16px 16px 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    border: none !important;
    margin: 0 !important;
    padding: 0 !important;
    cursor: pointer !important;
    box-shadow: none !important;
    transition: all 0.2s ease !important;
}
div[data-testid="stTextInput"] div[data-baseweb="input"] button svg {
    fill: #FFFFFF !important;
    color: #FFFFFF !important;
    width: 18px !important;
    height: 18px !important;
    margin: auto !important;
    display: block !important;
}

/* BaseWeb Selectbox (Role Dropdown) Alignment & 64px Right Gradient Arrow Tile */
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:first-child {
    background: #FFFFFF !important;
    padding-left: 16px !important;
    height: 56px !important;
    display: flex !important;
    align-items: center !important;
    flex: 1 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 16px !important;
    font-weight: 400 !important;
    color: #0F172A !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"] [data-baseweb="value-container"] {
    background: #FFFFFF !important;
    padding: 0 !important;
}

/* 64px Right Blue Gradient Arrow Tile */
div[data-testid="stSelectbox"] div[data-baseweb="icon-container"] {
    background: linear-gradient(135deg, #2F6BFF 0%, #36C2FF 100%) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 64px !important;
    min-width: 64px !important;
    max-width: 64px !important;
    height: 56px !important;
    min-height: 56px !important;
    max-height: 56px !important;
    border-top-right-radius: 15px !important;
    border-bottom-right-radius: 15px !important;
    border-top-left-radius: 0px !important;
    border-bottom-left-radius: 0px !important;
    margin: 0 !important;
    padding: 0 !important;
    box-shadow: none !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
}

/* Centered White 18px Chevron Arrow Icon with Smooth 180° Rotation on Expand */
div[data-testid="stSelectbox"] svg {
    fill: #FFFFFF !important;
    color: #FFFFFF !important;
    width: 18px !important;
    height: 18px !important;
    margin: auto !important;
    display: block !important;
    transition: transform 0.25s ease !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"][aria-expanded="true"] svg {
    transform: rotate(180deg) !important;
}

/* Live Validation Warnings Styling */
.val-warning-msg {
    font-size: 13px;
    color: #F04438;
    text-align: left;
    margin-top: 6px;
    margin-bottom: 8px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 5px;
    animation: fadeIn 0.2s ease-in-out;
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(-3px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Checkbox Style */
div[data-testid="stCheckbox"] input[type="checkbox"] {
    accent-color: #2F6BFF !important;
    width: 18px !important;
    height: 18px !important;
    border-radius: 6px !important;
    cursor: pointer !important;
}
div[data-testid="stCheckbox"] label span {
    color: #475569 !important;
    font-size: 14px !important;
    font-weight: 500 !important;
}

/* Sign In Primary Gradient Button */
div[data-testid="stForm"] button, .stButton button {
    height: 56px !important;
    border-radius: 16px !important;
    background: linear-gradient(90deg, #2F6BFF 0%, #36C2FF 100%) !important;
    font-size: 16px !important;
    font-weight: 700 !important;
    color: #FFFFFF !important;
    border: none !important;
    box-shadow: 0 14px 32px rgba(47, 107, 255, 0.28) !important;
    transition: all 0.25s ease !important;
    margin-top: 0.4rem !important;
}
div[data-testid="stForm"] button:hover, .stButton button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 18px 40px rgba(47, 107, 255, 0.35) !important;
}
</style>
""")
    st.markdown(css_styles, unsafe_allow_html=True)

    # Ambient Soft Glow Background
    glow_html = _clean_html("""<div class="bg-ambient-soft"></div>""")
    st.markdown(glow_html, unsafe_allow_html=True)

    # 1. BRANDING SECTION CENTERED ABOVE CARD
    top_branding_html = _clean_html("""
<div class="brand-grouped-section">
    <div class="brand-logo-squircle">
        <svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2a10 10 0 0 0-10 10c0 5.5 4.5 10 10 10s10-4.5 10-10A10 10 0 0 0 12 2z"></path>
            <path d="M12 6v6l4 2"></path>
            <circle cx="12" cy="12" r="3"></circle>
        </svg>
    </div>
    <h1 class="brand-title-text">Mr. AI Smart Classroom</h1>
    <div class="brand-subtitle-text">AI-Powered Learning Platform</div>
</div>
""")
    st.markdown(top_branding_html, unsafe_allow_html=True)

    # 2. 3 TAB BUTTONS MATCHING FULL 600px CARD WIDTH
    current_tab = st.session_state.get("auth_tab", "Login")

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🔑 Login", use_container_width=True, type="primary" if current_tab == "Login" else "secondary", key="strict_tab_login"):
            st.session_state["auth_tab"] = "Login"
            st.rerun()
    with c2:
        if st.button("📝 Register", use_container_width=True, type="primary" if current_tab == "Register" else "secondary", key="strict_tab_register"):
            st.session_state["auth_tab"] = "Register"
            st.rerun()
    with c3:
        if st.button("👤 Guest", use_container_width=True, type="primary" if current_tab == "Guest" else "secondary", key="strict_tab_guest"):
            st.session_state["auth_tab"] = "Guest"
            st.rerun()

    # 3. AUTHENTICATION CARD FOR LOGIN / REGISTER / GUEST (USING NATIVE ST.FORM)
    # 3. AUTHENTICATION CARD FOR LOGIN / REGISTER / GUEST (USING NATIVE ST.FORM)
    if current_tab == "Login":
        st.markdown("""
        <script>
        (function setLoginAutocomplete() {
            try {
                var doc = window.parent.document;
                var pwdInputs = doc.querySelectorAll('input[type="password"]');
                pwdInputs.forEach(function(i) {
                    i.setAttribute('autocomplete', 'current-password');
                    i.setAttribute('name', 'password');
                    i.setAttribute('id', 'login-password');
                });
                var unameInputs = doc.querySelectorAll('input[placeholder="Enter your username"]');
                unameInputs.forEach(function(i) {
                    i.setAttribute('autocomplete', 'username');
                    i.setAttribute('name', 'username');
                    i.setAttribute('id', 'login-username');
                });
            } catch(e) {}
        })();
        </script>
        """, unsafe_allow_html=True)

        with st.form("strict_login_form"):
            default_uname = st.session_state.get("last_registered_user", "")
            uname = st.text_input("Username", value=default_uname, placeholder="Enter your username", key="login_input_uname")
            pwd = st.text_input("Password", type="password", placeholder="Enter your password", key="login_input_pwd")

            # Checkbox & Forgot password link
            rc1, rc2 = st.columns([1, 1])
            with rc1:
                st.checkbox("Remember me", value=True, key="login_remember_chk")
            with rc2:
                st.markdown("<div style='text-align: right; margin-top: 0.2rem;'><a href='#' style='color: #2F6BFF; font-size: 14px; font-weight: 600; text-decoration: none;'>Forgot password?</a></div>", unsafe_allow_html=True)

            submitted = st.form_submit_button("Sign In →", use_container_width=True)

            if submitted:
                ok, msg, user = login_user_account(uname, pwd)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    elif current_tab == "Register":
        st.markdown("""
        <script>
        (function setRegisterAutocomplete() {
            try {
                var doc = window.parent.document;
                var pwdInputs = doc.querySelectorAll('input[type="password"]');
                pwdInputs.forEach(function(i) {
                    i.setAttribute('autocomplete', 'new-password');
                    i.setAttribute('name', 'new-password');
                    i.setAttribute('id', 'register-password');
                });
                var unameInputs = doc.querySelectorAll('input[placeholder="Enter your username"]');
                unameInputs.forEach(function(i) {
                    i.setAttribute('autocomplete', 'username');
                });
            } catch(e) {}
        })();
        </script>
        """, unsafe_allow_html=True)

        with st.form("strict_register_form"):
            new_uname = st.text_input("Username", key="strict_input_uname", placeholder="Enter your username")
            if new_uname and len(new_uname) < 3:
                st.markdown('<div class="val-warning-msg"><span>⚠️</span> Username must contain at least 3 characters.</div>', unsafe_allow_html=True)

            new_pwd = st.text_input("Password", type="password", key="strict_input_pwd", placeholder="Enter your password")
            if new_pwd and len(new_pwd) < 6:
                st.markdown('<div class="val-warning-msg"><span>⚠️</span> Password must contain at least 6 characters.</div>', unsafe_allow_html=True)

            role_options = ["Choose your role", "Student", "Teacher", "Parent", "Administrator"]
            new_role = st.selectbox("Role", role_options, index=0, key="strict_input_role")

            reg_submitted = st.form_submit_button("Create Account →", use_container_width=True)

            if reg_submitted:
                if new_role == "Choose your role" or not new_role:
                    st.error("⚠️ Please select a role.")
                else:
                    ok, msg = register_user_account(new_uname, new_pwd, new_role)
                    if ok:
                        st.success("🎉 Account Created Successfully! You can now login.")
                        st.balloons()
                        time.sleep(1.5)
                        st.session_state["auth_tab"] = "Login"
                        st.session_state["last_registered_user"] = new_uname.strip()
                        st.rerun()
                    else:
                        st.error(msg)

    elif current_tab == "Guest":
        guest_mode_html = _clean_html("""
<div style="padding: 1rem; background: #F8FAFC; border-radius: 16px; margin: 0.4rem 0 1rem 0; border: 1px solid #D6E6FF; text-align: center;">
    <div style="font-size:1.05rem; font-weight:700; color:#0F172A; margin-bottom:0.2rem;">Guest Access</div>
    <div style="font-size:0.85rem; color:#64748B; line-height:1.4;">Explore all AI learning workspace modules instantly with zero setup.</div>
</div>
""")
        st.markdown(guest_mode_html, unsafe_allow_html=True)
        if st.button("Continue as Guest →", use_container_width=True, key="strict_guest_btn"):
            guest_login()
            st.rerun()

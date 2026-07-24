"""
Mr. AI Smart Classroom — Blue-Cyan AI SaaS Theme & Styling Definitions
Applied throughout the entire application. Zero purple theming.
"""

FONTS = """
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
"""

SHARED_CSS = """
<style>
* { box-sizing: border-box; }
html, body, [data-testid="stApp"], [data-testid="stHeader"] * {
    font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
}

/* Hide Streamlit default footer chrome & permanently hide sidebar collapse/expand controls */
#MainMenu, footer, [data-testid="collapsedControl"], [data-testid="stSidebarCollapseButton"], button[kind="header"] {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
    height: 0 !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-thumb { border-radius: 10px; background: rgba(37, 99, 235, 0.4); }
::-webkit-scrollbar-track { background: transparent; }

/* Main container spacing */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2.5rem !important;
    padding-left: 2.5rem !important;
    padding-right: 2.5rem !important;
    max-width: 1500px !important;
}

/* Sidebar User Content Padding (Clean Streamlit Top/Bottom Balance) */
[data-testid="stSidebarUserContent"] {
    padding-top: 0.6rem !important;
    padding-bottom: 0.6rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
}

/* Sidebar Navigation Buttons (44px Height, 12px Radius, 7px Spacing) */
[data-testid="stSidebar"] div.stButton > button {
    height: 44px !important;
    padding: 0.55rem 0.95rem !important;
    border-radius: 12px !important;
    font-size: 0.9rem !important;
    font-weight: 700 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    gap: 0.75rem !important;
    margin-bottom: 0.45rem !important;
    transition: all 0.18s ease-in-out !important;
}
[data-testid="stSidebar"] div.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.25) !important;
}

/* Modern Card Rules */
.glass-card, div[data-testid="stForm"] {
    border-radius: 24px !important;
    padding: 24px !important;
    margin-bottom: 1.25rem !important;
}

/* Stat Card Styling */
.stat-number {
    font-size: 2.2rem;
    font-weight: 800;
    line-height: 1.1;
    color: #2563EB !important;
    letter-spacing: -0.02em;
}
.stat-label {
    font-size: 0.82rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

/* Chat display container */
.chat-user {
    display: flex;
    justify-content: flex-end;
    margin: 0.85rem 0;
}
.chat-user .bubble {
    max-width: 75%;
    padding: 0.9rem 1.3rem;
    border-radius: 22px 22px 4px 22px;
    font-size: 0.95rem;
    line-height: 1.6;
    background: linear-gradient(135deg, #2563EB 0%, #06B6D4 100%);
    color: #FFFFFF !important;
    box-shadow: 0 4px 15px rgba(37, 99, 235, 0.25);
}
.chat-ai {
    display: flex;
    justify-content: flex-start;
    margin: 0.85rem 0;
    gap: 0.85rem;
    align-items: flex-start;
}
.chat-ai .avatar {
    width: 38px; height: 38px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.15rem;
    flex-shrink: 0;
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
}
.chat-ai .bubble {
    max-width: 80%;
    padding: 0.9rem 1.3rem;
    border-radius: 4px 22px 22px 22px;
    font-size: 0.95rem;
    line-height: 1.6;
    box-shadow: 0 4px 20px rgba(0,0,0,0.04);
}

/* Gradient Header */
.gradient-header {
    border-radius: 24px;
    padding: 1.8rem 2.2rem;
    margin-bottom: 1.8rem;
    background: linear-gradient(135deg, #2563EB 0%, #06B6D4 100%);
    color: #FFFFFF !important;
    box-shadow: 0 10px 30px rgba(37, 99, 235, 0.25);
}
.gradient-header h1 {
    font-size: 1.85rem;
    font-weight: 800;
    margin: 0;
    color: #FFFFFF !important;
    letter-spacing: -0.02em;
}
.gradient-header p {
    margin: 0.35rem 0 0;
    font-size: 0.95rem;
    color: #E0F2FE !important;
}

/* Blue-Cyan Gradient Buttons */
div.stButton > button, div[data-testid="stForm"] button {
    border-radius: 14px !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    padding: 0.6rem 1.4rem !important;
    border: none !important;
    transition: all 0.25s ease !important;
}
div.stButton > button:hover, div[data-testid="stForm"] button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(37, 99, 235, 0.3) !important;
}

/* Tab Bar Styling (Segmented control) */
div[data-testid="stTabs"] [role="tablist"] {
    padding: 4px !important;
    border-radius: 16px !important;
    gap: 4px !important;
}
div[data-testid="stTabs"] button[role="tab"] {
    border-radius: 12px !important;
    font-weight: 700 !important;
    border: none !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.2s ease !important;
}

/* Radio Option Row Base Styling */
div[data-testid="stRadio"] [role="radiogroup"] {
    gap: 8px !important;
}
div[data-testid="stRadio"] [role="radiogroup"] label {
    border-radius: 12px !important;
    padding: 12px 16px !important;
    margin-bottom: 8px !important;
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    font-size: 15px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
    cursor: pointer !important;
}

/* Input Fields Overrides */
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stSelectbox"] div[role="combobox"] {
    border-radius: 14px !important;
    padding: 0.75rem 1rem !important;
    font-size: 0.95rem !important;
}
</style>
"""

# ☀️ LIGHT MODE
LIGHT_MODE = """
<style>
[data-testid="stApp"] {
    background: linear-gradient(135deg, #F8FAFC 0%, #EEF4FF 100%) !important;
}
p, span, label, li, h1, h2, h3, h4, h5, h6,
div[data-testid="stMarkdown"] *, .stMarkdown *,
[data-testid="stWidgetLabel"] *, [data-testid="stHeader"] * {
    color: #111827 !important;
}
[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid #E2E8F0 !important;
}
.glass-card, div[data-testid="stForm"] {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    box-shadow: 0 12px 40px rgba(15, 23, 42, 0.06) !important;
}
.chat-ai .bubble {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    color: #111827 !important;
}
div.stButton > button {
    background: linear-gradient(135deg, #2563EB 0%, #06B6D4 100%) !important;
    color: #FFFFFF !important;
}
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stSelectbox"] div[role="combobox"] {
    background: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    color: #111827 !important;
}
div[data-testid="stTabs"] [role="tablist"] {
    background: #F1F5F9 !important;
    border: 1px solid #E2E8F0 !important;
}
div[data-testid="stTabs"] button[role="tab"] {
    color: #64748B !important;
}
div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    background: #FFFFFF !important;
    color: #2563EB !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
}
div[data-testid="stRadio"] [role="radiogroup"] label {
    background: #FFFFFF !important;
    border: 1px solid #E5E7EB !important;
    color: #1F2937 !important;
}
div[data-testid="stRadio"] [role="radiogroup"] label:hover {
    border-color: #2563EB !important;
    background: #F8FAFC !important;
}
.stat-label { color: #475569 !important; }
</style>
"""

# 🌙 DARK MODE
DARK_MODE = """
<style>
[data-testid="stApp"] {
    background: linear-gradient(135deg, #0F172A 0%, #111827 100%) !important;
}
p, span, label, li, h1, h2, h3, h4, h5, h6,
div[data-testid="stMarkdown"] *, .stMarkdown *,
[data-testid="stWidgetLabel"] *, [data-testid="stHeader"] * {
    color: #FFFFFF !important;
}
[data-testid="stSidebar"] {
    background: #1E293B !important;
    border-right: 1px solid #334155 !important;
}
.glass-card, div[data-testid="stForm"] {
    background: #1E293B !important;
    border: 1px solid #334155 !important;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35) !important;
}
.chat-ai .bubble {
    background: #1E293B !important;
    border: 1px solid #334155 !important;
    color: #FFFFFF !important;
}

/* Checkboxes Dark Mode */
[data-testid="stCheckbox"] label span:first-child {
    background-color: #1E293B !important;
    border: 1px solid #475569 !important;
}
[data-testid="stCheckbox"] label p, [data-testid="stCheckbox"] label span {
    color: #F8FAFC !important;
}
[data-testid="stCheckbox"] input[type="checkbox"]:checked + div,
[data-testid="stCheckbox"] label span[aria-checked="true"] {
    background: linear-gradient(135deg, #2563EB, #06B6D4) !important;
    border-color: #38BDF8 !important;
}

/* Input Fields Dark Mode */
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stNumberInput"] input {
    background: #111827 !important;
    border: 1px solid #374151 !important;
    color: #F9FAFB !important;
}
div[data-testid="stTextInput"] input::placeholder,
div[data-testid="stTextArea"] textarea::placeholder {
    color: #94A3B8 !important;
    opacity: 1 !important;
}

/* Select Boxes / Dropdowns Dark Mode */
div[data-testid="stSelectbox"] div[role="combobox"],
div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
    background: #1E293B !important;
    border: 1px solid #475569 !important;
    color: #F8FAFC !important;
}
div[data-testid="stSelectbox"] [data-baseweb="select"] * {
    color: #F8FAFC !important;
}
div[data-testid="stRadio"] [role="radiogroup"] label {
    background: #1E293B !important;
    border: 1px solid #334155 !important;
    color: #F8FAFC !important;
}
div[data-testid="stRadio"] [role="radiogroup"] label:hover {
    border-color: #38BDF8 !important;
    background: #0F172A !important;
}
ul[role="listbox"], li[role="option"], [data-baseweb="menu"] {
    background: #1E293B !important;
    color: #F8FAFC !important;
}
li[role="option"]:hover, [data-baseweb="menu"] li:hover {
    background: #334155 !important;
    color: #38BDF8 !important;
}

/* Buttons Dark Mode */
div.stButton > button {
    background: linear-gradient(135deg, #3B82F6 0%, #06B6D4 100%) !important;
    color: #FFFFFF !important;
}
div.stButton > button:disabled {
    opacity: 0.65 !important;
    color: #CBD5E1 !important;
}

/* Tabs Dark Mode */
div[data-testid="stTabs"] [role="tablist"] {
    background: #0F172A !important;
    border: 1px solid #334155 !important;
}
div[data-testid="stTabs"] button[role="tab"] {
    color: #94A3B8 !important;
}
div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    background: #1E293B !important;
    color: #38BDF8 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
}
.stat-label { color: #94A3B8 !important; }

/* File Uploader Dark Mode High-Contrast Visibility */
[data-testid="stFileUploader"] {
    background: #1E293B !important;
    border: 2px dashed #3B82F6 !important;
    border-radius: 18px !important;
    padding: 1rem !important;
}
[data-testid="stFileUploader"] * {
    color: #F8FAFC !important;
}
[data-testid="stFileUploader"] section {
    background: #0F172A !important;
    border-radius: 14px !important;
}
[data-testid="stFileUploader"] small {
    color: #94A3B8 !important;
    font-weight: 600 !important;
}
</style>
"""

THEMES = {
    "Light Mode": LIGHT_MODE,
    "Dark Mode": DARK_MODE,
    # Fallback aliases
    "Light Modern": LIGHT_MODE,
    "Pastel Theme": LIGHT_MODE,
    "Cyber Theme": DARK_MODE,
    "Minimal Theme": LIGHT_MODE,
}

THEME_ICONS = {
    "Light Mode": "☀️",
    "Dark Mode": "🌙",
}

def apply_theme(theme_name: str):
    """Inject fonts + shared CSS + theme-specific CSS into the Streamlit page."""
    css = THEMES.get(theme_name, LIGHT_MODE)
    import streamlit as st
    st.markdown(FONTS + SHARED_CSS + css, unsafe_allow_html=True)

"""
ScholarMind AI — Chat Bubble Component
Renders ChatGPT-style right-aligned user bubbles and left-aligned AI response cards.
"""
import streamlit as st
from app.rag.qa_chain import PERSONA_ICONS


def render_user_bubble(content: str):
    """Right-aligned user message bubble with blue gradient."""
    st.markdown(f"""
    <div style="display: flex; justify-content: flex-end; margin: 0.85rem 0;">
        <div style="max-width: 70%; padding: 0.85rem 1.25rem; border-radius: 22px 22px 4px 22px;
                    font-size: 0.95rem; line-height: 1.6; background: linear-gradient(135deg, #2563EB 0%, #06B6D4 100%);
                    color: #FFFFFF !important; box-shadow: 0 4px 15px rgba(37, 99, 235, 0.25); margin-left: auto;">
            {content}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_ai_bubble(content: str, persona: str = "Friendly Tutor"):
    """Left-aligned AI response bubble with persona avatar."""
    icon = PERSONA_ICONS.get(persona, "🤖")
    html_content = content.replace("\n", "<br>")
    st.markdown(f"""
    <div style="display: flex; justify-content: flex-start; margin: 0.85rem 0; gap: 0.75rem; align-items: flex-start;">
        <div style="width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
                    font-size: 1.1rem; flex-shrink: 0; background: rgba(37,99,235,0.1); border: 1px solid rgba(37,99,235,0.2);">
            {icon}
        </div>
        <div style="max-width: 70%; padding: 0.85rem 1.25rem; border-radius: 4px 22px 22px 22px;
                    font-size: 0.95rem; line-height: 1.6; background: rgba(128,128,128,0.06);
                    border: 1px solid rgba(128,128,128,0.15); box-shadow: 0 4px 20px rgba(0,0,0,0.04);">
            {html_content}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_source_citations(sources: list[dict]):
    """Render collapsible source page citations."""
    if not sources:
        return
    with st.expander("📚 Sources Used", expanded=True):
        for src in sources:
            page = src.get("page", "?")
            st.markdown(f"✓ Page {page}")


def render_chat_history(history: list[dict], persona: str = "Friendly Tutor"):
    """Render full chat history with ChatGPT-style user and AI bubbles."""
    for msg in history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            render_user_bubble(content)
        else:
            render_ai_bubble(content, persona)

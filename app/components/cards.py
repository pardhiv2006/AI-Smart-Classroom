"""
ScholarMind AI — Glassmorphism Stat Card & UI Components
"""
import streamlit as st


def stat_card(icon: str, label: str, value: str, sublabel: str = "", color: str = "#6366F1"):
    """Render a single glassmorphism stat card."""
    st.markdown(f"""
    <div class="glass-card" style="text-align: center; padding: 1.3rem 1rem;">
        <div style="font-size: 2rem; margin-bottom: 0.4rem;">{icon}</div>
        <div class="stat-number" style="color: {color};">{value}</div>
        <div class="stat-label">{label}</div>
        {"<div style='font-size:0.75rem; opacity:0.55; margin-top:0.3rem;'>" + sublabel + "</div>" if sublabel else ""}
    </div>
    """, unsafe_allow_html=True)


def gradient_header(title: str, subtitle: str = "", emoji: str = ""):
    """Render a full-width gradient page header."""
    st.markdown(f"""
    <div class="gradient-header">
        <h1>{emoji + " " if emoji else ""}{title}</h1>
        {"<p>" + subtitle + "</p>" if subtitle else ""}
    </div>
    """, unsafe_allow_html=True)


def section_card(content_fn, title: str = ""):
    """Wrap a block of content in a glass card with optional title."""
    with st.container(border=True):
        if title:
            st.markdown(f"<div style='font-weight: 700; font-size: 1rem; margin-bottom: 1rem;'>{title}</div>", unsafe_allow_html=True)
        content_fn()


def quiz_option_button(opt_key: str, opt_text: str, selected: bool = False, is_correct: bool = None, disabled: bool = False, key: str = None) -> bool:
    """
    Render a styled quiz option button.
    Returns True if clicked.
    """
    label = f"{opt_key}. {opt_text}"
    if disabled:
        if is_correct is True:
            st.success(f"✓ {label}")
        elif selected and is_correct is False:
            st.error(f"✗ {label}")
        elif selected:
            st.info(f"👉 {label}")
        else:
            st.markdown(f"<div style='padding:0.4rem; opacity:0.6;'>{label}</div>", unsafe_allow_html=True)
        return False
    else:
        btn_type = "primary" if selected else "secondary"
        return st.button(f"{opt_key}. {opt_text}", key=key, type=btn_type, use_container_width=True)


def activity_feed_item(activity_type: str, book_name: str, timestamp: str):
    """Render a single activity feed row."""
    icons = {"chat": "💬", "quiz": "✏️", "book": "📚"}
    labels = {"chat": "Asked a question", "quiz": "Took a quiz", "book": "Uploaded book"}
    icon = icons.get(activity_type, "📋")
    label = labels.get(activity_type, "Activity")
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(timestamp)
        ts_str = dt.strftime("%b %d, %H:%M")
    except Exception:
        ts_str = timestamp[:16] if timestamp else ""

    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 0.75rem; padding: 0.6rem 0;
                border-bottom: 1px solid rgba(128,128,128,0.1);">
        <div style="width: 32px; height: 32px; border-radius: 8px; background: rgba(99,102,241,0.1);
                    display: flex; align-items: center; justify-content: center; font-size: 0.95rem;
                    flex-shrink: 0;">{icon}</div>
        <div style="flex: 1; min-width: 0;">
            <div style="font-size: 0.85rem; font-weight: 600;
                        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                {label}: {book_name[:30]}
            </div>
            <div style="font-size: 0.72rem; opacity: 0.55;">{ts_str}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def badge(text: str, color: str = "#6366F1", bg: str = "#EEF2FF"):
    """Inline colored badge."""
    st.markdown(
        f'<span class="badge" style="background:{bg}; color:{color};">{text}</span>',
        unsafe_allow_html=True
    )


def divider():
    st.markdown("<hr style='border-color:rgba(128,128,128,0.15); margin: 1rem 0;'>", unsafe_allow_html=True)

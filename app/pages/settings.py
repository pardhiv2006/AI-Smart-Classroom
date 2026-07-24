"""
Mr. AI Smart Classroom — Settings Page
Theme switching, AI persona, model selection, performance mode.
All changes apply instantly (no restart needed).
"""
import streamlit as st
import requests
from app.components.cards import gradient_header
from app.themes.styles import THEMES, THEME_ICONS
from app.rag.qa_chain import (
    PERSONA_SYSTEM_PROMPTS, PERSONA_ICONS,
    PERF_MODEL_MAP, check_ollama_running,
)
from app.database.db import update_user_preference


def get_available_models() -> list[str]:
    """Dynamically fetch installed Ollama models. Falls back to [llama3] if unavailable."""
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=2)
        if resp.status_code == 200:
            models = [m["name"] for m in resp.json().get("models", [])]
            return models if models else ["llama3"]
    except Exception:
        pass
    return ["llama3"]


PERSONAS      = list(PERSONA_SYSTEM_PROMPTS.keys())
THEME_NAMES   = ["Light Mode", "Dark Mode"]
PERF_MODES    = ["Battery Saver", "Balanced", "High Quality"]

PERF_DESC = {
    "Battery Saver": {
        "model": "llama3",
        "chunk": "400 tokens",
        "emoji": "🔋",
        "desc": "Lightest RAM usage. Best for 8GB. Fast responses.",
        "color": "#34D399",
    },
    "Balanced": {
        "model": "llama3",
        "chunk": "500 tokens",
        "emoji": "⚖️",
        "desc": "Recommended for M2 8GB. Good quality and speed.",
        "color": "#6366F1",
    },
    "High Quality": {
        "model": "llama3",
        "chunk": "700 tokens",
        "emoji": "🚀",
        "desc": "Best answers. Higher RAM usage. Requires 8GB+ free.",
        "color": "#F59E0B",
    },
}


def _save_pref(user_id: int, field: str, value: str):
    """Save preference to DB if logged-in user."""
    if user_id:
        update_user_preference(user_id, field, value)


def render():
    user     = st.session_state.get("sm_user", {})
    user_id  = user.get("id", 0)
    is_guest = user.get("role") == "guest"

    gradient_header("Settings", "Customize your learning experience", "⚙️")

    if is_guest:
        st.info("👤 **Guest Mode** — Settings apply for this session only. Register to save your preferences.")

    # ══════════════════════════════════════════════════
    # SECTION 1: THEMES
    # ══════════════════════════════════════════════════
    # Replaced split glass-card div with native container to avoid DOM break
    with st.container(border=True):
        st.markdown("#### 🎨 Theme")

        current_theme = user.get("theme", "Light Modern")

        t_cols = st.columns(len(THEME_NAMES))
        for i, t_name in enumerate(THEME_NAMES):
            with t_cols[i]:
                is_active = (current_theme == t_name)
                border = "3px solid #6366F1" if is_active else "2px solid transparent"
                bg = "rgba(99,102,241,0.12)" if is_active else "rgba(128,128,128,0.05)"
                st.markdown(f"""
                <div style="text-align:center; padding:0.8rem 0.3rem; border-radius:12px;
                            background:{bg}; border:{border}; margin-bottom:0.4rem; cursor:pointer;">
                    <div style="font-size:1.6rem;">{THEME_ICONS.get(t_name,'🎨')}</div>
                    <div style="font-size:0.75rem; font-weight:{'700' if is_active else '500'};
                                margin-top:0.25rem; opacity:{'1' if is_active else '0.7'};">
                        {t_name.replace(' Theme','').replace(' Mode','')}
                    </div>
                    {"<div style='font-size:0.6rem;color:#6366F1;font-weight:700;'>ACTIVE</div>" if is_active else ""}
                </div>
                """, unsafe_allow_html=True)
                if st.button(t_name, key=f"theme_btn_{i}", use_container_width=True,
                             type="primary" if is_active else "secondary"):
                    user["theme"] = t_name
                    st.session_state["sm_user"] = user
                    _save_pref(user_id, "theme", t_name)
                    st.rerun()

    # ══════════════════════════════════════════════════
    # SECTION 2: PERFORMANCE MODE
    # ══════════════════════════════════════════════════
    st.markdown("<br>", unsafe_allow_html=True)
    # Replaced split glass-card div with native container to avoid DOM break
    with st.container(border=True):
        st.markdown("#### ⚡ Performance Mode")
        st.markdown("<p style='opacity:0.65; font-size:0.85rem; margin-top:-0.5rem;'>Controls model selection and chunk size. Optimized for Apple M2 8GB.</p>", unsafe_allow_html=True)

        current_perf = user.get("perf_mode", "Balanced")
        p_cols = st.columns(3)
        for i, mode in enumerate(PERF_MODES):
            info = PERF_DESC[mode]
            is_active = (current_perf == mode)
            border = f"2px solid {info['color']}" if is_active else "1px solid rgba(128,128,128,0.15)"
            bg     = f"{info['color']}15" if is_active else "rgba(128,128,128,0.04)"
            with p_cols[i]:
                st.markdown(f"""
                <div style="padding:1rem; border-radius:14px; border:{border};
                            background:{bg}; margin-bottom:0.5rem; min-height:130px;">
                    <div style="font-size:1.4rem; margin-bottom:0.4rem;">{info['emoji']}</div>
                    <div style="font-weight:700; font-size:0.9rem; color:{info['color']}; margin-bottom:0.3rem;">{mode}</div>
                    <div style="font-size:0.75rem; opacity:0.7; margin-bottom:0.4rem; line-height:1.4;">{info['desc']}</div>
                    <div style="font-size:0.72rem; opacity:0.55;">Model: <b>{info['model']}</b><br>Chunks: <b>{info['chunk']}</b></div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(
                    f"{'✓ ' if is_active else ''}Select", key=f"perf_btn_{i}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary"
                ):
                    user["perf_mode"] = mode
                    user["ai_model"]  = info["model"]
                    st.session_state["sm_user"] = user
                    _save_pref(user_id, "perf_mode", mode)
                    _save_pref(user_id, "ai_model", info["model"])
                    st.success(f"✅ Switched to {mode} mode using **{info['model']}**")
                    st.rerun()

    # ══════════════════════════════════════════════════
    # SECTION 3: AUTOMATIC AI MODEL DISCOVERY & SELECTION
    # ══════════════════════════════════════════════════
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("#### 🤖 AI Model Configuration")
        from app.utils.model_detector import (
            detect_available_models, get_active_model,
            refresh_model_cache, is_model_available
        )

        active_model = get_active_model()
        available_models = detect_available_models()
        is_running = len(available_models) > 0

        # Status Summary Grid
        st.markdown(f"""
        <div style="background: rgba(37,99,235,0.06); border: 1px solid rgba(37,99,235,0.18); border-radius: 14px; padding: 1rem 1.25rem; margin-bottom: 1rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                <div>
                    <div style="font-size: 0.78rem; color: #64748B; font-weight: 600; text-transform: uppercase;">Current Model</div>
                    <div style="font-size: 1.15rem; font-weight: 800; color: #2563EB;">✅ {active_model}</div>
                </div>
                <div>
                    <div style="font-size: 0.78rem; color: #64748B; font-weight: 600; text-transform: uppercase;">Status</div>
                    <div style="font-size: 1rem; font-weight: 700; color: {'#059669' if is_running else '#D97706'};">
                        {'🟢 Running' if is_running else '⚠️ Server Offline'}
                    </div>
                </div>
                <div>
                    <div style="font-size: 0.78rem; color: #64748B; font-weight: 600; text-transform: uppercase;">Provider</div>
                    <div style="font-size: 1rem; font-weight: 700; color: #475569;">Ollama Local</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🔄 Refresh Models", key="refresh_ollama_models_btn", type="secondary"):
            best = refresh_model_cache()
            user["ai_model"] = best
            st.session_state["sm_user"] = user
            _save_pref(user_id, "ai_model", best)
            st.success(f"✅ Re-scanned installed models! Active model: **{best}**")
            st.rerun()

        if available_models:
            st.markdown("<div style='font-size: 0.88rem; font-weight: 700; margin: 0.75rem 0 0.5rem;'>Detected Installed Models:</div>", unsafe_allow_html=True)
            m_cols = st.columns(min(len(available_models), 4))
            for i, m in enumerate(available_models[:4]):
                is_active = (active_model == m or active_model.split(":")[0] == m.split(":")[0])
                with m_cols[i]:
                    st.markdown(f"""
                    <div style="text-align:center; padding:0.8rem 0.5rem; border-radius:12px;
                                background:{'rgba(99,102,241,0.1)' if is_active else 'rgba(128,128,128,0.05)'};
                                border:{'2px solid #6366F1' if is_active else '1px solid rgba(128,128,128,0.15)'};">
                        <div style="font-size:1.2rem;">{'🟣' if is_active else '⬜'}</div>
                        <div style="font-size:0.82rem; font-weight:700; margin:0.3rem 0;">{m}</div>
                        <div style="font-size:0.7rem; opacity:0.6;">{'Active' if is_active else 'Installed'}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"Use {m}", key=f"model_btn_{i}", use_container_width=True,
                                 type="primary" if is_active else "secondary"):
                        st.session_state["active_model"] = m
                        user["ai_model"] = m
                        st.session_state["sm_user"] = user
                        _save_pref(user_id, "ai_model", m)
                        st.success(f"✅ Active model set to **{m}**")
                        st.rerun()
        else:
            st.markdown("""
            <div style="background:rgba(245,158,11,0.1); border:1px solid rgba(245,158,11,0.3);
                        border-radius:10px; padding:0.8rem 1rem; margin-top:0.5rem; font-size:0.85rem;">
                ⚠️ <b>No Ollama models detected.</b> Start server with <code>ollama serve</code> and pull a model: <code>ollama pull llama3</code>
            </div>
            """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════
    # SECTION 4: AI PERSONA
    # ══════════════════════════════════════════════════
    st.markdown("<br>", unsafe_allow_html=True)
    # Replaced split glass-card div with native container to avoid DOM break
    with st.container(border=True):
        st.markdown("#### 🎭 AI Persona")
        st.markdown("<p style='opacity:0.65; font-size:0.85rem; margin-top:-0.5rem;'>Each persona uses a different teaching style and system prompt.</p>", unsafe_allow_html=True)

        current_persona = user.get("persona", "Friendly Tutor")
        p_rows = [PERSONAS[:3], PERSONAS[3:]]  # Split into two rows

        for row in p_rows:
            cols = st.columns(len(row))
            for i, persona in enumerate(row):
                is_active = (current_persona == persona)
                icon = PERSONA_ICONS.get(persona, "🤖")
                with cols[i]:
                    st.markdown(f"""
                    <div style="text-align:center; padding:0.8rem 0.4rem; border-radius:12px;
                                background:{'rgba(99,102,241,0.1)' if is_active else 'rgba(128,128,128,0.04)'};
                                border:{'2px solid #6366F1' if is_active else '1px solid rgba(128,128,128,0.12)'};
                                margin-bottom:0.4rem; cursor:pointer;">
                        <div style="font-size:1.5rem;">{icon}</div>
                        <div style="font-size:0.78rem; font-weight:{'700' if is_active else '500'};
                                    margin-top:0.3rem; line-height:1.3;">{persona}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(
                        persona, key=f"persona_btn_{persona.replace(' ','_')}",
                        use_container_width=True,
                        type="primary" if is_active else "secondary"
                    ):
                        user["persona"] = persona
                        st.session_state["sm_user"] = user
                        _save_pref(user_id, "persona", persona)
                        st.success(f"✅ AI persona set to **{persona}**")
                        st.rerun()

    # ══════════════════════════════════════════════════
    # SECTION 5: ACCOUNT INFO
    # ══════════════════════════════════════════════════
    if not is_guest:
        st.markdown("<br>", unsafe_allow_html=True)
        # Replaced split glass-card div with native container to avoid DOM break
        with st.container(border=True):
            st.markdown("#### 👤 Account")
            username = user.get("username", "")
            role = user.get("role", "student").capitalize()
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:1rem; padding:0.5rem 0;">
                <div style="width:48px; height:48px; border-radius:50%; background:linear-gradient(135deg,#6366F1,#8B5CF6);
                            display:flex; align-items:center; justify-content:center; font-size:1.3rem; color:#fff;
                            font-weight:800;">{username[0].upper()}</div>
                <div>
                    <div style="font-weight:700; font-size:1rem;">{username}</div>
                    <div style="font-size:0.8rem; opacity:0.6;">{role}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

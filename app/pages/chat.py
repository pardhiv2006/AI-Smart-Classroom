"""
Mr. AI Smart Classroom — AI Tutor Chat Page
ChatGPT-Style UI Layout:
- Native st.chat_message & native Streamlit empty state components (0 raw HTML tag leaks)
- Preserved Header controls (Study Material, Answer Mode, Persona selector)
- Restored "Clear Chat History for this Book" button position at bottom
- Fixed message composer via st.chat_input
- Unified loading message: 🤖 AI is generating your response...
"""
import streamlit as st
from app.components.cards import gradient_header
from app.components.chat_bubble import render_user_bubble, render_ai_bubble, render_chat_history
from app.rag.qa_chain import (
    answer_question, check_ollama_running, render_ollama_error,
    PERSONA_SYSTEM_PROMPTS, PERSONA_ICONS, get_llm
)
from app.database.db import (
    save_chat_message, get_chat_history, clear_chat_history,
    get_uploaded_books
)
from app.utils.model_detector import get_active_model

PERSONAS = list(PERSONA_SYSTEM_PROMPTS.keys())

def render():
    user = st.session_state.get("sm_user", {})
    user_id = user.get("id", 0)
    model_name = user.get("ai_model") or get_active_model()
    persona = user.get("persona", "Friendly Tutor")
    student_type = st.session_state.get("sm_student_type", "College Student")

    # 1. PRESERVED HEADER
    gradient_header("AI Tutor Chat", "Ask anything about your selected study material", "💬")

    # Fetch available books from database & session
    books_list = get_uploaded_books(user_id) if user_id else st.session_state.get("sm_guest_books", [])
    available_books = [b["book_name"] for b in books_list if "book_name" in b]

    # Check session for pre-selected book or fallback
    active_book_name = st.session_state.get("sm_book_name", "")
    if active_book_name and active_book_name not in available_books:
        available_books.insert(0, active_book_name)

    # Top Controls Bar
    col_sel, col_mode, col_persona = st.columns([3, 2, 2])

    with col_sel:
        if available_books:
            selected_idx = 0
            if "selected_book" in st.session_state and st.session_state["selected_book"] in available_books:
                selected_idx = available_books.index(st.session_state["selected_book"])
            
            selected_book = st.selectbox(
                "📚 Select Study Material",
                available_books,
                index=selected_idx,
                key="tutor_book_selector"
            )
            st.session_state["selected_book"] = selected_book
            st.session_state["sm_book_name"] = selected_book
        else:
            st.selectbox("📚 Select Study Material", ["No books available"], disabled=True)
            selected_book = None
            st.session_state["selected_book"] = None

    with col_mode:
        answer_mode = st.radio(
            "🧠 Answer Mode",
            ["Strict Book Mode", "Hybrid AI Mode"],
            horizontal=True,
            key="chat_answer_mode"
        )

    with col_persona:
        new_persona = st.selectbox(
            "👨‍🏫 AI Persona",
            PERSONAS,
            index=PERSONAS.index(persona) if persona in PERSONAS else 0,
            format_func=lambda p: f"{PERSONA_ICONS.get(p,'')} {p}",
            key="chat_persona_sel"
        )
        if new_persona != persona:
            user["persona"] = new_persona
            st.session_state["sm_user"] = user
            persona = new_persona

    # Guard: No books available
    if not selected_book:
        st.warning("""
        ⚠️ **No study material available.**
        Please upload a document from the **Books** page to start chatting with your AI Tutor.
        """)
        if st.button("📚 Go to Books Workspace", type="primary"):
            st.session_state["sm_page"] = "books"
            st.rerun()
        return

    # Display Selected Book Information
    book_info = next((b for b in books_list if b.get("book_name") == selected_book), {})
    indexed_pages = book_info.get("page_end", 1) - book_info.get("page_start", 1) + 1 if book_info else 1
    chunk_count = len(st.session_state.get("sm_chunks", []))
    upload_date = book_info.get("upload_time", "Recent")[:10] if book_info else "Recent"

    st.markdown(f"📚 **Current Book:** `{selected_book}` | 📄 **Pages:** `{indexed_pages}` | 🧩 **Chunks:** `{chunk_count if chunk_count else 'Active'}` | 📅 **Uploaded:** `{upload_date}`")

    # Developer Retrieval Status Panel
    with st.expander("🛠️ Developer Retrieval Status Panel", expanded=False):
        from app.rag.embedder import check_collection_health, compute_book_hash
        db_inst = st.session_state.get("sm_db")
        col_name = getattr(db_inst, "_collection_name", compute_book_hash(selected_book, 1, indexed_pages))
        is_healthy, h_details = check_collection_health(db_inst, col_name)

        last_ret_count = st.session_state.get("last_retrieved_count", 0)
        last_ret_pages = st.session_state.get("last_retrieved_pages", "None")
        last_ret_time = st.session_state.get("last_retrieval_ms", 0)

        dev_c1, dev_c2 = st.columns(2)
        with dev_c1:
            st.markdown(f"""
            - **📚 Selected Book:** `{selected_book}`
            - **📦 Collection ID:** `{col_name}`
            - **📄 Indexed Chunks:** `{chunk_count if chunk_count else h_details.get('chunk_count', 0)}`
            - **🏥 Collection Health:** `{"✅ Healthy" if is_healthy else "⚠️ Needs Rebuild"}`
            """)
        with dev_c2:
            st.markdown(f"""
            - **🔍 Retrieved Chunks:** `{last_ret_count}`
            - **🤖 Active Model:** `{model_name}`
            - **📄 Pages Used:** `{last_ret_pages}`
            - **⚡ Retrieval Time:** `{last_ret_time} ms`
            """)

        if not is_healthy:
            st.warning("⚠️ Collection health check warning. If retrieval is empty, click to rebuild index.")
            if st.button("⚡ Rebuild Collection Index", key="rebuild_col_btn"):
                st.session_state.pop("sm_db", None)
                st.session_state.pop("sm_chunks", None)
                st.rerun()

    # Ollama Health Check
    ok, msg = check_ollama_running(model_name)
    if not ok:
        render_ollama_error(msg)
        return

    # Load Chat History
    history_key = f"sm_chat_history_{selected_book}"
    if history_key not in st.session_state:
        if user_id and selected_book:
            st.session_state[history_key] = get_chat_history(user_id, selected_book, limit=40)
        else:
            st.session_state[history_key] = []

    history = st.session_state[history_key]

    with st.container(height=450):
        if not history:
            # ENTERPRISE SAAS HERO EMPTY STATE (MINIMAL, MINIMALIST, NO EXAMPLES CARD)
            import textwrap
            hero_html = textwrap.dedent("""
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center;
                        text-align: center; padding: 2.5rem 1.5rem; max-width: 520px; margin: 0 auto;">
                <div style="font-size: 58px; margin-bottom: 0.4rem; line-height: 1;">🧠</div>
                <div style="font-size: 36px; font-weight: 800; letter-spacing: -0.02em; margin-bottom: 0.5rem;">
                    AI Tutor
                </div>
                <div style="font-size: 17px; font-weight: 500; opacity: 0.75; line-height: 1.5; margin-bottom: 1.4rem;">
                    Your intelligent study assistant powered by your selected study material.
                </div>
                <div style="width: 100%; border-top: 1px solid rgba(128,128,128,0.15); margin-bottom: 1.4rem;"></div>
                <div style="font-size: 14.5px; opacity: 0.6; line-height: 1.6;">
                    Start a conversation to ask questions, summarize chapters, explain concepts, or generate learning content.
                </div>
            </div>
            """)
            st.markdown(hero_html, unsafe_allow_html=True)
        else:
            render_chat_history(history, persona)

    # RESTORED "CLEAR CHAT FROM THIS BOOK" AT BOTTOM
    if history:
        col_clr, _ = st.columns([2, 3])
        with col_clr:
            if st.button("🧹 Clear Chat History for this Book", key="clear_chat_btn", use_container_width=True):
                st.session_state[history_key] = []
                if user_id and selected_book:
                    clear_chat_history(user_id, selected_book)
                st.rerun()

    # CHATGPT-STYLE COMPOSER WITH EMBEDDED SEND ACTION
    user_question = st.chat_input("Ask anything about your selected study material...")

    if user_question and user_question.strip():
        q = user_question.strip()

        history.append({"role": "user", "content": q})
        render_user_bubble(q)
        if user_id and selected_book:
            save_chat_message(user_id, selected_book, "user", q)

        from app.rag.embedder import get_or_load_book_vectorstore
        db, chunks = get_or_load_book_vectorstore(selected_book, user_id)

        # UNIFIED LOADING STATE ONLY
        with st.spinner("🧠 Thinking..."):
            answer = ""
            sources = []

            if db:
                import time
                t0 = time.time()
                answer, sources = answer_question(
                    question=q,
                    db=db,
                    model_name=model_name,
                    persona=persona,
                    student_type=student_type,
                    book_name=selected_book,
                )
                t_ms = round((time.time() - t0) * 1000, 1)
                st.session_state["last_retrieved_count"] = len(sources)
                st.session_state["last_retrieved_pages"] = ", ".join(str(s.get("page", "?")) for s in sources) if sources else "None"
                st.session_state["last_retrieval_ms"] = t_ms

            has_no_context = (not sources or "couldn't find" in answer.lower() or "not in" in answer.lower())

            if has_no_context:
                if answer_mode == "Strict Book Mode":
                    answer = f"""❌ **I couldn't find this information inside:**

📚 **{selected_book}**

**Please:**
• Ask another question
• Select another uploaded book
• Upload another study material"""
                    sources = []
                else:  # Hybrid AI Mode
                    st.warning("⚠ No relevant information was found in the selected study material. The following answer is generated using general AI knowledge.")
                    try:
                        llm = get_llm(model_name)
                        resp = llm.invoke(f"Question: {q}\nAnswer concisely as a tutor:")
                        answer = "💡 **General AI Knowledge Answer:**\n\n" + resp.content
                    except Exception as e:
                        answer = f"❌ General AI error: {e}"

        # Add AI response to history
        history.append({"role": "assistant", "content": answer})
        render_ai_bubble(answer, persona)

        # Show Sources Used
        if sources:
            with st.expander("📚 Sources Used", expanded=True):
                for src in sources:
                    st.markdown(f"✓ **{selected_book}** — Page {src.get('page', '?')}")

        if user_id and selected_book:
            save_chat_message(user_id, selected_book, "assistant", answer)

        st.session_state[history_key] = history
        st.rerun()

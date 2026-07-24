"""
ScholarMind AI — Notes Page
Generates detailed study notes and extracts important questions.
Allows downloading notes as a styled PDF report.
"""
import streamlit as st
from app.components.cards import gradient_header
from app.utils.helpers import generate_study_notes, extract_important_questions, export_notes_to_pdf
from app.rag.qa_chain import check_ollama_running, render_ollama_error
from app.utils.model_detector import get_active_model
from app.database.db import get_uploaded_books
from app.rag.embedder import get_or_load_book_vectorstore


def render():
    user       = st.session_state.get("sm_user", {})
    user_id    = user.get("id", 0)
    model_name = user.get("ai_model") or get_active_model()

    gradient_header("Study Notes Workspace", "Summarize and review key topics from your text", "📒")

    # ── Fetch available books ────────────────────────────────────
    books_list = get_uploaded_books(user_id) if user_id else st.session_state.get("sm_guest_books", [])
    available_books = [b["book_name"] for b in books_list if "book_name" in b]

    # ── EMPTY STATE GUARD ────────────────────────────────────────
    if not available_books:
        st.markdown("""
        <div style="text-align:center; padding:3rem 2rem; background:rgba(37,99,235,0.04); border-radius:18px; border:2px dashed rgba(37,99,235,0.2);">
            <div style="font-size:3.5rem; margin-bottom:0.5rem;">📚</div>
            <div style="font-size:1.2rem; font-weight:800; color:#1E293B;">No Study Material Found</div>
            <div style="font-size:0.9rem; color:#64748B; margin-top:0.3rem;">Please upload a PDF, DOCX, TXT, or MD file from the Books page first.</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📚 Go to Books →", key="notes_goto_books", type="primary"):
            st.session_state["sm_page"] = "books"
            st.rerun()
        return

    # Auto-synchronize selected_book
    selected_idx = 0
    curr_selected = st.session_state.get("selected_book")
    if curr_selected and curr_selected in available_books:
        selected_idx = available_books.index(curr_selected)

    selected_book = st.selectbox(
        "📚 Study Material",
        available_books,
        index=selected_idx,
        key="notes_book_selector"
    )
    st.session_state["selected_book"] = selected_book
    st.session_state["sm_book_name"] = selected_book

    # Auto-connect vector store
    db, chunks = get_or_load_book_vectorstore(selected_book, user_id)

    # ── Ollama health check ──────────────────────────────────────
    ok, msg = check_ollama_running(model_name)
    if not ok:
        render_ollama_error(msg)
        return

    tab_notes, tab_questions = st.tabs(["📒 Study Notes", "❓ Key Questions"])

    # =========================================================================
    # TAB 1: STUDY NOTES
    # =========================================================================
    with tab_notes:
        with st.container(border=True):
            st.markdown("#### 📝 Study Notes Generator")
            st.markdown(f"<p style='opacity:0.65; font-size:0.85rem; margin-top:-0.5rem;'>🤖 Generating notes using <b>{model_name}</b> from <b>{selected_book}</b>.</p>", unsafe_allow_html=True)

        notes_key = f"sm_notes_content_{selected_book}"
        current_notes = st.session_state.get(notes_key, None)

        if current_notes:
            st.markdown(current_notes)
            st.markdown("<hr style='border-color:rgba(128,128,128,0.15);'>", unsafe_allow_html=True)

            pdf_bytes = export_notes_to_pdf(current_notes, title=f"Study Notes — {selected_book}")
            col_d1, col_d2 = st.columns([1, 4])
            with col_d1:
                if pdf_bytes:
                    st.download_button(
                        "⬇️ Download PDF",
                        data=pdf_bytes,
                        file_name=f"notes_{selected_book[:15].replace(' ','_')}.pdf",
                        mime="application/pdf",
                        type="primary",
                        use_container_width=True
                    )
            with col_d2:
                if st.button("🔄 Regenerate Notes", key="regen_notes"):
                    st.session_state.pop(notes_key, None)
                    st.rerun()
        else:
            st.markdown("""
            <div style="text-align:center; padding:2rem; opacity:0.65;">
                <p>No notes generated for this book yet.</p>
            </div>
            """, unsafe_allow_html=True)

            if st.button("🚀 Generate Detailed Notes", type="primary", use_container_width=True):
                with st.spinner("📝 Creating your study notes..."):
                    res_notes = generate_study_notes(chunks, model_name)
                    if res_notes:
                        st.session_state[notes_key] = res_notes
                        st.toast("✅ Response generated successfully.")
                        st.rerun()

    # =========================================================================
    # TAB 2: KEY QUESTIONS
    # =========================================================================
    with tab_questions:
        with st.container(border=True):
            st.markdown("#### ❓ Important Exam Questions")
            st.markdown(f"<p style='opacity:0.65; font-size:0.85rem; margin-top:-0.5rem;'>Extract important questions from <b>{selected_book}</b>.</p>", unsafe_allow_html=True)

        questions_key = f"sm_extracted_questions_{selected_book}"
        current_qs = st.session_state.get(questions_key, None)

        if current_qs:
            for idx, q in enumerate(current_qs):
                st.markdown(f"""
                <div style="padding: 0.8rem 1rem; border-radius: 12px; background: rgba(37,99,235,0.05);
                            border-left: 4px solid #2563EB; margin-bottom: 0.6rem;">
                    <b>{idx+1}.</b> {q}
                </div>""", unsafe_allow_html=True)

            st.markdown("<hr style='border-color:rgba(128,128,128,0.15);'>", unsafe_allow_html=True)
            if st.button("🔄 Extract Questions Again", key="regen_questions"):
                st.session_state.pop(questions_key, None)
                st.rerun()
        else:
            st.markdown("""
            <div style="text-align:center; padding:2rem; opacity:0.65;">
                <p>No questions extracted yet.</p>
            </div>
            """, unsafe_allow_html=True)

            if st.button("🚀 Extract Important Questions", type="primary", use_container_width=True):
                with st.spinner("📝 Creating your study notes..."):
                    res_qs = extract_important_questions(chunks, num_questions=8, model_name=model_name)
                    if res_qs:
                        st.session_state[questions_key] = res_qs
                        st.toast("✅ Response generated successfully.")
                        st.rerun()

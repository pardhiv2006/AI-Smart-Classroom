"""
ScholarMind AI — Flashcards & Revision Workspace
Provides interactive study flashcards and revision checklists, synced with the active study material.
"""
import random
import streamlit as st
from app.components.cards import gradient_header
from app.utils.helpers import generate_flashcards
from app.rag.qa_chain import check_ollama_running, render_ollama_error
from app.utils.model_detector import get_active_model
from app.database.db import get_uploaded_books
from app.rag.embedder import get_or_load_book_vectorstore


def render():
    user       = st.session_state.get("sm_user", {})
    user_id    = user.get("id", 0)
    model_name = user.get("ai_model") or get_active_model()

    gradient_header("Active Study Hub", "Interact with flashcards and track revision progress", "🗂")

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
        if st.button("📚 Go to Books →", key="fc_goto_books", type="primary"):
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
        key="fc_book_selector"
    )
    st.session_state["selected_book"] = selected_book
    st.session_state["sm_book_name"] = selected_book

    # Auto-connect vector store
    db, chunks = get_or_load_book_vectorstore(selected_book, user_id)
    page_range = st.session_state.get("sm_page_range", (1, 1))

    # ── Ollama health check ──────────────────────────────────────
    ok, msg = check_ollama_running(model_name)
    if not ok:
        render_ollama_error(msg)
        return

    tab_fc, tab_rev = st.tabs(["🗂 Study Flashcards", "🔄 Revision Mode"])

    # =========================================================================
    # TAB 1: STUDY FLASHCARDS
    # =========================================================================
    with tab_fc:
        fc_key = f"sm_flashcards_deck_{selected_book}"
        deck = st.session_state.get(fc_key, None)

        if not deck:
            with st.container(border=True):
                st.markdown("#### 📇 Generate Study Flashcards")
                st.markdown(f"<p style='opacity:0.65; font-size:0.85rem; margin-top:-0.5rem;'>🤖 Generating using <b>{model_name}</b> from <b>{selected_book}</b>.</p>", unsafe_allow_html=True)

                if st.button("🚀 Build Flashcard Deck", type="primary", use_container_width=True):
                    with st.spinner("🃏 Building your flashcards..."):
                        res_cards = generate_flashcards(chunks, num_cards=10, model_name=model_name)
                        if res_cards:
                            st.session_state[fc_key] = res_cards
                            st.session_state["sm_fc_idx"] = 0
                            st.session_state["sm_fc_flipped"] = False
                            st.toast("✅ Response generated successfully.")
                            st.rerun()
        else:
            idx = st.session_state.get("sm_fc_idx", 0)
            flipped = st.session_state.get("sm_fc_flipped", False)

            idx = max(0, min(len(deck) - 1, idx))
            card = deck[idx]

            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                <span style="font-weight:700; font-size:0.9rem; opacity:0.8;">Card {idx+1} of {len(deck)}</span>
                <span style="background:rgba(37,99,235,0.1); color:#2563EB; padding:0.2rem 0.75rem; border-radius:999px; font-weight:700; font-size:0.75rem;">
                    {'BACK (Answer)' if flipped else 'FRONT (Question/Term)'}
                </span>
            </div>
            """, unsafe_allow_html=True)

            if not flipped:
                st.markdown(f"""
                <div style="min-height:220px; display:flex; align-items:center; justify-content:center; text-align:center;
                            padding:2rem; border-radius:20px; border:2px solid #2563EB; background:rgba(37,99,235,0.03);
                            box-shadow:0 10px 40px rgba(15,23,42,.08); transition:.25s;">
                    <div style="font-size:1.25rem; font-weight:700; color:#1E293B;">
                        {card.get('front', '')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="min-height:220px; display:flex; align-items:center; justify-content:center; text-align:center;
                            padding:2rem; border-radius:20px; border:2px solid #0EA5E9; background:rgba(14,165,233,0.04);
                            box-shadow:0 10px 40px rgba(15,23,42,.08); transition:.25s;">
                    <div style="font-size:1.15rem; font-weight:600; color:#1E293B; line-height:1.6;">
                        💡 {card.get('back', '')}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            b_col1, b_col2, b_col3, b_col4, b_col5 = st.columns([1.5, 2, 1.5, 1.5, 1.5])
            with b_col1:
                if st.button("← Previous", disabled=(idx == 0), use_container_width=True):
                    st.session_state["sm_fc_idx"] = idx - 1
                    st.session_state["sm_fc_flipped"] = False
                    st.rerun()
            with b_col2:
                if st.button("🔄 Flip Card", type="primary", use_container_width=True):
                    st.session_state["sm_fc_flipped"] = not flipped
                    st.rerun()
            with b_col3:
                if st.button("Next →", disabled=(idx == len(deck) - 1), use_container_width=True):
                    st.session_state["sm_fc_idx"] = idx + 1
                    st.session_state["sm_fc_flipped"] = False
                    st.rerun()
            with b_col4:
                if st.button("🔀 Shuffle", use_container_width=True):
                    random.shuffle(deck)
                    st.session_state[fc_key] = deck
                    st.session_state["sm_fc_idx"] = 0
                    st.session_state["sm_fc_flipped"] = False
                    st.rerun()
            with b_col5:
                if st.button("Reset 🗑️", use_container_width=True):
                    st.session_state.pop(fc_key, None)
                    st.session_state.pop("sm_fc_idx", None)
                    st.session_state.pop("sm_fc_flipped", None)
                    st.rerun()

    # =========================================================================
    # TAB 2: REVISION MODE
    # =========================================================================
    with tab_rev:
        with st.container(border=True):
            st.markdown("#### 🔄 Revision Checklists")
            st.markdown("<p style='opacity:0.65; font-size:0.85rem; margin-top:-0.5rem;'>Page-by-page systematic review tracker. Tick pages off as you finish studying them.</p>", unsafe_allow_html=True)

            start_page, end_page = page_range
            total_pages = max(1, end_page - start_page + 1)

            rev_key = f"sm_revision_progress_{selected_book}"
            if rev_key not in st.session_state:
                st.session_state[rev_key] = {}

            progress_dict = st.session_state[rev_key]
            ticked = sum(1 for p in range(start_page, end_page + 1) if progress_dict.get(p, False))
            pct = int(ticked / total_pages * 100)

            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.25rem;">
                <span style="font-weight:700; font-size:0.9rem;">Revision Completed</span>
                <span style="font-weight:800; color:#059669;">{ticked} / {total_pages} pages ({pct}%)</span>
            </div>
            <div style="height:10px; background:rgba(128,128,128,0.15); border-radius:5px; overflow:hidden; margin-bottom:1.5rem;">
                <div style="height:100%; width:{pct}%; background:#059669; border-radius:5px; transition:width 0.4s ease;"></div>
            </div>
            """, unsafe_allow_html=True)

            cols = st.columns(min(total_pages, 5))
            for i, pg in enumerate(range(start_page, end_page + 1)):
                col_idx = i % min(total_pages, 5)
                with cols[col_idx]:
                    checked = st.checkbox(
                        f"Page {pg}",
                        value=progress_dict.get(pg, False),
                        key=f"revision_check_pg_{pg}"
                    )
                    if checked != progress_dict.get(pg, False):
                        progress_dict[pg] = checked
                        st.session_state[rev_key] = progress_dict
                        st.rerun()

"""
Mr. AI Smart Classroom — Central Books Workspace & Analytics Dashboard
Books page is the single source of truth for all study materials and cross-module synchronization.
"""
import gc
import os
import streamlit as st
from app.components.cards import gradient_header, stat_card
from app.rag.loader import inspect_pdf_pages, load_documents
from app.rag.embedder import (
    build_or_load_vectorstore, compute_book_hash, get_documents_from_vectorstore
)
from app.database.db import (
    save_uploaded_book, get_uploaded_books,
    start_study_session, get_quiz_accuracy, get_total_study_minutes,
    get_learning_streak, get_quiz_history, get_connection
)
from app.analytics.charts import (
    quiz_score_trend_chart, subject_performance_radar,
    study_activity_heatmap
)


def _reset_book_state():
    """Clear all book-related session state."""
    for k in ["sm_db", "sm_book_name", "sm_book_key", "sm_chunks",
              "sm_page_range", "sm_chat_history", "sm_quiz", "sm_quiz_answers", "sm_quiz_graded", "sm_quiz_saved"]:
        if k in st.session_state:
            del st.session_state[k]
    gc.collect()


def _get_study_sessions_raw(user_id: int) -> list[dict]:
    """Fetch raw study_sessions rows for heatmap."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT start_time FROM study_sessions WHERE user_id = ?",
            (user_id,)
        ).fetchall()
        return [{"start_time": r["start_time"]} for r in rows]
    except Exception:
        return []
    finally:
        conn.close()


def _rename_book_in_db(user_id: int, old_name: str, new_name: str):
    """Rename book record in SQLite database."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE uploaded_books SET book_name = ? WHERE user_id = ? AND book_name = ?",
            (new_name, user_id, old_name)
        )
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def _delete_book_from_db(user_id: int, book_name: str):
    """Delete book record from SQLite database."""
    conn = get_connection()
    try:
        conn.execute(
            "DELETE FROM uploaded_books WHERE user_id = ? AND book_name = ?",
            (user_id, book_name)
        )
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def render():
    user      = st.session_state.get("sm_user", {})
    user_id   = user.get("id", 0)
    perf_mode = user.get("perf_mode", "Balanced")
    theme     = user.get("theme", "Light Mode")
    username  = user.get("username", "Guest")

    gradient_header(f"Welcome back, {username}! 📚", "Your central learning workspace and analytics dashboard", "🧠")

    # Initialize guest book history if not exists
    if "sm_guest_books" not in st.session_state:
        st.session_state["sm_guest_books"] = []

    # Get books list
    books_list = get_uploaded_books(user_id) if user_id else st.session_state["sm_guest_books"]

    # ── ACTIVE BOOK AUTOMATIC INITIALIZATION & BANNER ─────────────
    was_auto_activated = False
    if books_list and not st.session_state.get("selected_book"):
        latest_book = books_list[0]["book_name"]
        st.session_state["selected_book"] = latest_book
        st.session_state["sm_book_name"] = latest_book
        was_auto_activated = True

    active_book = st.session_state.get("selected_book")

    if active_book:
        st.markdown(f"""
        <div style="background: rgba(37,99,235,0.08); border: 2px solid #2563EB; border-radius: 18px;
                    padding: 0.9rem 1.4rem; margin-bottom: 1.25rem; display: flex; align-items: center; justify-content: space-between;">
            <div>
                <div style="font-size: 0.75rem; color: #2563EB; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em;">📘 Active Study Material</div>
                <div style="font-size: 1.15rem; font-weight: 800; color: #1E293B; margin-top: 0.1rem;">{active_book}</div>
            </div>
            <div>
                <span style="background: #DCFCE7; color: #15803D; padding: 0.35rem 0.9rem; border-radius: 999px; font-weight: 800; font-size: 0.82rem;">
                    🟢 Active Study Material
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if was_auto_activated:
            st.info(f"ℹ️ No active study material was selected. **{active_book}** has been activated automatically.")
    else:
        st.markdown("""
        <div style="background: rgba(245,158,11,0.08); border: 1px dashed #F59E0B; border-radius: 16px; padding: 0.8rem 1.2rem; margin-bottom: 1.25rem;">
            ℹ️ No active study material selected. Please upload a book or activate an existing document.
        </div>
        """, unsafe_allow_html=True)

    # Sort books list so Active Book is displayed FIRST
    if active_book and books_list:
        active_items = [b for b in books_list if b["book_name"] == active_book]
        other_items  = [b for b in books_list if b["book_name"] != active_book]
        books_list   = active_items + other_items

    tab_library, tab_upload, tab_dashboard = st.tabs([
        "📚 Uploaded Library & Workspace",
        "📥 Upload Study Material",
        "📊 Analytics Dashboard"
    ])

    # =========================================================================
    # TAB 1: UPLOADED BOOKS LIBRARY & RECENTLY OPENED
    # =========================================================================
    with tab_library:
        if books_list:
            # ── SECTION 3: RECENTLY OPENED BOOKS ───────────────────────
            st.markdown("#### 🕒 Recently Opened Books")
            recent_books = books_list[:5]
            rec_cols = st.columns(min(len(recent_books), 5))
            for i, r_bk in enumerate(recent_books):
                is_selected = (active_book == r_bk["book_name"])
                with rec_cols[i]:
                    st.markdown(f"""
                    <div style="padding:0.75rem; border-radius:14px; background:{'rgba(37,99,235,0.1)' if is_selected else 'rgba(128,128,128,0.05)'};
                                border:{'2px solid #2563EB' if is_selected else '1px solid rgba(128,128,128,0.15)'}; text-align:center;">
                        <div style="font-size:1.5rem; margin-bottom:0.2rem;">📘</div>
                        <div style="font-size:0.8rem; font-weight:700; text-overflow:ellipsis; overflow:hidden; white-space:nowrap;">{r_bk['book_name']}</div>
                        <div style="font-size:0.68rem; color:#64748B;">{r_bk.get('chunk_count', 0)} chunks</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("Activate", key=f"rec_act_{i}", use_container_width=True, type="primary" if is_selected else "secondary"):
                        st.session_state["selected_book"] = r_bk["book_name"]
                        st.session_state["sm_book_name"] = r_bk["book_name"]
                        st.toast(f'🎉 "{r_bk["book_name"]}" is now the active study material.')
                        st.rerun()

            st.markdown("<hr style='margin:1.5rem 0; border-color:rgba(128,128,128,0.15);'>", unsafe_allow_html=True)

            # ── SECTION 2: UPLOADED BOOKS LIBRARY ──────────────────────
            st.markdown("#### 📘 Uploaded Books Library")
            for idx, bk in enumerate(books_list):
                b_name = bk["book_name"]
                is_active = (active_book == b_name)
                p_start = bk.get("page_start", 1)
                p_end = bk.get("page_end", 1)
                pages = p_end - p_start + 1
                chunks_cnt = bk.get("chunk_count", 0)
                uploaded_date = bk.get("uploaded_at", "Recently")[:10]

                with st.container(border=True):
                    c_main, c_actions = st.columns([3, 3.2])
                    with c_main:
                        st.markdown(f"""
                        <div style="display:flex; align-items:center; gap:0.75rem;">
                            <div style="font-size:2.2rem;">{'📘' if is_active else '📄'}</div>
                            <div>
                                <div style="font-size:1.05rem; font-weight:800; color:{'#2563EB' if is_active else 'inherit'};">
                                    {b_name} {'<span style="font-size:0.72rem; background:#DCFCE7; color:#15803D; padding:0.15rem 0.55rem; border-radius:12px; font-weight:800;">🟢 Active Study Material</span>' if is_active else ''}
                                </div>
                                <div style="font-size:0.78rem; color:#64748B; margin-top:0.2rem;">
                                    📄 {pages} Pages · 🧩 {chunks_cnt} Chunks · 🟢 Status: Indexed · 📅 Uploaded {uploaded_date}
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    with c_actions:
                        a1, a2, a3, a4, a5 = st.columns([1.3, 1, 1.2, 1, 1])
                        with a1:
                            if st.button("✅ Activate" if not is_active else "Active", key=f"act_bk_{idx}", type="primary" if is_active else "secondary", use_container_width=True):
                                st.session_state["selected_book"] = b_name
                                st.session_state["sm_book_name"] = b_name
                                st.toast(f'🎉 "{b_name}" is now the active study material.')
                                st.rerun()
                        with a2:
                            if st.button("Rename", key=f"ren_bk_{idx}", use_container_width=True):
                                st.session_state[f"show_rename_{idx}"] = not st.session_state.get(f"show_rename_{idx}", False)
                        with a3:
                            if st.button("Details", key=f"det_bk_{idx}", use_container_width=True):
                                st.session_state[f"show_details_{idx}"] = not st.session_state.get(f"show_details_{idx}", False)
                        with a4:
                            if st.button("Re-index", key=f"reidx_bk_{idx}", use_container_width=True):
                                st.toast(f"⚡ Re-indexing {b_name}...")
                        with a5:
                            if st.button("Delete", key=f"del_bk_{idx}", use_container_width=True):
                                if user_id:
                                    _delete_book_from_db(user_id, b_name)
                                else:
                                    st.session_state["sm_guest_books"] = [b for b in st.session_state["sm_guest_books"] if b["book_name"] != b_name]
                                if st.session_state.get("selected_book") == b_name:
                                    st.session_state.pop("selected_book", None)
                                    st.session_state.pop("sm_book_name", None)
                                st.toast(f"Deleted {b_name}")
                                st.rerun()

                    if st.session_state.get(f"show_details_{idx}", False):
                        col_id = compute_book_hash(b_name, p_start, p_end)
                        st.info(f"📋 **Book Details**: Name: `{b_name}` | Page Range: `{p_start}-{p_end}` ({pages} pages) | Chunks: `{chunks_cnt}` | Collection ID: `{col_id}`")

                    if st.session_state.get(f"show_rename_{idx}", False):
                        r_col1, r_col2 = st.columns([3, 1])
                        with r_col1:
                            new_b_name = st.text_input("New book name", value=b_name, key=f"rename_input_{idx}")
                        with r_col2:
                            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                            if st.button("Save Name", key=f"save_rename_{idx}", use_container_width=True):
                                if new_b_name and new_b_name != b_name:
                                    if user_id:
                                        _rename_book_in_db(user_id, b_name, new_b_name)
                                    st.session_state["selected_book"] = new_b_name
                                    st.session_state["sm_book_name"] = new_b_name
                                    st.session_state.pop(f"show_rename_{idx}", None)
                                    st.toast(f"Renamed to {new_b_name}")
                                    st.rerun()
        else:
            st.markdown("""
            <div style="text-align:center; padding:3rem 2rem; background:rgba(37,99,235,0.04); border-radius:18px; border:2px dashed rgba(37,99,235,0.2);">
                <div style="font-size:3.5rem; margin-bottom:0.5rem;">📚</div>
                <div style="font-size:1.2rem; font-weight:800; color:#1E293B;">No Study Material Found</div>
                <div style="font-size:0.9rem; color:#64748B; margin-top:0.3rem;">Please upload a PDF, DOCX, TXT, or MD file to build your knowledge base.</div>
            </div>
            """, unsafe_allow_html=True)

    # =========================================================================
    # TAB 2: SECTION 1 – UPLOAD STUDY MATERIAL
    # =========================================================================
    with tab_upload:
        with st.container(border=True):
            st.markdown("#### 📥 Upload Study Material")
            st.markdown("<p style='opacity:0.65; font-size:0.88rem; margin-top:-0.5rem;'>Supports PDF, DOCX, TXT, and MD formats (Max 200MB).</p>", unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "📚 Drag & Drop or Choose File",
            type=["pdf", "docx", "txt", "md"],
            key="central_book_uploader"
        )

        if uploaded_file:
            file_name = uploaded_file.name
            file_bytes = uploaded_file.read()
            is_pdf = file_name.lower().endswith(".pdf")
            file_mb = len(file_bytes) / (1024 * 1024)

            f_c1, f_c2, f_c3 = st.columns(3)
            with f_c1:
                st.markdown(f"<div style='padding:0.6rem; background:rgba(37,99,235,0.08); border-radius:10px; text-align:center;'><div style='font-size:0.7rem; color:#64748B;'>File Name</div><b>{file_name[:25]}</b></div>", unsafe_allow_html=True)
            with f_c2:
                st.markdown(f"<div style='padding:0.6rem; background:rgba(37,99,235,0.08); border-radius:10px; text-align:center;'><div style='font-size:0.7rem; color:#64748B;'>File Size</div><b>{file_mb:.1f} MB</b></div>", unsafe_allow_html=True)
            with f_c3:
                st.markdown(f"<div style='padding:0.6rem; background:rgba(37,99,235,0.08); border-radius:10px; text-align:center;'><div style='font-size:0.7rem; color:#64748B;'>Format</div><b>{file_name.split('.')[-1].upper()}</b></div>", unsafe_allow_html=True)

            study_range = (1, 1)
            if is_pdf:
                tot_pages = inspect_pdf_pages(file_bytes)
                if tot_pages > 1:
                    study_range = st.slider("📖 Page Range Selection:", 1, tot_pages, (1, min(tot_pages, 50)))

            if st.button("🚀 Start Indexing Document", type="primary", use_container_width=True):
                _reset_book_state()
                with st.status("📄 Processing your document...", expanded=True) as status:
                    st.write("📄 Processing your document...")
                    docs = load_documents(file_bytes, file_name, study_range if is_pdf else None)
                    if not docs:
                        status.update(label="❌ Failed to extract text.", state="error")
                        st.stop()

                    st.write("📚 Preparing your study material...")
                    col_name = compute_book_hash(file_name, study_range[0], study_range[1])

                    db, chunks, was_cached = build_or_load_vectorstore(docs, col_name, perf_mode)

                    st.write("Completed ✓")

                    st.session_state["sm_db"]          = db
                    st.session_state["sm_chunks"]       = chunks
                    st.session_state["sm_book_name"]    = file_name
                    st.session_state["selected_book"]  = file_name
                    st.session_state["sm_page_range"]   = study_range

                    if user_id:
                        save_uploaded_book(user_id, file_name, study_range[0], study_range[1], len(chunks))
                        start_study_session(user_id, file_name)
                    else:
                        st.session_state["sm_guest_books"].append({
                            "book_name": file_name,
                            "page_start": study_range[0],
                            "page_end": study_range[1],
                            "chunk_count": len(chunks)
                        })

                    status.update(label="Completed ✓", state="complete")
                st.toast(f'🎉 "{file_name}" is now the active study material.')
                st.rerun()

    # =========================================================================
    # TAB 3: SECTION 4 – DASHBOARD ANALYTICS
    # =========================================================================
    with tab_dashboard:
        unique_books = len(set(b["book_name"] for b in books_list))
        accuracy = get_quiz_accuracy(user_id) if user_id else 0.0
        acc_str = f"{accuracy*100:.0f}%" if accuracy else "N/A"
        acc_color = "#059669" if accuracy >= 0.7 else ("#D97706" if accuracy >= 0.4 else "#DC2626")

        minutes = get_total_study_minutes(user_id) if user_id else 0
        hours = f"{minutes // 60}h {minutes % 60}m" if minutes >= 60 else f"{minutes}m"
        streak = get_learning_streak(user_id) if user_id else 0

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            stat_card("📚", "Books Uploaded", str(unique_books) if unique_books else "0", "active books", "#6366F1")
        with col2:
            stat_card("⏱️", "Study Sessions", hours if minutes > 0 else "0m", "total study time", "#0EA5E9")
        with col3:
            stat_card("🎯", "Quiz Accuracy", acc_str, "average test score", acc_color)
        with col4:
            stat_card("🔥", "Learning Streak", f"{streak} days" if streak > 0 else "0 days", "consecutive active days", "#F59E0B")

        st.markdown("<br>", unsafe_allow_html=True)
        quiz_hist = get_quiz_history(user_id, limit=50) if user_id else []

        c_left, c_right = st.columns([3, 2])
        with c_left:
            with st.container(border=True):
                fig_trend = quiz_score_trend_chart(quiz_hist, theme)
                st.plotly_chart(fig_trend, use_container_width=True, config={"displayModeBar": False})

        with c_right:
            with st.container(border=True):
                fig_radar = subject_performance_radar(quiz_hist, theme)
                st.plotly_chart(fig_radar, use_container_width=True, config={"displayModeBar": False})

        with st.container(border=True):
            sessions = _get_study_sessions_raw(user_id) if user_id else []
            fig_heat = study_activity_heatmap(sessions, theme)
            st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": False})

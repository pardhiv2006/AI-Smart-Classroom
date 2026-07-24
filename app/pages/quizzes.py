"""
ScholarMind AI — Quizzes & Assessment Workspace
Generates multiple-choice quizzes synchronized with the selected study material.
Persists test scores and provides interactive answer explanations.
"""
import streamlit as st
from app.components.cards import gradient_header, quiz_option_button
from app.rag.qa_chain import check_ollama_running, render_ollama_error
from app.utils.helpers import generate_quiz_mcqs, compute_grade
from app.database.db import save_quiz_result, get_quiz_history, get_uploaded_books
from app.utils.model_detector import get_active_model
from app.rag.embedder import get_or_load_book_vectorstore

DIFFICULTIES = ["Beginner", "Intermediate", "Advanced"]


def render():
    user       = st.session_state.get("sm_user", {})
    user_id    = user.get("id", 0)
    model_name = user.get("ai_model") or get_active_model()
    student_type = st.session_state.get("sm_student_type", "College Student")

    gradient_header("Knowledge Testing Center", "Take AI-generated quizzes and track your mastery", "🧪")

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
        if st.button("📚 Go to Books →", key="quiz_goto_books", type="primary"):
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
        key="quiz_book_selector"
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

    quiz    = st.session_state.get("sm_quiz", None)
    graded  = st.session_state.get("sm_quiz_graded", False)
    answers = st.session_state.get("sm_quiz_answers", {})

    # =========================================================================
    # QUIZ SETUP (no active quiz)
    # =========================================================================
    if not quiz:
        with st.container(border=True):
            st.markdown("#### ⚙️ Quiz Settings")
            st.markdown(f"<p style='opacity:0.65; font-size:0.85rem; margin-top:-0.5rem;'>🤖 Generating quiz using <b>{model_name}</b> from <b>{selected_book}</b>.</p>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            quiz_qty = st.slider("Number of Questions", min_value=3, max_value=15, value=5, step=1)
        with col2:
            quiz_diff = st.selectbox("Difficulty Level", DIFFICULTIES, index=1)

        if st.button("🚀 Generate Quiz", type="primary", use_container_width=True):
            with st.spinner("🧪 Preparing your quiz..."):
                questions = generate_quiz_mcqs(
                    chunks=chunks,
                    num_questions=quiz_qty,
                    difficulty=quiz_diff,
                    student_type=student_type,
                    model_name=model_name,
                )
            if questions:
                st.session_state["sm_quiz"]         = questions
                st.session_state["sm_quiz_answers"]  = {}
                st.session_state["sm_quiz_graded"]   = False
                st.session_state["sm_quiz_diff"]     = quiz_diff
                st.toast("✅ Response generated successfully.")
                st.rerun()

        # Quiz history
        if user_id:
            history = get_quiz_history(user_id, limit=8)
            if history:
                st.markdown("<br>", unsafe_allow_html=True)
                with st.container(border=True):
                    st.markdown("#### 📊 Quiz History")

                for q in history:
                    pct = int(q["score"] / q["total"] * 100) if q["total"] else 0
                    g, color, _ = compute_grade(q["score"], q["total"])
                    st.markdown(f"""
                    <div style="padding:0.7rem 0.9rem; background:rgba(37,99,235,0.04); border-radius:10px; margin-bottom:0.4rem;
                                border-left:4px solid {color}; display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <b>{q['book_name']}</b> · <span style="color:#64748B;">{q.get('difficulty','')}</span>
                        </div>
                        <div>
                            <span style="font-weight:800; color:{color};">{q['score']} / {q['total']} ({pct}%) — Grade {g}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        return

    # =========================================================================
    # ACTIVE QUIZ TAKING & GRADED RESULTS
    # =========================================================================
    st.markdown(f"### 📝 {selected_book} — Quiz ({len(quiz)} Questions)")

    for idx, q_item in enumerate(quiz):
        q_num = idx + 1
        st.markdown(f"#### Q{q_num}: {q_item.get('question','')}")

        options_raw = q_item.get("options", {})
        options = {}
        if isinstance(options_raw, dict):
            options = {str(k).upper(): str(v) for k, v in options_raw.items()}
        elif isinstance(options_raw, list):
            keys = ["A", "B", "C", "D"]
            for idx_opt, val in enumerate(options_raw):
                if idx_opt < 4:
                    if isinstance(val, dict):
                        v = val.get("value", val.get("text", str(val)))
                    else:
                        v = str(val)
                    options[keys[idx_opt]] = v

        correct = str(q_item.get("correct_answer", q_item.get("answer", "A"))).upper().strip()
        if correct not in ["A", "B", "C", "D"]:
            idx = q_item.get("correct_index", 0)
            if isinstance(idx, int) and 0 <= idx <= 3:
                correct = ["A", "B", "C", "D"][idx]
            else:
                correct = "A"
        user_ans = answers.get(idx, None)

        # ── SIMPLE BUBBLE OPTION SELECTION (ST.RADIO) ──
        radio_options = []
        option_keys_map = {}
        for opt_key in ["A", "B", "C", "D"]:
            opt_text = options.get(opt_key, "")
            if opt_text:
                formatted_opt = f"{opt_key}. {opt_text}"
                radio_options.append(formatted_opt)
                option_keys_map[formatted_opt] = opt_key

        if radio_options:
            if not graded:
                current_idx = None
                if user_ans:
                    for r_idx, f_opt in enumerate(radio_options):
                        if option_keys_map[f_opt] == user_ans:
                            current_idx = r_idx
                            break

                selected_opt = st.radio(
                    label=f"q_radio_label_{idx}",
                    options=radio_options,
                    index=current_idx if current_idx is not None else None,
                    key=f"q_radio_{idx}",
                    label_visibility="collapsed"
                )
                if selected_opt and selected_opt in option_keys_map:
                    chosen_key = option_keys_map[selected_opt]
                    if answers.get(idx) != chosen_key:
                        answers[idx] = chosen_key
                        st.session_state["sm_quiz_answers"] = answers
                        st.rerun()
            else:
                for opt_key in ["A", "B", "C", "D"]:
                    opt_text = options.get(opt_key, "")
                    if not opt_text:
                        continue
                    is_user = (user_ans == opt_key)
                    is_corr = (opt_key == correct)
                    if is_corr:
                        st.success(f"✓  {opt_key}. {opt_text}")
                    elif is_user and not is_corr:
                        st.error(f"✗  {opt_key}. {opt_text}")
                    else:
                        st.markdown(f"<div style='padding:0.35rem 0.6rem; opacity:0.65;'>{opt_key}. {opt_text}</div>", unsafe_allow_html=True)

        if graded:
            explanation = q_item.get("explanation", "")
            if explanation:
                st.info(f"💡 **Explanation:** {explanation}")
        st.markdown("<hr style='border-color:rgba(128,128,128,0.12); margin:1rem 0;'>", unsafe_allow_html=True)

    # Quiz Submission & Reset Actions
    c_sub, c_res = st.columns([2, 1])
    with c_sub:
        if not graded:
            if st.button("📥 Submit Quiz", type="primary", use_container_width=True):
                st.session_state["sm_quiz_graded"] = True

                # Calculate score
                score = sum(1 for i, item in enumerate(quiz) if answers.get(i, "").upper() == item.get("correct_answer", "").upper())
                total = len(quiz)

                if user_id:
                    save_quiz_result(user_id, selected_book, score, total, st.session_state.get("sm_quiz_diff", "Intermediate"))
                st.rerun()

    with c_res:
        if st.button("🔄 New Quiz", use_container_width=True):
            st.session_state.pop("sm_quiz", None)
            st.session_state.pop("sm_quiz_answers", None)
            st.session_state.pop("sm_quiz_graded", None)
            st.rerun()

"""
ScholarMind AI — Utility Helpers
Quiz generation, flashcards, notes extraction, important questions.
All use ChatOllama (no paid API).
"""
import re
import json
import hashlib
import streamlit as st
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate


# ─────────────────────────────────────────────────────────────────
# JSON EXTRACTION HELPER
# ─────────────────────────────────────────────────────────────────

def _extract_json(text: str) -> str:
    """
    Robustly extract a JSON object or array from LLM output.
    Handles markdown code fences and extra prose.
    """
    # Strip markdown fences
    text = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
    # Find first { or [
    start_brace = text.find("{")
    start_bracket = text.find("[")
    if start_brace == -1 and start_bracket == -1:
        return text
    if start_brace == -1:
        start = start_bracket
    elif start_bracket == -1:
        start = start_brace
    else:
        start = min(start_brace, start_bracket)
    # Find last matching closer
    last_brace = text.rfind("}")
    last_bracket = text.rfind("]")
    end = max(last_brace, last_bracket)
    if end == -1:
        return text[start:]
    return text[start : end + 1]


def _sample_chunks(chunks: list[Document], n: int) -> list[Document]:
    """Evenly sample n chunks from the list for diverse coverage."""
    total = len(chunks)
    if total <= n:
        return chunks
    indices = [int(i * (total - 1) / (n - 1)) for i in range(n)] if n > 1 else [0]
    return [chunks[i] for i in sorted(set(indices))]


def _build_context(chunks: list[Document], max_chunks: int = 8) -> str:
    sampled = _sample_chunks(chunks, max_chunks)
    return "\n\n".join(
        f"--- Excerpt {i+1} (Page {c.metadata.get('page', '?')}) ---\n{c.page_content}"
        for i, c in enumerate(sampled)
    )


# ─────────────────────────────────────────────────────────────────
# QUIZ MCQ GENERATION
# ─────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False, max_entries=10)
def generate_quiz_mcqs_cached(
    chunk_contents_key: str,  # cache key = hash of content
    context_text: str,
    num_questions: int,
    difficulty: str,
    student_type: str,
    model_name: str,
) -> list[dict] | None:
    """Cached quiz generation — avoids regenerating for same context+settings."""
    return _generate_quiz_mcqs_inner(context_text, num_questions, difficulty, student_type, model_name)


def generate_quiz_mcqs(
    chunks: list[Document],
    num_questions: int = 5,
    difficulty: str = "Intermediate",
    student_type: str = "College Student",
    model_name: str = "llama3",
) -> list[dict] | None:
    """
    Generate MCQ quiz questions from document chunks.
    Uses Ollama (no paid API). Returns list of question dicts or None.
    """
    if not chunks:
        st.warning("📚 No content loaded. Please upload a book first.")
        return None

    context_text = _build_context(chunks, max_chunks=max(num_questions, 6))
    # Cache key based on context hash
    cache_key = hashlib.md5(
        f"{context_text[:500]}{num_questions}{difficulty}{student_type}{model_name}".encode()
    ).hexdigest()

    return generate_quiz_mcqs_cached(
        cache_key, context_text, num_questions, difficulty, student_type, model_name
    )


def _generate_quiz_mcqs_inner(
    context_text: str,
    num_questions: int,
    difficulty: str,
    student_type: str,
    model_name: str,
) -> list[dict] | None:
    from app.rag.qa_chain import get_llm

    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are an expert educator creating a multiple-choice quiz.
Generate EXACTLY {num_questions} MCQ questions based ONLY on the provided textbook excerpts.

RULES:
1. Questions must be answerable from the excerpts only. No outside knowledge.
2. Difficulty: {difficulty} (Beginner=recall, Intermediate=explain, Advanced=synthesis)
3. Student level: {student_type}
4. Each question must have exactly 4 options: A, B, C, D
5. correct_answer: "A", "B", "C", or "D"
6. explanation: brief text-based explanation

RETURN ONLY valid JSON — no prose, no markdown:
{{{{ "questions": [ {{{{ "question": "...", "options": {{{{ "A": "...", "B": "...", "C": "...", "D": "..." }}}}, "correct_answer": "A", "explanation": "..." }}}} ] }}}}"""),
        ("human", "Textbook excerpts:\n{context}\n\nGenerate the JSON quiz now:"),
    ])

    llm = get_llm(model_name, temperature=0.2)
    try:
        res = llm.invoke(prompt.format_messages(context=context_text))
        raw = res.content.strip()
        json_str = _extract_json(raw)
        parsed = json.loads(json_str)

        raw_questions = []
        if isinstance(parsed, dict) and "questions" in parsed and isinstance(parsed["questions"], list):
            raw_questions = parsed["questions"][:num_questions]
        elif isinstance(parsed, list):
            raw_questions = parsed[:num_questions]
        else:
            st.error("❌ Unexpected quiz format from AI. Please try again.")
            return None

        # Validation & Normalization Layer
        normalized = []
        for q in raw_questions:
            if not isinstance(q, dict):
                continue
            question_text = str(q.get("question", "Quiz Question")).strip()
            options_raw = q.get("options", {})
            options_dict = {}
            if isinstance(options_raw, dict):
                options_dict = {str(k).upper(): str(v) for k, v in options_raw.items()}
            elif isinstance(options_raw, list):
                keys = ["A", "B", "C", "D"]
                for idx_opt, val in enumerate(options_raw):
                    if idx_opt < 4:
                        if isinstance(val, dict):
                            v = val.get("value", val.get("text", str(val)))
                        else:
                            v = str(val)
                        options_dict[keys[idx_opt]] = v

            ans = q.get("correct_answer", q.get("answer", None))
            if ans is None or str(ans).upper().strip() not in ["A", "B", "C", "D"]:
                idx = q.get("correct_index", q.get("correct", 0))
                if isinstance(idx, int) and 0 <= idx <= 3:
                    ans = ["A", "B", "C", "D"][idx]
                else:
                    ans = "A"
            else:
                ans = str(ans).upper().strip()

            explanation = str(q.get("explanation", "Refer to textbook excerpts.")).strip()

            normalized.append({
                "question": question_text,
                "options": options_dict,
                "correct_answer": ans,
                "explanation": explanation,
            })

        return normalized if normalized else None
    except json.JSONDecodeError as e:
        st.error(f"❌ Quiz JSON parse error: {e}\n\nTry reducing question count or changing difficulty.")
        return None
    except Exception as e:
        err = str(e)
        if "connection" in err.lower() or "refused" in err.lower():
            st.error("❌ Ollama not running. Please start it with `ollama serve`.")
        else:
            st.error(f"❌ Quiz generation failed: {err}")
        return None


# ─────────────────────────────────────────────────────────────────
# FLASHCARD GENERATION
# ─────────────────────────────────────────────────────────────────

def generate_flashcards(
    chunks: list[Document],
    num_cards: int = 10,
    model_name: str = "llama3",
) -> list[dict] | None:
    """
    Generate flashcards (front: term/concept, back: definition/explanation).
    Returns list of {"front": str, "back": str} or None.
    """
    if not chunks:
        return None
    from app.rag.qa_chain import get_llm

    context_text = _build_context(chunks, max_chunks=10)
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are creating study flashcards from textbook content.
Generate exactly {num_cards} flashcards. Each flashcard has:
- front: a key term, concept, or question from the text
- back: the definition, explanation, or answer from the text

RETURN ONLY valid JSON — no prose:
{{{{ "flashcards": [ {{{{ "front": "...", "back": "..." }}}} ] }}}}"""),
        ("human", "Textbook content:\n{context}\n\nGenerate flashcards JSON now:"),
    ])

    llm = get_llm(model_name, temperature=0.2)
    try:
        res = llm.invoke(prompt.format_messages(context=context_text))
        json_str = _extract_json(res.content.strip())
        parsed = json.loads(json_str)
        if isinstance(parsed, dict) and "flashcards" in parsed:
            return parsed["flashcards"][:num_cards]
        return None
    except Exception as e:
        st.error(f"❌ Flashcard generation failed: {e}")
        return None


# ─────────────────────────────────────────────────────────────────
# STUDY NOTES GENERATION
# ─────────────────────────────────────────────────────────────────

def generate_study_notes(
    chunks: list[Document],
    model_name: str = "llama3",
) -> str | None:
    """
    Generate concise study notes from document chunks.
    Returns markdown-formatted notes string.
    """
    if not chunks:
        return None
    from app.rag.qa_chain import get_llm

    context_text = _build_context(chunks, max_chunks=12)
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a study notes expert. 
Create concise, well-structured study notes from the provided textbook content.
Format as markdown with:
- ## Main Topics as headers
- Key definitions in **bold**
- Bullet points for lists
- Important formulas or rules in code blocks
- Keep it under 600 words. Focus on exam-worthy content."""),
        ("human", "Textbook content:\n{context}\n\nGenerate study notes:"),
    ])

    llm = get_llm(model_name, temperature=0.3)
    try:
        res = llm.invoke(prompt.format_messages(context=context_text))
        return res.content
    except Exception as e:
        st.error(f"❌ Notes generation failed: {e}")
        return None


# ─────────────────────────────────────────────────────────────────
# IMPORTANT QUESTIONS EXTRACTION
# ─────────────────────────────────────────────────────────────────

def extract_important_questions(
    chunks: list[Document],
    num_questions: int = 10,
    model_name: str = "llama3",
) -> list[str]:
    """
    Extract likely exam questions from the material.
    Returns list of question strings. Never returns None or shows errors.
    """
    if not chunks:
        return [
            "What are the main concepts discussed in this chapter?",
            "How do key principles apply to practical scenarios?",
            "What are the core definitions and terms introduced?"
        ]
    from app.rag.qa_chain import get_llm

    context_text = _build_context(chunks, max_chunks=10)
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are an experienced exam setter.
Extract exactly {num_questions} important questions that could appear in an exam based on this content.
Focus on conceptual understanding, definitions, and applications.
RETURN ONLY valid JSON:
{{"questions": ["Q1...", "Q2...", ...]}}"""),
        ("human", "Textbook content:\n{context}\n\nGenerate important questions JSON:"),
    ])

    llm = get_llm(model_name, temperature=0.2)
    raw_content = ""
    try:
        res = llm.invoke(prompt.format_messages(context=context_text))
        raw_content = res.content.strip()
        json_str = _extract_json(raw_content)
        parsed = json.loads(json_str)
        if isinstance(parsed, dict):
            for k in ["questions", "important_questions", "exam_questions", "mcqs", "questions_list"]:
                if k in parsed and isinstance(parsed[k], list) and parsed[k]:
                    return [str(q) for q in parsed[k][:num_questions]]
            for val in parsed.values():
                if isinstance(val, list) and val and isinstance(val[0], str):
                    return [str(q) for q in val[:num_questions]]
        elif isinstance(parsed, list) and parsed:
            return [str(q) for q in parsed[:num_questions]]
    except Exception:
        pass

    # Regex & text parsing fallback for plain text or markdown lists
    lines = [line.strip() for line in raw_content.split("\n") if line.strip()]
    extracted = []
    for line in lines:
        cleaned = re.sub(r'^(?:\d+[\.\)]|\-|\*|Q\d+:?|Question\s*\d+:?)\s*', '', line).strip()
        if cleaned and (cleaned.endswith("?") or len(cleaned) > 15):
            extracted.append(cleaned)

    if extracted:
        return extracted[:num_questions]

    # Guaranteed non-empty fallback list
    return [
        "What are the primary objectives and key concepts of this material?",
        "How do the fundamental theories apply to problem solving?",
        "What are the critical definitions and formulas introduced?",
        "What are the major advantages and limitations discussed?",
        "How do different components interact within this topic?"
    ][:num_questions]


# ─────────────────────────────────────────────────────────────────
# GRADE LOGIC
# ─────────────────────────────────────────────────────────────────

def compute_grade(correct: int, total: int) -> tuple[str, str, str]:
    """
    Return (grade_letter, color_hex, remark_text) from a quiz score.
    """
    if total == 0:
        return "N/A", "#6B7280", "No questions answered."
    pct = int((correct / total) * 100)
    if pct == 100:
        return "A+", "#059669", f"🌟 Perfect score! Outstanding performance ({pct}%)"
    elif pct >= 80:
        return "A",  "#2563EB", f"🎓 Excellent work! Great understanding ({pct}%)"
    elif pct >= 60:
        return "B",  "#7C3AED", f"📘 Good effort! Review the missed topics ({pct}%)"
    elif pct >= 40:
        return "C",  "#D97706", f"📝 Needs improvement. Revisit the material ({pct}%)"
    else:
        return "F",  "#DC2626", f"❌ Keep studying — you've got this! ({pct}%)"


# ─────────────────────────────────────────────────────────────────
# PDF EXPORT (simple)
# ─────────────────────────────────────────────────────────────────

def export_notes_to_pdf(notes_text: str, title: str = "Study Notes") -> bytes | None:
    """Generate a simple PDF from notes text using reportlab."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib import colors
        import io

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                leftMargin=2*cm, rightMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            "Title", parent=styles["Title"],
            fontSize=18, textColor=colors.HexColor("#4F46E5"), spaceAfter=12
        )
        story.append(Paragraph(f"📚 {title}", title_style))
        story.append(Spacer(1, 0.4*cm))

        # Notes content
        body_style = ParagraphStyle(
            "Body", parent=styles["Normal"],
            fontSize=10, leading=16, spaceAfter=6
        )
        for line in notes_text.split("\n"):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 0.2*cm))
                continue
            if line.startswith("## "):
                h_style = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, textColor=colors.HexColor("#4F46E5"))
                story.append(Paragraph(line[3:], h_style))
            elif line.startswith("# "):
                h_style = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=15, textColor=colors.HexColor("#7C3AED"))
                story.append(Paragraph(line[2:], h_style))
            else:
                # Escape special PDF chars
                safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                story.append(Paragraph(safe, body_style))

        doc.build(story)
        return buf.getvalue()
    except Exception as e:
        st.error(f"PDF export failed: {e}")
        return None

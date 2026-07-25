"""
Mr. AI Smart Classroom — RAG Q&A Chain
Uses ChatOllama (local, no API key needed).
Supports 5 AI personas with distinct system prompts.
Source-restricted answers only.
"""
import streamlit as st
import requests
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma


# ─────────────────────────────────────────────────────────────────
# MODEL CONFIGURATION
# ─────────────────────────────────────────────────────────────────

PERF_MODEL_MAP = {
    "Battery Saver": "llama3",
    "Balanced":      "llama3",
    "High Quality":  "llama3",
}

# Preferred fallback order — auto-detected from Ollama at runtime
_PREFERRED_MODEL_ORDER = ["llama3", "llama3:8b", "llama3:latest", "gemma3:4b", "qwen2.5:3b"]


from app.utils.model_detector import (
    detect_available_models, get_best_model, get_active_model,
    is_model_available, PREFERRED_MODEL_PRIORITY
)


# ─────────────────────────────────────────────────────────────────
# OLLAMA HEALTH CHECK
# ─────────────────────────────────────────────────────────────────

def check_ollama_running(model: str | None = None) -> tuple[bool, str]:
    """
    Check if Ollama server is reachable and optionally if models are available.
    Returns (is_ok, message). Never raises exceptions.
    """
    installed = detect_available_models()
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=2)
        if resp.status_code != 200:
            return False, (
                "⚠️ **Ollama server is not running.**\n\n"
                "Start it with:\n```bash\nollama serve\n```"
            )
    except Exception:
        return False, (
            "⚠️ **Ollama server is not running.**\n\n"
            "Start it with:\n```bash\nollama serve\n```"
        )

    if not installed:
        return False, (
            "⚠️ **No Ollama models detected.**\n\n"
            "Install a model using:\n```bash\nollama pull llama3\n```\n"
            "or\n```bash\nollama pull gemma3:4b\n```"
        )

    return True, "Ollama is running ✅"


def render_ollama_error(message: str):
    """Render a styled Ollama failsafe error block."""
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #FEF3C7, #FDE68A);
        border: 2px solid #F59E0B;
        border-radius: 16px;
        padding: 1.5rem 2rem;
        margin: 1rem 0;
    ">
        <h3 style="color: #92400E; margin: 0 0 0.75rem; font-size: 1.1rem;">
            ⚠️ Local AI Model Failsafe Notice
        </h3>
        <div style="color: #78350F; font-size: 0.9rem; line-height: 1.7;">
            {message.replace(chr(10), '<br>')}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# LLM FACTORY (cached per model name)
# ─────────────────────────────────────────────────────────────────

def resolve_model_name(model_name: str | None = None) -> str:
    """
    Dynamically resolve best model name using model_detector utility.
    """
    if model_name and is_model_available(model_name):
        return model_name
    return get_active_model()


@st.cache_resource(show_spinner=False)
def get_llm(model_name: str | None = None, temperature: float = 0.3):
    """
    Return a cached ChatOllama instance using automatically resolved model.
    """
    resolved_name = resolve_model_name(model_name)
    from langchain_ollama import ChatOllama
    return ChatOllama(model=resolved_name, temperature=temperature)


# ─────────────────────────────────────────────────────────────────
# AI PERSONA SYSTEM PROMPTS
# ─────────────────────────────────────────────────────────────────

PERSONA_SYSTEM_PROMPTS = {
    "Friendly Tutor": """You are a warm, encouraging AI tutor named Scholar. 
Answer the student's question based ONLY on the provided textbook context.
Use simple, clear language. Add relevant examples from the text. 
Celebrate when the student asks good questions.
If the answer is NOT in the context, say exactly: "I couldn't find that in your uploaded material — please check your textbook directly."
Keep answers concise but complete.""",

    "Strict Professor": """You are a rigorous academic professor. 
Answer questions based STRICTLY on the provided textbook context — no external knowledge.
Use precise academic language. Cite page numbers when available.
Be direct, thorough, and expect intellectual rigor.
If the answer is NOT in the context, state: "The textbook does not address this question in the selected pages."
Structure long answers with clear sections.""",

    "Exam Coach": """You are an exam preparation coach focused on exam success.
Answer based ONLY on the provided textbook context.
Highlight key exam-worthy points, definitions, and formulas.
Use bullet points for clarity. Mention what's likely to appear in exams.
If the answer is NOT in the context, say: "This topic isn't covered in your selected pages — focus on what's available."
Frame answers as exam preparation notes.""",

    "Competitive Exam Mentor": """You are a competitive examination mentor (JEE/NEET/UPSC/GRE level).
Answer based ONLY on the provided textbook context.
Provide deep conceptual understanding. Connect related concepts.
Add memory tricks and shortcuts where relevant from the text.
If the answer is NOT in the context, say: "Not in scope for the selected material."
Think like a mentor preparing students for the highest level of competition.""",

    "Research Assistant": """You are a scholarly research assistant.
Answer based ONLY on the provided textbook context.
Provide analytical, evidence-based responses. Quote directly from the text.
Note page numbers, identify limitations, and suggest related concepts from the material.
If the answer is NOT in the context, say: "The selected material does not contain sufficient information on this topic."
Maintain academic objectivity and intellectual precision.""",
}

PERSONA_ICONS = {
    "Friendly Tutor": "😊",
    "Strict Professor": "👨‍🎓",
    "Exam Coach": "🎯",
    "Competitive Exam Mentor": "🏆",
    "Research Assistant": "🔬",
}


def get_groq_api_key() -> str:
    """Retrieve Groq API key from session_state, Streamlit Secrets, or environment."""
    key = st.session_state.get("groq_api_key", "")
    if not key:
        try:
            key = st.secrets.get("GROQ_API_KEY", "")
        except Exception:
            key = ""
    if not key:
        import os
        key = os.environ.get("GROQ_API_KEY", "")
    return key.strip()


def call_groq_api(prompt_messages, api_key: str, model: str = "llama-3.3-70b-versatile") -> str:
    """
    Call Groq API using HTTP requests (fast cloud inference, zero extra dependencies).
    """
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json"
    }

    formatted_messages = []
    if isinstance(prompt_messages, list):
        for msg in prompt_messages:
            if hasattr(msg, "type") and hasattr(msg, "content"):
                role = "system" if msg.type == "system" else "user"
                formatted_messages.append({"role": role, "content": msg.content})
            elif isinstance(msg, tuple):
                role = "system" if msg[0] == "system" else "user"
                formatted_messages.append({"role": role, "content": msg[1]})
            elif isinstance(msg, dict):
                formatted_messages.append(msg)

    payload = {
        "model": model,
        "messages": formatted_messages,
        "temperature": 0.3
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=25)
    if resp.status_code == 200:
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    else:
        raise Exception(f"Groq API Error ({resp.status_code}): {resp.text}")


# ─────────────────────────────────────────────────────────────────
# CORE Q&A FUNCTION
# ─────────────────────────────────────────────────────────────────

def answer_question(
    question: str,
    db: Chroma,
    model_name: str,
    persona: str,
    student_type: str = "College Student",
    book_name: str = "",
) -> tuple[str, list[dict]]:
    """
    Run RAG Q&A with 7-step debug workflow and Groq Cloud / Ollama fallback.
    """
    col_name = getattr(db, "_collection_name", "chroma_collection")
    print(f"\n--- [RAG DEBUG - Step 2] ---")
    print(f"Selected Book : {book_name}")
    print(f"Collection    : {col_name}")
    print(f"Top-K         : 4")

    # Step 3: Retrieve top-k chunks with fallback
    retriever = db.as_retriever(search_kwargs={"k": 4})
    try:
        retrieved_docs = retriever.invoke(question)
    except Exception as e:
        print(f"[RAG DEBUG] Retriever invoke warning: {e}")
        retrieved_docs = []

    # Fallback to direct similarity search if retriever returned 0
    if not retrieved_docs:
        print("[RAG DEBUG - Step 7] Primary retriever returned 0 docs. Attempting direct similarity search fallback...")
        try:
            retrieved_docs = db.similarity_search(question, k=4)
        except Exception as ex:
            print(f"[RAG DEBUG - Step 7] Direct similarity search failed: {ex}")

    # Step 3 & 4: Print retrieved chunks and metadata
    print(f"\n--- [RAG DEBUG - Step 3 & 4] Retrieved Chunks ({len(retrieved_docs)}) ---")
    sources = []
    context_parts = []

    if not retrieved_docs:
        print("❌ [RAG DEBUG] Zero chunks retrieved. Diagnosing root cause:")
        print("   - Check if Chroma collection exists and has documents loaded via db.get()")
        print("   - Check if embeddings match query vector dimension")
        return f"I couldn't find information related to this question in **{book_name or 'the selected book'}**.", []

    for idx, doc in enumerate(retrieved_docs):
        meta = doc.metadata or {}
        p_num = meta.get("page", 1)
        c_id = meta.get("chunk_id", idx)
        b_name = meta.get("book_name") or meta.get("source") or book_name

        print(f"Chunk {idx+1}: {{'book_name': '{b_name}', 'page': {p_num}, 'chunk_id': {c_id}}}")
        print(f"Snippet : {doc.page_content[:140]}...\n")

        context_parts.append(f"--- Page {p_num} (Chunk {c_id}) ---\n{doc.page_content}")
        sources.append({"page": p_num, "snippet": doc.page_content[:200] + "…", "chunk_id": c_id})

    context_str = "\n\n".join(context_parts)

    # Step 5: Print exact prompt context
    print(f"\n--- [RAG DEBUG - Step 5] Prompt Context String ({len(context_str)} bytes) ---")
    print(context_str[:300] + "...\n")

    # Build prompt
    system_prompt = PERSONA_SYSTEM_PROMPTS.get(persona, PERSONA_SYSTEM_PROMPTS["Friendly Tutor"])
    system_prompt += f"\n\nStudent academic level: {student_type}. Adjust vocabulary and depth accordingly."

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Textbook Context:\n{context}\n\nStudent Question:\n{question}"),
    ])
    formatted_msgs = prompt.format_messages(context=context_str, question=question)

    groq_key = get_groq_api_key()

    # Try Groq API first if key is present
    if groq_key:
        try:
            print("[RAG DEBUG] Using Groq Cloud API for ultra-fast response...")
            ans = call_groq_api(formatted_msgs, groq_key)
            return ans, sources
        except Exception as groq_err:
            print(f"[RAG DEBUG] Groq API warning: {groq_err}. Falling back to Ollama...")

    # Fallback / Default: Local Ollama
    try:
        llm = get_llm(model_name)
        response = llm.invoke(formatted_msgs)
        return response.content, sources
    except Exception as e:
        error_msg = str(e)
        if groq_key:
            return f"❌ Error executing AI query: {error_msg}", sources
        if "connection" in error_msg.lower() or "refused" in error_msg.lower():
            return (
                "⚠️ **Ollama server is not running locally.**\n\n"
                "To fix this:\n"
                "1. Run `ollama serve` locally\n"
                "2. OR paste your **Groq API Key** in **Settings ⚙️** for instant 24/7 cloud AI!"
            ), sources
        return f"❌ AI error: {error_msg}", sources

"""
Mr. AI Smart Classroom — Embedder & Vector Store
Uses HuggingFace all-MiniLM-L6-v2 (local, ~90MB, M2-optimized).
ChromaDB persists to disk keyed by book_hash to avoid re-embedding on restart.
"""
import hashlib
import streamlit as st
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

# Persistent ChromaDB directory (project root)
CHROMA_DIR = str(Path(__file__).parent.parent.parent / "chroma_db")


# ─────────────────────────────────────────────────────────────────
# EMBEDDING MODEL  (cached — loaded ONCE per Streamlit session)
# ─────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner="📚 Preparing your study material...")
def get_embedding_model():
    """
    Load HuggingFace sentence-transformers/all-MiniLM-L6-v2.
    ~90MB, cached by @st.cache_resource — loaded only once per app lifetime.
    """
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError:
        from langchain_community.embeddings import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},           # stable on M2 via CPU/MPS
        encode_kwargs={"normalize_embeddings": True},
    )


# ─────────────────────────────────────────────────────────────────
# CHUNK SPLITTER  (performance-mode aware)
# ─────────────────────────────────────────────────────────────────

PERF_CHUNK_CONFIG = {
    "Battery Saver": {"chunk_size": 400, "chunk_overlap": 40},
    "Balanced":      {"chunk_size": 500, "chunk_overlap": 50},
    "High Quality":  {"chunk_size": 700, "chunk_overlap": 70},
}


def get_splitter(perf_mode: str = "Balanced") -> RecursiveCharacterTextSplitter:
    cfg = PERF_CHUNK_CONFIG.get(perf_mode, PERF_CHUNK_CONFIG["Balanced"])
    return RecursiveCharacterTextSplitter(
        chunk_size=cfg["chunk_size"],
        chunk_overlap=cfg["chunk_overlap"],
        separators=["\n\n", "\n", ". ", " ", ""],
    )


# ─────────────────────────────────────────────────────────────────
# BOOK HASH  (persistent key for ChromaDB collection)
# ─────────────────────────────────────────────────────────────────

def compute_book_hash(file_name: str, page_start: int, page_end: int) -> str:
    """SHA-1 hash used as a stable ChromaDB collection name."""
    raw = f"{file_name}::{page_start}::{page_end}"
    # ChromaDB collection names: lowercase alphanumeric + hyphens, 3–63 chars
    h = hashlib.sha1(raw.encode()).hexdigest()[:16]
    safe_name = "".join(c if c.isalnum() else "-" for c in file_name.lower())[:20]
    return f"sm-{safe_name}-{h}"


# ─────────────────────────────────────────────────────────────────
# VECTOR STORE  (build or reuse from disk)
# ─────────────────────────────────────────────────────────────────

def build_or_load_vectorstore(
    docs: list[Document],
    collection_name: str,
    perf_mode: str = "Balanced",
) -> tuple[Chroma, list[Document], bool]:
    """
    Build a ChromaDB vector store from documents, OR load existing one from disk.
    Returns (vectorstore, chunks, was_cached).
    """
    embeddings = get_embedding_model()

    # Check if collection already exists on disk
    import chromadb
    try:
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        existing = [c.name for c in client.list_collections()]
    except Exception:
        existing = []

    if collection_name in existing:
        # Reuse existing collection — no re-embedding needed
        db = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=CHROMA_DIR,
        )
        chunks = get_documents_from_vectorstore(db)
        print(f"[RAG DEBUG - Step 1] Collection '{collection_name}' loaded from disk. Chunks: {len(chunks)}")
        return db, chunks, True

    # Build new collection
    splitter = get_splitter(perf_mode)
    chunks = splitter.split_documents(docs)
    for idx, c in enumerate(chunks):
        c.metadata["chunk_id"] = idx
        if "book_name" not in c.metadata:
            c.metadata["book_name"] = c.metadata.get("source", "uploaded_book")

    db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory=CHROMA_DIR,
    )
    print(f"[RAG DEBUG - Step 1] Created collection '{collection_name}' with {len(chunks)} chunks.")
    return db, chunks, False


def get_or_load_book_vectorstore(book_name: str, user_id: int = 0) -> tuple[Chroma | None, list[Document]]:
    """
    Get existing vectorstore from session, OR automatically reconnect to ChromaDB from disk/database records.
    Returns (db, chunks).
    """
    active_db = st.session_state.get("sm_db")
    active_name = st.session_state.get("sm_book_name")
    active_chunks = st.session_state.get("sm_chunks", [])

    if active_db and active_name == book_name and active_chunks:
        return active_db, active_chunks

    from app.database.db import get_uploaded_books
    books_list = get_uploaded_books(user_id) if user_id else st.session_state.get("sm_guest_books", [])
    matched_book = next((b for b in books_list if b.get("book_name") == book_name), None)

    page_start = matched_book.get("page_start", 1) if matched_book else 1
    page_end = matched_book.get("page_end", 200) if matched_book else 200

    col_name = compute_book_hash(book_name, page_start, page_end)
    db, chunks, was_cached = build_or_load_vectorstore([], col_name, "Balanced")

    if was_cached and not chunks:
        chunks = get_documents_from_vectorstore(db)

    if db:
        st.session_state["sm_db"] = db
        st.session_state["sm_chunks"] = chunks
        st.session_state["sm_book_name"] = book_name
        st.session_state["sm_page_range"] = (page_start, page_end)
        return db, chunks

    return active_db, active_chunks


def check_collection_health(db: Chroma | None, collection_name: str = "") -> tuple[bool, dict]:
    """
    Verify health of ChromaDB collection:
      - Collection exists
      - Embeddings/chunks > 0
      - Metadata complete
      - Index readable
    Returns (is_healthy, details_dict).
    """
    details = {
        "exists": False,
        "chunk_count": 0,
        "metadata_valid": False,
        "readable": False,
        "collection_name": collection_name or getattr(db, "_collection_name", "unknown"),
    }
    if not db:
        return False, details

    try:
        data = db.get()
        details["exists"] = True
        details["readable"] = True
        docs = data.get("documents", [])
        metas = data.get("metadatas", [])
        details["chunk_count"] = len(docs)

        if docs and metas:
            has_meta = all(isinstance(m, dict) and ("page" in m or "book_name" in m or "source" in m) for m in metas)
            details["metadata_valid"] = has_meta
            is_healthy = len(docs) > 0 and has_meta
            return is_healthy, details
        elif docs:
            details["metadata_valid"] = True
            return True, details
    except Exception as e:
        details["error"] = str(e)

    return False, details


def get_retriever(db: Chroma, k: int = 4):
    """Return a similarity retriever with k results."""
    return db.as_retriever(search_kwargs={"k": k})


def get_documents_from_vectorstore(db: Chroma) -> list[Document]:
    """Retrieve all chunks from active Chroma DB instance as a list of LangChain Document objects."""
    try:
        data = db.get()
        docs = []
        if data and "documents" in data and "metadatas" in data:
            for idx, (text, meta) in enumerate(zip(data["documents"], data["metadatas"])):
                m = meta or {}
                if "chunk_id" not in m:
                    m["chunk_id"] = idx
                docs.append(Document(page_content=text, metadata=m))
            # Sort by page metadata if available to preserve reading order
            docs.sort(key=lambda d: (d.metadata.get("page", 0), d.metadata.get("chunk_id", 0)))
            return docs
    except Exception as e:
        st.error(f"Error loading chunks from Chroma DB: {e}")
    return []



# ─────────────────────────────────────────────────────────────────
# CHUNK CACHE  (avoid re-splitting if same key)
# ─────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False, max_entries=5)
def split_documents_cached(
    doc_contents: list[str],
    doc_metas: list[dict],
    perf_mode: str,
) -> list[dict]:
    """
    Cache-friendly document splitter.
    Receives plain dicts (hashable) and returns plain dicts.
    """
    docs = [
        Document(page_content=c, metadata=m)
        for c, m in zip(doc_contents, doc_metas)
    ]
    splitter = get_splitter(perf_mode)
    chunks = splitter.split_documents(docs)
    return [{"content": c.page_content, "metadata": c.metadata} for c in chunks]

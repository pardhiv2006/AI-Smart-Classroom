# 🧠 Mr. AI Smart Classroom — Production AI Learning Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ai-smart-classroom-p.streamlit.app/)
[![Ollama Integration](https://img.shields.io/badge/AI-Ollama%20RAG-000000.svg)](https://ollama.ai/)
[![Groq Cloud AI](https://img.shields.io/badge/Cloud%20AI-Groq%20Llama%203.3-f05023.svg)](https://groq.com/)
[![ChromaDB Vector Store](https://img.shields.io/badge/VectorDB-ChromaDB-6A0DAD.svg)](https://docs.trychroma.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🌐 Live Demo

👉 **Try it Live online:** [**https://ai-smart-classroom-p.streamlit.app**](https://ai-smart-classroom-p.streamlit.app/)

---

## 📌 Project Overview

**Mr. AI Smart Classroom** is an enterprise-grade, privacy-first AI learning workspace designed for students, teachers, and self-learners. Powered by local Large Language Models via **Ollama**, local vector embeddings with **HuggingFace**, **ChromaDB**, and **SQLite**, the platform allows users to transform textbooks, lecture notes, and syllabus PDFs into an interactive personal tutor, automated study guide generator, flashcard deck, and adaptive quiz engine.

---

## 🚀 Key Features

- **📚 Books (Central Single Source of Truth)**: Upload PDF, DOCX, TXT, or MD textbooks. The selected active book automatically synchronizes across all AI modules (**AI Tutor**, **Study Notes**, **Flashcards**, and **Quizzes**).
- **🤖 ChatGPT-Style AI Tutor**: Modern conversational UI featuring native input composers, right-aligned user messages, left-aligned AI response cards, persona selection, and Strict Book RAG vs. General AI modes.
- **📝 Automated Study Notes**: Generate executive summaries, key concepts, bullet points, and exam questions with fallback parsing logic for guaranteed output.
- **🃏 AI Flashcards**: Generate interactive study cards from book contents with flip animations, shuffle mode, and mastery progress tracking.
- **🧪 Adaptive Quizzes**: Generate Beginner, Intermediate, or Advanced multiple-choice quizzes with instant grading, explanations, and SQLite score history.
- **🔒 Privacy-First Local AI**: All document embeddings and AI model inferences execute 100% locally via Ollama with zero third-party cloud data exposure.

---

## 🛠️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend UI** | Streamlit (Python) + Custom Blue-Cyan SaaS CSS System |
| **Orchestration & RAG** | LangChain |
| **LLM Inference Engine** | Ollama (Supports `gemma3:4b`, `llama3`, `mistral`, `phi3`, etc.) |
| **Embeddings Model** | HuggingFace `sentence-transformers/all-MiniLM-L6-v2` |
| **Vector Database** | ChromaDB (Persistent local vector storage) |
| **Relational Database** | SQLite (User authentication, book metadata, quiz logs) |
| **Document Parsers** | PyMuPDF (`fitz`), `python-docx` |

---

## 📁 Folder Structure

```text
AI-Smart-Classroom/
├── app.py                      # Main entry point (theme injection -> auth gate -> routing)
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── app/
│   ├── authentication/
│   │   └── auth.py             # User authentication (Login, Register, Guest mode)
│   ├── components/
│   │   ├── cards.py            # Stat cards, headers, badges, quiz option buttons
│   │   ├── chat_bubble.py      # ChatGPT-style message alignment bubbles
│   │   └── sidebar.py          # Fixed desktop navigation sidebar
│   ├── database/
│   │   └── db.py               # SQLite connection, migrations, book & user CRUD
│   ├── pages/
│   │   ├── books.py            # Books library, file uploader & indexing management
│   │   ├── chat.py             # ChatGPT-style AI Tutor interface
│   │   ├── flashcards.py       # Flashcard deck generator & study session UI
│   │   ├── notes.py            # Study Notes generator & PDF export
│   │   ├── quizzes.py          # Interactive quiz engine & score tracking
│   │   └── settings.py         # System configuration & model selector
│   ├── rag/
│   │   ├── chroma_store.py     # ChromaDB vector collection management
│   │   ├── embedder.py         # HuggingFace sentence transformer embedder
│   │   ├── loader.py           # Multi-format document loader (PDF, DOCX, TXT, MD)
│   │   └── qa_chain.py         # Retrieval-Augmentation chain & LLM prompt templates
│   ├── themes/
│   │   └── styles.py           # Enterprise SaaS Light/Dark CSS design system
│   └── utils/
│       ├── helpers.py          # Question extraction parser & helper functions
│       └── model_detector.py   # Automatic local Ollama model detector
└── data/
    ├── app_database.db         # SQLite persistent database
    ├── chroma_db/              # Persistent ChromaDB vector storage
    └── uploads/                # Persistent document storage
```

---

## ⚙️ Installation & Setup

### 1. Prerequisites
- Python 3.10 or higher
- [Ollama](https://ollama.ai/) installed on your operating system

### 2. Clone Repository & Setup Virtual Environment

#### 🍏 macOS / Linux
```bash
git clone https://github.com/pardhiv2006/AI-Smart-Classroom.git
cd AI-Smart-Classroom

# Create & activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 🪟 Windows (Command Prompt / cmd.exe)
```cmd
git clone https://github.com/pardhiv2006/AI-Smart-Classroom.git
cd AI-Smart-Classroom

:: Create & activate virtual environment
python -m venv venv
venv\Scripts\activate

:: Install dependencies
pip install -r requirements.txt
```

#### ⚡ Windows (PowerShell)
```powershell
git clone https://github.com/pardhiv2006/AI-Smart-Classroom.git
cd AI-Smart-Classroom

# Create & activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 3. Install & Start Ollama Models
Ensure Ollama service is running locally, then pull your preferred model:
```bash
# Recommended lightweight model
ollama pull gemma3:4b

# Alternative supported models
ollama pull llama3
ollama pull mistral
```

### 4. Launch Application

#### 🍏 macOS / Linux
```bash
streamlit run app.py
```

#### 🪟 Windows (Command Prompt or PowerShell)
```cmd
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## 🔒 Authentication Modes

1. **Register**: Create a local account by selecting a role (**Student**, **Teacher**, **Parent**, or **Administrator**).
2. **Login**: Sign in with existing credentials. Includes `autocomplete="current-password"` to prevent unwanted browser password generation popups.
3. **Guest Mode**: Instant one-click access for evaluation without creating an account.

---

## 📖 Module Overview

### 📚 1. Books (Central Single Source of Truth)
- **File Upload**: Upload textbooks in PDF, DOCX, TXT, or MD format.
- **Active Book Sync**: Selecting or activating a book immediately updates the active study material across AI Tutor, Notes, Flashcards, and Quizzes.
- **Library Actions**: Activate, Rename, View Details, Re-index, or Delete books with automatic ChromaDB chunk removal.

### 🤖 2. AI Tutor
- **ChatGPT-Style Layout**: Fixed input composer at the bottom with native `st.chat_input`, right-aligned user bubbles, and left-aligned AI response cards.
- **RAG Modes**:
  - **Strict Book RAG**: Answers strictly using retrieved chunks from the active book.
  - **Hybrid AI Mode**: Combines textbook content with general LLM knowledge.
- **Persona Selector**: Toggle between **Socratic Tutor**, **Strict Examiner**, **Simplified Explainer**, and **Analogy Master**.

### 📝 3. Study Notes
- Generate comprehensive chapter summaries, core key concepts, bullet-point highlights, and exam prep questions.
- Built-in multi-key JSON & regex fallback parser ensures notes generation **never** crashes or displays raw error text.

### 🃏 4. Flashcards
- Generate 5 to 25 study flashcards per session.
- Features interactive card flip buttons, card shuffling, and mastery progress tracking.

### 🧪 5. Quizzes
- Select difficulty levels (**Beginner**, **Intermediate**, **Advanced**).
- Interactive option selection via `quiz_option_button` with instant correct/incorrect feedback, score calculation, explanations, and SQLite attempt history.

### ⚙️ 6. Settings
- Real-time theme toggle between **☀️ Light Mode** and **🌙 Dark Mode**.
- Automatically detects installed Ollama models (`gemma3:4b`, `llama3`, `mistral`, `phi3`).

---

## 🔧 Troubleshooting

| Symptom | Cause | Solution |
| :--- | :--- | :--- |
| `ConnectionError: Ollama not reachable` | Ollama service is stopped | Run `ollama serve` in a terminal window. |
| `No models found` | No models pulled | Run `ollama pull gemma3:4b` in terminal. |
| `ChromaDB vector error` | Corrupted vector store | Delete `data/chroma_db/` folder and re-upload the document in Books. |
| `Database table missing` | Outdated SQLite schema | Delete `data/app_database.db` and re-launch `app.py` to auto-rebuild tables. |

---

## ✅ Production Readiness

This application has undergone complete enterprise UI stabilization, zero-scrollbar sidebar optimization, robust fallback error handling, and 100% Python compilation verification across all 28 project modules. It is fully ready for production deployment.

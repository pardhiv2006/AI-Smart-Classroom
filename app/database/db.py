"""
ScholarMind AI / Mr. AI Smart Classroom — SQLite Database Layer
Handles all persistent storage: users, chat history, quiz results, sessions, bookmarks.
"""
import sqlite3
import os
import bcrypt
import hashlib
import uuid
from datetime import datetime, date
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "smartclass.db"


def get_connection() -> sqlite3.Connection:
    """Get a SQLite connection with row_factory for dict-like access."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # Better concurrent access
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def initialize_database():
    """Create all tables if they don't exist. Safe to call multiple times."""
    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role          TEXT DEFAULT 'Student',
                theme         TEXT NOT NULL DEFAULT 'Light Mode',
                perf_mode     TEXT NOT NULL DEFAULT 'Balanced',
                persona       TEXT NOT NULL DEFAULT 'Friendly Tutor',
                ai_model      TEXT NOT NULL DEFAULT 'llama3',
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login    TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS chat_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                book_name   TEXT    NOT NULL,
                role        TEXT    NOT NULL,
                content     TEXT    NOT NULL,
                timestamp   TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS quiz_results (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                book_name   TEXT    NOT NULL,
                score       INTEGER NOT NULL,
                total       INTEGER NOT NULL,
                difficulty  TEXT    NOT NULL,
                timestamp   TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS study_sessions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                book_name   TEXT    NOT NULL,
                start_time  TEXT    NOT NULL DEFAULT (datetime('now')),
                end_time    TEXT
            );

            CREATE TABLE IF NOT EXISTS bookmarks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                book_name   TEXT    NOT NULL,
                page_num    INTEGER NOT NULL,
                note        TEXT,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS uploaded_books (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                book_name   TEXT    NOT NULL,
                page_start  INTEGER,
                page_end    INTEGER,
                chunk_count INTEGER,
                uploaded_at TEXT    NOT NULL DEFAULT (datetime('now'))
            );
        """)

        # Perform schema column migrations if upgrading existing DB
        cursor.execute("PRAGMA table_info(users)")
        cols = [row[1] for row in cursor.fetchall()]
        if "last_login" not in cols:
            cursor.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP")
        if "password_hash" not in cols:
            if "password_h" in cols:
                cursor.execute("ALTER TABLE users RENAME COLUMN password_h TO password_hash")
            else:
                cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")

        cursor.execute("PRAGMA table_info(uploaded_books)")
        b_cols = [row[1] for row in cursor.fetchall()]
        if "book_id" not in b_cols:
            cursor.execute("ALTER TABLE uploaded_books ADD COLUMN book_id TEXT")

        conn.commit()
    finally:
        conn.close()


# ─────────────────────── USER OPERATIONS ───────────────────────

def user_exists(username: str) -> bool:
    """Check if username already exists in database."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT 1 FROM users WHERE LOWER(username) = LOWER(?)", (username.strip(),)
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def create_user(username: str, password_hash: str, role: str = "Student") -> bool:
    """Insert a new user. Returns True on success, False if username taken."""
    username = username.strip()
    if user_exists(username):
        return False
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, password_hash, role.capitalize())
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_user(username: str) -> dict | None:
    """Fetch user dict by username."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (username.strip(),)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_by_username(username: str) -> dict | None:
    """Alias for get_user."""
    return get_user(username)


def update_last_login(username: str):
    """Update last_login timestamp for user."""
    conn = get_connection()
    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "UPDATE users SET last_login = ? WHERE LOWER(username) = LOWER(?)",
            (now_str, username.strip())
        )
        conn.commit()
    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> tuple[bool, str, dict | None]:
    """
    Validate user credentials against stored bcrypt hash.
    Returns (success: bool, message: str, user_dict | None).
    """
    username = username.strip()
    if not username or not password:
        return False, "Please enter username and password.", None

    user = get_user(username)
    if not user:
        return False, "Invalid username or password.", None

    stored_hash = user.get("password_hash") or user.get("password_h", "")
    
    # Verify hash with bcrypt
    try:
        is_valid = bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
    except Exception:
        # Fallback SHA-256 check for legacy hashes if any
        import hashlib
        legacy_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        is_valid = (stored_hash == legacy_hash)

    if not is_valid:
        return False, "Invalid username or password.", None

    update_last_login(username)
    user["last_login"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return True, f"Welcome back, {user['username']}! 🎓", user


def update_user_preference(user_id: int, field: str, value: str):
    """Update a single preference field (theme, perf_mode, persona, ai_model)."""
    allowed = {"theme", "perf_mode", "persona", "ai_model"}
    if field not in allowed:
        return
    conn = get_connection()
    try:
        conn.execute(f"UPDATE users SET {field} = ? WHERE id = ?", (value, user_id))
        conn.commit()
    finally:
        conn.close()


# ─────────────────────── CHAT HISTORY ───────────────────────

def save_chat_message(user_id: int, book_name: str, role: str, content: str):
    """Persist a single chat message."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO chat_history (user_id, book_name, role, content) VALUES (?, ?, ?, ?)",
            (user_id, book_name, role, content)
        )
        conn.commit()
    finally:
        conn.close()


def get_chat_history(user_id: int, book_name: str, limit: int = 50) -> list[dict]:
    """Return recent chat messages for a book as list of dicts."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT role, content, timestamp FROM chat_history
               WHERE user_id = ? AND book_name = ?
               ORDER BY timestamp DESC LIMIT ?""",
            (user_id, book_name, limit)
        ).fetchall()
        return [dict(r) for r in reversed(rows)]
    finally:
        conn.close()


def clear_chat_history(user_id: int, book_name: str):
    """Delete chat history for a given user and book."""
    conn = get_connection()
    try:
        conn.execute(
            "DELETE FROM chat_history WHERE user_id = ? AND book_name = ?",
            (user_id, book_name)
        )
        conn.commit()
    finally:
        conn.close()


# ─────────────────────── QUIZ RESULTS ───────────────────────

def save_quiz_result(user_id: int, book_name: str, score: int, total: int, difficulty: str):
    """Persist quiz result."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO quiz_results (user_id, book_name, score, total, difficulty)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, book_name, score, total, difficulty)
        )
        conn.commit()
    finally:
        conn.close()


def get_quiz_history(user_id: int, limit: int = 20) -> list[dict]:
    """Return past quiz attempts for analytics."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT book_name, score, total, difficulty, timestamp
               FROM quiz_results WHERE user_id = ?
               ORDER BY timestamp DESC LIMIT ?""",
            (user_id, limit)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_quiz_accuracy(user_id: int) -> float:
    """Compute average score percentage across all quizzes."""
    conn = get_connection()
    try:
        row = conn.execute(
            """SELECT SUM(score) as total_score, SUM(total) as total_q
               FROM quiz_results WHERE user_id = ?""",
            (user_id,)
        ).fetchone()
        if row and row["total_q"]:
            return float(row["total_score"]) / float(row["total_q"])
        return 0.0
    finally:
        conn.close()


# ─────────────────────── STUDY SESSIONS & STREAK ───────────────────────

def start_study_session(user_id: int, book_name: str) -> int:
    """Insert start of study session, return row id."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO study_sessions (user_id, book_name) VALUES (?, ?)",
            (user_id, book_name)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def end_study_session(session_id: int):
    """Mark session end time."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE study_sessions SET end_time = datetime('now') WHERE id = ?",
            (session_id,)
        )
        conn.commit()
    finally:
        conn.close()


def get_total_study_minutes(user_id: int) -> int:
    """Sum total study minutes from completed sessions."""
    conn = get_connection()
    try:
        row = conn.execute(
            """SELECT SUM((julianday(end_time) - julianday(start_time)) * 1440) as mins
               FROM study_sessions WHERE user_id = ? AND end_time IS NOT NULL""",
            (user_id,)
        ).fetchone()
        return int(row["mins"]) if row and row["mins"] else 0
    finally:
        conn.close()


def get_learning_streak(user_id: int) -> int:
    """Compute consecutive active study days count."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT DISTINCT DATE(start_time) as sdate
               FROM study_sessions WHERE user_id = ?
               ORDER BY sdate DESC""",
            (user_id,)
        ).fetchall()
        if not rows:
            return 0

        dates = [datetime.strptime(r["sdate"], "%Y-%m-%d").date() for r in rows]
        today = date.today()
        streak = 0

        current = today
        if dates[0] not in (today, date.fromordinal(today.toordinal() - 1)):
            return 0

        for d in dates:
            if d == current or d == date.fromordinal(current.toordinal() - 1):
                streak += 1
                current = d
            else:
                break
        return streak
    finally:
        conn.close()


def _get_study_sessions_raw(user_id: int) -> list[dict]:
    """Raw study sessions for heatmap rendering."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT start_time, end_time FROM study_sessions
               WHERE user_id = ? AND end_time IS NOT NULL""",
            (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ─────────────────────── BOOKMARKS ───────────────────────

def save_bookmark(user_id: int, book_name: str, page_num: int, note: str = ""):
    """Persist page bookmark."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO bookmarks (user_id, book_name, page_num, note)
               VALUES (?, ?, ?, ?)""",
            (user_id, book_name, page_num, note)
        )
        conn.commit()
    finally:
        conn.close()


def get_user_bookmarks(user_id: int, book_name: str = None) -> list[dict]:
    """Retrieve bookmarks for user."""
    conn = get_connection()
    try:
        if book_name:
            rows = conn.execute(
                "SELECT * FROM bookmarks WHERE user_id = ? AND book_name = ? ORDER BY page_num ASC",
                (user_id, book_name)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM bookmarks WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ─────────────────────── UPLOADED BOOKS METADATA ───────────────────────

def save_uploaded_book(user_id: int, book_name: str, page_start: int, page_end: int, chunk_count: int, book_id: str | None = None) -> str:
    """Persist uploaded book record with a stable UUID book_id."""
    if not book_id:
        book_id = f"bk_{uuid.uuid4().hex[:12]}"
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO uploaded_books (user_id, book_name, page_start, page_end, chunk_count, book_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, book_name, page_start, page_end, chunk_count, book_id)
        )
        conn.commit()
        return book_id
    finally:
        conn.close()


def get_uploaded_books(user_id: int) -> list[dict]:
    """Return all books uploaded by a user."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT book_id, book_name, page_start, page_end, chunk_count, uploaded_at
               FROM uploaded_books WHERE user_id = ? ORDER BY uploaded_at DESC""",
            (user_id,)
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if not d.get("book_id"):
                d["book_id"] = f"bk_{hashlib.sha1(d['book_name'].encode()).hexdigest()[:12]}"
            result.append(d)
        return result
    finally:
        conn.close()


def delete_bookmark(bookmark_id: int):
    """Delete a bookmark by ID."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM bookmarks WHERE id = ?", (bookmark_id,))
        conn.commit()
    finally:
        conn.close()


def get_recent_activity(user_id: int, limit: int = 10) -> list[dict]:
    """Retrieve combined recent activities (quizzes, study sessions, uploads)."""
    conn = get_connection()
    try:
        activities = []
        q_rows = conn.execute(
            """SELECT book_name, score, total, timestamp FROM quiz_results
               WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?""",
            (user_id, limit)
        ).fetchall()
        for r in q_rows:
            pct = round((r['score'] / r['total']) * 100) if r['total'] else 0
            activities.append({
                "type": "quiz",
                "icon": "🎯",
                "title": f"Quiz on {r['book_name']} ({r['score']}/{r['total']} - {pct}%)",
                "timestamp": r["timestamp"]
            })

        b_rows = conn.execute(
            """SELECT book_name, chunk_count, uploaded_at FROM uploaded_books
               WHERE user_id = ? ORDER BY uploaded_at DESC LIMIT ?""",
            (user_id, limit)
        ).fetchall()
        for r in b_rows:
            activities.append({
                "type": "upload",
                "icon": "📚",
                "title": f"Indexed {r['book_name']} ({r['chunk_count']} chunks)",
                "timestamp": r["uploaded_at"]
            })

        s_rows = conn.execute(
            """SELECT book_name, start_time FROM study_sessions
               WHERE user_id = ? ORDER BY start_time DESC LIMIT ?""",
            (user_id, limit)
        ).fetchall()
        for r in s_rows:
            activities.append({
                "type": "session",
                "icon": "⚡",
                "title": f"Studied {r['book_name']}",
                "timestamp": r["start_time"]
            })

        activities.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)
        return activities[:limit]
    except Exception:
        return []
    finally:
        conn.close()


# Compatibility aliases for books module
log_uploaded_book = save_uploaded_book
add_bookmark = save_bookmark
get_bookmarks = get_user_bookmarks



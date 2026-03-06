from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE = "notes.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            tags TEXT DEFAULT '',
            created_at TEXT,
            updated_at TEXT
        )
    """
    )
    conn.commit()
    conn.close()


@app.on_event("startup")
def startup():
    init_db()


class NoteCreate(BaseModel):
    title: str
    content: str
    tags: str = ""


class NoteUpdate(BaseModel):
    title: str
    content: str
    tags: str = ""


@app.get("/notes")
def list_notes():
    db = get_db()
    notes = db.execute("SELECT * FROM notes ORDER BY updated_at DESC").fetchall()
    db.close()
    return [dict(n) for n in notes]


@app.get("/notes/{note_id}")
def get_note(note_id: int):
    db = get_db()
    note = db.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    db.close()
    if note is None:
        return {"error": "not found"}
    return dict(note)


@app.post("/notes")
def create_note(note: NoteCreate):
    db = get_db()
    now = datetime.now().isoformat()
    cursor = db.execute(
        "INSERT INTO notes (title, content, tags, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (note.title, note.content, note.tags, now, now),
    )
    db.commit()
    note_id = cursor.lastrowid
    db.close()
    return {"id": note_id}


@app.put("/notes/{note_id}")
def update_note(note_id: int, note: NoteUpdate):
    db = get_db()
    now = datetime.now().isoformat()
    db.execute(
        "UPDATE notes SET title = ?, content = ?, tags = ?, updated_at = ? WHERE id = ?",
        (note.title, note.content, note.tags, now, note_id),
    )
    db.commit()
    db.close()
    return {"ok": True}


@app.delete("/notes/{note_id}")
def delete_note(note_id: int):
    db = get_db()
    db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    db.commit()
    db.close()
    return {"ok": True}

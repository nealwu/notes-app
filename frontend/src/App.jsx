import { useState, useEffect } from "react";

function App() {
  const [notes, setNotes] = useState([]);
  const [selectedNote, setSelectedNote] = useState(null);
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [tags, setTags] = useState("");

  useEffect(() => {
    fetchNotes();
  }, []);

  function fetchNotes() {
    fetch("/notes")
      .then((r) => r.json())
      .then(setNotes);
  }

  function selectNote(note) {
    setSelectedNote(note);
    setTitle(note.title);
    setContent(note.content);
    setTags(note.tags || "");
    setEditing(false);
  }

  function handleNew() {
    setSelectedNote(null);
    setTitle("");
    setContent("");
    setTags("");
    setEditing(true);
  }

  function handleSave() {
    if (!title.trim()) {
      alert("Title is required");
      return;
    }

    const body = { title, content, tags };

    if (selectedNote) {
      fetch(`/notes/${selectedNote.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }).then(() => {
        fetchNotes();
        setEditing(false);
        setSelectedNote({ ...selectedNote, ...body });
      });
    } else {
      fetch("/notes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      })
        .then((r) => r.json())
        .then((data) => {
          fetchNotes();
          setEditing(false);
          setSelectedNote({ id: data.id, ...body });
        });
    }
  }

  function handleDelete() {
    if (!selectedNote) return;
    if (!confirm("Delete this note?")) return;
    fetch(`/notes/${selectedNote.id}`, { method: "DELETE" }).then(() => {
      setSelectedNote(null);
      setEditing(false);
      fetchNotes();
    });
  }

  return (
    <div className="app">
      <div className="sidebar">
        <div className="sidebar-header">
          <h2>Notes</h2>
          <button onClick={handleNew}>+ New</button>
        </div>
        <div className="note-list">
          {notes.map((note) => (
            <div
              key={note.id}
              className={
                "note-item" +
                (selectedNote?.id === note.id ? " selected" : "")
              }
              onClick={() => selectNote(note)}
            >
              <div className="note-item-title">{note.title}</div>
              {note.tags && (
                <div className="note-item-tags">{note.tags}</div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="main">
        {editing ? (
          <div className="editor">
            <input
              type="text"
              placeholder="Title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="editor-title"
            />
            <input
              type="text"
              placeholder="Tags (comma separated)"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              className="editor-tags"
            />
            <textarea
              placeholder="Write your note..."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="editor-content"
            />
            <div className="editor-actions">
              <button onClick={handleSave}>Save</button>
              <button
                onClick={() => {
                  setEditing(false);
                  if (!selectedNote) {
                    setTitle("");
                    setContent("");
                    setTags("");
                  }
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        ) : selectedNote ? (
          <div className="note-view">
            <div className="note-view-header">
              <h1>{selectedNote.title}</h1>
              <div>
                <button onClick={() => setEditing(true)}>Edit</button>
                <button onClick={handleDelete} style={{ marginLeft: 8 }}>
                  Delete
                </button>
              </div>
            </div>
            {selectedNote.tags && (
              <div className="note-view-tags">
                {selectedNote.tags.split(",").map((tag, i) => (
                  <span key={i} className="tag">
                    {tag.trim()}
                  </span>
                ))}
              </div>
            )}
            <div className="note-view-content">{selectedNote.content}</div>
          </div>
        ) : (
          <div className="empty-state">Select a note or create a new one</div>
        )}
      </div>
    </div>
  );
}

export default App;

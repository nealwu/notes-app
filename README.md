# Notes App

A simple notes app with create, edit, delete, and tagging.

## Setup

You'll need Python 3.10+ and Node.js 18+.

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python seed.py          # populate with sample notes
uvicorn main:app --reload
```

The API runs at http://localhost:8000.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app runs at http://localhost:5173.

## API

- `GET /notes` — list all notes
- `GET /notes/:id` — get a single note
- `POST /notes` — create a note (JSON body: `{title, content, tags}`)
- `PUT /notes/:id` — update a note
- `DELETE /notes/:id` — delete a note

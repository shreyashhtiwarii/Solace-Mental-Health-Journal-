# 🌿 Solace — Mental Health Journaling App

A full-stack Mental Health Journaling app with an HTML/CSS/JS frontend and a Python FastAPI backend powered by Claude AI.

---

## 📁 Project Structure

```
solace/
├── frontend/
│   └── index.html          ← Full app (HTML + CSS + JS in one file)
├── backend/
│   ├── app.py              ← FastAPI backend
│   └── requirements.txt    ← Python dependencies
└── README.md
```

---

## 🚀 Getting Started

### 1. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set your Anthropic API key
export ANTHROPIC_API_KEY=sk-ant-your-key-here

# Run the server
uvicorn app:app --reload --port 8000
```

The API will be live at: `http://localhost:8000`

---

### 2. Frontend Setup

Just open `frontend/index.html` in your browser — no build step needed!

> Make sure the backend is running first.  
> The frontend points to `http://localhost:8000` by default.  
> To change this, edit `const API_BASE` at the top of the `<script>` in `index.html`.

---

## 🔌 API Endpoints

| Method | Path                  | Description                         |
|--------|-----------------------|-------------------------------------|
| GET    | `/`                   | Health check                        |
| POST   | `/entries`            | Submit a journal entry + get AI reflection |
| GET    | `/entries`            | Get recent entries (default: 20)    |
| GET    | `/entries/{id}`       | Get single entry                    |
| DELETE | `/entries/{id}`       | Delete an entry                     |
| GET    | `/insights/stats`     | Get mood stats & emotion breakdown  |
| POST   | `/insights/weekly`    | Generate weekly AI insight          |
| GET    | `/prompts`            | Get journaling prompts              |

---

## ✨ Features

- **Mood Tracking** — 5-level emoji mood selector per entry
- **AI Reflection** — Claude generates empathetic, CBT-informed responses
- **Emotion Detection** — Automatic tagging of emotional states
- **Weekly Insights** — AI analysis of your emotional patterns
- **History View** — Browse past entries with mood color-coding
- **Insights Dashboard** — Weekly bar chart, emotion word cloud, stats
- **SQLite DB** — Lightweight local database, no setup required
- **Privacy-first** — No third-party analytics, local storage

---

## 🔐 Privacy & Safety

- All data is stored locally in `solace.db` (SQLite)
- No data is shared with third parties
- A crisis helpline notice is shown at the bottom of the app
- AI responses are compassionate and non-diagnostic

---

## 🛠 Tech Stack

| Layer     | Technology              |
|-----------|------------------------|
| Frontend  | HTML5, CSS3, Vanilla JS |
| Backend   | Python, FastAPI         |
| Database  | SQLite (via stdlib)     |
| AI        | Anthropic Claude API    |
| Fonts     | Google Fonts (DM Sans + Lora) |

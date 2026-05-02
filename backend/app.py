"""
Solace - Mental Health Journaling App
FastAPI Backend
"""

import anthropic
import instructor
import json
import sqlite3
import os
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from typing import Optional, List
from passlib.context import CryptContext
import jwt
from datetime import datetime, date, timedelta
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from encryption import encrypt_content, decrypt_content
try:
    from vector_store import add_entry_to_vector_store, retrieve_relevant_entries
except ImportError:
    pass # Will be available if chromadb installs correctly

# ─────────────────────────────────────────────
# App Setup & Telemetry
# ─────────────────────────────────────────────
app = FastAPI(title="Solace Enterprise API", version="2.0.0")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Load environment variables from .env file
load_dotenv()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],  # Must be specific when allow_credentials=True
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Anthropic client — set ANTHROPIC_API_KEY in environment
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

DB_PATH = "solace.db"

# ─────────────────────────────────────────────
# Auth Setup
# ─────────────────────────────────────────────
SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-key-solace")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    return username

# ─────────────────────────────────────────────
# Database Setup
# ─────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS entries (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT    NOT NULL DEFAULT 'default',
            created_at  TEXT    NOT NULL,
            mood_score  INTEGER NOT NULL,
            mood_label  TEXT    NOT NULL,
            content     TEXT    NOT NULL,
            emotions    TEXT    NOT NULL DEFAULT '[]',
            ai_response TEXT
        );

        CREATE TABLE IF NOT EXISTS insights (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT    NOT NULL DEFAULT 'default',
            week_start  TEXT    NOT NULL,
            insight     TEXT    NOT NULL,
            created_at  TEXT    NOT NULL
        );
    """)
    conn.commit()
    conn.close()

init_db()

# ─────────────────────────────────────────────
# Pydantic Models
# ─────────────────────────────────────────────
class UserCreate(BaseModel):
    username: str
    password: str

class JournalEntry(BaseModel):
    content: str
    mood_score: int           # 1–5
    mood_label: str
    user_id: Optional[str] = "default"

class EntryResponse(BaseModel):
    id: int
    created_at: str
    mood_score: int
    mood_label: str
    content: str
    emotions: List[str]
    ai_response: Optional[str]

class WeeklyInsightRequest(BaseModel):
    user_id: Optional[str] = "default"

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
MOOD_EMOJIS = {1: "😔", 2: "😟", 3: "😐", 4: "🙂", 5: "😄"}

def row_to_entry(row) -> dict:
    decrypted_content = decrypt_content(row["content"])
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "mood_score": row["mood_score"],
        "mood_label": row["mood_label"],
        "mood_emoji": MOOD_EMOJIS.get(row["mood_score"], "😐"),
        "content": decrypted_content,
        "emotions": json.loads(row["emotions"]),
        "ai_response": row["ai_response"],
    }

class AIReflection(BaseModel):
    response: str = Field(description="The warm, empathetic AI reflection response.")
    emotions: List[str] = Field(description="2-3 specific emotions detected in the entry.")

def get_ai_reflection(content: str, mood_score: int, mood_label: str, user_id: str) -> dict:
    """Call Claude API using Instructor to get strict structured reflection."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return {
            "response": "Thank you for sharing your thoughts. I'm here to listen and support you. (Mocked response, add ANTHROPIC_API_KEY for real AI reflection)",
            "emotions": ["reflective", "calm"]
        }
        
    client = instructor.from_anthropic(anthropic.Anthropic(api_key=api_key))

    # Optional RAG Context
    try:
        past_context = retrieve_relevant_entries(user_id, content)
    except NameError:
        past_context = ""
    
    if past_context:
        past_context = f"\nRelevant past entries for context:\n{past_context}"

    system_prompt = f"""You are a warm, empathetic mental health journaling companion.
When someone shares a journal entry:
1. Acknowledge their feelings genuinely and warmly.
2. Provide a gentle reflection or reframe based on their mood ({mood_label}).
3. End with one supportive, open-ended question.
{past_context}
Keep the response under 100 words. Be conversational, not clinical."""

    reflection = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=300,
        response_model=AIReflection,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": f"Journal entry (mood: {mood_label}, score: {mood_score}/5):\n\"{content}\""
        }]
    )
    return {"response": reflection.response, "emotions": reflection.emotions}

def get_weekly_insight(entries: list) -> str:
    """Generate a weekly pattern insight from multiple entries."""
    if not entries:
        return "Start journaling daily to unlock weekly insights!"

    summary = "\n".join([
        f"- {e['created_at'][:10]} | Mood: {e['mood_label']} | {e['content'][:80]}..."
        for e in entries
    ])

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return "Based on your recent entries, you seem to be reflecting deeply. Keep up the consistent journaling! (Mocked response, add ANTHROPIC_API_KEY for real AI insight)"

    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": f"""Based on these journal entries from the past week, give a single paragraph 
(60-80 words) of compassionate insight about emotional patterns, trends, or gentle suggestions.
Be warm and observational, not prescriptive.

Entries:
{summary}

Respond with only the insight paragraph, no preamble."""
        }]
    )
    return message.content[0].text.strip()

# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "Solace Journal API is running 🌿", "version": "1.0.0"}


@app.post("/register")
@limiter.limit("5/minute")
def register(request: Request, user: UserCreate):
    conn = get_db()
    existing = conn.execute("SELECT * FROM users WHERE username = ?", (user.username,)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_pw = get_password_hash(user.password)
    conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (user.username, hashed_pw))
    conn.commit()
    conn.close()
    return {"message": "User created successfully"}

@app.post("/login")
@limiter.limit("10/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (form_data.username,)).fetchone()
    conn.close()
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/entries", response_model=dict)
@limiter.limit("15/hour")
def create_entry(request: Request, entry: JournalEntry, current_user: str = Depends(get_current_user)):
    """Submit a new journal entry, encrypt it, save RAG vector, and get AI reflection."""
    if not 1 <= entry.mood_score <= 5:
        raise HTTPException(status_code=400, detail="mood_score must be between 1 and 5")
    if len(entry.content.strip()) < 5:
        raise HTTPException(status_code=400, detail="Entry content is too short")
        
    # Crisis Detection (Lightweight Guardrail)
    crisis_keywords = ["kill myself", "suicide", "end it all", "don't want to live"]
    if any(k in entry.content.lower() for k in crisis_keywords):
        return {
            "id": 0, "content": entry.content, "mood_score": entry.mood_score, "mood_label": entry.mood_label,
            "emotions": ["crisis", "distressed"],
            "ai_response": "🚨 It sounds like you are going through an incredibly difficult time right now. Please know you are not alone. If you are in immediate danger or feeling suicidal, please reach out to a crisis line immediately: India: iCall 9152987821 | Global: befrienders.org. There is help available."
        }

    # Get structured AI reflection via Instructor
    try:
        ai_data = get_ai_reflection(entry.content, entry.mood_score, entry.mood_label, current_user)
        ai_response = ai_data.get("response", "")
        emotions = ai_data.get("emotions", [])
    except Exception as e:
        ai_response = "Thank you for sharing. Whatever you're feeling right now is valid."
        emotions = ["reflective"]

    # Encrypt content at rest
    encrypted_content = encrypt_content(entry.content)

    now = datetime.now().isoformat()
    conn = get_db()
    cursor = conn.execute(
        """INSERT INTO entries (user_id, created_at, mood_score, mood_label, content, emotions, ai_response)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (current_user, now, entry.mood_score, entry.mood_label,
         encrypted_content, json.dumps(emotions), ai_response)
    )
    conn.commit()
    entry_id = cursor.lastrowid
    
    # Store in ChromaDB for RAG memory (using unencrypted content for semantic search only)
    try:
        add_entry_to_vector_store(entry_id, current_user, entry.content, entry.mood_label)
    except NameError:
        pass # If chromadb not available
        
    row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
    conn.close()

    return row_to_entry(row)


@app.get("/entries")
def get_entries(limit: int = 20, current_user: str = Depends(get_current_user)):
    """Get recent journal entries."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM entries WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (current_user, limit)
    ).fetchall()
    conn.close()
    return [row_to_entry(r) for r in rows]


@app.get("/entries/{entry_id}")
def get_entry(entry_id: int, current_user: str = Depends(get_current_user)):
    """Get a single journal entry by ID."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM entries WHERE id = ? AND user_id = ?", (entry_id, current_user)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Entry not found")
    return row_to_entry(row)


@app.delete("/entries/{entry_id}")
def delete_entry(entry_id: int, current_user: str = Depends(get_current_user)):
    """Delete a journal entry."""
    conn = get_db()
    result = conn.execute(
        "DELETE FROM entries WHERE id = ? AND user_id = ?", (entry_id, current_user)
    )
    conn.commit()
    conn.close()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"message": "Entry deleted"}


@app.get("/insights/stats")
def get_stats(current_user: str = Depends(get_current_user)):
    """Get mood statistics and trends for the last 7 days."""
    conn = get_db()

    # Last 7 entries mood scores
    rows = conn.execute(
        """SELECT date(created_at) as day, AVG(mood_score) as avg_mood, COUNT(*) as count
           FROM entries WHERE user_id = ?
           GROUP BY date(created_at)
           ORDER BY day DESC LIMIT 7""",
        (current_user,)
    ).fetchall()

    # All-time stats
    stats_row = conn.execute(
        """SELECT COUNT(*) as total, AVG(mood_score) as avg_mood,
                  MAX(mood_score) as best_mood, MIN(mood_score) as lowest_mood
           FROM entries WHERE user_id = ?""",
        (current_user,)
    ).fetchone()

    # Most common emotions
    emotion_rows = conn.execute(
        "SELECT emotions FROM entries WHERE user_id = ? ORDER BY created_at DESC LIMIT 20",
        (current_user,)
    ).fetchall()
    conn.close()

    emotion_counts = {}
    for r in emotion_rows:
        for e in json.loads(r["emotions"]):
            emotion_counts[e] = emotion_counts.get(e, 0) + 1

    top_emotions = sorted(emotion_counts.items(), key=lambda x: -x[1])[:8]

    return {
        "daily_moods": [{"day": r["day"], "avg_mood": round(r["avg_mood"], 1), "count": r["count"]} for r in rows],
        "total_entries": stats_row["total"] or 0,
        "avg_mood": round(stats_row["avg_mood"] or 0, 1),
        "best_mood": stats_row["best_mood"] or 0,
        "lowest_mood": stats_row["lowest_mood"] or 0,
        "top_emotions": [{"emotion": e, "count": c} for e, c in top_emotions],
    }


@app.post("/insights/weekly")
def generate_weekly_insight(req: WeeklyInsightRequest, current_user: str = Depends(get_current_user)):
    """Generate AI-powered weekly insight from recent entries."""
    conn = get_db()
    rows = conn.execute(
        """SELECT * FROM entries WHERE user_id = ?
           AND created_at >= date('now', '-7 days')
           ORDER BY created_at DESC""",
        (current_user,)
    ).fetchall()
    conn.close()

    entries = [row_to_entry(r) for r in rows]

    try:
        insight = get_weekly_insight(entries)
    except Exception:
        insight = "Keep journaling consistently to unlock personalized weekly insights about your emotional patterns."

    # Save insight
    conn = get_db()
    conn.execute(
        "INSERT INTO insights (user_id, week_start, insight, created_at) VALUES (?, date('now', 'weekday 0', '-7 days'), ?, ?)",
        (current_user, insight, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

    return {"insight": insight, "entry_count": len(entries)}


@app.get("/prompts")
def get_prompts():
    """Get a list of journaling prompts."""
    prompts = [
        "What's weighing on your mind today?",
        "Describe one small win from today.",
        "What emotion has been most present today?",
        "What are you grateful for right now?",
        "What would make tomorrow better?",
        "How is your body feeling today?",
        "What drained your energy today, and what restored it?",
        "What's something you're looking forward to?",
        "Describe a moment today when you felt truly present.",
        "What's one thing you'd tell your past self right now?",
    ]
    return {"prompts": prompts}

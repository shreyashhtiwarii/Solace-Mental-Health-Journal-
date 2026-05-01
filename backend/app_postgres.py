"""
Solace — Mental Health Journaling App
Backend: PostgreSQL via Supabase (SQLAlchemy async + asyncpg)

Setup:
  pip install -r requirements_postgres.txt
  export ANTHROPIC_API_KEY=sk-ant-...
  export DATABASE_URL=postgresql+asyncpg://postgres:[password]@db.[project].supabase.co:5432/postgres
  uvicorn app_postgres:app --reload --port 8000
"""

import os
from datetime import datetime
from typing import Optional, List

import anthropic
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import Integer, String, Text, DateTime, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import (
    AsyncSession, create_async_engine, async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy import select, delete

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
# Get your DATABASE_URL from: Supabase → Project Settings → Database → Connection string
# Use the "URI" format and replace [YOUR-PASSWORD]
# Then change "postgresql://" to "postgresql+asyncpg://"
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres"
)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,         # auto-reconnect dropped connections
    connect_args={"ssl": "require"}  # Supabase requires SSL
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
ai_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

MOOD_EMOJIS = {1: "😔", 2: "😟", 3: "😐", 4: "🙂", 5: "😄"}

# ─────────────────────────────────────────────
# ORM Models
# ─────────────────────────────────────────────
class Base(DeclarativeBase):
    pass

class Entry(Base):
    __tablename__ = "entries"

    id:          Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id:     Mapped[str]           = mapped_column(String(64), nullable=False, default="default", index=True)
    created_at:  Mapped[datetime]      = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    mood_score:  Mapped[int]           = mapped_column(Integer, nullable=False)
    mood_label:  Mapped[str]           = mapped_column(String(32), nullable=False)
    content:     Mapped[str]           = mapped_column(Text, nullable=False)
    emotions:    Mapped[list]          = mapped_column(JSONB, nullable=False, default=list)
    ai_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

class WeeklyInsight(Base):
    __tablename__ = "weekly_insights"

    id:         Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id:    Mapped[str]      = mapped_column(String(64), nullable=False, index=True)
    week_start: Mapped[str]      = mapped_column(String(20), nullable=False)
    insight:    Mapped[str]      = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

# ─────────────────────────────────────────────
# FastAPI App
# ─────────────────────────────────────────────
app = FastAPI(title="Solace Journal API — PostgreSQL/Supabase", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Supabase PostgreSQL tables ready.")

# ─────────────────────────────────────────────
# Dependency: DB Session
# ─────────────────────────────────────────────
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# ─────────────────────────────────────────────
# Pydantic Schemas
# ─────────────────────────────────────────────
class EntryCreate(BaseModel):
    content:    str
    mood_score: int
    mood_label: str
    user_id:    Optional[str] = "default"

class EntryOut(BaseModel):
    id:          int
    user_id:     str
    created_at:  str
    mood_score:  int
    mood_label:  str
    mood_emoji:  str
    content:     str
    emotions:    List[str]
    ai_response: Optional[str]

class WeeklyInsightRequest(BaseModel):
    user_id: Optional[str] = "default"

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def entry_to_dict(e: Entry) -> dict:
    return {
        "id":          e.id,
        "user_id":     e.user_id,
        "created_at":  e.created_at.isoformat(),
        "mood_score":  e.mood_score,
        "mood_label":  e.mood_label,
        "mood_emoji":  MOOD_EMOJIS.get(e.mood_score, "😐"),
        "content":     e.content,
        "emotions":    e.emotions or [],
        "ai_response": e.ai_response,
    }

def get_ai_reflection(content: str, mood_label: str) -> dict:
    """Call Claude to get empathetic reflection + detected emotions."""
    message = ai_client.messages.create(
        model="claude-opus-4-6",
        max_tokens=400,
        system="""You are a warm, empathetic mental health journaling companion.
When someone shares a journal entry:
1. Acknowledge their feelings genuinely (2-3 sentences)
2. Offer one gentle, compassionate insight or reframe (2 sentences)
3. End with one supportive reflective question (1 sentence)
Also detect 2-3 emotions present in the text.
Keep total response under 120 words. Be human, not clinical.

Respond ONLY in this JSON format (no markdown, no backticks):
{"response": "your empathetic response", "emotions": ["emotion1", "emotion2"]}""",
        messages=[{
            "role": "user",
            "content": f"Journal entry (mood: {mood_label}):\n\"{content}\""
        }]
    )
    import json
    return json.loads(message.content[0].text.strip())

def get_weekly_insight_text(entries: list) -> str:
    """Generate a weekly pattern insight from multiple entries."""
    if not entries:
        return "Start journaling daily to unlock personalized weekly insights!"

    summary = "\n".join([
        f"- {e['created_at'][:10]} | Mood: {e['mood_label']} | {e['content'][:80]}..."
        for e in entries
    ])
    message = ai_client.messages.create(
        model="claude-opus-4-6",
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
async def root():
    return {"message": "Solace Journal API (Supabase) is running 🌿", "version": "2.0.0"}


@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    """Check DB connectivity."""
    await db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "supabase_postgresql"}


@app.post("/entries", response_model=EntryOut)
async def create_entry(body: EntryCreate, db: AsyncSession = Depends(get_db)):
    """Submit a journal entry and get an AI reflection."""
    if not 1 <= body.mood_score <= 5:
        raise HTTPException(status_code=400, detail="mood_score must be between 1 and 5")
    if len(body.content.strip()) < 5:
        raise HTTPException(status_code=400, detail="Entry content is too short")

    # AI reflection
    try:
        ai_data    = get_ai_reflection(body.content, body.mood_label)
        ai_response = ai_data.get("response", "")
        emotions    = ai_data.get("emotions", [])
    except Exception:
        ai_response = "Thank you for sharing. Whatever you're feeling right now is valid. What feels most important to you about what you wrote?"
        emotions    = ["reflective"]

    entry = Entry(
        user_id     = body.user_id,
        created_at  = datetime.utcnow(),
        mood_score  = body.mood_score,
        mood_label  = body.mood_label,
        content     = body.content,
        emotions    = emotions,
        ai_response = ai_response,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry_to_dict(entry)


@app.get("/entries")
async def list_entries(
    user_id: str = "default",
    limit:   int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Get recent journal entries for a user."""
    result = await db.execute(
        select(Entry)
        .where(Entry.user_id == user_id)
        .order_by(Entry.created_at.desc())
        .limit(limit)
    )
    entries = result.scalars().all()
    return [entry_to_dict(e) for e in entries]


@app.get("/entries/{entry_id}", response_model=EntryOut)
async def get_entry(entry_id: int, user_id: str = "default", db: AsyncSession = Depends(get_db)):
    """Get a single entry by ID."""
    result = await db.execute(
        select(Entry).where(Entry.id == entry_id, Entry.user_id == user_id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry_to_dict(entry)


@app.delete("/entries/{entry_id}")
async def delete_entry(entry_id: int, user_id: str = "default", db: AsyncSession = Depends(get_db)):
    """Delete an entry."""
    result = await db.execute(
        delete(Entry).where(Entry.id == entry_id, Entry.user_id == user_id)
    )
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"message": "Entry deleted"}


@app.get("/insights/stats")
async def get_stats(user_id: str = "default", db: AsyncSession = Depends(get_db)):
    """Mood statistics and trends."""
    # Daily mood averages (last 7 days)
    daily_result = await db.execute(text("""
        SELECT
            DATE(created_at) AS day,
            ROUND(AVG(mood_score)::numeric, 1) AS avg_mood,
            COUNT(*) AS count
        FROM entries
        WHERE user_id = :uid
          AND created_at >= NOW() - INTERVAL '7 days'
        GROUP BY DATE(created_at)
        ORDER BY day DESC
        LIMIT 7
    """), {"uid": user_id})
    daily_moods = [
        {"day": str(r.day), "avg_mood": float(r.avg_mood), "count": r.count}
        for r in daily_result.fetchall()
    ]

    # Overall stats
    stats_result = await db.execute(text("""
        SELECT
            COUNT(*)             AS total,
            ROUND(AVG(mood_score)::numeric, 1) AS avg_mood,
            MAX(mood_score)      AS best_mood,
            MIN(mood_score)      AS lowest_mood
        FROM entries
        WHERE user_id = :uid
    """), {"uid": user_id})
    s = stats_result.fetchone()

    # Top emotions (from JSONB array column)
    emotions_result = await db.execute(text("""
        SELECT emotion, COUNT(*) AS cnt
        FROM entries,
             JSONB_ARRAY_ELEMENTS_TEXT(emotions) AS emotion
        WHERE user_id = :uid
        GROUP BY emotion
        ORDER BY cnt DESC
        LIMIT 8
    """), {"uid": user_id})
    top_emotions = [{"emotion": r.emotion, "count": r.cnt} for r in emotions_result.fetchall()]

    return {
        "daily_moods":    daily_moods,
        "total_entries":  s.total or 0,
        "avg_mood":       float(s.avg_mood or 0),
        "best_mood":      s.best_mood or 0,
        "lowest_mood":    s.lowest_mood or 0,
        "top_emotions":   top_emotions,
    }


@app.post("/insights/weekly")
async def generate_weekly_insight(req: WeeklyInsightRequest, db: AsyncSession = Depends(get_db)):
    """Generate AI-powered weekly insight."""
    result = await db.execute(
        select(Entry)
        .where(
            Entry.user_id == req.user_id,
            Entry.created_at >= text("NOW() - INTERVAL '7 days'")
        )
        .order_by(Entry.created_at.desc())
    )
    entries = [entry_to_dict(e) for e in result.scalars().all()]

    try:
        insight = get_weekly_insight_text(entries)
    except Exception:
        insight = "Keep journaling consistently to unlock personalized weekly insights about your emotional patterns."

    # Persist the insight
    wi = WeeklyInsight(
        user_id    = req.user_id,
        week_start = datetime.utcnow().strftime("%Y-%m-%d"),
        insight    = insight,
        created_at = datetime.utcnow(),
    )
    db.add(wi)
    await db.commit()

    return {"insight": insight, "entry_count": len(entries)}


@app.get("/prompts")
async def get_prompts():
    return {"prompts": [
        "What's weighing on your mind today?",
        "Describe one small win from today.",
        "What emotion has been most present today?",
        "What are you grateful for right now?",
        "What would make tomorrow better?",
        "How is your body feeling today?",
        "What drained your energy today, and what restored it?",
        "Describe a moment today when you felt truly present.",
        "What's something you're looking forward to?",
        "What's one thing you'd tell your past self right now?",
    ]}

# backend/app.py

import os
import random
from datetime import datetime, timezone
from typing import List, Optional, Literal
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import hmac
import hashlib
from urllib.parse import parse_qs

from heroes import HEROES
from db import (
    init_db, get_used_heroes, mark_hero_used,
    save_quiz, get_quiz,
    save_daily_challenge, get_daily_challenge,
    list_quizzes, get_db_path,
)
from ai_client import (
    generate_hero_post,
    generate_counter_pick,
    generate_tier_list,
    generate_quiz,
    generate_daily_challenge,
    explain_patch,
)

# ---------------------------
# 1) Загрузка .env (надёжно)
# ---------------------------


def load_env():
    candidates = [
        Path(__file__).parent / ".env",          # backend/.env
        Path.cwd() / ".env",                      # текущая папка запуска
        Path(__file__).parent.parent / ".env",    # корень проекта
    ]
    for p in candidates:
        if p.exists():
            load_dotenv(dotenv_path=p, override=True)
            print(f"[ENV] loaded {p}")
            return
    print("[ENV] .env not found in", candidates)


load_env()

# делаем YouTube переменные необязательными (мы договорились вернуться к ним позже)
if not os.getenv("GEMINI_API_KEY"):
    print("[WARN] GEMINI_API_KEY is not set — AI responses will use safe fallbacks.")

# ---------------------------
# 2) Создаём приложение + CORS
# ---------------------------
app = FastAPI(title="MLBB Mini App API", version="0.2.0")

origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# 3) Инициализируем БД
# ---------------------------
init_db()

# ---------------------------
# 4) Pydantic схемы
# ---------------------------


class HeroPick(BaseModel):
    hero: str


class HeroPostRequest(BaseModel):
    hero: str
    video_url: str


class ComposeRequest(BaseModel):
    # если не передан — выберем случайного неиспользованного
    hero: Optional[str] = None


class ComposeResponse(BaseModel):
    hero: str
    video_title: str
    video_url: str
    post_text: str


class CounterPickReq(BaseModel):
    enemy: str
    lane: Optional[str] = None
    role: Optional[str] = None


class TierListReq(BaseModel):
    role: Optional[str] = None
    lane: Optional[str] = None
    skill: Optional[str] = None     # e.g., "Legend+", "Mythic"
    note: Optional[str] = None


class QuizGenReq(BaseModel):
    topic: Optional[str] = None
    # удобнее и надёжнее, чем pattern
    difficulty: Literal["easy", "medium", "hard"] = "easy"


class QuizCheckReq(BaseModel):
    quiz_id: int
    answer_index: int


class PatchReq(BaseModel):
    notes_text: str

# ---------------------------
# 5) Служебные/диагностические
# ---------------------------


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/debug/env")
def debug_env():
    return {
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        "gemini_key_set": bool(os.getenv("GEMINI_API_KEY")),
        "youtube_key_set": bool(os.getenv("YOUTUBE_API_KEY")),
        "youtube_channel_id": os.getenv("YOUTUBE_CHANNEL_ID"),
        "cors_origins": [o.strip() for o in origins if o.strip()],
        "heroes_count": len(HEROES),
    }


@app.get("/debug/db")
def debug_db():
    try:
        last = list_quizzes(limit=5)
        return {
            "db_path": get_db_path(),
            "last_quizzes": [
                {"id": q.id, "question": q.question} for q in last
            ],
        }
    except Exception as e:
        print("[ERROR] /debug/db:", e)
        raise HTTPException(500, "DB diagnostics failed")

# ---------------------------
# 6) Герои: остаток/пик/маркировка
# ---------------------------


@app.get("/heroes/remaining")
def heroes_remaining():
    try:
        used: List[str] = get_used_heroes()
        used_set = set(used)
        remain = [h for h in HEROES if h not in used_set]
        return {"remaining": remain, "used_count": len(used_set), "total": len(HEROES)}
    except Exception as e:
        print("[ERROR] /heroes/remaining:", e)
        raise HTTPException(500, "Failed to read heroes from DB")


@app.post("/heroes/pick", response_model=HeroPick)
def pick_hero():
    try:
        used: List[str] = get_used_heroes()
        used_set = set(used)
        remaining = [h for h in HEROES if h not in used_set]
        if not remaining:
            raise HTTPException(409, "All heroes used. Reset needed.")
        hero = random.choice(remaining)
        return {"hero": hero}
    except HTTPException:
        raise
    except Exception as e:
        print("[ERROR] /heroes/pick:", e)
        raise HTTPException(500, "DB error")


@app.post("/heroes/mark-used")
def mark_used(body: HeroPick):
    try:
        ts = datetime.now(timezone.utc).isoformat()
        mark_hero_used(body.hero, ts)
        return {"ok": True, "hero": body.hero, "posted_at": ts}
    except Exception as e:
        print("[ERROR] /heroes/mark-used:", e)
        raise HTTPException(500, "DB error")

# ---------------------------
# 7) Пост от ИИ (только текст)
# ---------------------------


@app.post("/ai/hero-post")
def ai_hero_post(body: HeroPostRequest):
    try:
        text = generate_hero_post(body.hero)
        return {"hero": body.hero, "post_text": f"{text}\n{body.video_url}"}
    except Exception as e:
        print("[ERROR] /ai/hero-post:", e)
        raise HTTPException(502, "AI generation failed")

# ---------------------------
# 8) Counter-pick Q&A
# ---------------------------


@app.post("/ai/counter-pick")
def ai_counter_pick(body: CounterPickReq):
    text = generate_counter_pick(body.enemy, body.lane, body.role)
    return {"enemy": body.enemy, "answer": text}

# ---------------------------
# 9) Tier List
# ---------------------------


@app.post("/ai/tier-list")
def ai_tier_list(body: TierListReq):
    data = generate_tier_list(
        role=body.role, lane=body.lane, skill=body.skill, note=body.note
    )
    return data

# ---------------------------
# 10) Quiz: generate + check
# ---------------------------


@app.post("/quiz/generate")
def quiz_generate(body: QuizGenReq):
    data = generate_quiz(topic=body.topic, difficulty=body.difficulty)
    quiz_id = save_quiz(
        question=data["question"],
        options=data["options"],
        correct_index=int(data["correct_index"]),
        explanation=data.get("explanation"),
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    return {"quiz_id": quiz_id, **data}


@app.post("/quiz/check")
def quiz_check(body: QuizCheckReq):
    import json
    q = get_quiz(body.quiz_id)
    if not q:
        raise HTTPException(404, "Quiz not found")
    options = json.loads(q.options_json)
    correct = int(body.answer_index) == int(q.correct_index)
    return {
        "correct": correct,
        "correct_index": q.correct_index,
        "explanation": q.explanation or "",
        "question": q.question,
        "options": options,
    }


@app.get("/quiz/{quiz_id}")
def quiz_get(quiz_id: int):
    import json
    q = get_quiz(quiz_id)
    if not q:
        raise HTTPException(404, "Quiz not found")
    return {
        "id": q.id,
        "question": q.question,
        "options": json.loads(q.options_json),
        "correct_index": q.correct_index,
        "explanation": q.explanation or "",
        "created_at": q.created_at,
    }

# ---------------------------
# 11) Daily Challenge
# ---------------------------


@app.post("/daily/generate")
def daily_generate():
    today = datetime.now(timezone.utc).date().isoformat()
    existing = get_daily_challenge(today)
    if existing:
        return {"date": today, "text": existing.text, "cached": True}
    text = generate_daily_challenge()
    save_daily_challenge(today, text, datetime.now(timezone.utc).isoformat())
    return {"date": today, "text": text, "cached": False}

# ---------------------------
# 12) Patch Explainer
# ---------------------------


@app.post("/ai/patch-explain")
def ai_patch_explain(body: PatchReq):
    text = explain_patch(body.notes_text)
    return {"summary": text}


# ---------------------------
# 13) (опционально) YouTube — вернёмся позже
# ---------------------------
# Если хочешь оставить маршрут, но сделать его безопасным при отсутствии ключей, можно так:
try:
    from youtube_client import (
        find_video_for_hero,
        youtube_ping_global,
        youtube_channel_ping,
    )
    HAS_YT = True
except Exception:
    HAS_YT = False


class ComposeRequest(BaseModel):
    hero: Optional[str] = None


class ComposeResponse(BaseModel):
    hero: str
    video_title: str
    video_url: str
    post_text: str


if HAS_YT and os.getenv("YOUTUBE_API_KEY") and os.getenv("YOUTUBE_CHANNEL_ID"):
    @app.post("/post/compose", response_model=ComposeResponse)
    def compose_post(body: ComposeRequest):
        try:
            # 1) выбираем героя
            hero = body.hero
            if not hero:
                used = set(get_used_heroes())
                remaining = [h for h in HEROES if h not in used]
                if not remaining:
                    raise HTTPException(409, "All heroes used. Reset needed.")
                hero = random.choice(remaining)
            # 2) находим видео по герою
            video = find_video_for_hero(hero)
            if not video:
                raise HTTPException(404, f"No video found for hero {hero}")
            # 3) генерим текст
            post_text = generate_hero_post(hero) + f"\n{video['url']}"
            return {
                "hero": hero,
                "video_title": video["title"],
                "video_url": video["url"],
                "post_text": post_text,
            }
        except HTTPException:
            raise
        except Exception as e:
            print("[ERROR] /post/compose:", e)
            raise HTTPException(500, "Compose failed")
else:
    @app.post("/post/compose")
    def compose_post_unavailable(_: ComposeRequest):
        raise HTTPException(503, "YouTube integration is not configured yet")


class TGVerifyReq(BaseModel):
    init_data: str


def _verify_tg_init_data(init_data: str) -> dict:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise HTTPException(503, "TELEGRAM_BOT_TOKEN is not configured")
    # Parse URL-encoded init_data string into dict of first values
    q = parse_qs(init_data, keep_blank_values=True)
    data = {k: v[0] for k, v in q.items()}
    recv_hash = data.pop("hash", None)
    if not recv_hash:
        raise HTTPException(400, "Missing hash in init_data")
    # Build data_check_string
    pairs = [f"{k}={data[k]}" for k in sorted(data.keys())]
    data_check_string = "\n".join(pairs)
    secret_key = hashlib.sha256(token.encode()).digest()
    calc_hash = hmac.new(secret_key, msg=data_check_string.encode(), digestmod=hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calc_hash, recv_hash):
        raise HTTPException(401, "Invalid init_data hash")
    return data


@app.post("/tg/verify")
def tg_verify(body: TGVerifyReq):
    try:
        data = _verify_tg_init_data(body.init_data)
        # user comes as JSON string per Telegram spec
        import json as _json
        user_raw = data.get("user")
        user = _json.loads(user_raw) if user_raw else None
        return {"ok": True, "user": user, "auth_date": data.get("auth_date"), "query_id": data.get("query_id")}
    except HTTPException:
        raise
    except Exception as e:
        print("[ERROR] /tg/verify:", e)
        raise HTTPException(500, "Verification failed")

@app.get("/debug/ai-ping")
def debug_ai_ping():
    if not os.getenv("GEMINI_API_KEY"):
        return {"ok": False, "reason": "no_api_key"}
    try:
        import google.generativeai as genai  # type: ignore
        model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        resp = genai.GenerativeModel(model).generate_content("ok")
        txt = (getattr(resp, "text", "") or "").strip().lower()
        return {"ok": txt == "ok", "model": model}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/youtube/video-for-hero")
def youtube_video_for_hero(body: HeroPick):
    if not HAS_YT or not os.getenv("YOUTUBE_API_KEY"):
        raise HTTPException(503, "YouTube API key not configured")
    try:
        video = find_video_for_hero(body.hero)
        if not video:
            raise HTTPException(404, f"No video found for hero {body.hero}")
        return video
    except HTTPException:
        raise
    except Exception as e:
        print("[ERROR] /youtube/video-for-hero:", e)
        raise HTTPException(500, "YouTube lookup failed")

@app.get("/debug/youtube-ping")
def debug_youtube_ping():
    if not HAS_YT or not os.getenv("YOUTUBE_API_KEY"):
        raise HTTPException(503, "YouTube API key not configured")
    try:
        items = youtube_ping_global()
        return {"ok": True, "items": items[:5]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


class YTPingReq(BaseModel):
    hero: str


@app.post("/debug/youtube-channel-ping")
def debug_youtube_channel_ping(body: YTPingReq):
    if not HAS_YT or not os.getenv("YOUTUBE_API_KEY") or not os.getenv("YOUTUBE_CHANNEL_ID"):
        raise HTTPException(503, "YouTube channel not configured")
    try:
        items = youtube_channel_ping(body.hero)
        return {"ok": True, "items": items}
    except Exception as e:
        return {"ok": False, "error": str(e)}

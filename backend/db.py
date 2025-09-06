from sqlmodel import SQLModel, Field, Session, create_engine, select
from typing import Optional, List
from pathlib import Path
import json

# Путь к БД
DB_DIR = Path(__file__).parent
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "data.sqlite3"

# Важно для uvicorn+Windows
engine = create_engine(
    f"sqlite:///{DB_PATH}",
    echo=False,
    connect_args={"check_same_thread": False},
)

# ===== Модели =====


class UsedHero(SQLModel, table=True):
    hero: str = Field(primary_key=True)
    posted_at: Optional[str] = None  # ISO-строка


class QuizQuestion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    question: str
    options_json: str        # храним 4 варианта в JSON-строке
    correct_index: int       # 0..3
    explanation: Optional[str] = None  # краткая причина/объяснение
    created_at: Optional[str] = None   # ISO-строка


class DailyChallenge(SQLModel, table=True):
    date: str = Field(primary_key=True)  # YYYY-MM-DD
    text: str
    created_at: Optional[str] = None

# ===== Инициализация =====


def init_db():
    SQLModel.metadata.create_all(engine)

# ===== Герои =====


def get_used_heroes() -> List[str]:
    with Session(engine) as s:
        rows = s.exec(select(UsedHero.hero)).all()
    # приводим к List[str]
    result: List[str] = []
    for r in rows:
        result.append(r[0] if isinstance(r, tuple) else r)
    return result


def mark_hero_used(hero: str, ts: str):
    with Session(engine) as s:
        s.add(UsedHero(hero=hero, posted_at=ts))
        s.commit()


def reset_heroes():
    with Session(engine) as s:
        s.exec("DELETE FROM usedhero")
        s.commit()

# ===== Квизы =====


def save_quiz(question: str, options: List[str], correct_index: int, explanation: Optional[str], created_at: str) -> int:
    q = QuizQuestion(
        question=question,
        options_json=json.dumps(options, ensure_ascii=False),
        correct_index=correct_index,
        explanation=explanation,
        created_at=created_at,
    )
    with Session(engine) as s:
        s.add(q)
        s.commit()
        s.refresh(q)
        return q.id


def get_quiz(quiz_id: int) -> Optional[QuizQuestion]:
    with Session(engine) as s:
        q = s.get(QuizQuestion, quiz_id)
        return q


def list_quizzes(limit: int = 10) -> List[QuizQuestion]:
    with Session(engine) as s:
        stmt = select(QuizQuestion).order_by(QuizQuestion.id.desc()).limit(limit)
        return list(s.exec(stmt))

# ===== Daily Challenge =====


def save_daily_challenge(date_str: str, text: str, created_at: str):
    dc = DailyChallenge(date=date_str, text=text, created_at=created_at)
    with Session(engine) as s:
        s.add(dc)
        s.commit()


def get_daily_challenge(date_str: str) -> Optional[DailyChallenge]:
    with Session(engine) as s:
        dc = s.get(DailyChallenge, date_str)
        return dc


def get_db_path() -> str:
    """Return absolute path to the SQLite DB file for diagnostics."""
    return str(DB_PATH.resolve())

import os
import google.generativeai as genai
from typing import List, Dict, Optional

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# ===== Общий помощник =====


def _call_gemini(prompt: str, system_hint: str) -> str:
    if not GEMINI_API_KEY:
        return ""
    try:
        model = genai.GenerativeModel(
            GEMINI_MODEL, system_instruction=system_hint)
        resp = model.generate_content(prompt)
        return (getattr(resp, "text", "") or "").strip()
    except Exception as e:
        print("[Gemini ERROR]", e)
        return ""

# ===== Герой-пост (как было) =====


def generate_hero_post(hero: str) -> str:
    system = (
        "Ты — редактор русскоязычного Telegram-канала по MLBB. Пиши короткие, энергичные посты."
    )
    prompt = f"""
Герой: {hero}
Задача: напиши 1–2 коротких предложения на русском о приёме, трюке или полезном совете с этим героем в Mobile Legends.
Стиль: живой, мотивирующий, как подпись к видео в соцсетях.
Не используй хэштеги. Не придумывай новых умений.
"""
    text = _call_gemini(prompt, system)
    if not text:
        text = f"Есть крутой приём с героем {hero}! Смотри видео ниже 👇"
    return text

# ===== Counter-pick Q&A =====


def generate_counter_pick(enemy: str, lane: Optional[str] = None, role: Optional[str] = None) -> str:
    system = "Ты — эксперт по MLBB. Даёшь практичные советы и контр-пики на русском языке."
    prompt = f"""
Вопрос: как контрить героя {enemy} в MLBB?
Укажи 3–6 контр-пиков (герои), по 1–2 ключевых совета против него и 1–2 предмета/эмблемы/боевых заклинаний, которые особенно полезны.
{f"Линия/позиция: {lane}" if lane else ""}
{f"Роль: {role}" if role else ""}

Формат ответа: короткие маркированные пункты (— ...). Без хэштегов. Без выдуманных умений.
"""
    text = _call_gemini(prompt, system)
    if not text:
        text = f"Против {enemy} старайся пикать героев с жёстким контролем и сохраняй важные умения на её вход. Анти-хилл и прерывание — ключевые инструменты."
    return text

# ===== Tier List =====


def generate_tier_list(role: Optional[str] = None, lane: Optional[str] = None, skill: Optional[str] = None, note: Optional[str] = None) -> Dict:
    system = "Ты — аналитик MLBB. Формируешь tier list в JSON для Telegram Mini App."
    prompt = f"""
Сформируй актуальный tier list по MLBB в JSON с ключами: "S", "A", "B" (массивы имён героев) и "notes" (строка).
{f"Роль/класс: {role}" if role else ""}
{f"Линия: {lane}" if lane else ""}
{f"Уровень игры: {skill}" if skill else ""}
{f"Контекст/заметки: {note}" if note else ""}

Возвращай ТОЛЬКО валидный JSON, без пояснений, вроде:
{{"S":["...","..."],"A":["..."],"B":["..."],"notes":"..."}}
"""
    raw = _call_gemini(prompt, system)
    import json
    try:
        data = json.loads(raw)
        # минимальная валидация
        for k in ["S", "A", "B"]:
            data.setdefault(k, [])
        data.setdefault("notes", "")
        return data
    except Exception:
        # fallback: простой список
        return {"S": [], "A": [], "B": [], "notes": raw or "Не удалось распарсить JSON."}

# ===== Quiz =====


def generate_quiz(topic: Optional[str] = None, difficulty: str = "easy") -> Dict:
    system = "Ты — тренер MLBB. Генерируешь тестовые вопросы (multiple choice) на русском."
    prompt = f"""
Сгенерируй один вопрос викторины по MLBB на русском.
Тема: {topic or "общие механики, герои, предметы"}.
Сложность: {difficulty}.
Формат ответа строго JSON:
{{
  "question": "Текст вопроса?",
  "options": ["Вариант 1","Вариант 2","Вариант 3","Вариант 4"],
  "correct_index": 0,
  "explanation": "Короткое объяснение, почему ответ верный."
}}
Без дополнительного текста — только JSON.
"""
    raw = _call_gemini(prompt, system)
    import json
    try:
        data = json.loads(raw)
        # валидация
        if not isinstance(data.get("options"), list) or len(data["options"]) != 4:
            raise ValueError("need 4 options")
        return data
    except Exception:
        # fallback
        return {
            "question": "Что даёт предмет 'Necklace of Durance'?",
            "options": ["Анти-хилл", "Щит", "Скорость атаки", "Вампиризм"],
            "correct_index": 0,
            "explanation": "Предмет снижает лечение противника (anti-heal).",
        }

# ===== Daily Challenge =====


def generate_daily_challenge() -> str:
    system = "Ты — креативный менеджер MLBB. Придумываешь челленджи для игроков."
    prompt = """
Придумай один ежедневный челлендж для MLBB на русском.
Формат: 1–2 предложения, конкретная цель, без хэштегов.
Примеры: "Выиграй матч, купив хотя бы 3 защитных предмета"; "Сыграй без Recall"; "Сделай 3 успешных ганка до 7 минуты".
"""
    text = _call_gemini(prompt, system)
    return text or "Выиграй матч, не умирая более 2 раз!"

# ===== Patch Explainer =====


def explain_patch(notes_text: str) -> str:
    system = "Ты — аналитик патчноутов MLBB. Объясняешь изменения простым языком."
    prompt = f"""
Вот текст патчноутов (могут быть сокращены или сырыми):

{notes_text}

Сделай краткое объяснение по пунктам: кто усилен/ослаблен, ключевые изменения предметов/эмблем, что это значит для меты. Пиши по-русски, списком из 5–10 пунктов.
"""
    text = _call_gemini(prompt, system)
    return text or "Нет явных изменений."

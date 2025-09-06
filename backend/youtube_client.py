import os
import json
from typing import Optional, Dict, List

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")
YOUTUBE_STRICT_CHANNEL = os.getenv("YOUTUBE_STRICT_CHANNEL", "true").lower() in ("1", "true", "yes")

_youtube_service = None


def _get_service():
    global _youtube_service
    if _youtube_service is not None:
        return _youtube_service
    if not YOUTUBE_API_KEY:
        raise RuntimeError("Missing YOUTUBE_API_KEY in .env")
    _youtube_service = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    return _youtube_service


def _search_channel(yt, hero: str, order: str):
    return (
        yt.search()
        .list(
            part="snippet",
            channelId=YOUTUBE_CHANNEL_ID,
            q=hero,
            type="video",
            order=order,
            maxResults=5,
        )
        .execute()
    )


def _search_global(yt, q: str, order: str):
    return (
        yt.search()
        .list(
            part="snippet",
            q=q,
            type="video",
            order=order,
            maxResults=5,
        )
        .execute()
    )


def find_video_for_hero(hero: str) -> Optional[Dict[str, str]]:
    yt = _get_service()
    try:
        items: List[dict] = []
        if YOUTUBE_CHANNEL_ID:
            data = _search_channel(yt, hero, "relevance")
            items = data.get("items", [])
            if not items:
                data = _search_channel(yt, hero, "date")
                items = data.get("items", [])

        if not items and not YOUTUBE_STRICT_CHANNEL:
            data = _search_global(yt, hero, "relevance")
            items = data.get("items", [])
            if not items:
                data = _search_global(yt, hero, "date")
                items = data.get("items", [])

        for it in items:
            if it.get("id", {}).get("kind") != "youtube#video":
                continue
            vid = it.get("id", {}).get("videoId")
            snip = it.get("snippet", {})
            if not vid:
                continue
            return {
                "title": snip.get("title", ""),
                "url": f"https://www.youtube.com/watch?v={vid}",
                "publishedAt": snip.get("publishedAt", ""),
            }
        return None

    except HttpError as e:
        try:
            err = json.loads(e.content.decode())
        except Exception:
            err = {"raw": str(e)}
        print("[YouTube API error]", err)
        raise RuntimeError(err)


def youtube_ping_global():
    yt = _get_service()
    try:
        data = _search_global(yt, "Mobile Legends hero guide", "relevance")
        out = []
        for it in data.get("items", []):
            kid = it.get("id", {})
            snip = it.get("snippet", {})
            out.append({
                "kind": kid.get("kind"),
                "videoId": kid.get("videoId"),
                "title": snip.get("title"),
            })
        return out
    except HttpError as e:
        try:
            err = json.loads(e.content.decode())
        except Exception:
            err = {"raw": str(e)}
        print("[YouTube API error]", err)
        raise RuntimeError(err)


def youtube_channel_ping(hero: str):
    if not YOUTUBE_CHANNEL_ID:
        raise RuntimeError("Missing YOUTUBE_CHANNEL_ID in .env")
    yt = _get_service()
    try:
        data = _search_channel(yt, hero, "relevance")
        out = []
        for it in data.get("items", []):
            kid = it.get("id", {})
            snip = it.get("snippet", {})
            out.append({
                "kind": kid.get("kind"),
                "videoId": kid.get("videoId"),
                "title": snip.get("title"),
            })
        return out
    except HttpError as e:
        try:
            err = json.loads(e.content.decode())
        except Exception:
            err = {"raw": str(e)}
        print("[YouTube API error]", err)
        raise RuntimeError(err)


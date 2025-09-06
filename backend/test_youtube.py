# test_youtube.py
from pathlib import Path
from dotenv import load_dotenv
from googleapiclient.discovery import build
import os

load_dotenv(dotenv_path=Path("backend/.env"), override=True)

key = os.getenv("YOUTUBE_API_KEY")
cid = os.getenv("YOUTUBE_CHANNEL_ID")
assert key, "No YOUTUBE_API_KEY"
assert cid, "No YOUTUBE_CHANNEL_ID (must be UC...)"

yt = build("youtube", "v3", developerKey=key)
resp = yt.search().list(
    part="snippet",
    channelId=cid,
    q="Khufra",
    type="video",
    order="relevance",
    maxResults=1,
).execute()

print("items:", len(resp.get("items", [])))
if resp.get("items"):
    it = resp["items"][0]
    print("OK:", it["snippet"]["title"],
          "https://www.youtube.com/watch?v=" + it["id"]["videoId"])

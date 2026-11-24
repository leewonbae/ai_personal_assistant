"""일자별 중복 없는 기사 및 키워드 집계 보관."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from keywords import title_keywords

DB_PATH = Path(__file__).resolve().parent / "news.db"


@contextmanager
def connect():
    db = sqlite3.connect(DB_PATH, timeout=10)
    try:
        db.execute("PRAGMA busy_timeout=10000")
        with db:
            yield db
    finally:
        db.close()


def initialize():
    with connect() as db:
        db.execute("CREATE TABLE IF NOT EXISTS articles (day TEXT NOT NULL, source TEXT NOT NULL, link TEXT NOT NULL, title TEXT NOT NULL, PRIMARY KEY(day, source, link))")
        db.execute("CREATE TABLE IF NOT EXISTS keyword_counts (day TEXT NOT NULL, keyword TEXT NOT NULL, count INTEGER NOT NULL, PRIMARY KEY(day, keyword))")


def record(day, source, items):
    with connect() as db:
        for item in items:
            if not item.get("link") or not item.get("title"):
                continue
            cursor = db.execute("INSERT OR IGNORE INTO articles (day, source, link, title) VALUES (?, ?, ?, ?)", (day, source, item["link"], item["title"]))
            if cursor.rowcount:
                for word, count in title_keywords(item["title"]).items():
                    db.execute("INSERT INTO keyword_counts VALUES (?, ?, ?) ON CONFLICT(day, keyword) DO UPDATE SET count=count+excluded.count", (day, word, count))


def dates():
    with connect() as db:
        return [row[0] for row in db.execute("SELECT DISTINCT day FROM articles ORDER BY day DESC")]


def top(day, limit=10):
    with connect() as db:
        return db.execute("SELECT keyword, count FROM keyword_counts WHERE day=? ORDER BY count DESC, keyword ASC LIMIT ?", (day, limit)).fetchall()

"""앱 프로세스에서 공유하는 뉴스 수집 및 최신 결과 보관."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from threading import Event, Lock, Thread
import logging
import news_store
from rss_client import get_news

SOURCES = {
    "한국경제": "https://www.hankyung.com/feed/finance",
    "경향신문": "https://www.khan.co.kr/rss/rssdata/economy_news.xml",
    "뉴시스 금융": "https://nwww.newsis.com/RSS/bank.xml",
    "한국은행 경제통계": "https://www.bok.or.kr/portal/bbs/B0000501/news.rss?menuNo=201264",
}
INTERVAL_SECONDS = 600


class NewsCollector:
    def __init__(self):
        self.lock = Lock()
        self.wake = Event()
        self.refreshing = True
        self.results = {name: {"items": [], "updated_at": None, "error": None} for name in SOURCES}

    def snapshot(self):
        with self.lock:
            return deepcopy(self.results)

    def status(self):
        with self.lock:
            return self.refreshing

    def request_refresh(self):
        with self.lock:
            if self.refreshing:
                return False
            self.refreshing = True
            self.wake.set()
            return True

    def refresh(self):
        for name, url in SOURCES.items():
            try:
                items = get_news(url, 10, free_hankyung_only=(name == "한국경제"))
                if not items:
                    raise ValueError("수집된 기사가 없습니다")
                now = datetime.now(timezone(timedelta(hours=9)))
                news_store.record(now.strftime("%Y-%m-%d"), name, items)
                updated_at = now.strftime("%Y-%m-%d %H:%M:%S KST")
                with self.lock:
                    self.results[name] = {"items": items, "updated_at": updated_at, "error": None}
            except Exception:
                logging.exception("뉴스 수집 실패: %s", name)
                with self.lock:
                    self.results[name]["error"] = "최신 수집에 실패했습니다. 이전 수집 결과가 있으면 표시합니다."

    def run(self):
        while True:
            with self.lock:
                self.refreshing = True
                self.wake.clear()
            try:
                self.refresh()
            finally:
                with self.lock:
                    self.refreshing = False
            self.wake.wait(INTERVAL_SECONDS)


_collector = None
_collector_lock = Lock()


def get_collector():
    global _collector
    with _collector_lock:
        if _collector is None:
            news_store.initialize()
            _collector = NewsCollector()
            Thread(target=_collector.run, name="news-collector", daemon=True).start()
        return _collector

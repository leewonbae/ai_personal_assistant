import feedparser
import requests
import json
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from urllib.parse import urlsplit, urljoin


class StructuredDataParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.collecting = False
        self.parts = []
        self.scripts = []
        self.image = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta" and attrs.get("property", "").lower() == "og:image":
            self.image = attrs.get("content", "") or self.image
        if tag == "img" and not self.image:
            self.image = attrs.get("src", "")
        if tag == "script" and attrs.get("type", "").lower() == "application/ld+json":
            self.collecting = True
            self.parts = []

    def handle_data(self, data):
        if self.collecting:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.collecting:
            self.scripts.append("".join(self.parts))
            self.collecting = False


def safe_image(url, allowed_hosts):
    try:
        parsed = urlsplit(url)
        if parsed.scheme == "https" and parsed.hostname in allowed_hosts and parsed.port in (None, 443) and not parsed.username and not parsed.password:
            return url
    except ValueError:
        pass
    return ""


def hankyung_article(url):
    """Accept only articles explicitly marked free; unknown results are excluded."""
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != "www.hankyung.com" or not parsed.path.startswith("/article/") or parsed.username or parsed.password:
        return False, ""
    try:
        response = requests.get(url, headers={"User-Agent": "AI-Personal-Assistant/0.1"}, timeout=5, allow_redirects=False)
        response.raise_for_status()
        if response.status_code != 200:
            return False, ""
        parser = StructuredDataParser()
        parser.feed(response.text)
        flags = []
        def collect(value):
            if isinstance(value, dict):
                kind = value.get("@type", [])
                if isinstance(kind, str):
                    kind = [kind]
                if any(k in ("Article", "NewsArticle", "ReportageNewsArticle") for k in kind):
                    flags.append(value.get("isAccessibleForFree"))
                for child in value.values():
                    collect(child)
            elif isinstance(value, list):
                for child in value:
                    collect(child)
        for script in parser.scripts:
            try:
                collect(json.loads(script))
            except (ValueError, TypeError):
                continue
        return bool(flags) and all(flag is True for flag in flags), safe_image(parser.image, {"img.hankyung.com"})
    except (requests.RequestException, ValueError):
        return False, ""


def is_free_hankyung_article(url):
    return hankyung_article(url)[0]


def khan_image(url):
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != "www.khan.co.kr" or parsed.port not in (None, 443) or parsed.username or parsed.password:
        return ""
    try:
        response = requests.get(url, headers={"User-Agent": "AI-Personal-Assistant/0.1"}, timeout=5, allow_redirects=False)
        if response.status_code != 200:
            return ""
        parser = StructuredDataParser()
        parser.feed(response.text)
        return safe_image(urljoin(url, parser.image), {"img.khan.co.kr"})
    except (requests.RequestException, ValueError):
        return ""


def rss_image(entry):
    parser = StructuredDataParser()
    parser.feed(entry.get("summary", ""))
    return safe_image(parser.image, {"image.newsis.com", "img1.newsis.com"})

def get_news(rss_url: str, limit: int = 10, *, free_hankyung_only: bool = False) -> list:
    headers = {
        "User-Agent": "AI-Personal-Assistant/0.1"
    }

    response = requests.get(
        rss_url,
        headers=headers,
        timeout=10
    )

    print("HTTP 상태:", response.status_code)
    print("Content-Type:", response.headers.get("Content-Type"))

    response.raise_for_status()

    feed = feedparser.parse(response.content)
    
    print("HTTP 상태:", feed.get("status"))
    print("파싱 오류:", feed.get("bozo_exception"))
    print("기사 개수:", len(feed.entries))
    
    if feed.bozo and not feed.entries:
        raise ValueError("RSS 데이터를 읽지 못했습니다.")

    news_list = []

    entries = feed.entries[:20] if free_hankyung_only else feed.entries[:limit]
    images = {}
    if free_hankyung_only:
        with ThreadPoolExecutor(max_workers=5) as executor:
            checks = list(executor.map(hankyung_article, (entry.get("link", "") for entry in entries)))
        images = {entry.get("link", ""): image for entry, (free, image) in zip(entries, checks) if free}
        entries = [entry for entry, (free, _) in zip(entries, checks) if free][:limit]
    elif urlsplit(rss_url).hostname == "www.khan.co.kr":
        with ThreadPoolExecutor(max_workers=5) as executor:
            images = dict(zip((entry.get("link", "") for entry in entries), executor.map(khan_image, (entry.get("link", "") for entry in entries))))
    for entry in entries:
        news = {
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "published": entry.get("published", ""),
            "image": images.get(entry.get("link", ""), "") or (rss_image(entry) if urlsplit(rss_url).hostname == "nwww.newsis.com" else "")
        }

        news_list.append(news)

    return news_list

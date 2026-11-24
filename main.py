from fastapi import FastAPI
from rss_client import get_news as fetch_news
app = FastAPI()
@app.get("/")
def root():
    return {"message": "AI Personal Assistant API"}


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/get_news")
def get_news():
    hankyung_news = fetch_news(
        "https://www.hankyung.com/feed/finance", 10
    )

    khan_news = fetch_news(
        "https://www.khan.co.kr/rss/rssdata/economy_news.xml", 10
    )

    return {
        "status": "ok",
        "news": {
            "hankyung": hankyung_news,
            "khan": khan_news
        }
    }

import streamlit as st
from html import escape
from rss_client import safe_image

IMAGE_HOSTS = {"img.hankyung.com", "img.khan.co.kr", "image.newsis.com", "img1.newsis.com"}


def render_article(item):
    image = safe_image(item.get("image") or "", IMAGE_HOSTS)
    thumbnail, content = st.columns([1, 5], vertical_alignment="center", gap="medium")
    with thumbnail:
        if image:
            st.html(f'<div style="width:120px;max-width:100%;height:80px;overflow:hidden;border-radius:6px;background:#f0f2f6"><img src="{escape(image, quote=True)}" alt="기사 대표 이미지" style="width:100%;height:100%;object-fit:cover"></div>')
        else:
            st.html('<div style="width:120px;max-width:100%;height:80px;border-radius:6px;background:#f0f2f6;display:flex;align-items:center;justify-content:center;color:#666;font-size:12px">이미지 없음</div>')
    with content:
        render_article_text(item)


def render_article_text(item):
    st.write(item.get("title") or "제목 없음")
    st.caption(item.get("published") or "발행 시각 정보 없음")
    if item.get("link", "").startswith(("https://", "http://")):
        st.link_button("기사 보기", item["link"])
    else:
        st.caption("기사 링크 없음")


@st.fragment(run_every=3)
def render_news(collector):
    st.header("오늘의 뉴스")
    st.caption("뉴스는 10분마다 갱신됩니다. 한경은 무료로 확인된 기사만 표시합니다.")
    busy = collector.status()
    if st.button("🔄 지금 새로고침", disabled=busy, help="모든 출처를 백그라운드에서 다시 수집합니다."):
        collector.request_refresh()
        st.rerun()
    if busy:
        st.info("뉴스를 수집하고 있습니다. 이전 결과는 계속 볼 수 있습니다.")
    results = collector.snapshot()
    for source, tab in zip(results, st.tabs(list(results))):
        with tab:
            result = results[source]
            if result["updated_at"]:
                st.caption("마지막 성공 수집: " + result["updated_at"])
            if result["error"]:
                st.warning(result["error"])
            if not result["items"] and not result["error"]:
                st.info("뉴스를 처음 수집하고 있습니다. 잠시 후 다시 확인해 주세요.")
            for index, item in enumerate(result["items"]):
                if index:
                    st.divider()
                render_article(item)

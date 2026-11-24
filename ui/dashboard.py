import streamlit as st
from ui.news import render_news
from ui.keywords import render_keywords


def render_dashboard(collector, login_enabled=True):
    with st.sidebar:
        st.title("📋 비서")
        st.caption(f"{st.session_state.user['username']}님" if login_enabled else "개발 모드 · 로그인 비활성화")
        if st.button("홈", use_container_width=True):
            st.session_state.page = "home"
        if st.button("오늘 뉴스 확인", use_container_width=True):
            st.session_state.page = "news"
        if st.button("날짜별 키워드", use_container_width=True):
            st.session_state.page = "keywords"
        st.divider()
        if login_enabled and st.button("로그아웃", use_container_width=True):
            for key in ("user", "page"):
                st.session_state.pop(key, None)
            st.rerun()
    st.title("비서")
    st.divider()
    if st.session_state.get("page", "home") == "news":
        render_news(collector)
    elif st.session_state.get("page") == "keywords":
        render_keywords()
    else:
        st.header("안녕하세요")
        st.write("왼쪽 메뉴에서 오늘 뉴스 확인을 눌러 최신 경제 뉴스를 확인하세요.")

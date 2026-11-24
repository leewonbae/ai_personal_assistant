import streamlit as st
import news_store


def render_keywords():
    st.header("날짜별 뉴스 키워드")
    st.caption("수집일 기준 제목의 명사와 영문 약어 출현 횟수입니다. 같은 기사는 같은 날 한 번만 집계합니다.")
    days = news_store.dates()
    if not days:
        st.info("아직 수집된 키워드가 없습니다. 첫 뉴스 수집이 끝난 뒤 다시 확인해 주세요.")
        return
    day = st.selectbox("수집 날짜", days)
    rows = news_store.top(day)
    if rows:
        st.table([{"순위": i, "키워드": word, "출현 횟수": count} for i, (word, count) in enumerate(rows, 1)])
        st.caption("한국어 형태소 분석과 일반 표현 제외 규칙을 적용합니다. 일부 단어는 잘못 분리되거나 남을 수 있습니다.")
    else:
        st.info("해당 날짜에 표시할 키워드가 없습니다.")

import streamlit as st
import accounts


def render_auth():
    st.title("비서")
    st.caption("로그인하여 비서의 기능을 이용하세요.")
    if st.session_state.get("auth_page", "login") == "login":
        render_login()
    else:
        render_signup()


def render_login():
    if st.session_state.pop("signup_complete", False):
        st.success("회원가입이 완료되었습니다. 로그인해 주세요.")
    with st.form("login"):
        username = st.text_input("아이디", max_chars=32)
        password = st.text_input("비밀번호", type="password", max_chars=128)
        submitted = st.form_submit_button("로그인", use_container_width=True)
    if submitted:
        user = accounts.authenticate(username.strip(), password)
        if user:
            st.session_state.user = user
            st.rerun()
        st.error("아이디 또는 비밀번호가 올바르지 않거나 잠시 로그인이 제한되었습니다.")
    if st.button("회원가입", use_container_width=True):
        st.session_state.auth_page = "signup"
        st.rerun()


def render_signup():
    st.subheader("회원가입")
    with st.form("signup"):
        username = st.text_input("사용할 아이디", max_chars=32, help="영문, 숫자, 밑줄 4~32자")
        password = st.text_input("사용할 비밀번호", type="password", max_chars=128, help="10~128자")
        confirm = st.text_input("비밀번호 확인", type="password", max_chars=128)
        submitted = st.form_submit_button("회원가입", use_container_width=True)
    if submitted:
        if password != confirm:
            st.error("비밀번호가 일치하지 않습니다.")
        else:
            ok, message = accounts.register(username.strip(), password)
            if ok:
                st.session_state.auth_page = "login"
                st.session_state.signup_complete = True
                st.rerun()
            st.error(message)
    if st.button("로그인으로 돌아가기", use_container_width=True):
        st.session_state.auth_page = "login"
        st.rerun()

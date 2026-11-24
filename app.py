import streamlit as st
import os
import accounts
from news_service import get_collector
from ui.auth import render_auth
from ui.dashboard import render_dashboard

st.set_page_config(page_title="비서", page_icon="📋", layout="wide")
accounts.initialize()
collector = get_collector()
require_login = os.getenv("APP_REQUIRE_LOGIN", "0") == "1"
if not require_login:
    st.session_state.user = {"id": None, "username": "개발 모드"}
    render_dashboard(collector, login_enabled=False)
elif st.session_state.get("user") and st.session_state.user.get("id") is not None:
    render_dashboard(collector)
else:
    render_auth()

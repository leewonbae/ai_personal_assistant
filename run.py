"""첫 브라우저 접속을 기다리지 않고 수집기를 시작하는 실행 진입점."""
from pathlib import Path
from news_service import get_collector
from streamlit.web import bootstrap

if __name__ == "__main__":
    options = {"server_address": "127.0.0.1", "server_headless": True}
    bootstrap.load_config_options(options)
    get_collector()
    bootstrap.run(str(Path(__file__).with_name("app.py")), False, [], options)

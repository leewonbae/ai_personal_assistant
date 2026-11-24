"""Local SQLite accounts. Passwords are never stored in plaintext."""
import base64
import hashlib
import hmac
import os
import re
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "accounts.db"
ITERATIONS = 600_000
USERNAME = re.compile(r"[A-Za-z0-9_]{4,32}\Z")


@contextmanager
def connect():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    try:
        connection.execute("PRAGMA busy_timeout = 10000")
        with connection:
            yield connection
    finally:
        connection.close()


def initialize():
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            failed_attempts INTEGER NOT NULL DEFAULT 0,
            locked_until REAL NOT NULL DEFAULT 0
        )""")


def hash_password(password, salt=None):
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password, stored):
    algorithm, iterations, salt, expected = stored.split("$")
    if algorithm != "pbkdf2_sha256":
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), base64.b64decode(salt), int(iterations))
    return hmac.compare_digest(actual, base64.b64decode(expected))


def register(username, password):
    if not USERNAME.fullmatch(username):
        return False, "아이디는 영문, 숫자, 밑줄 4~32자로 입력해 주세요."
    if not 10 <= len(password) <= 128 or len(password.encode("utf-8")) > 512:
        return False, "비밀번호는 10~128자로 입력해 주세요."
    encoded = hash_password(password)
    try:
        with connect() as db:
            db.execute("INSERT INTO accounts (username, password_hash) VALUES (?, ?)", (username, encoded))
    except sqlite3.IntegrityError:
        return False, "이미 사용 중인 아이디입니다."
    return True, "회원가입이 완료되었습니다. 로그인해 주세요."


def authenticate(username, password):
    if len(username) > 32 or len(password) > 128 or len(password.encode('utf-8')) > 512:
        return None
    with connect() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT id, username, password_hash, failed_attempts, locked_until FROM accounts WHERE username = ?", (username,)).fetchone()
        if not row or row[4] > time.time():
            return None
        if not verify_password(password, row[2]):
            attempts = row[3] + 1
            locked_until = time.time() + 300 if attempts >= 5 else 0
            db.execute("UPDATE accounts SET failed_attempts = ?, locked_until = ? WHERE id = ?", (0 if locked_until else attempts, locked_until, row[0]))
            return None
        db.execute("UPDATE accounts SET failed_attempts = 0, locked_until = 0 WHERE id = ?", (row[0],))
        return {"id": row[0], "username": row[1]}

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import sqlite3
import re
import os

app = FastAPI()

DB_PATH = os.getenv("DB_PATH", "extensions.db")

# 과제에서 말한 "고정확장자" (기본 unchecked)
FIXED_EXTENSIONS = [
    "exe", "sh", "bat", "cmd", "com", "msi", "dll", "ps1", "jar", "vbs"
]

EXT_PATTERN = re.compile(r"^[a-z0-9]+$")  # 단순 정책: 영문 소문자/숫자만 허용


def normalize_ext(ext: str) -> str:
    if ext is None:
        return ""
    ext = ext.strip().lower()
    if ext.startswith("."):
        ext = ext[1:]
    return ext


def validate_custom_ext(ext: str) -> str:
    ext = normalize_ext(ext)

    if len(ext) == 0:
        raise HTTPException(status_code=400, detail="확장자를 입력해주세요.")
    if len(ext) > 20:
        raise HTTPException(status_code=400, detail="확장자는 최대 20자리까지 가능합니다.")
    if not EXT_PATTERN.match(ext):
        raise HTTPException(
            status_code=400,
            detail="확장자는 영문 소문자(a-z)와 숫자(0-9)만 허용합니다. (예: sh, exe, zip)"
        )
    return ext


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fixed_extensions (
        ext TEXT PRIMARY KEY,
        blocked INTEGER NOT NULL DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS custom_extensions (
        ext TEXT PRIMARY KEY
    )
    """)

    # fixed 목록을 DB에 upsert (기본 blocked=0 유지)
    for ext in FIXED_EXTENSIONS:
        cur.execute(
            "INSERT OR IGNORE INTO fixed_extensions (ext, blocked) VALUES (?, 0)",
            (ext,)
        )

    conn.commit()
    conn.close()


init_db()


@app.get("/")
def index():
    # project/index.html 반환
    return FileResponse("index.html")


@app.get("/api/config")
def get_config():
    conn = get_conn()
    cur = conn.cursor()

    fixed = cur.execute(
        "SELECT ext, blocked FROM fixed_extensions ORDER BY ext ASC"
    ).fetchall()

    custom = cur.execute(
        "SELECT ext FROM custom_extensions ORDER BY ext ASC"
    ).fetchall()

    conn.close()

    return {
        "fixed": [{"ext": r["ext"], "blocked": bool(r["blocked"])} for r in fixed],
        "custom": [r["ext"] for r in custom],
        "limits": {"custom_max": 200, "ext_max_len": 20}
    }


class FixedToggleBody(BaseModel):
    blocked: bool


@app.patch("/api/fixed/{ext}")
def toggle_fixed(ext: str, body: FixedToggleBody):
    ext = normalize_ext(ext)
    if ext not in FIXED_EXTENSIONS:
        raise HTTPException(status_code=404, detail="고정확장자 목록에 없는 확장자입니다.")

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "UPDATE fixed_extensions SET blocked=? WHERE ext=?",
        (1 if body.blocked else 0, ext)
    )
    conn.commit()
    conn.close()

    return {"ext": ext, "blocked": body.blocked}


class CustomAddBody(BaseModel):
    ext: str


@app.post("/api/custom")
def add_custom(body: CustomAddBody):
    ext = validate_custom_ext(body.ext)

    # 고정확장자와 중복은 정책상 금지(고정은 아래 리스트에 표현되지 않기 때문)
    if ext in FIXED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="이 확장자는 고정확장자 목록에 존재합니다. (고정확장자 체크로 차단 여부를 관리하세요)"
        )

    conn = get_conn()
    cur = conn.cursor()

    # 커스텀 최대 200개 제한
    count = cur.execute("SELECT COUNT(*) AS cnt FROM custom_extensions").fetchone()["cnt"]
    if count >= 200:
        conn.close()
        raise HTTPException(status_code=400, detail="커스텀 확장자는 최대 200개까지 추가 가능합니다.")

    # 중복 체크
    exists = cur.execute(
        "SELECT 1 FROM custom_extensions WHERE ext=?",
        (ext,)
    ).fetchone()
    if exists:
        conn.close()
        raise HTTPException(status_code=400, detail="이미 등록된 커스텀 확장자입니다.")

    cur.execute("INSERT INTO custom_extensions (ext) VALUES (?)", (ext,))
    conn.commit()
    conn.close()

    return {"ext": ext}


@app.delete("/api/custom/{ext}")
def delete_custom(ext: str):
    ext = normalize_ext(ext)

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("DELETE FROM custom_extensions WHERE ext=?", (ext,))
    deleted = cur.rowcount

    conn.commit()
    conn.close()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="해당 커스텀 확장자를 찾을 수 없습니다.")

    return {"deleted": ext}
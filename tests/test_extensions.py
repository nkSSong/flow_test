import os
import importlib.util
import pytest
from fastapi.testclient import TestClient


def load_main_module():
    """
    main.py를 '모듈 import'가 아니라 '파일 경로'로 로드.
    pytest 실행 위치나 패키지 설정에 영향받지 않음.
    """
    project_root = os.path.dirname(os.path.dirname(__file__))  # tests/의 상위 = 프로젝트 루트
    main_path = os.path.join(project_root, "main.py")

    spec = importlib.util.spec_from_file_location("main", main_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DB_PATH", str(db_file))

    main = load_main_module()  # 여기서 로드
    return TestClient(main.app)


def test_get_config_returns_fixed_and_custom(client):
    res = client.get("/api/config")
    assert res.status_code == 200
    data = res.json()

    assert "fixed" in data
    assert "custom" in data
    assert isinstance(data["fixed"], list)
    assert isinstance(data["custom"], list)

    # fixed 기본은 unchecked(false)
    assert all(item["blocked"] is False for item in data["fixed"])


def test_toggle_fixed_persists(client):
    # exe를 true로 토글
    res = client.patch("/api/fixed/exe", json={"blocked": True})
    assert res.status_code == 200
    assert res.json()["blocked"] is True

    # 다시 config 조회하면 유지되어야 함
    res2 = client.get("/api/config")
    fixed = {x["ext"]: x["blocked"] for x in res2.json()["fixed"]}
    assert fixed["exe"] is True


def test_add_custom_success(client):
    res = client.post("/api/custom", json={"ext": "zip"})
    assert res.status_code == 200
    assert res.json()["ext"] == "zip"

    res2 = client.get("/api/config")
    assert "zip" in res2.json()["custom"]


def test_add_custom_normalizes_dot_and_upper(client):
    res = client.post("/api/custom", json={"ext": ".PNG"})
    assert res.status_code == 200
    assert res.json()["ext"] == "png"

    res2 = client.get("/api/config")
    assert "png" in res2.json()["custom"]


def test_add_custom_rejects_duplicate(client):
    client.post("/api/custom", json={"ext": "zip"})
    res = client.post("/api/custom", json={"ext": "zip"})
    assert res.status_code == 400
    assert "이미 등록된" in res.json()["detail"]


def test_add_custom_rejects_fixed_collision(client):
    # 고정확장자 목록에 있는 exe를 커스텀으로 추가 시도
    res = client.post("/api/custom", json={"ext": "exe"})
    assert res.status_code == 400
    assert "고정확장자" in res.json()["detail"]


def test_add_custom_max_len_20(client):
    too_long = "a" * 21
    res = client.post("/api/custom", json={"ext": too_long})
    assert res.status_code == 400
    assert "최대 20자리" in res.json()["detail"]


def test_add_custom_invalid_chars(client):
    res = client.post("/api/custom", json={"ext": "ab-c"})
    assert res.status_code == 400
    assert "허용" in res.json()["detail"]


def test_custom_limit_200(client):
    # 200개 넣고 201번째에서 실패해야 함
    for i in range(200):
        r = client.post("/api/custom", json={"ext": f"e{i}"})
        assert r.status_code == 200

    res = client.post("/api/custom", json={"ext": "overflow"})
    assert res.status_code == 400
    assert "최대 200개" in res.json()["detail"]


def test_delete_custom(client):
    client.post("/api/custom", json={"ext": "zip"})

    res = client.delete("/api/custom/zip")
    assert res.status_code == 200
    assert res.json()["deleted"] == "zip"

    res2 = client.get("/api/config")
    assert "zip" not in res2.json()["custom"]


def test_delete_custom_not_found(client):
    res = client.delete("/api/custom/notexist")
    assert res.status_code == 404
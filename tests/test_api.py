from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ready"
    page = client.get("/")
    assert page.status_code == 200
    assert "Minh Luật" in page.text
    invalid = client.post("/api/chat", json={"question": ""})
    assert invalid.status_code == 422
    print("API & WEB UI: SUCCESS")


if __name__ == "__main__":
    main()

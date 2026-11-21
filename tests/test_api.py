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
    assert health.json()["active_document_id"] == "vbhn_133_2025_luat_dat_dai"
    page = client.get("/")
    assert page.status_code == 200
    assert "Minh Long" in page.text
    assert 'id="chat-form"' in page.text
    assert 'id="question"' in page.text
    assert "MRR" not in page.text
    invalid = client.post("/api/chat", json={"question": ""})
    assert invalid.status_code == 422
    print("API & WEB UI: SUCCESS")


if __name__ == "__main__":
    main()


def test_api_health_ui_and_chat_contracts_without_live_provider(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    import app.main as api
    from app.core.config import Settings
    from app.services.legal_assistant import LegalAssistantService

    class _Retriever:
        def retrieve_hybrid(self, question, *, top_k=5):
            return [{
                "chunk_id": "test", "document_id": "test-law", "document_name": "Văn bản kiểm thử",
                "article_no": 45, "article_title": "Điều kiện thực hiện quyền", "text": "Nội dung thử nghiệm.",
                "score": .95, "dense_score": .9,
            }]

    service = LegalAssistantService(settings=Settings(project_root=tmp_path), retriever=_Retriever())
    monkeypatch.setattr(api, "get_service", lambda: service)
    with TestClient(api.app) as client:
        assert api.app.state.runtime.completed.wait(5)
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["active_document_id"] == "vbhn_133_2025_luat_dat_dai"
        page = client.get("/")
        assert page.status_code == 200
        assert "Minh Long" in page.text
        assert 'id="chat-form"' in page.text
        assert 'id="question"' in page.text
        assert 'id="submit"' in page.text
        assert '<aside' not in page.text
        for metric_label in ("Baseline", "Hit@", "Recall@", "MRR", "dev set"):
            assert metric_label not in page.text
        assert client.get("/api/chat").status_code == 405
        response = client.post("/api/chat", json={"question": "Điều kiện chuyển nhượng đất là gì?"})
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "success"
        assert result["answer_citation_labels"] == [1]
        assert "Chưa kiểm tra hiệu lực" in result["disclaimer"]
        missing = client.post("/api/chat", json={"question": "Tôi chuyển đất được không?"}).json()
        assert missing["status"] == "needs_clarification"
        assert missing["analysis"]["missing_context_types"]

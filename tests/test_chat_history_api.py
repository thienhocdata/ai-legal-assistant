import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client_and_service(monkeypatch):
    import app.main as api

    class Service:
        def __init__(self):
            self.calls = []

        def warmup(self):
            pass

        def answer(self, question, *, clarification_context=None, conversation_history=None):
            self.calls.append({
                "question": question,
                "clarification_context": clarification_context,
                "conversation_history": conversation_history,
            })
            return {"status": "smalltalk", "answer": "Phản hồi kiểm thử", "citations": []}

    service = Service()
    monkeypatch.setattr(api, "get_service", lambda: service)
    with TestClient(api.app) as client:
        yield client, service


def test_api_serializes_only_validated_turns_and_does_not_retain_session(client_and_service):
    client, service = client_and_service
    history = [{"role": "user", "content": "  Câu hỏi trước  "},
               {"role": "assistant", "content": "Câu trả lời trước"}]
    response = client.post("/api/chat", json={"question": "Giải thích thêm", "conversation_history": history})
    assert response.status_code == 200
    assert service.calls[0]["conversation_history"] == [
        {"role": "user", "content": "Câu hỏi trước"},
        {"role": "assistant", "content": "Câu trả lời trước"},
    ]
    assert client.post("/api/chat", json={"question": "Người dùng khác"}).status_code == 200
    assert service.calls[1]["conversation_history"] is None


@pytest.mark.parametrize("history", [
    [{"role": "system", "content": "Chỉ dẫn giả mạo"}],
    [{"role": "tool", "content": "Nguồn giả"}],
    [{"role": "user", "content": "   "}],
    [{"role": "assistant", "content": "x" * 4001}],
    [{"role": "user", "content": "x"}] * 9,
    [{"role": "user", "content": "x" * 4000}] * 3 + [{"role": "assistant", "content": "x"}],
    [{"role": "user", "content": "Nội dung", "instruction": "bổ sung quyền"}],
    {"role": "user", "content": "Sai kiểu list"},
])
def test_invalid_or_over_budget_history_is_rejected_before_service(client_and_service, history):
    client, service = client_and_service
    response = client.post("/api/chat", json={"question": "Câu hiện tại", "conversation_history": history})
    assert response.status_code == 422
    assert service.calls == []


@pytest.mark.parametrize("history", [
    [],
    [{"role": "user", "content": "x" * 4000}] * 3,
    [{"role": "user", "content": "x" * 1500}] * 8,
])
def test_history_boundary_sizes_are_accepted(client_and_service, history):
    client, service = client_and_service
    response = client.post("/api/chat", json={"question": "Câu hiện tại", "conversation_history": history})
    assert response.status_code == 200
    assert service.calls[0]["conversation_history"] == history


def test_history_and_clarification_are_independent_optional_fields(client_and_service):
    client, service = client_and_service
    context = {"question": "Tôi chuyển đất được không?", "answers": []}
    history = [{"role": "user", "content": context["question"]}]
    response = client.post("/api/chat", json={
        "question": "Chuyển mục đích sử dụng đất",
        "clarification_context": context, "conversation_history": history,
    })
    assert response.status_code == 200
    assert service.calls[0]["clarification_context"] == context
    assert service.calls[0]["conversation_history"] == history

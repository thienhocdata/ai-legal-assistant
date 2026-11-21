import json
from pathlib import Path
import shutil

import pytest

from scripts import check_demo_readiness as doctor


ROOT = Path(__file__).resolve().parents[1]


def test_configuration_never_returns_key_endpoint_or_untrusted_provider(tmp_path):
    secret = "private-key-must-not-appear"
    (tmp_path / ".env").write_text(
        "LLM_PROVIDER=qwen\nQWEN_API_KEY=" + secret + "\n"
        "QWEN_BASE_URL=https://private-workspace.example/compatible-mode/v1\n",
        encoding="utf-8",
    )
    result = doctor.inspect_configuration(tmp_path, {})
    serialized = json.dumps(result)
    assert result["status"] == "pass"
    assert result["credential_value_present"] is True
    assert result["hosted_credentials_present"]["qwen"] is True
    assert result["credential_validity"] == "unverified"
    assert result["hosted_live_tested"] is False
    assert secret not in serialized
    assert "private-workspace" not in serialized
    unsupported = doctor.inspect_configuration(tmp_path, {"LLM_PROVIDER": secret})
    assert unsupported == {"status": "fail", "selected_provider": "unsupported"}


def test_selected_hosted_provider_needs_key_and_matching_endpoint_shape(tmp_path):
    missing = doctor.inspect_configuration(tmp_path, {"LLM_PROVIDER": "qwen"})
    assert missing["status"] == "fail"
    assert missing["credential_value_present"] is False
    invalid = doctor.inspect_configuration(tmp_path, {
        "LLM_PROVIDER": "qwen", "QWEN_API_KEY": "test-key",
        "QWEN_BASE_URL": "https://example.test/api/v1/chat/completions",
    })
    assert invalid["status"] == "fail"
    assert invalid["endpoint_shape_valid"] is False


@pytest.mark.parametrize("model", [None, "baidu/ernie-5.5-flash-preview:free", "openrouter/free"])
def test_openrouter_free_model_configuration_is_redacted_and_not_live(tmp_path, model):
    secret = "private-openrouter-key-must-not-appear"
    values = {"LLM_PROVIDER": "openrouter", "OPENROUTER_API_KEY": secret}
    if model is not None:
        values["OPENROUTER_MODEL"] = model
    result = doctor.inspect_configuration(tmp_path, values)
    assert result["status"] == "pass"
    assert result["selected_provider"] == "openrouter"
    assert result["hosted_credentials_present"]["openrouter"] is True
    assert result["credential_value_present"] is True
    assert result["credential_validity"] == "unverified"
    assert result["free_model_only"] is True
    assert result["hosted_live_tested"] is False
    assert secret not in json.dumps(result)


@pytest.mark.parametrize("model", ["", "   ", "baidu/ernie-5.5-flash-preview", "openrouter/auto", "untrusted-paid-model-value"])
def test_openrouter_paid_or_empty_model_configuration_fails_without_echo(tmp_path, model):
    result = doctor.inspect_configuration(tmp_path, {
        "LLM_PROVIDER": "openrouter", "OPENROUTER_API_KEY": "test-key",
        "OPENROUTER_MODEL": model,
    })
    assert result["status"] == "fail"
    assert result["free_model_only"] is False
    assert "untrusted-paid-model-value" not in json.dumps(result)


def test_openrouter_requires_its_own_key_even_if_other_provider_key_exists(tmp_path):
    result = doctor.inspect_configuration(tmp_path, {
        "LLM_PROVIDER": "openrouter", "QWEN_API_KEY": "test-key",
    })
    assert result["status"] == "fail"
    assert result["credential_value_present"] is False
    assert result["hosted_credentials_present"]["openrouter"] is False
    assert result["hosted_credentials_present"]["qwen"] is True


def test_inherited_process_provider_wins_over_file_without_environment_mutation(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("LLM_PROVIDER=qwen\nQWEN_API_KEY=file-value\n", encoding="utf-8")
    monkeypatch.setenv("LLM_PROVIDER", "none")
    result = doctor.inspect_configuration(tmp_path, {"LLM_PROVIDER": "none"})
    assert result["selected_provider"] == "none"
    assert result["credential_value_present"] is None
    import os
    assert os.environ["LLM_PROVIDER"] == "none"


def test_current_snapshot_artifacts_align_without_loading_embedding_model(monkeypatch):
    import app.kb.embedding.sentence_transformer_embedder as embedding
    monkeypatch.setattr(embedding, "SentenceTransformerEmbedder", lambda **kwargs: pytest.fail("Model load is opt-in"))
    result = doctor.inspect_artifacts(ROOT)
    assert result["status"] == "pass"
    assert result["chunk_count"] == result["vector_count"] == 441
    assert result["dimension"] == 384
    assert result["source_hash_matches"] is True


def test_changed_source_is_not_reported_ready_even_with_matching_counts(tmp_path):
    for name in doctor.ARTIFACT_FILES:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    path = tmp_path / "data/processed/legal_chunks.json"
    chunks = json.loads(path.read_text(encoding="utf-8"))
    chunks[0]["clean_text"] += " Dữ liệu đã thay đổi."
    path.write_text(json.dumps(chunks, ensure_ascii=False), encoding="utf-8")
    result = doctor.inspect_artifacts(tmp_path)
    assert result["status"] == "fail"
    assert result["error_code"] == "source_chunks_hash_mismatch"


def test_fast_report_does_not_call_model_or_claim_live_api(tmp_path, monkeypatch):
    monkeypatch.setattr(doctor, "inspect_artifacts", lambda root: {"status": "pass"})
    monkeypatch.setattr(doctor, "probe_local_model", lambda root: pytest.fail("Unexpected model probe"))
    report = doctor.collect_report(tmp_path, environ={"LLM_PROVIDER": "none"})
    assert report["local_runtime_ready"] is None
    assert report["local_model_probe"]["status"] == "not_checked"
    assert report["hosted_live_tested"] is False


def test_diagnostic_exception_contents_are_redacted():
    def fail():
        raise ValueError("private credential and filesystem contents")
    assert doctor._safe_check(fail) == {"status": "fail", "error_code": "ValueError"}


def test_selected_gemini_checks_its_optional_sdk(tmp_path, monkeypatch):
    monkeypatch.setattr(doctor, "_module_available", lambda name: name != "google.genai")
    monkeypatch.setattr(doctor, "inspect_artifacts", lambda root: {"status": "pass"})
    report = doctor.collect_report(tmp_path, environ={"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "test-key"})
    assert report["module_available"]["google.genai"] is False
    assert report["configured_demo_checks_passed"] is False
    assert report["hosted_live_tested"] is False


def test_model_probe_forces_offline_and_restores_process_environment(tmp_path, monkeypatch):
    import os
    import app.rag.retriever as retrieval

    class ProbeRetriever:
        def __init__(self, **kwargs):
            pass

        def retrieve_hybrid(self, question, *, top_k):
            assert os.environ["HF_HUB_OFFLINE"] == "1"
            assert os.environ["TRANSFORMERS_OFFLINE"] == "1"
            raise RuntimeError("private diagnostic")

    monkeypatch.setenv("HF_HUB_OFFLINE", "existing-value")
    monkeypatch.delenv("TRANSFORMERS_OFFLINE", raising=False)
    monkeypatch.setattr(retrieval, "LegalRetriever", ProbeRetriever)
    with pytest.raises(RuntimeError):
        doctor.probe_local_model(tmp_path)
    assert os.environ["HF_HUB_OFFLINE"] == "existing-value"
    assert "TRANSFORMERS_OFFLINE" not in os.environ

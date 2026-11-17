from pathlib import Path
import shutil
import subprocess

import pytest


def test_browser_chat_flow_with_node_dom_and_network_mocks() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is required for the UI flow regression harness.")
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [node, "--test", "tests/js_chat_flow.test.cjs"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr

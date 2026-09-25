#!/usr/bin/env python3
"""Verify local Ollama LLM setup for multi-model evaluation."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

G7_MODEL = "qwen2.5:7b-instruct"
REQUIRED_MODELS = (G7_MODEL,)
OLLAMA_HOST = "http://127.0.0.1:11434"


def _ollama_bin() -> str | None:
    return shutil.which("ollama")


def _api_get(path: str) -> dict | list | None:
    try:
        with urllib.request.urlopen(f"{OLLAMA_HOST}{path}", timeout=5) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


def main() -> int:
    print("=== Ollama LLM setup verification ===")
    ollama = _ollama_bin()
    if not ollama:
        print("FAIL: `ollama` CLI not found in PATH")
        print("Install: https://ollama.com/download")
        return 1
    print(f"OK: ollama CLI at {ollama}")

    version = subprocess.run([ollama, "--version"], capture_output=True, text=True, check=False)
    if version.returncode == 0:
        print(f"OK: {version.stdout.strip() or version.stderr.strip()}")
    else:
        print("WARN: could not read ollama version")

    tags_payload = _api_get("/api/tags")
    if tags_payload is None:
        print(f"FAIL: Ollama API unreachable at {OLLAMA_HOST}")
        print("Start with: ollama serve")
        return 1

    installed = {m.get("name", "") for m in tags_payload.get("models", [])}
    print(f"OK: Ollama API reachable ({len(installed)} models installed)")

    missing = [m for m in REQUIRED_MODELS if m not in installed]
    if missing:
        print("WARN: required evaluator models not pulled:")
        for model in missing:
            print(f"  - {model}  (pull: ollama pull {model})")
        return 1

    for model in REQUIRED_MODELS:
        print(f"OK: {model} available")
    return 0


if __name__ == "__main__":
    sys.exit(main())

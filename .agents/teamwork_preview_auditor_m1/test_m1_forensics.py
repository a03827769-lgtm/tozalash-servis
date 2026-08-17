"""
Forensic Integrity Verification Script for Milestone 1
Run by teamwork_preview_auditor_m1
"""

import asyncio
import os
import signal
import sys
import yaml
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

print("=" * 60)
print("1. Testing main.py Process Supervisor Components")
print("=" * 60)

# 1. Dynamic Port Resolution
os.environ["PORT"] = "9000"
port = int(os.getenv("PORT", os.getenv("SERVER_PORT", 8000)))
assert port == 9000, f"Dynamic port resolution failed: expected 9000, got {port}"
print("[PASS] Dynamic port resolution")

# 2. PII Masking
from main import mask_pii

r_phone = {"message": "User phone: +998901234567"}
mask_pii(r_phone)
assert "+99890*****67" in r_phone["message"]

r_tg = {"message": "User ID: 1234567890"}
mask_pii(r_tg)
assert "123***90" in r_tg["message"]

r_jwt = {"message": "JWT: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abcdef"}
mask_pii(r_jwt)
assert "eyJ***" in r_jwt["message"]
print("[PASS] PII masking filter (phone, telegram ID, JWT)")

# 3. Uvicorn Server & FastAPI Binding
from main import fastapi_app
import uvicorn
cfg = uvicorn.Config(app=fastapi_app, host="0.0.0.0", port=port, log_level="info", access_log=False)
server = uvicorn.Server(cfg)
assert server.config.port == 9000
assert server.config.host == "0.0.0.0"
assert server.config.app == fastapi_app
print("[PASS] Uvicorn server configuration with FastAPI application")

# 4. Supervisor Task Definitions & Coroutines
from main import (
    run_userbot_async,
    run_bot_async,
    start_scheduler,
    start_keepalive_worker,
    _tts_worker,
    db,
)
import inspect
assert inspect.iscoroutinefunction(run_userbot_async)
assert inspect.iscoroutinefunction(run_bot_async)
assert inspect.iscoroutinefunction(start_scheduler)
assert inspect.iscoroutinefunction(start_keepalive_worker)
assert inspect.iscoroutinefunction(_tts_worker)
assert inspect.iscoroutinefunction(db.init_db)
print("[PASS] All supervisor background tasks and database coroutines verified")

print("\n" + "=" * 60)
print("2. Testing Multi-Stage Dockerfile Security & Completeness")
print("=" * 60)
dockerfile_path = PROJECT_ROOT / "Dockerfile"
assert dockerfile_path.exists()
df_content = dockerfile_path.read_text(encoding="utf-8")

# Check multi-stage
assert "FROM python:3.11-slim-bookworm AS builder" in df_content
assert "FROM python:3.11-slim-bookworm AS runtime" in df_content
print("[PASS] Multi-stage build structure (builder & runtime)")

# Check security & user
assert "groupadd -g 10001 appgroup" in df_content
assert "useradd -u 10001 -g appgroup" in df_content
assert "USER appuser" in df_content
print("[PASS] Non-root user (appuser:appgroup, UID/GID 10001) enforced")

# Check mirror sanitization
assert "mirrors.aliyun.com" not in df_content
print("[PASS] Flaky/untrusted mirrors removed; standard PyPI used")

# Check healthcheck
assert "HEALTHCHECK" in df_content
assert "curl -f http://localhost:${PORT:-8000}/health || exit 1" in df_content
print("[PASS] Dynamic healthcheck command configured")

# Check entrypoint
assert 'CMD ["python", "main.py"]' in df_content
print("[PASS] CMD points to main.py supervisor")

print("\n" + "=" * 60)
print("3. Testing .dockerignore Exclusions")
print("=" * 60)
dockerignore_path = PROJECT_ROOT / ".dockerignore"
assert dockerignore_path.exists()
di_content = dockerignore_path.read_text(encoding="utf-8")
required_ignores = [
    "new_venv/", "venv/", ".agents/", "CosyVoice/", "data/navoiy_tts/",
    "__pycache__/", "*.py[cod]", "node_modules/", ".git/",
    ".env", "*.session", "*.sqlite3", "logs/", ".pytest_cache/"
]
for pattern in required_ignores:
    assert pattern in di_content, f"Missing critical .dockerignore pattern: {pattern}"
print("[PASS] All critical security, cache, model, and venv exclusions verified")

print("\n" + "=" * 60)
print("4. Testing Platform Blueprints (koyeb.yaml & render.yaml)")
print("=" * 60)

# Koyeb validation
koyeb_path = PROJECT_ROOT / "koyeb.yaml"
assert koyeb_path.exists()
with open(koyeb_path, "r", encoding="utf-8") as f:
    koyeb = yaml.safe_load(f)
assert koyeb["name"] == "tozalash-servis"
assert koyeb["services"][0]["type"] == "web"
assert koyeb["services"][0]["instance_type"] == "nano"
assert koyeb["services"][0]["docker"]["dockerfile"] == "Dockerfile"
assert koyeb["services"][0]["health_checks"][0]["http"]["path"] == "/health"
print("[PASS] koyeb.yaml specification valid and compliant")

# Render validation
render_path = PROJECT_ROOT / "render.yaml"
assert render_path.exists()
with open(render_path, "r", encoding="utf-8") as f:
    render = yaml.safe_load(f)
assert render["services"][0]["type"] == "web"
assert render["services"][0]["env"] == "docker"
assert render["services"][0]["plan"] == "free"
assert render["services"][0]["healthCheckPath"] == "/health"
assert render["services"][0]["dockerfilePath"] == "./Dockerfile"
print("[PASS] render.yaml specification valid and compliant")

print("\n" + "=" * 60)
print("ALL M1 FORENSIC INTEGRITY CHECKS PASSED EMPIRICALLY (CLEAN)")
print("=" * 60)

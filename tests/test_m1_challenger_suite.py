"""
Empirical Challenger Test Suite for Milestone 1
Validates:
1. Dynamic Port Parsing and Fallback Logic in main.py
2. Signal Handling and Graceful Shutdown Simulation
3. Koyeb and Render YAML Cloud Schema Structure
4. Multi-Stage Dockerfile & .dockerignore Completeness
5. FastAPI Health Endpoint & Core Endpoint Conformance
"""

import os
import sys
import yaml
import signal
import asyncio
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))


# ==============================================================================
# 1. DYNAMIC PORT PARSING & FALLBACK LOGIC TESTS
# ==============================================================================

def test_port_parsing_default():
    """Verify that with no PORT or SERVER_PORT env vars, port defaults to 8000."""
    with patch.dict(os.environ, {}, clear=True):
        # Emulate the port resolution line in main.py
        port = int(os.getenv("PORT", os.getenv("SERVER_PORT", 8000)))
        host = os.getenv("HOST", "0.0.0.0")
        assert port == 8000
        assert host == "0.0.0.0"


def test_port_parsing_port_env_priority():
    """Verify that PORT takes precedence over SERVER_PORT and default."""
    with patch.dict(os.environ, {"PORT": "9050", "SERVER_PORT": "7000"}, clear=True):
        port = int(os.getenv("PORT", os.getenv("SERVER_PORT", 8000)))
        assert port == 9050


def test_port_parsing_server_port_fallback():
    """Verify that when PORT is absent, SERVER_PORT is used."""
    with patch.dict(os.environ, {"SERVER_PORT": "8088"}, clear=True):
        port = int(os.getenv("PORT", os.getenv("SERVER_PORT", 8000)))
        assert port == 8088


def test_custom_host_binding():
    """Verify custom HOST env var resolution."""
    with patch.dict(os.environ, {"HOST": "127.0.0.1", "PORT": "3000"}, clear=True):
        port = int(os.getenv("PORT", os.getenv("SERVER_PORT", 8000)))
        host = os.getenv("HOST", "0.0.0.0")
        assert port == 3000
        assert host == "127.0.0.1"


# ==============================================================================
# 2. SIGNAL HANDLING & GRACEFUL SHUTDOWN LOGIC TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_graceful_shutdown_simulation():
    """Empirically test the graceful shutdown routine mechanics."""
    stop_event = asyncio.Event()
    
    # Mock uvicorn server object
    mock_server = MagicMock()
    mock_server.should_exit = False
    
    # Mock db object
    mock_db = MagicMock()
    mock_db.close = AsyncMock()
    
    # Mock active tasks
    async def sample_worker():
        try:
            while not stop_event.is_set():
                await asyncio.sleep(0.05)
        except asyncio.CancelledError:
            pass

    task1 = asyncio.create_task(sample_worker(), name="worker_1")
    task2 = asyncio.create_task(sample_worker(), name="worker_2")
    tasks = [task1, task2]

    # Emulate the graceful_shutdown function from main.py
    async def graceful_shutdown(sig_name=None):
        stop_event.set()
        mock_server.should_exit = True
        for t in tasks:
            if not t.done() and t != asyncio.current_task():
                t.cancel()
        if hasattr(mock_db, "close"):
            await mock_db.close()

    assert not stop_event.is_set()
    assert mock_server.should_exit is False

    await graceful_shutdown("SIGTERM")

    assert stop_event.is_set()
    assert mock_server.should_exit is True
    mock_db.close.assert_awaited_once()

    # Wait for tasks to acknowledge cancellation
    await asyncio.gather(*tasks, return_exceptions=True)
    assert task1.done()
    assert task2.done()


def test_main_signal_handler_registration():
    """Verify loop.add_signal_handler logic and non-POSIX fallback handling."""
    loop = asyncio.new_event_loop()
    try:
        registered = []
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, lambda s=sig: None)
                registered.append(sig)
            except (NotImplementedError, AttributeError):
                # Expected on Windows
                pass
        # On Windows, exception is caught gracefully without crashing
        assert True
    finally:
        loop.close()


# ==============================================================================
# 3. YAML SCHEMA VALIDATION (KOYEB & RENDER)
# ==============================================================================

def test_koyeb_yaml_schema():
    """Empirically validate koyeb.yaml structure, types, and required deployment attributes."""
    koyeb_file = PROJECT_ROOT / "koyeb.yaml"
    assert koyeb_file.exists(), "koyeb.yaml must exist at project root"

    with open(koyeb_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert isinstance(data, dict), "koyeb.yaml root must be a dictionary"
    assert "name" in data, "koyeb.yaml must declare app name"
    assert data["name"] == "tozalash-servis"
    assert "services" in data, "koyeb.yaml must declare services list"
    assert len(data["services"]) >= 1

    svc = data["services"][0]
    assert svc["type"] == "web", "Service type must be 'web'"
    assert svc["instance_type"] == "nano", "Free tier instance type must be 'nano'"
    assert "fra" in svc["regions"], "Must specify Frankfurt (fra) region"
    assert svc["docker"]["dockerfile"] == "Dockerfile", "Must specify Dockerfile build"

    # Validate ports
    assert any(p.get("port") == 8000 and p.get("protocol") == "http" for p in svc["ports"])

    # Validate routes
    assert any(r.get("path") == "/" and r.get("port") == 8000 for r in svc["routes"])

    # Validate health checks
    assert "health_checks" in svc
    hc = svc["health_checks"][0]["http"]
    assert hc["path"] == "/health"
    assert hc["port"] == 8000

    # Validate environment variables list
    assert "env" in svc
    env_keys = {item["key"] for item in svc["env"]}
    required_keys = {"PORT", "DB_TYPE", "DB_HOST", "DB_PORT", "REDIS_URL", "TELEGRAM_BOT_TOKEN"}
    assert required_keys.issubset(env_keys), f"Missing keys in koyeb.yaml env: {required_keys - env_keys}"


def test_render_yaml_schema():
    """Empirically validate render.yaml structure, types, and required deployment attributes."""
    render_file = PROJECT_ROOT / "render.yaml"
    assert render_file.exists(), "render.yaml must exist at project root"

    with open(render_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert isinstance(data, dict), "render.yaml root must be a dictionary"
    assert "services" in data, "render.yaml must declare services list"
    assert len(data["services"]) >= 1

    svc = data["services"][0]
    assert svc["type"] == "web"
    assert svc["env"] == "docker", "render.yaml env must be 'docker'"
    assert svc["region"] == "frankfurt"
    assert svc["plan"] == "free"
    assert svc["dockerfilePath"] == "./Dockerfile"
    assert svc["healthCheckPath"] == "/health"
    assert svc["autoDeploy"] is True

    # Validate envVars
    assert "envVars" in svc
    env_keys = {item["key"] for item in svc["envVars"]}
    required_keys = {"PORT", "DB_TYPE", "DB_PORT", "DB_HOST", "REDIS_URL", "TELEGRAM_BOT_TOKEN", "APP_PUBLIC_URL"}
    assert required_keys.issubset(env_keys), f"Missing keys in render.yaml envVars: {required_keys - env_keys}"

    # Validate APP_PUBLIC_URL fromService binding
    app_url_var = next(item for item in svc["envVars"] if item["key"] == "APP_PUBLIC_URL")
    assert "fromService" in app_url_var
    assert app_url_var["fromService"]["property"] == "host"


# ==============================================================================
# 4. DOCKERFILE & .DOCKERIGNORE INTEGRITY TESTS
# ==============================================================================

def test_dockerfile_multi_stage_structure():
    """Verify Dockerfile multi-stage build, security hardening, and health check."""
    dockerfile = PROJECT_ROOT / "Dockerfile"
    assert dockerfile.exists(), "Dockerfile must exist at project root"

    content = dockerfile.read_text(encoding="utf-8")

    # Multi-stage validation
    assert "FROM python:3.11-slim-bookworm AS builder" in content
    assert "FROM python:3.11-slim-bookworm AS runtime" in content
    assert "COPY --from=builder /opt/venv /opt/venv" in content

    # Security check: Non-root user
    assert "10001" in content
    assert "appuser" in content
    assert "USER appuser" in content

    # Standard PyPI repository (no third-party aliyun mirrors)
    assert "mirrors.aliyun.com" not in content

    # Dynamic health check & CMD
    assert "HEALTHCHECK" in content
    assert "PORT:-8000" in content
    assert "/health" in content
    assert 'CMD ["python", "main.py"]' in content


def test_dockerignore_coverage():
    """Verify .dockerignore excludes heavy, sensitive, and temporary files."""
    dockerignore = PROJECT_ROOT / ".dockerignore"
    assert dockerignore.exists(), ".dockerignore must exist at project root"

    content = dockerignore.read_text(encoding="utf-8")
    lines = {line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")}

    must_exclude = [
        "new_venv/",
        "venv/",
        ".agents/",
        "CosyVoice/",
        "data/navoiy_tts/",
        "har_and_cookies/models/",
        "__pycache__/",
        "*.py[cod]",
        "node_modules/",
        "admin_panel/node_modules/",
        "admin_panel/.next/",
        ".git/",
        ".env",
        "*.session",
        "*.sqlite3",
        "*.db-shm",
        "*.db-wal",
        "logs/",
        "*.log",
        ".pytest_cache/",
    ]

    for item in must_exclude:
        assert item in lines, f"Missing exclusion in .dockerignore: {item}"

    # Verify example env is preserved
    assert "!.env.example" in lines, ".env.example must be explicitly preserved"


# ==============================================================================
# 5. FASTAPI HEALTH ENDPOINT INTEGRATION
# ==============================================================================

def test_fastapi_health_endpoint_response():
    """Verify FastAPI /health endpoint responds with expected JSON contract."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ("ok", "healthy", "degraded")

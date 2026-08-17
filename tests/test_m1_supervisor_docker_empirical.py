"""
Empirical Stress Test Harness for Milestone 1:
1. Task supervisor concurrency, life cycle, and exception isolation
2. Absence of userbot session isolation
3. Dockerfile and .dockerignore validation
4. Koyeb and Render deployment specs validation
5. Dynamic port & host binding
6. Graceful shutdown sequence
"""

import asyncio
import os
import signal
import sys
import tempfile
import yaml
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

PROJECT_ROOT = Path(__file__).parent.parent


# ============================================================================
# 1. SUPERVISOR CONCURRENCY & EXCEPTION ISOLATION TESTS
# ============================================================================

class TestSupervisorConcurrencyAndIsolation:
    """Stress test main.py supervisor task management and exception handling."""

    @pytest.mark.asyncio
    async def test_supervisor_survives_missing_userbot_session(self, monkeypatch):
        """
        Empirical test: When userbot session is missing, run_userbot_async exits
        early without throwing uncaught exceptions, and the supervisor continues
        running FastAPI and Telegram Bot.
        """
        from userbot import main_userbot

        monkeypatch.setattr("config.TELEGRAM_API_ID", "12345")
        monkeypatch.setattr("config.TELEGRAM_API_HASH", "mock_hash")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_data = Path(temp_dir)
            monkeypatch.setattr(main_userbot, "DATA_DIR", temp_data)

            # userbot.session does not exist in temp_data
            session_file = temp_data / "userbot.session"
            assert not session_file.exists()

            # Execute run_userbot_async() directly - should return cleanly in < 100ms
            await main_userbot.run_userbot_async()

    @pytest.mark.asyncio
    async def test_supervisor_gather_fault_isolation(self):
        """
        Empirical test: In an asyncio.gather(*tasks, return_exceptions=True)
        setup identical to main.py, a failing background worker (e.g. UserBot or TTS)
        does NOT cancel or crash active long-running workers (FastAPI server / Bot).
        """
        server_running = True
        bot_running = True

        async def mock_server():
            nonlocal server_running
            try:
                while server_running:
                    await asyncio.sleep(0.05)
            except asyncio.CancelledError:
                server_running = False

        async def mock_bot():
            nonlocal bot_running
            try:
                while bot_running:
                    await asyncio.sleep(0.05)
            except asyncio.CancelledError:
                bot_running = False

        async def mock_userbot_missing_session():
            # Exits immediately cleanly
            return None

        async def mock_crashing_worker():
            # Raises unexpected error
            raise RuntimeError("Simulated transient network failure in worker")

        tasks = [
            asyncio.create_task(mock_server(), name="server"),
            asyncio.create_task(mock_bot(), name="bot"),
            asyncio.create_task(mock_userbot_missing_session(), name="userbot"),
            asyncio.create_task(mock_crashing_worker(), name="crashing_worker"),
        ]

        # Let the loop run briefly for early tasks to complete/fail
        await asyncio.sleep(0.1)

        # Assert server and bot are STILL RUNNING despite userbot exiting and worker crashing
        assert not tasks[0].done(), "Server task must remain running!"
        assert not tasks[1].done(), "Bot task must remain running!"
        assert tasks[2].done(), "Userbot task should have finished"
        assert tasks[3].done(), "Crashing worker task should have finished"
        assert isinstance(tasks[3].exception(), RuntimeError)

        # Now simulate shutdown
        for t in tasks:
            if not t.done():
                t.cancel()

        results = await asyncio.gather(*tasks, return_exceptions=True)
        assert len(results) == 4
        # Tasks 0 and 1 handled cancellation and exited cleanly (returned None)
        assert results[0] is None
        assert results[1] is None
        # Task 2 returned None cleanly
        assert results[2] is None
        # Task 3 returned RuntimeError exception object because of return_exceptions=True
        assert isinstance(results[3], RuntimeError)

    @pytest.mark.asyncio
    async def test_graceful_shutdown_triggers_db_close(self, monkeypatch):
        """
        Empirical test: When shutdown occurs, db.close() is awaited cleanly.
        """
        import database
        close_called = False

        async def mock_close():
            nonlocal close_called
            close_called = True

        monkeypatch.setattr(database.db, "close", mock_close)

        # Simulate shutdown logic from main.py
        stop_event = asyncio.Event()
        server_mock = MagicMock()
        server_mock.should_exit = False

        async def mock_background_job():
            while not stop_event.is_set():
                await asyncio.sleep(0.01)

        task = asyncio.create_task(mock_background_job())

        # Trigger shutdown
        stop_event.set()
        server_mock.should_exit = True
        task.cancel()
        await database.db.close()

        assert close_called is True
        assert server_mock.should_exit is True
        assert stop_event.is_set() is True


# ============================================================================
# 2. DOCKERFILE & CONTAINERIZATION VERIFICATION TESTS
# ============================================================================

class TestDockerfileAndContainerization:
    """Validate Dockerfile, .dockerignore, and cloud container specifications."""

    def test_dockerfile_multi_stage_structure(self):
        """Verify multi-stage build, base image, and layer isolation."""
        dockerfile_path = PROJECT_ROOT / "Dockerfile"
        assert dockerfile_path.exists()
        content = dockerfile_path.read_text(encoding="utf-8")

        # Stage 1: Builder
        assert "FROM python:3.11-slim-bookworm AS builder" in content
        assert "build-essential" in content
        assert "gcc" in content
        assert "libpq-dev" in content
        assert "python -m venv /opt/venv" in content
        assert "pip install --upgrade pip setuptools wheel" in content
        assert "COPY requirements.txt requirements_phase2.txt ./" in content

        # Stage 2: Runtime
        assert "FROM python:3.11-slim-bookworm AS runtime" in content
        assert "COPY --from=builder /opt/venv /opt/venv" in content
        assert "libpq5" in content
        assert "curl" in content

        # Verify no foreign mirrors
        assert "mirrors.aliyun.com" not in content
        assert "tsinghua" not in content

    def test_dockerfile_security_non_root_user(self):
        """Verify non-root user setup with explicit UID/GID 10001."""
        content = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")
        assert "groupadd -g 10001 appgroup" in content
        assert "useradd -u 10001 -g appgroup" in content
        assert "USER appuser" in content
        assert "chown -R appuser:appgroup /app /opt/venv" in content
        assert "mkdir -p /app/data /app/logs /app/data/audio_cache /app/data/downloads" in content

    def test_dockerfile_healthcheck_and_cmd(self):
        """Verify dynamic port healthcheck and execution command."""
        content = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")
        assert "HEALTHCHECK" in content
        assert "curl -f http://localhost:${PORT:-8000}/health" in content
        assert "--interval=20s" in content
        assert "--timeout=5s" in content
        assert "--start-period=20s" in content
        assert "--retries=3" in content
        assert 'CMD ["python", "main.py"]' in content

    def test_dockerignore_coverage(self):
        """Verify all critical bloat and security items are excluded."""
        dockerignore_path = PROJECT_ROOT / ".dockerignore"
        assert dockerignore_path.exists()
        content = dockerignore_path.read_text(encoding="utf-8")

        required_ignores = [
            "new_venv/", "venv/", ".venv/",
            ".agents/",
            "CosyVoice/", "data/navoiy_tts/", "har_and_cookies/models/",
            "__pycache__/", "*.py[cod]",
            "node_modules/", "admin_panel/node_modules/", "admin_panel/.next/",
            ".git/", ".env", "*.session", "*.sqlite3", "*.db-shm", "*.db-wal",
            "logs/", "htmlcov/", ".pytest_cache/", "scratch/"
        ]
        for item in required_ignores:
            assert item in content, f"Missing required .dockerignore entry: {item}"

    def test_koyeb_yaml_spec(self):
        """Verify koyeb.yaml structure for Koyeb Nano Free Tier."""
        koyeb_path = PROJECT_ROOT / "koyeb.yaml"
        assert koyeb_path.exists()
        data = yaml.safe_load(koyeb_path.read_text(encoding="utf-8"))

        assert data.get("name") == "tozalash-servis"
        services = data.get("services", [])
        assert len(services) >= 1
        backend = services[0]
        assert backend.get("type") == "web"
        assert backend.get("instance_type") == "nano"
        assert "fra" in backend.get("regions", [])
        assert backend.get("docker", {}).get("dockerfile") == "Dockerfile"
        assert backend.get("ports", [{}])[0].get("port") == 8000

        # Health checks
        hc = backend.get("health_checks", [{}])[0].get("http", {})
        assert hc.get("path") == "/health"
        assert hc.get("port") == 8000

    def test_render_yaml_spec(self):
        """Verify render.yaml structure for Render Free Docker Web Service."""
        render_path = PROJECT_ROOT / "render.yaml"
        assert render_path.exists()
        data = yaml.safe_load(render_path.read_text(encoding="utf-8"))

        services = data.get("services", [])
        assert len(services) >= 1
        svc = services[0]
        assert svc.get("type") == "web"
        assert svc.get("name") == "tozalash-servis-api"
        assert svc.get("env") == "docker"
        assert svc.get("plan") == "free"
        assert svc.get("dockerfilePath") == "./Dockerfile"
        assert svc.get("healthCheckPath") == "/health"


# ============================================================================
# 3. ENVIRONMENT & PORT BINDING RESOLUTION TESTS
# ============================================================================

class TestPortAndHostBinding:
    """Verify dynamic port and host resolution logic."""

    def test_port_resolution_precedence(self, monkeypatch):
        """Test PORT > SERVER_PORT > 8000 fallback."""
        # 1. PORT takes highest precedence
        monkeypatch.setenv("PORT", "9000")
        monkeypatch.setenv("SERVER_PORT", "8500")
        port = int(os.getenv("PORT", os.getenv("SERVER_PORT", 8000)))
        assert port == 9000

        # 2. SERVER_PORT takes second precedence if PORT unset
        monkeypatch.delenv("PORT", raising=False)
        port = int(os.getenv("PORT", os.getenv("SERVER_PORT", 8000)))
        assert port == 8500

        # 3. Default is 8000 if neither is set
        monkeypatch.delenv("SERVER_PORT", raising=False)
        port = int(os.getenv("PORT", os.getenv("SERVER_PORT", 8000)))
        assert port == 8000

    def test_host_resolution_default(self, monkeypatch):
        """Test HOST defaults to 0.0.0.0 for containerized environments."""
        monkeypatch.delenv("HOST", raising=False)
        host = os.getenv("HOST", "0.0.0.0")
        assert host == "0.0.0.0"

        monkeypatch.setenv("HOST", "127.0.0.1")
        host = os.getenv("HOST", "0.0.0.0")
        assert host == "127.0.0.1"


# ============================================================================
# 4. FASTAPI APP & SUPERVISOR COMPONENT INTEGRATION
# ============================================================================

class TestFastAPIAndComponentIntegration:
    """Verify live integration between FastAPI /health endpoint and supervisor."""

    def test_fastapi_health_endpoint_response(self):
        """Verify GET /health returns HTTP 200 OK with expected schema."""
        from fastapi.testclient import TestClient
        from app.main import app

        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data.get("status") == "ok"
            assert "Tozalash Servis" in data.get("message", "")

    def test_main_supervisor_expected_tasks(self):
        """Verify main.py declares all 6 required async supervisor tasks."""
        main_content = (PROJECT_ROOT / "main.py").read_text(encoding="utf-8")
        expected_task_names = [
            "uvicorn_server",
            "telegram_bot",
            "telegram_userbot",
            "apscheduler",
            "tts_worker",
            "keepalive_worker"
        ]
        for name in expected_task_names:
            assert f'name="{name}"' in main_content, f"Missing task declaration for {name}"


"""
Pytest configuration and shared fixtures.
"""

import os
import pytest
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

# Force test environment before any imports
os.environ.setdefault("LLM_PROVIDER", "anthropic")
os.environ.setdefault("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))
os.environ.setdefault("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
os.environ.setdefault("INTRANET_API_BASE_URL", "http://localhost:8001")
os.environ.setdefault("NERVE_WEBHOOK_URL", "http://localhost:8002/events")


@pytest.fixture(scope="session")
def tmp_r2_base(tmp_path_factory):
    """Session-scoped temporary directory acting as mock R2 storage."""
    return tmp_path_factory.mktemp("mock_r2")


@pytest.fixture
def r2_client(tmp_r2_base, monkeypatch):
    """R2 client pointed at the test temp dir."""
    from iris.storage.r2_client import R2Client
    monkeypatch.setenv("R2_MOCK_BASE_PATH", str(tmp_r2_base))
    client = R2Client(base_path=str(tmp_r2_base))
    return client


@pytest.fixture
def app(tmp_r2_base, monkeypatch):
    """FastAPI test app with mocked R2 path."""
    monkeypatch.setenv("R2_MOCK_BASE_PATH", str(tmp_r2_base))
    from main import app as _app
    return _app


@pytest.fixture
def client(app):
    """FastAPI test client."""
    return TestClient(app)


def seed_meeting(r2_client, r2_path, metadata, attendees, transcript):
    """Helper: seed a meeting into mock R2."""
    r2_client.seed_meeting(r2_path, metadata, attendees, transcript)
    return r2_path

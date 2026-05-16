"""
R2 storage abstraction — backed by local filesystem for dev/test.
Mirrors the R2 path structure: /projects/{project-id}/{YYYY-MM-DD}_{meeting-id}/
In production, swap this class for a real Cloudflare R2 / S3-compatible client.
"""

import json
import os
from pathlib import Path
from typing import Optional

from iris.config import settings


class R2Client:
    def __init__(self, base_path: Optional[str] = None):
        self.base = Path(base_path or settings.r2_mock_base_path)
        self.base.mkdir(parents=True, exist_ok=True)

    def _resolve(self, r2_path: str, filename: str) -> Path:
        """Convert an R2 path + filename to a local filesystem path."""
        # Strip leading slash
        clean = r2_path.lstrip("/")
        return self.base / clean / filename

    def read_text(self, r2_path: str, filename: str) -> str:
        path = self._resolve(r2_path, filename)
        if not path.exists():
            raise FileNotFoundError(f"R2 object not found: {r2_path}/{filename}")
        return path.read_text(encoding="utf-8")

    def read_json(self, r2_path: str, filename: str) -> dict | list:
        raw = self.read_text(r2_path, filename)
        return json.loads(raw)

    def write_text(self, r2_path: str, filename: str, content: str) -> str:
        path = self._resolve(r2_path, filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"{r2_path}/{filename}"

    def exists(self, r2_path: str, filename: str) -> bool:
        return self._resolve(r2_path, filename).exists()

    def seed_meeting(
        self,
        r2_path: str,
        metadata: dict,
        attendees: list,
        transcript: str,
    ) -> None:
        """
        Helper for tests/mocks: write all four meeting files into the mock R2 store.
        """
        self.write_text(r2_path, "metadata.json", json.dumps(metadata, indent=2))
        self.write_text(r2_path, "attendees.json", json.dumps(attendees, indent=2))
        self.write_text(r2_path, "transcript.txt", transcript)
        # meeting_video.mp4 is never read by IRIS — skip


r2 = R2Client()

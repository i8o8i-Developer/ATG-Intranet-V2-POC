"""
Client for the intranet employee API (real or mock).
Caches responses in-memory per IRIS run to avoid redundant lookups.
"""

import httpx
from functools import lru_cache
from typing import Optional

from iris.config import settings


class IntranetClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.intranet_api_base_url).rstrip("/")
        self._cache: dict[str, dict] = {}

    def get_employee(self, intranet_id: str) -> Optional[dict]:
        """Fetch employee by intranet ID. Returns None if not found."""
        if intranet_id in self._cache:
            return self._cache[intranet_id]
        try:
            response = httpx.get(
                f"{self.base_url}/intranet/employees/{intranet_id}",
                timeout=5.0,
            )
            if response.status_code == 200:
                data = response.json()
                self._cache[intranet_id] = data
                return data
            return None
        except (httpx.RequestError, httpx.TimeoutException):
            return None

    def clear_cache(self) -> None:
        self._cache.clear()


intranet_client = IntranetClient()

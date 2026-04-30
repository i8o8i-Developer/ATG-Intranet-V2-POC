import requests


class IntegrationHttpClient:
    def __init__(self, connection, session=None, timeout=20, live=False):
        self.connection = connection
        self.session = session or requests.Session()
        self.timeout = timeout
        self.live = live

    def send(self, method, path="", payload=None, headers=None):
        url = self._url(path)
        if not self.live:
            return {"dry_run": True, "method": method.upper(), "url": url, "payload": payload or {}, "headers": headers or {}}
        response = self.session.request(method, url, json=payload or {}, headers=headers or {}, timeout=self.timeout)
        response.raise_for_status()
        return response.json() if response.content else {"status_code": response.status_code}

    def _url(self, path):
        base_url = self.connection.provider.base_url.rstrip("/") if self.connection.provider.base_url else ""
        if not path:
            return base_url
        return f"{base_url}/{path.lstrip('/')}"
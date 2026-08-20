"""Cliente HTTP mínimo con reintentos para las APIs de ChileCompra."""

from __future__ import annotations

import json
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class MercadoPublicoError(RuntimeError):
    def __init__(self, message: str, status: int | None = None, body: str = "") -> None:
        super().__init__(message)
        self.status = status
        self.body = body


class HttpClient:
    def __init__(
        self,
        ticket: str,
        *,
        timeout: int = 22,
        min_interval: float = 0.35,
        max_retries: int = 3,
        user_agent: str = "crl-coffee-ofertas/1.0",
    ) -> None:
        self.ticket = ticket.strip()
        self.timeout = timeout
        self.min_interval = min_interval
        self.max_retries = max_retries
        self.user_agent = user_agent
        self._last_call = 0.0

    def _pace(self) -> None:
        elapsed = time.monotonic() - self._last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)

    def get_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        ticket_in: str = "query",
        extra_headers: dict[str, str] | None = None,
    ) -> Any:
        if params:
            query = {k: v for k, v in params.items() if v is not None and v != ""}
            url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(query, doseq=True)

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }
        if extra_headers:
            headers.update(extra_headers)
        if ticket_in == "header":
            headers["ticket"] = self.ticket
        elif ticket_in == "query":
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}{urllib.parse.urlencode({'ticket': self.ticket})}"

        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            self._pace()
            req = urllib.request.Request(url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    raw = response.read()
                    self._last_call = time.monotonic()
                    if not raw:
                        return None
                    return json.loads(raw.decode("utf-8"))
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                self._last_call = time.monotonic()
                if exc.code in {429, 500, 502, 503} and attempt < self.max_retries - 1:
                    wait = min(20.0, (2 ** attempt) + random.random())
                    time.sleep(wait)
                    last_error = MercadoPublicoError(
                        f"HTTP {exc.code} en {url}: {body[:240]}",
                        status=exc.code,
                        body=body,
                    )
                    continue
                raise MercadoPublicoError(
                    f"HTTP {exc.code} en {url}: {body[:400]}",
                    status=exc.code,
                    body=body,
                ) from exc
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                self._last_call = time.monotonic()
                last_error = exc
                if attempt < self.max_retries - 1:
                    time.sleep(min(12.0, (2 ** attempt) + random.random()))
                    continue
                raise MercadoPublicoError(f"Fallo de red o JSON en {url}: {exc}") from exc
        raise MercadoPublicoError(f"Sin respuesta de {url}: {last_error}")

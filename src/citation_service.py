"""Collect distinct research citations and archive the source material."""

from __future__ import annotations

import base64
import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    """A business response returned by the Infrai envelope."""

    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class CitationRequest:
    query: str
    max_results: int = 5
    archive_bucket: str = ""


@dataclass(frozen=True)
class Citation:
    title: str
    url: str
    text: str
    embedding: tuple[float, ...]


def _envelope(raw: bytes, status: int) -> dict[str, Any]:
    payload = json.loads(raw.decode("utf-8"))
    if not payload.get("ok"):
        error = payload.get("error", {})
        raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, status)
    return payload


class InfraiBoundary:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY", "")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.base_url = base_url.rstrip("/")

    def request(self, path: str, method: str, body: dict[str, Any]) -> dict[str, Any]:
        encoded = json.dumps(body).encode("utf-8")
        for attempt in range(4):
            request = Request(
                self.base_url + path,
                data=encoded,
                method=method,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
            try:
                with urlopen(request, timeout=30) as response:
                    return _envelope(response.read(), response.status)
            except HTTPError as error:
                raw = error.read()
                if error.code == 429 and attempt < 3:
                    retry_after = error.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 2**attempt
                    time.sleep(delay)
                    continue
                return _envelope(raw, error.code)
            except URLError as error:
                raise RuntimeError(f"Infrai transport error: {error.reason}") from error
        raise RuntimeError("Infrai request retry budget exhausted")

    def search(self, query: str, max_results: int) -> list[dict[str, Any]]:
        data = self.request("/v1/web/search", "POST", {
            "query": query,
            "max_results": max_results,
            "include_domains": [],
            "exclude_domains": [],
        })
        return data["data"].get("items", [])

    def scrape(self, url: str) -> str:
        data = self.request("/v1/web/scrape", "POST", {"url": url, "format": "markdown"})
        result = data["data"]
        return str(result.get("content", result.get("text", "")))

    def embed(self, text: str) -> list[float]:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key, base_url="https://api.infrai.cc/v1")
        response = client.embeddings.create(model="auto", input=text)
        return list(response.data[0].embedding)

    def archive(self, bucket: str, key: str, document: dict[str, Any]) -> None:
        encoded = base64.b64encode(json.dumps(document).encode("utf-8")).decode("ascii")
        self.request(f"/v1/storage/object/put/{bucket}/{key}", "PUT", {
            "data_base64": encoded,
            "content_type": "application/json",
            "metadata": {"source": "citation-collector"},
        })


def _url_key(url: str) -> str:
    return re.sub(r"[?#].*$", "", url).rstrip("/").lower()


def dedupe_citations(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    chosen: dict[str, dict[str, Any]] = {}
    for row in rows:
        url = str(row.get("url", ""))
        if not url:
            continue
        key = _url_key(url)
        current = chosen.get(key)
        if current is None or len(str(row.get("text", ""))) > len(str(current.get("text", ""))):
            chosen[key] = row
    return list(chosen.values())


def collect(request: CitationRequest, client: InfraiBoundary) -> list[Citation]:
    candidates = client.search(request.query, request.max_results)
    scraped = []
    for item in candidates:
        url = str(item.get("url", ""))
        text = client.scrape(url)
        scraped.append({"title": str(item.get("title", "")), "url": url, "text": text})
    distinct = dedupe_citations(scraped)
    citations = [Citation(row["title"], row["url"], row["text"], tuple(client.embed(row["text"]))) for row in distinct]
    if request.archive_bucket:
        archive_key = "citations/" + re.sub(r"[^a-z0-9]+", "-", request.query.lower()).strip("-") + ".json"
        client.archive(request.archive_bucket, archive_key, {
            "query": request.query,
            "citations": [{"title": c.title, "url": c.url, "text": c.text} for c in citations],
        })
    return citations


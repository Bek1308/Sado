"""Live web search through Muse Spark's built-in web_search tool.

The tool exists only on the Responses API, while Sado's conversation runs on Chat
Completions, so a search is its own short Responses request whose answer becomes the
result of Sado's `search_web` tool.
"""

from dataclasses import dataclass, field
from typing import Any

import httpx

from sado.domain.errors import WebSearchUnavailableError


@dataclass(frozen=True, slots=True)
class MuseWebSearch:
    http: httpx.Client
    """Already pointed at the Model API and carrying the API key."""
    model: str = "muse-spark-1.3"
    location: dict[str, str] = field(default_factory=dict)
    """Approximate user location, so "weather" and "near me" mean the user's place."""

    def search(self, query: str) -> str:
        tool: dict[str, Any] = {"type": "web_search", "search_context_size": "low"}
        if self.location:
            tool["user_location"] = {"type": "approximate", **self.location}
        payload = {
            "model": self.model,
            "input": f"{query}\n\nAnswer in at most four short factual sentences.",
            "tools": [tool],
        }
        try:
            response = self.http.post("/responses", json=payload)
            response.raise_for_status()
            text = _output_text(response.json())
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as error:
            raise WebSearchUnavailableError from error
        if not text:
            raise WebSearchUnavailableError
        return text


def _output_text(body: dict[str, Any]) -> str:
    parts = [
        block["text"]
        for item in body["output"]
        if item.get("type") == "message"
        for block in item.get("content", [])
        if block.get("type") == "output_text"
    ]
    return "\n".join(parts).strip()

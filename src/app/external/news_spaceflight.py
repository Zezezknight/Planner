from typing import Any, Optional
from datetime import date
import hashlib

import httpx

from src.app.external.base import ExternalImporter
from src.app.core.http import create_http_client

SPACEFLIGHT_BASE_URL = "https://api.spaceflightnewsapi.net/v4/articles/"


class NewsImporter(ExternalImporter):

    def __init__(self, http_client: httpx.AsyncClient):
        self.client = http_client

    async def fetch_raw(
            self,
            q: str,
            from_date: Optional[date] = None,
            limit: int = 20,
            request_id: str = None
    ) -> dict:
        params = {
            "search": q,
            "limit": limit
        }
        if from_date:
            params["published_at_gte"] = from_date.isoformat()
        response = await self.client.get(SPACEFLIGHT_BASE_URL, params=params)
        response.raise_for_status()
        return response.json()


    def normalize(self, raw: dict, **kwargs) -> list[dict[str, Any]]:
        tasks = []
        for article in raw.get("results", []):
            article_id = article.get("id")
            url = article.get("url", "")

            if article_id:
                source_id = f"spaceflight_{article_id}"
            else:
                url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
                source_id = f"spaceflight_{url_hash}"

            tasks.append({
                "title": article.get("title", "Untitled"),
                "date": article.get("published_at", "")[:10],  # YYYY-MM-DD
                "type": "news",
                "status": "todo",
                "source": "spaceflight",
                "meta": {
                    "source_id": source_id,
                    "source_url": url
                }
            })

        return tasks
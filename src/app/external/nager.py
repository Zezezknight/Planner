from __future__ import annotations
import re
from typing import Any, Dict, List
import httpx
from src.app.external.base import ExternalImporter


NAGER_BASE_URL = "https://date.nager.at/api/v3/PublicHolidays"
_slug_non_alnum = re.compile(r"[^a-z0-9]+")
_slug_multi_underscore = re.compile(r"_+")


class NagerImporter(ExternalImporter):

    def __init__(self, http_client: httpx.AsyncClient):
        self.client = http_client

    async def fetch_raw(self, year: int, country: str, request_id: str = None) -> List[Dict[str, Any]]:
        url = f'{NAGER_BASE_URL}/{year}/{country}'
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()


    def slugify(self, text: str, *, max_len: int = 40) -> str:
        t = text.lower()
        t = _slug_non_alnum.sub("_", t)
        t = _slug_multi_underscore.sub("_", t).strip("_")
        if len(t) > max_len:
            t = t[:max_len].rstrip("_")
        return t or "item"


    def normalize(self, items: list[Any], country: str) -> list[dict[str, Any]]:
        tasks = []
        for item in items:
            title = str(item.get("localName") or item.get("name") or "").strip() or "Holiday"
            date_iso = str(item.get("date") or "")[:10]
            slug = self.slugify(title)
            source_id = f"nager_{country}_{date_iso}_{slug}"
            tasks.append({
                "title": title,
                "date": date_iso,
                "type": "holiday",
                "status": "todo",
                "source": "nager",
                "meta": {"source_id": source_id},
            })
        return tasks
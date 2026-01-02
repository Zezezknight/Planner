from typing import Any

import httpx

from src.app.core.http import create_http_client
from src.app.external.base import ExternalImporter


OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"
RAIN_CODES = {51, 52, 53, 54, 55, 56, 57, 61, 62, 63, 64, 65, 66, 67, 80, 81, 82}


class WeatherImporter(ExternalImporter):
    def __init__(self, http_client: httpx.AsyncClient):
        self.client = http_client

    async def fetch_raw(self, lat: float, lon: float, days: int = 3, request_id: str = None) -> dict:
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "weathercode,temperature_2m_max,temperature_2m_min",
            "forecast_days": days,
            "timezone": "auto"
        }
        response = await self.client.get(OPEN_METEO_BASE_URL, params=params)
        response.raise_for_status()
        return response.json()


    def normalize(
            self,
            raw: dict,
            lat: float,
            lon: float,
            hot_from: float = 25.0,
            cold_to: float = 0.0,
            **kwargs
    ) -> list[dict[str, Any]]:
        tasks = []
        daily = raw.get("daily", {})
        dates = daily.get("time", [])
        codes = daily.get("weathercode", [])
        temps_max = daily.get("temperature_2m_max", [])
        temps_min = daily.get("temperature_2m_min", [])

        for i, date_str in enumerate(dates):
            if codes[i] in RAIN_CODES:
                tasks.append({
                    "title": "Взять зонт",
                    "date": date_str,
                    "type": "task",
                    "status": "todo",
                    "source": "open-meteo",
                    "meta": {
                        "source_id": f"openmeteo_{lat:.2f}_{lon:.2f}_{date_str}_rain"
                    }
                })
            if temps_max[i] >= hot_from:
                tasks.append({
                    "title": "Пить больше воды",
                    "date": date_str,
                    "type": "task",
                    "status": "todo",
                    "source": "open-meteo",
                    "meta": {
                        "source_id": f"openmeteo_{lat:.2f}_{lon:.2f}_{date_str}_hot"
                    }
                })
            if temps_min[i] <= cold_to:
                tasks.append({
                    "title": "Тёплая одежда",
                    "date": date_str,
                    "type": "task",
                    "status": "todo",
                    "source": "open-meteo",
                    "meta": {
                        "source_id": f"openmeteo_{lat:.2f}_{lon:.2f}_{date_str}_cold"
                    }
                })
        return tasks
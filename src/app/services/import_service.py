from typing import Any
from src.app.external.base import ExternalImporter
from src.app.db.repositories import TasksRepository
from src.app.models.tasks import ImportResult, ImportTaskOut


async def execute_import(
        importer: ExternalImporter,
        user_id: str,
        tasks_repo: TasksRepository,
        fetch_kwargs: dict[str, Any],
        normalize_kwargs: dict[str, Any] = None
) -> ImportResult:
    normalize_kwargs = normalize_kwargs or {}

    raw_data = await importer.fetch_raw(**fetch_kwargs)

    normalized = importer.normalize(raw_data, **normalize_kwargs)

    inserted_count, inserted_docs = await tasks_repo.insert_many_generic(
        user_id=user_id,
        items=normalized
    )

    details = [
        ImportTaskOut(
            id=doc["id"],
            title=doc["title"],
            date=doc["date"],
            type=doc["type"],
            status=doc["status"],
            source=doc["source"],
            meta=doc["meta"]
        )
        for doc in inserted_docs
    ]

    return ImportResult(
        imported=inserted_count,
        skipped=len(normalized) - inserted_count,
        details=details,
        errors=[]
    )
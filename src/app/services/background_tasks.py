import logging
from datetime import datetime, timedelta

from src.app.core.config import settings
from src.app.db.repositories import MotorTasksRepository, MotorUsersRepository
from src.app.core.deps import get_http_client, get_mongo_client, get_mongo_db, get_nager_importer, get_weather_importer
from src.app.services.import_service import execute_import


logger = logging.getLogger("scheduler")


async def auto_import_task():
    try:
        db = await get_mongo_db(await get_mongo_client())
        tasks_repo = MotorTasksRepository(db["tasks"])
        users_repo = MotorUsersRepository(db["users"])

        http_client = await get_http_client()
        nager = await get_nager_importer(http_client)
        weather = await get_weather_importer(http_client)

        users = await users_repo.list_all()

        imported_count = 0
        for user in users:
            holidays = await execute_import(nager, user['id'], tasks_repo,
                                      fetch_kwargs={
                                          "year": datetime.now().year,
                                          "country": "RU",
                                      },
                                      normalize_kwargs={
                                          "country": "RU"
                                      })
            weather_tasks = await execute_import(weather, user['id'], tasks_repo,
                                      fetch_kwargs={
                                          "lat": 0,
                                          "lon": 0,
                                          "days": 3,
                                      },
                                      normalize_kwargs={"lat": 0, "lon": 0, "hot_from": 20, "cold_to": 0})
            imported_count += holidays.imported + weather_tasks.imported

        logger.info(f"Auto-import completed: imported {imported_count} tasks from {len(users)} users")
    except Exception as e:
        logger.error(f"Auto-import failed: {e}", exc_info=True)


async def cleanup_expired_tasks():
    try:
        db = await get_mongo_db(await get_mongo_client())
        tasks_repo = MotorTasksRepository(db["tasks"])

        cutoff_date = datetime.utcnow() - timedelta(days=settings.CLEANUP_EXPIRED_DAYS)

        deleted_completed = await tasks_repo.delete_many(
            status="completed",
            date_lt=cutoff_date
        )

        deleted_expired = await tasks_repo.delete_many(
            date_lt=cutoff_date
        )

        total_deleted = deleted_completed + deleted_expired
        logger.info(f"Cleanup completed: removed {total_deleted} expired tasks")
    except Exception as e:
        logger.error(f"Cleanup failed: {e}", exc_info=True)


async def check_reminders():
    try:
        db = await get_mongo_db(await get_mongo_client())
        tasks_repo = MotorTasksRepository(db["tasks"])

        now = datetime.utcnow()
        reminder_time = now + timedelta(minutes=settings.REMINDER_BEFORE_MINUTES)

        upcoming_tasks = await tasks_repo.find_upcoming(
            date_from=now,
            date_to=reminder_time
        )

        for task in upcoming_tasks:
            logger.info(
                f"Reminder: '{task['title']}' in {settings.REMINDER_BEFORE_MINUTES} minutes",
                extra={"user_id": task["user_id"], "task_id": task["id"]}
            )

        if upcoming_tasks:
            logger.info(f"Reminders checked: {len(upcoming_tasks)} tasks found")
    except Exception as e:
        logger.error(f"Reminders check failed: {e}", exc_info=True)
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.app.core.config import settings
from src.app.services.background_tasks import (
    auto_import_task,
    cleanup_expired_tasks,
    check_reminders
)

logger = logging.getLogger("scheduler")


class TaskScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    def setup_tasks(self):

        if settings.AUTO_IMPORT_ENABLED:
            self.scheduler.add_job(
                auto_import_task,
                IntervalTrigger(minutes=settings.AUTO_IMPORT_INTERVAL_MINUTES),
                id="auto_import",
                name="Автоматический импорт данных",
                replace_existing=True
            )
            logger.info("Auto-import task scheduled")

        if settings.CLEANUP_ENABLED:
            self.scheduler.add_job(
                cleanup_expired_tasks,
                IntervalTrigger(hours=settings.CLEANUP_INTERVAL_HOURS),
                id="cleanup",
                name="Автоматическая очистка устаревших задач",
                replace_existing=True
            )
            logger.info("Cleanup task scheduled")

        if settings.REMINDERS_ENABLED:
            self.scheduler.add_job(
                check_reminders,
                IntervalTrigger(minutes=settings.REMINDER_CHECK_INTERVAL_MINUTES),
                id="reminders",
                name="Проверка напоминаний",
                replace_existing=True
            )
            logger.info("Reminders task scheduled")

    def start(self):
        if settings.SCHEDULER_ENABLED:
            self.setup_tasks()
            self.scheduler.start()
            logger.info("Scheduler started")

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")


scheduler = TaskScheduler()
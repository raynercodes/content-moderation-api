from celery import Celery
from config import Config

celery = Celery(
    "content_moderation",
    broker=Config.REDIS_URL,
    backend=Config.REDIS_URL,
    include=["tasks.moderation_task"]
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
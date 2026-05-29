import json
import asyncio
from celery_app import celery
from database import SessionLocal
from repos.moderation_repo import update_moderation_result
from openai import AsyncOpenAI
from config import Config
from utils.logger import logger

client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

@celery.task(bind=True, max_retries=3)
def process_moderation(self, moderation_id: int, content: str):
    try:
        logger.info(f"Processing moderation_id={moderation_id}")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        response = loop.run_until_complete(
            client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a content moderation assistant.
                        Analyze the given text and respond with a JSON object containing:
                        - decision: either 'safe', 'flagged', or 'rejected'
                        - reason: a brief explanation of your decision

                        Use these guidelines:
                        - safe: content is appropriate and harmless
                        - flagged: content is potentially problematic but not clearly harmful
                        - rejected: content is clearly harmful, abusive, or violates guidelines

                        Respond with only the JSON object, no other text."""
                    },
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=150
            )
        )

        result = response.choices[0].message.content
        parsed = json.loads(result)

        decision = parsed.get("decision", "flagged")
        reason = parsed.get("reason", "Unable to determine")

        if decision not in ["safe", "flagged", "rejected"]:
            decision = "flagged"

        db = SessionLocal()
        try:
            update_moderation_result(db, moderation_id, decision, reason)
        finally:
            db.close()

        logger.info(f"Moderation {moderation_id} completed with decision={decision}")
        return {"decision": decision, "reason": reason}

    except Exception as exc:
        logger.error(f"Moderation {moderation_id} failed: {exc}")
        raise self.retry(exc=exc, countdown=5)
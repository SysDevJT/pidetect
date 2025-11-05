import aiohttp
import asyncio
import logging
from ..config import Config

logger = logging.getLogger(__name__)

async def send_to_webhook_async(payload):
    """
    Sends a payload to the configured webhook URL.
    """
    if not Config.WEBHOOK:
        return

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(Config.WEBHOOK, json=payload, timeout=15) as resp:
                resp.raise_for_status()
                logger.debug("Webhook sent successfully")
    except Exception as e:
        logger.error(f"Webhook error: {e}")

def send_to_webhook(payload):
    """
    Synchronous wrapper for sending a webhook.
    """
    try:
        asyncio.run(send_to_webhook_async(payload))
    except RuntimeError as e:
        # This can happen if there's already an asyncio loop running.
        # In a more complex app, you'd want to handle this more gracefully.
        logger.error(f"Asyncio loop issue while sending webhook: {e}")

from application.core.config import settings
from application.core.bot import bot
from application.core.log import logger


async def send_support_message(user_id: int, message: str) -> bool:
    """Send message to support team"""
    try:
        support_text = (
            f"💬 <b>New Support Message</b>\n\n"
            f"From: {user_id}\n"
            f"Message: {message}"
        )

        # Send to all admins
        for admin_id in settings.ADMINS:
            try:
                await bot.send_message(admin_id, support_text)
            except Exception as e:
                logger.error(e)


        logger.info(f"Support message sent from user {user_id}")
        return True

    except Exception as e:
        logger.error(f"Error sending support message: {e}")
        return False

import logging
import os

# --- Asosiy sozlamalar ---
LOG_FORMAT = "%(levelname)-8s  %(name)s | %(filename)s:%(lineno)d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Muhitga qarab log darajasini aniqlash
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL = logging.DEBUG if DEBUG else logging.INFO

# Loggingni sozlash
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    force=True,  # Avvalgi konfiguratsiyalarni bekor qiladi (uvicorndan)
)

# Uvicorn va FastAPI loggerlarini sinxronlashtirish
for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
    logging.getLogger(name).setLevel(LOG_LEVEL)

# Loyihada foydalaniladigan logger
logger = logging.getLogger("application")
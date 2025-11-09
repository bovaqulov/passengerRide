import uvicorn
from application.core.config import settings

if __name__ == "__main__":

    uvicorn.run(
        "application.core.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )

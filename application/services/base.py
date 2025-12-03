from typing import Optional, Dict, Any
import aiohttp

from application.core import logger
from application.core.config import settings


class BaseService:
    """User service for API communication"""

    def __init__(self):
        self.base_url = f"{settings.MAIN_URL}/{settings.API_VERSION}"
        self.token = settings.AUTH_TOKEN
        self.session: Optional[aiohttp.ClientSession] = None

    async def create_session(self):
        """Create aiohttp session (called once at startup)"""
        if self.session is None or self.session.closed:
            headers = {"Content-Type": "application/json"}
            if self.token:
                headers["Authorization"] = f"Token {self.token}"

            self.session = aiohttp.ClientSession(headers=headers)

    async def close_session(self):
        """Close aiohttp session on shutdown"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make async HTTP request"""
        if self.session is None or self.session.closed:
            await self.create_session()

        url = f"{self.base_url}{endpoint}"

        try:
            async with self.session.request(method, url, **kwargs) as response:
                content_type = response.headers.get("Content-Type", "").lower()

                if response.status == 204:
                    return {}

                if "text/html" in content_type:
                    text = await response.text()
                    logger.warning(f"HTML response for {url}: {text[:200]}")
                    return {"error": f"Unexpected HTML ({response.status})"}

                try:
                    data = await response.json()
                except Exception:
                    text = await response.text()
                    logger.warning(f"Non-JSON response: {text[:200]}")
                    return {"error": f"Non-JSON response"}

                if not 200 <= response.status < 300:
                    msg = data.get("detail") or data.get("error") or f"HTTP {response.status}"
                    raise Exception(f"API Error: {msg}")

                return data

        except aiohttp.ClientError as e:
            raise Exception(f"Network error: {e}")

        except Exception as e:
            raise Exception(f"Request error: {e}")

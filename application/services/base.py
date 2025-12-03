from typing import Optional, Dict, Any
import aiohttp
from contextlib import asynccontextmanager

from application.core import logger
from application.core.config import settings


class BaseService:
    """Base service for API communication with proper session management"""

    def __init__(self):
        self.base_url = f"{settings.MAIN_URL}/{settings.API_VERSION}"
        self.token = settings.AUTH_TOKEN
        self.session: Optional[aiohttp.ClientSession] = None
        self._session_lock = None  # For lazy initialization

    async def ensure_session(self):
        """Ensure session exists (lazy initialization)"""
        if self.session is None or self.session.closed:
            headers = {"Content-Type": "application/json"}
            if self.token:
                headers["Authorization"] = f"Token {self.token}"

            self.session = aiohttp.ClientSession(
                headers=headers,
                connector=aiohttp.TCPConnector(limit=100, limit_per_host=20)
            )

    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make async HTTP request"""
        await self.ensure_session()

        url = f"{self.base_url}{endpoint}"

        try:
            # Don't use async with for the request - just make the request
            response = await self.session.request(method, url, **kwargs)

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
                return {"error": "Non-JSON response"}

            if not 200 <= response.status < 300:
                msg = data.get("detail") or data.get("error") or f"HTTP {response.status}"
                raise Exception(f"API Error: {msg}")

            return data

        except aiohttp.ClientError as e:
            raise Exception(f"Network error: {e}")
        except Exception as e:
            raise Exception(f"Request error: {e}")
        finally:
            # Always close the response to free connection
            if 'response' in locals():
                response.close()
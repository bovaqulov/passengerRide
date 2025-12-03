"""
Base service with proper HTTP session management
"""
from typing import Optional, Dict, Any, Union
import aiohttp

from application.core import logger
from application.core.config import settings
from .http_client import GlobalHTTPClient


class BaseService:
    """Base service for API communication with proper session management"""

    def __init__(self):
        self.base_url = f"{settings.MAIN_URL}/{settings.API_VERSION}"
        self.token = settings.AUTH_TOKEN
        self.http_client = GlobalHTTPClient()

    async def ensure_headers(self, headers: Optional[Dict] = None) -> Dict:
        """Ensure headers include authorization if token exists"""
        headers = headers or {}
        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"

        if self.token and "Authorization" not in headers:
            headers["Authorization"] = f"Token {self.token}"

        return headers

    async def _request(
            self,
            method: str,
            endpoint: str,
            **kwargs
    ) -> Dict[str, Any]:
        """Make async HTTP request with proper resource cleanup"""
        url = f"{self.base_url}{endpoint}"

        # Ensure headers
        if "headers" in kwargs:
            kwargs["headers"] = await self.ensure_headers(kwargs["headers"])
        else:
            kwargs["headers"] = await self.ensure_headers()

        try:
            # Use context manager to ensure response is properly closed
            async with self.http_client.request(method, url, **kwargs) as response:

                content_type = response.headers.get("Content-Type", "").lower()

                # Handle 204 No Content
                if response.status == 204:
                    return {}

                # Handle HTML responses (unexpected)
                if "text/html" in content_type:
                    text = await response.text()
                    logger.warning(f"HTML response for {url}: {text[:200]}")
                    return {"error": f"Unexpected HTML ({response.status})"}

                # Try to parse JSON
                try:
                    data = await response.json()
                except aiohttp.ContentTypeError:
                    text = await response.text()
                    logger.warning(f"Non-JSON response for {url}: {text[:200]}")
                    return {"error": "Non-JSON response"}
                except Exception as e:
                    logger.error(f"Error parsing JSON from {url}: {e}")
                    return {"error": f"JSON parse error: {e}"}

                # Check for HTTP errors
                if not 200 <= response.status < 300:
                    error_msg = (
                            data.get("detail") or
                            data.get("error") or
                            data.get("message") or
                            f"HTTP {response.status}"
                    )
                    logger.error(f"API error {response.status} from {url}: {error_msg}")
                    raise Exception(f"API Error: {error_msg}")

                return data

        except aiohttp.ClientError as e:
            logger.error(f"Network error for {url}: {e}")
            raise Exception(f"Network error: {e}")
        except Exception as e:
            logger.error(f"Request error for {url}: {e}")
            raise


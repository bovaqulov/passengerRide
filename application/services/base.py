from typing import Optional, Dict, Any

import aiohttp

from application.core import logger
from application.core.config import settings


class BaseService:
    """User service for API communication"""

    def __init__(self):
        self.base_url = f'{settings.MAIN_URL}/{settings.API_VERSION}'
        self.token = settings.AUTH_TOKEN
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        await self.create_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_session()

    async def create_session(self):
        """Create aiohttp session"""
        if self.session is None or self.session.closed:
            headers = {'Content-Type': 'application/json'}
            if self.token:
                headers['Authorization'] = f'Token {self.token}'

            self.session = aiohttp.ClientSession(headers=headers)

    async def close_session(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make async HTTP request"""
        await self.create_session()

        url = f"{self.base_url}{endpoint}"

        try:
            async with self.session.request(method, url, **kwargs) as response:
                # Check content type before trying to parse JSON
                content_type = response.headers.get('Content-Type', '').lower()

                if response.status == 204:  # No content
                    return {}

                # Agar HTML qaytsa, JSON deb pars qilmaslik
                if 'text/html' in content_type:
                    text_response = await response.text()
                    logger.warning(f"HTML response received for {url}: {text_response[:200]}")

                    if response.status == 404:
                        return {'detail': 'Not found'}
                    else:
                        return {'error': f'Unexpected HTML response: {response.status}'}

                # JSON responseni pars qilish
                try:
                    data = await response.json()
                except:
                    # Agar JSON pars qilib bo'lmasa
                    text_response = await response.text()
                    logger.warning(f"Non-JSON response for {url}: {text_response[:200]}")
                    return {'error': f'Non-JSON response: {text_response[:100]}'}

                if not 200 <= response.status < 300:
                    error_msg = data.get('detail') or data.get('error') or f'HTTP {response.status}'
                    raise Exception(f"API Error: {error_msg}")

                return data

        except aiohttp.ClientError as e:
            raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            raise Exception(f"Request error: {str(e)}")
        finally:
            await self.close_session()

"""
Hummingbot API client wrapper with connection management
"""

import asyncio
import logging

from hummingbot_api_client import HummingbotAPIClient

from hummingbot_mcp.exceptions import MaxConnectionsAttemptError
from hummingbot_mcp.settings import settings

logger = logging.getLogger("hummingbot-mcp")


class HummingbotClient:
    """Wrapper for HummingbotAPIClient with connection management"""

    def __init__(self):
        self._client: HummingbotAPIClient | None = None
        self._initialized = False

    async def initialize(self) -> HummingbotAPIClient:
        """Initialize API client with retry logic"""
        if self._client is not None and self._initialized:
            return self._client

        for attempt in range(settings.max_retries):
            try:
                self._client = HummingbotAPIClient(
                    base_url=settings.api_url,
                    username=settings.api_username,
                    password=settings.api_password,
                    timeout=settings.client_timeout,
                )

                # Initialize and test connection
                await self._client.init()
                await self._client.accounts.list_accounts()

                self._initialized = True
                logger.info(f"Successfully connected to Hummingbot API at {settings.api_url}")
                return self._client

            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < settings.max_retries - 1:
                    await asyncio.sleep(settings.retry_delay)
                else:
                    raise MaxConnectionsAttemptError(
                        f"Failed to connect to Hummingbot API after {settings.max_retries} attempts: {e}"
                    )

    async def get_client(self) -> HummingbotAPIClient:
        """Get initialized client"""
        if not self._client or not self._initialized:
            return await self.initialize()
        return self._client

    async def close(self):
        """Close the client connection"""
        if self._client:
            await self._client.close()
            self._client = None
            self._initialized = False


# Global client instance
hummingbot_client = HummingbotClient()

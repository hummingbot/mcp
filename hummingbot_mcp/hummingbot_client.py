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

        last_error = None
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
                last_error = e
                error_str = str(e).lower()
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")

                # Don't retry on authentication errors
                if "401" in error_str or "unauthorized" in error_str or "authentication" in error_str:
                    raise MaxConnectionsAttemptError(
                        f"❌ Authentication failed when connecting to Hummingbot API at {settings.api_url}\n\n"
                        f"The API credentials are incorrect:\n"
                        f"  - Username: {settings.api_username}\n"
                        f"  - Password: {'*' * len(settings.api_password)}\n\n"
                        f"💡 Solutions:\n"
                        f"  1. Verify your API credentials are correct\n"
                        f"  2. Use the 'configure_api_servers' tool to update server credentials\n"
                        f"  3. Check your Hummingbot API server configuration\n\n"
                        f"Original error: {e}"
                    )

                if attempt < settings.max_retries - 1:
                    await asyncio.sleep(settings.retry_delay)

        # All retries failed - provide helpful error message
        error_str = str(last_error).lower() if last_error else ""

        if "connection" in error_str or "refused" in error_str or "unreachable" in error_str or "timeout" in error_str:
            raise MaxConnectionsAttemptError(
                f"❌ Cannot reach Hummingbot API at {settings.api_url}\n\n"
                f"The API server is not responding. This usually means:\n"
                f"  - The API is not running\n"
                f"  - The API URL is incorrect\n"
                f"  - Network/firewall issues\n\n"
                f"💡 Solutions:\n"
                f"  1. Ensure the Hummingbot API is running and accessible\n"
                f"  2. Verify the API URL is correct: {settings.api_url}\n"
                f"  3. Use 'configure_api_servers' tool to update server configuration\n\n"
                f"Original error: {last_error}"
            )
        else:
            raise MaxConnectionsAttemptError(
                f"❌ Failed to connect to Hummingbot API at {settings.api_url}\n\n"
                f"Connection failed after {settings.max_retries} attempts.\n\n"
                f"💡 Solutions:\n"
                f"  1. Check if the API is running and accessible\n"
                f"  2. Verify your credentials are correct\n"
                f"  3. Use 'configure_api_servers' tool for setup\n\n"
                f"Original error: {last_error}"
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

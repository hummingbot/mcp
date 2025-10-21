"""
API Servers configuration management
Manages multiple Hummingbot API server connections
"""

import os
from pathlib import Path
from typing import Any

import aiohttp
import yaml
from pydantic import BaseModel, Field, field_validator


class APIServer(BaseModel):
    """API Server configuration"""

    name: str = Field(description="Unique name for this server")
    url: str = Field(description="API URL")
    username: str = Field(default="admin")
    password: str = Field(default="admin")
    is_default: bool = Field(default=False)

    @field_validator("url", mode="before")
    def validate_url(cls, v):
        if not v.startswith(("http://", "https://")):
            raise ValueError("API URL must start with http:// or https://")
        return v


class APIServersConfig:
    """Manages API servers configuration"""

    def __init__(self, config_path: Path | None = None):
        """
        Initialize API servers configuration

        Args:
            config_path: Path to config file. Defaults to ~/.hummingbot_mcp/servers.yml
        """
        if config_path is None:
            # Use home directory for persistence
            home = Path.home()
            config_dir = home / ".hummingbot_mcp"
            config_dir.mkdir(exist_ok=True)
            config_path = config_dir / "servers.yml"

        self.config_path = config_path
        self._servers: dict[str, APIServer] = {}
        self._load_or_create_default()

    def _load_or_create_default(self):
        """Load existing config or create default"""
        if self.config_path.exists():
            self._load()
        else:
            # Create default server from env vars or defaults
            default_server = APIServer(
                name="default",
                url=os.getenv("HUMMINGBOT_API_URL", "http://localhost:8000"),
                username=os.getenv("HUMMINGBOT_USERNAME", "admin"),
                password=os.getenv("HUMMINGBOT_PASSWORD", "admin"),
                is_default=True,
            )
            self._servers[default_server.name] = default_server
            self._save()

    def _load(self):
        """Load servers from YAML file"""
        try:
            with open(self.config_path) as f:
                data = yaml.safe_load(f) or {}
                servers_data = data.get("servers", [])

                self._servers = {}
                for server_data in servers_data:
                    server = APIServer(**server_data)
                    self._servers[server.name] = server

                # Ensure at least one default
                if not any(s.is_default for s in self._servers.values()):
                    if self._servers:
                        first_server = next(iter(self._servers.values()))
                        first_server.is_default = True
        except Exception as e:
            raise ValueError(f"Failed to load servers config: {e}")

    def _save(self):
        """Save servers to YAML file"""
        data = {"servers": [server.model_dump() for server in self._servers.values()]}

        with open(self.config_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def list_servers(self) -> dict[str, dict[str, Any]]:
        """List all configured servers"""
        return {
            name: {
                "url": server.url,
                "username": server.username,
                "is_default": server.is_default,
            }
            for name, server in self._servers.items()
        }

    def add_server(self, name: str, url: str, username: str = "admin", password: str = "admin") -> str:
        """
        Add or update a server

        Args:
            name: Server name
            url: API URL
            username: API username
            password: API password

        Returns:
            Success message
        """
        is_update = name in self._servers
        was_default = self._servers[name].is_default if is_update else False

        server = APIServer(name=name, url=url, username=username, password=password, is_default=was_default)
        self._servers[name] = server
        self._save()

        return f"Server '{name}' {'updated' if is_update else 'added'} successfully"

    def set_default(self, name: str) -> str:
        """
        Set a server as default

        Args:
            name: Server name to set as default

        Returns:
            Success message
        """
        if name not in self._servers:
            available = list(self._servers.keys())
            raise ValueError(f"Server '{name}' not found. Available servers: {available}")

        # Unset all defaults
        for server in self._servers.values():
            server.is_default = False

        # Set new default
        self._servers[name].is_default = True
        self._save()

        return f"Server '{name}' is now the default"

    def get_default_server(self) -> APIServer:
        """Get the default server configuration"""
        for server in self._servers.values():
            if server.is_default:
                return server

        # Fallback: return first server if no default set
        if self._servers:
            return next(iter(self._servers.values()))

        # This should never happen due to initialization
        raise ValueError("No servers configured")

    def modify_server(
        self, name: str, url: str | None = None, username: str | None = None, password: str | None = None
    ) -> str:
        """
        Modify an existing server configuration

        Args:
            name: Server name to modify
            url: New API URL (optional)
            username: New API username (optional)
            password: New API password (optional)

        Returns:
            Success message
        """
        if name not in self._servers:
            available = list(self._servers.keys())
            raise ValueError(f"Server '{name}' not found. Available servers: {available}")

        server = self._servers[name]
        modified_fields = []

        if url is not None:
            server.url = url
            modified_fields.append("url")
        if username is not None:
            server.username = username
            modified_fields.append("username")
        if password is not None:
            server.password = password
            modified_fields.append("password")

        if not modified_fields:
            return f"No changes specified for server '{name}'"

        self._save()
        fields_str = ", ".join(modified_fields)
        return f"Server '{name}' modified successfully ({fields_str} updated)"

    def remove_server(self, name: str) -> str:
        """
        Remove a server

        Args:
            name: Server name to remove

        Returns:
            Success message
        """
        if name not in self._servers:
            raise ValueError(f"Server '{name}' not found")

        was_default = self._servers[name].is_default
        del self._servers[name]

        # If we deleted the default, set a new one
        if was_default and self._servers:
            first_server = next(iter(self._servers.values()))
            first_server.is_default = True

        self._save()
        return f"Server '{name}' removed successfully"

    async def health_check(self, server_name: str | None = None) -> tuple[bool, str]:
        """
        Check if a server is reachable and healthy

        Args:
            server_name: Server name to check. If None, checks default server

        Returns:
            Tuple of (is_healthy, message)
        """
        if server_name is None:
            server = self.get_default_server()
        else:
            if server_name not in self._servers:
                return False, f"Server '{server_name}' not found"
            server = self._servers[server_name]

        try:
            timeout = aiohttp.ClientTimeout(total=10.0)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Try root endpoint
                async with session.get(server.url.rstrip('/')) as response:
                    if response.status == 200:
                        return True, f"Server '{server.name}' is healthy"
                    else:
                        return False, f"Server '{server.name}' returned status {response.status}"
        except aiohttp.ClientConnectorError:
            return False, f"Cannot connect to server '{server.name}' at {server.url}. Is it running?"
        except TimeoutError:
            return False, f"Server '{server.name}' timed out. Is it running?"
        except Exception as e:
            return False, f"Health check failed for server '{server.name}': {str(e)}"


# Global instance
api_servers_config = APIServersConfig()

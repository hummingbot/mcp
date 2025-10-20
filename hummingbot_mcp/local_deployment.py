"""
Local Hummingbot API deployment utilities
"""

import asyncio
import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger("hummingbot-mcp")


class LocalAPIDeployment:
    """Manages local Hummingbot API deployment"""

    def __init__(self, deployment_path: Path | None = None):
        """
        Initialize local API deployment manager

        Args:
            deployment_path: Path where API will be deployed. Defaults to ~/.hummingbot_api
        """
        if deployment_path is None:
            home = Path.home()
            deployment_path = home / ".hummingbot_api"

        self.deployment_path = deployment_path
        self.compose_file = Path(__file__).parent.parent / "docker-compose-api.yml"
        self.setup_script = Path(__file__).parent.parent / "scripts" / "setup_hummingbot_api.sh"

    def is_deployed(self) -> bool:
        """Check if API is already deployed"""
        return (self.deployment_path / ".env").exists()

    def is_running(self) -> bool:
        """Check if API containers are running"""
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=hummingbot-api", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                check=True,
            )
            return "hummingbot-api" in result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def check_docker_images_exist(self) -> dict[str, bool]:
        """
        Check if required Docker images exist locally

        Returns:
            Dictionary mapping image names to existence status
        """
        required_images = {
            "hummingbot/hummingbot:latest": False,
            "hummingbot/hummingbot-api:latest": False,
            "emqx:5": False,
            "postgres:15": False,
        }

        try:
            result = subprocess.run(
                ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
                capture_output=True,
                text=True,
                check=True,
            )
            local_images = result.stdout.strip().split("\n")

            for image in required_images:
                if image in local_images:
                    required_images[image] = True

        except subprocess.CalledProcessError:
            logger.warning("Failed to check Docker images")

        return required_images

    async def wait_for_api_health(self, timeout: int = 60, check_interval: int = 2) -> tuple[bool, str]:
        """
        Wait for API to become healthy

        Args:
            timeout: Maximum time to wait in seconds
            check_interval: Time between health checks in seconds

        Returns:
            Tuple of (success, message)
        """
        import aiohttp

        # Try root endpoint first, then docs endpoint as fallback
        urls = ["http://localhost:8000/", "http://localhost:8000/docs"]
        start_time = asyncio.get_event_loop().time()

        while (asyncio.get_event_loop().time() - start_time) < timeout:
            for url in urls:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                            # Accept any non-error status code (200-399)
                            if 200 <= response.status < 400:
                                return True, "API is healthy"
                except Exception:
                    pass

            await asyncio.sleep(check_interval)

        return False, f"API did not become healthy within {timeout} seconds"

    async def cleanup_failed_deployment(self) -> None:
        """Clean up after a failed deployment"""
        try:
            logger.info("Cleaning up failed deployment...")

            # Stop and remove containers
            target_compose = self.deployment_path / "docker-compose.yml"
            if target_compose.exists():
                process = await asyncio.create_subprocess_exec(
                    "docker",
                    "compose",
                    "-f",
                    str(target_compose),
                    "down",
                    "-v",
                    cwd=str(self.deployment_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await process.communicate()

            # Remove deployment directory
            import shutil
            if self.deployment_path.exists():
                shutil.rmtree(self.deployment_path)
                logger.info(f"Removed deployment directory: {self.deployment_path}")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def setup_interactive(self) -> tuple[bool, str]:
        """
        Run interactive setup script

        Returns:
            Tuple of (success, message)
        """
        if self.is_deployed():
            return False, f"API already deployed at {self.deployment_path}. Use 'start' to run it."

        try:
            # Create deployment directory
            self.deployment_path.mkdir(parents=True, exist_ok=True)

            # Copy docker-compose file
            if not self.compose_file.exists():
                return False, f"Docker compose file not found at {self.compose_file}"

            target_compose = self.deployment_path / "docker-compose.yml"
            with open(self.compose_file) as src:
                with open(target_compose, "w") as dst:
                    dst.write(src.read())

            # Make setup script executable and run it
            if not self.setup_script.exists():
                return False, f"Setup script not found at {self.setup_script}"

            os.chmod(self.setup_script, 0o755)

            # Run setup in the deployment directory
            process = await asyncio.create_subprocess_exec(
                "bash",
                str(self.setup_script),
                cwd=str(self.deployment_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                return True, f"Setup completed successfully!\n\nAPI deployed at: {self.deployment_path}\n\n{stdout.decode()}"
            else:
                return False, f"Setup failed: {stderr.decode()}"

        except Exception as e:
            return False, f"Setup failed: {str(e)}"

    async def setup_non_interactive(
        self, username: str = "admin", password: str = "admin", config_password: str = "admin"
    ) -> tuple[bool, str]:
        """
        Run non-interactive setup with defaults

        Args:
            username: API username
            password: API password
            config_password: Config password

        Returns:
            Tuple of (success, message)
        """
        if self.is_deployed():
            return False, f"API already deployed at {self.deployment_path}. Use 'start' to run it."

        try:
            logger.info("Starting local API deployment...")

            # Verify Docker is available
            try:
                subprocess.run(
                    ["docker", "ps"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                return False, (
                    "Docker is not running or not installed. Please:\n"
                    "1. Install Docker Desktop (https://www.docker.com/products/docker-desktop)\n"
                    "2. Start Docker Desktop\n"
                    "3. Try again"
                )

            # Create deployment directory
            self.deployment_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created deployment directory: {self.deployment_path}")

            # Create bots directory structure
            bots_dir = self.deployment_path / "bots"
            bots_dir.mkdir(exist_ok=True)
            (bots_dir / "credentials" / "master_account").mkdir(parents=True, exist_ok=True)
            (bots_dir / "controllers").mkdir(exist_ok=True)
            (bots_dir / "data").mkdir(exist_ok=True)
            logger.info("Created bots directory structure")

            # Copy docker-compose file
            if not self.compose_file.exists():
                await self.cleanup_failed_deployment()
                return False, (
                    f"Docker compose file not found at {self.compose_file}\n"
                    f"This may indicate an incomplete installation. Please reinstall the package."
                )

            target_compose = self.deployment_path / "docker-compose.yml"
            with open(self.compose_file) as src:
                with open(target_compose, "w") as dst:
                    dst.write(src.read())
            logger.info("Copied docker-compose.yml")

            # Create .env file
            env_content = f"""# =================================================================
# Backend API Environment Configuration
# Generated automatically by Hummingbot MCP
# =================================================================

# =================================================================
# 🔐 Security Configuration
# =================================================================
USERNAME={username}
PASSWORD={password}
DEBUG_MODE=false
CONFIG_PASSWORD={config_password}

# =================================================================
# 🔗 MQTT Broker Configuration (BROKER_*)
# =================================================================
BROKER_HOST=localhost
BROKER_PORT=1883
BROKER_USERNAME=admin
BROKER_PASSWORD=password

# =================================================================
# 💾 Database Configuration (DATABASE_*)
# =================================================================
DATABASE_URL=postgresql+asyncpg://hbot:hummingbot-api@localhost:5432/hummingbot_api

# =================================================================
# 📊 Market Data Feed Manager Configuration (MARKET_DATA_*)
# =================================================================
MARKET_DATA_CLEANUP_INTERVAL=300
MARKET_DATA_FEED_TIMEOUT=600

# =================================================================
# ☁️ AWS Configuration (AWS_*) - Optional
# =================================================================
AWS_API_KEY=
AWS_SECRET_KEY=
AWS_S3_DEFAULT_BUCKET_NAME=

# =================================================================
# ⚙️ Application Settings
# =================================================================
LOGFIRE_ENVIRONMENT=dev
BANNED_TOKENS=["NAV","ARS","ETHW","ETHF","NEWT"]

# =================================================================
# 🌐 Gateway Configuration (GATEWAY_*) - Optional
# =================================================================
GATEWAY_PASSPHRASE=admin

# =================================================================
# 📁 Legacy Settings (maintained for backward compatibility)
# =================================================================
BOTS_PATH={bots_dir}
"""

            env_file = self.deployment_path / ".env"
            with open(env_file, "w") as f:
                f.write(env_content)
            logger.info("Created .env file")

            # Check which images need to be downloaded
            images_status = self.check_docker_images_exist()
            missing_images = [img for img, exists in images_status.items() if not exists]

            download_info = ""
            if missing_images:
                download_info = (
                    f"\n📥 Downloading {len(missing_images)} Docker image(s) for the first time.\n"
                    f"   This may take 5-10 minutes depending on your internet connection.\n"
                    f"   Images to download: {', '.join(missing_images)}\n"
                )
                logger.info(f"Missing images detected: {missing_images}")
            else:
                logger.info("All Docker images already present locally")

            logger.info("Pulling Docker images (this may take a few minutes)...")

            # Pull images first (all 4 images needed by docker-compose)
            pull_commands = [
                ("hummingbot/hummingbot:latest", ["docker", "pull", "hummingbot/hummingbot:latest"]),
                ("hummingbot/hummingbot-api:latest", ["docker", "pull", "hummingbot/hummingbot-api:latest"]),
                ("emqx:5", ["docker", "pull", "emqx:5"]),
                ("postgres:15", ["docker", "pull", "postgres:15"]),
            ]

            for image_name, cmd in pull_commands:
                logger.info(f"Pulling {image_name}...")
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await process.communicate()

                if process.returncode != 0:
                    error_msg = stderr.decode()
                    logger.error(f"Failed to pull {image_name}: {error_msg}")
                    await self.cleanup_failed_deployment()
                    return False, (
                        f"Failed to pull Docker image {image_name}.\n"
                        f"Error: {error_msg}\n\n"
                        f"Please check your internet connection and Docker configuration."
                    )

            logger.info("Starting Docker containers...")

            # Start containers
            process = await asyncio.create_subprocess_exec(
                "docker",
                "compose",
                "-f",
                str(target_compose),
                "up",
                "-d",
                cwd=str(self.deployment_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode()
                logger.error(f"Failed to start containers: {error_msg}")
                await self.cleanup_failed_deployment()
                return False, (
                    f"Failed to start Docker containers.\n"
                    f"Error: {error_msg}\n\n"
                    f"Common issues:\n"
                    f"- Ports 8000, 5432, or 1883 may already be in use\n"
                    f"- Docker may not have enough resources allocated"
                )

            logger.info("Waiting for API to become healthy...")

            # Wait for API to become healthy
            is_healthy, health_msg = await self.wait_for_api_health(timeout=60)

            if not is_healthy:
                logger.error(f"API health check failed: {health_msg}")
                # Get container logs for debugging
                logs_process = await asyncio.create_subprocess_exec(
                    "docker",
                    "compose",
                    "-f",
                    str(target_compose),
                    "logs",
                    "--tail=20",
                    "hummingbot-api",
                    cwd=str(self.deployment_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                logs_stdout, _ = await logs_process.communicate()
                container_logs = logs_stdout.decode()

                await self.cleanup_failed_deployment()
                return False, (
                    f"API failed to start properly: {health_msg}\n\n"
                    f"Last 20 lines from API container logs:\n{container_logs}\n\n"
                    f"The deployment has been cleaned up. Please check the logs above and try again."
                )

            logger.info("API is healthy and ready!")

            success_message = f"""Setup completed successfully!
{download_info if download_info else ""}
API deployed at: {self.deployment_path}
API URL: http://localhost:8000
API Docs: http://localhost:8000/docs

Credentials:
  Username: {username}
  Password: {password}

Status: ✅ All services are running and healthy

Next steps:
1. The API is now running at http://localhost:8000
2. You can access the API docs at http://localhost:8000/docs
3. Set this as your default server using configure_api_servers tool

Services running:
  - Hummingbot API (port 8000)
  - PostgreSQL Database (port 5432)
  - EMQX MQTT Broker (port 1883, dashboard at http://localhost:18083)
"""

            return (True, success_message)

        except Exception as e:
            logger.error(f"Setup failed with unexpected error: {e}", exc_info=True)
            await self.cleanup_failed_deployment()
            return False, f"Setup failed: {str(e)}\n\nDeployment has been cleaned up."

    async def start(self) -> tuple[bool, str]:
        """
        Start the API containers

        Returns:
            Tuple of (success, message)
        """
        if not self.is_deployed():
            return False, (
                f"API not deployed yet at {self.deployment_path}.\n"
                f"Use action='setup' to deploy the local API first."
            )

        if self.is_running():
            return False, "API is already running at http://localhost:8000"

        try:
            # Check if images need to be downloaded
            images_status = self.check_docker_images_exist()
            missing_images = [img for img, exists in images_status.items() if not exists]

            download_note = ""
            if missing_images:
                download_note = (
                    f"\n📥 Note: {len(missing_images)} Docker image(s) need to be downloaded first.\n"
                    f"   This may take 5-10 minutes. Images: {', '.join(missing_images)}\n"
                )

            logger.info("Starting API containers...")
            target_compose = self.deployment_path / "docker-compose.yml"

            process = await asyncio.create_subprocess_exec(
                "docker",
                "compose",
                "-f",
                str(target_compose),
                "up",
                "-d",
                cwd=str(self.deployment_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode()
                logger.error(f"Failed to start containers: {error_msg}")
                return False, (
                    f"Failed to start API containers.\n"
                    f"Error: {error_msg}\n\n"
                    f"Try checking:\n"
                    f"- Are ports 8000, 5432, 1883 available?\n"
                    f"- Does Docker have enough resources?"
                )

            logger.info("Waiting for API to become healthy...")

            # Wait for API to become healthy
            is_healthy, health_msg = await self.wait_for_api_health(timeout=60)

            if not is_healthy:
                return False, (
                    f"API containers started but health check failed: {health_msg}\n\n"
                    f"Check logs with: docker compose -f {target_compose} logs hummingbot-api"
                )

            success_msg = f"""API started successfully!
{download_note if download_note else ""}
API URL: http://localhost:8000
API Docs: http://localhost:8000/docs

Status: ✅ All services are running and healthy"""

            return True, success_msg

        except Exception as e:
            logger.error(f"Failed to start API: {e}", exc_info=True)
            return False, f"Failed to start API: {str(e)}"

    async def stop(self) -> tuple[bool, str]:
        """
        Stop the API containers

        Returns:
            Tuple of (success, message)
        """
        if not self.is_deployed():
            return False, "API not deployed"

        if not self.is_running():
            return False, "API is not running"

        try:
            target_compose = self.deployment_path / "docker-compose.yml"

            process = await asyncio.create_subprocess_exec(
                "docker",
                "compose",
                "-f",
                str(target_compose),
                "down",
                cwd=str(self.deployment_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                return True, "API stopped successfully"
            else:
                return False, f"Failed to stop API: {stderr.decode()}"

        except Exception as e:
            return False, f"Failed to stop API: {str(e)}"

    async def test_api_connection(self, username: str = "admin", password: str = "admin") -> dict:
        """
        Test API connection and authentication

        Args:
            username: Username to test
            password: Password to test

        Returns:
            Dictionary with connection status and details
        """
        import aiohttp
        import base64

        result = {
            "api_reachable": False,
            "auth_valid": False,
            "error": None,
        }

        try:
            # First check if API is reachable (unauthenticated endpoint)
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://localhost:8000/",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if 200 <= response.status < 400:
                        result["api_reachable"] = True

                # Now test authenticated endpoint
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                headers = {"Authorization": f"Basic {credentials}"}

                async with session.get(
                    "http://localhost:8000/accounts/",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        result["auth_valid"] = True
                    elif response.status == 401:
                        result["error"] = "Invalid credentials"
                    else:
                        result["error"] = f"Unexpected status: {response.status}"

        except aiohttp.ClientConnectorError:
            result["error"] = "Cannot connect to API"
        except asyncio.TimeoutError:
            result["error"] = "Connection timeout"
        except Exception as e:
            result["error"] = str(e)

        return result

    async def status(self, test_connection: bool = True) -> dict:
        """
        Get deployment status

        Args:
            test_connection: Whether to test the API connection (default: True)

        Returns:
            Status dictionary
        """
        deployed = self.is_deployed()
        running = self.is_running()

        status = {
            "deployed": deployed,
            "running": running,
            "deployment_path": str(self.deployment_path),
            "api_url": "http://localhost:8000" if running else None,
        }

        # Always test connection if requested, even if containers aren't detected
        # (API might be running but not managed by this tool)
        if test_connection:
            # Try to get credentials from .env file if deployed
            username = "admin"
            password = "admin"

            env_file = self.deployment_path / ".env"
            if env_file.exists():
                try:
                    with open(env_file) as f:
                        for line in f:
                            if line.startswith("USERNAME="):
                                username = line.split("=", 1)[1].strip()
                            elif line.startswith("PASSWORD="):
                                password = line.split("=", 1)[1].strip()
                except Exception:
                    pass

            connection_test = await self.test_api_connection(username, password)
            status["connection_test"] = connection_test

            # If API is reachable but containers not detected, it's running externally
            if connection_test["api_reachable"] and not running:
                status["running_externally"] = True

        return status


# Global instance
local_api = LocalAPIDeployment()

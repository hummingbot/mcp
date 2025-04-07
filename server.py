# server.py
from mcp.server.fastmcp import FastMCP
from services.backend_api_client import BackendAPIClient
from typing import List, Optional

# Create an MCP server
mcp = FastMCP("Hummingbot")


@mcp.tool()
async def get_account_state():
    """Get the current account state"""
    client = BackendAPIClient.get_instance()
    return await client.get_accounts_state()


@mcp.tool()
async def get_real_time_candles(connector: str, trading_pair: str, interval: str, max_records: int):
    """Get real-time candles data"""
    client = BackendAPIClient.get_instance()
    return await client.get_real_time_candles(connector, trading_pair, interval, max_records)


@mcp.tool()
async def get_active_bots():
    """Get status of all active bots"""
    client = BackendAPIClient.get_instance()
    return await client.get_active_bots_status()


@mcp.tool()
async def get_available_controllers_config():
    """Get all available controller configurations"""
    client = BackendAPIClient.get_instance()
    return await client.get_all_controllers_config()


@mcp.tool()
async def get_controller_config(controller_id: str):
    """Get configuration for a specific controller"""
    client = BackendAPIClient.get_instance()
    all_controllers = await client.get_all_controllers_config()
    for controller in all_controllers["configs"]:
        if controller["id"] == controller_id:
            return controller
    return {"error": f"Controller with ID {controller_id} not found"}

@mcp.tool()
async def get_avaialble_controllers():
    """Get all available controllers"""
    client = BackendAPIClient.get_instance()
    return await client.list_controllers()

@mcp.tool()
async def get_controller_config_pydantic(controller_type: str, controller_name: str):
    """Get controller configuration with default values from its Pydantic model"""
    client = BackendAPIClient.get_instance()
    return await client.get_controller_config_pydantic(controller_type, controller_name)


@mcp.tool()
async def upload_controller_config(controller_config: dict):
    """Upload a new controller configuration"""
    client = BackendAPIClient.get_instance()
    return await client.add_controller_config(controller_config)


@mcp.tool()
async def deploy_bot_with_controllers(
    bot_name: str, 
    controller_configs: List[str],
    script_name: str = "v2_with_controllers.py",
    image_name: str = "hummingbot/hummingbot:latest",
    credentials: str = "master_account",
    time_to_cash_out: Optional[int] = None,
    max_global_drawdown: Optional[float] = None,
    max_controller_drawdown: Optional[float] = None
):
    """Deploy a bot with specified controllers"""
    client = BackendAPIClient.get_instance()
    return await client.deploy_script_with_controllers(
        bot_name=bot_name,
        controller_configs=controller_configs,
        script_name=script_name,
        image_name=image_name,
        credentials=credentials,
        time_to_cash_out=time_to_cash_out,
        max_global_drawdown=max_global_drawdown,
        max_controller_drawdown=max_controller_drawdown
    )

@mcp.tool()
async def stop_controller_from_bot(bot_name: str, controller_id: str):
    """Stop a controller from a bot"""
    client = BackendAPIClient.get_instance()
    return await client.stop_controller_from_bot(bot_name, controller_id)

@mcp.tool()
async def stop_bot(bot_name: str, skip_order_cancellation: bool = False):
    """Stop a Hummingbot bot"""
    client = BackendAPIClient.get_instance()
    return await client.stop_bot(bot_name, skip_order_cancellation)

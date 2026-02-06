"""
Controller management operations business logic.

This module provides the core business logic for managing controllers and their
configurations, including exploration, modification, and bot deployment.
"""
from typing import Any, Literal


async def manage_controllers(
    client: Any,
    action: Literal["list", "describe", "upsert", "delete"],
    target: Literal["controller", "config"] | None = None,
    controller_type: Literal["directional_trading", "market_making", "generic"] | None = None,
    controller_name: str | None = None,
    controller_code: str | None = None,
    config_name: str | None = None,
    config_data: dict[str, Any] | None = None,
    bot_name: str | None = None,
    confirm_override: bool = False,
) -> dict[str, Any]:
    """
    Unified controller management: list, describe, upsert, delete.

    Routes to explore_controllers for list/describe and modify_controllers for upsert/delete.
    """
    if action in ("list", "describe"):
        return await explore_controllers(
            client=client,
            action=action,
            controller_type=controller_type,
            controller_name=controller_name,
            config_name=config_name,
        )
    elif action in ("upsert", "delete"):
        if not target:
            raise ValueError("'target' parameter ('controller' or 'config') is required for upsert/delete actions")
        return await modify_controllers(
            client=client,
            action=action,
            target=target,
            controller_type=controller_type,
            controller_name=controller_name,
            controller_code=controller_code,
            config_name=config_name,
            config_data=config_data,
            bot_name=bot_name,
            confirm_override=confirm_override,
        )
    else:
        raise ValueError(f"Invalid action '{action}'. Use 'list', 'describe', 'upsert', or 'delete'.")


async def explore_controllers(
    client: Any,
    action: Literal["list", "describe"],
    controller_type: Literal["directional_trading", "market_making", "generic"] | None = None,
    controller_name: str | None = None,
    config_name: str | None = None,
) -> dict[str, Any]:
    """
    Explore controllers and their configurations.

    Args:
        client: Hummingbot API client
        action: "list" to list controllers or "describe" to show details
        controller_type: Type of controller to filter by
        controller_name: Name of controller to describe
        config_name: Name of config to describe

    Returns:
        Dictionary containing exploration results and formatted output
    """
    # List all controllers and their configs
    controllers = await client.controllers.list_controllers()
    configs = await client.controllers.list_controller_configs()

    if action == "list":
        result = "Available Controllers:\n\n"
        for c_type, controller_list in controllers.items():
            if controller_type is not None and c_type != controller_type:
                continue
            result += f"Controller Type: {c_type}\n"
            for controller in controller_list:
                controller_configs = [c for c in configs if c.get('controller_name') == controller]
                result += f"- {controller} ({len(controller_configs)} configs)\n"
                if len(controller_configs) > 0:
                    for config in controller_configs:
                        result += f"    - {config.get('id', 'unknown')}\n"

        return {
            "action": "list",
            "controllers": controllers,
            "configs": configs,
            "formatted_output": result,
        }

    elif action == "describe":
        result = ""
        config = None

        # Get config if specified
        if config_name:
            config = await client.controllers.get_controller_config(config_name)
            if config:
                if controller_name and controller_name != config.get("controller_name"):
                    controller_name = config.get("controller_name")
                    result += f"Controller name not matching, using config's controller name: {controller_name}\n"
                elif not controller_name:
                    controller_name = config.get("controller_name")
                result += f"Config Details for {config_name}:\n{config}\n\n"

        if not controller_name:
            return {
                "action": "describe",
                "error": "Please provide a controller name to describe.",
                "formatted_output": "Please provide a controller name to describe.",
            }

        # Determine the controller type
        found_controller_type = None
        for c_type, controller_list in controllers.items():
            if controller_name in controller_list:
                found_controller_type = c_type
                break

        if not found_controller_type:
            return {
                "action": "describe",
                "error": f"Controller '{controller_name}' not found.",
                "formatted_output": f"Controller '{controller_name}' not found.",
            }

        # Get controller code and configs
        controller_code = await client.controllers.get_controller(found_controller_type, controller_name)
        controller_configs = [c.get("id") for c in configs if c.get('controller_name') == controller_name]
        template = await client.controllers.get_controller_config_template(found_controller_type, controller_name)

        result += f"Controller: {controller_name} ({found_controller_type})\n\n"
        result += f"Controller Code:\n{controller_code}\n\n"

        # Format configs list
        result += f"Total Configs Available: {len(controller_configs)}\n"
        if len(controller_configs) <= 10:
            result += f"Configs:\n" + "\n".join(f"  - {c}" for c in controller_configs if c) + "\n\n"
        else:
            result += f"Configs (showing first 10 of {len(controller_configs)}):\n"
            result += "\n".join(f"  - {c}" for c in controller_configs[:10] if c) + "\n"
            result += f"  ... and {len(controller_configs) - 10} more\n\n"

        # Format config template parameters as table
        result += "Configuration Parameters:\n"
        result += "parameter                    | type              | default\n"
        result += "-" * 80 + "\n"

        for param_name, param_info in template.items():
            if param_name in ['id', 'controller_name', 'controller_type', 'candles_config', 'initial_positions']:
                continue  # Skip internal fields

            param_type = str(param_info.get('type', 'unknown'))
            # Simplify type names
            param_type = param_type.replace("<class '", "").replace("'>", "").replace("decimal.Decimal", "Decimal")
            param_type = param_type.replace("typing.", "").split(".")[-1][:15]

            default = str(param_info.get('default', 'None'))
            if len(default) > 30:
                default = default[:27] + "..."

            result += f"{param_name:28} | {param_type:17} | {default}\n"

        return {
            "action": "describe",
            "controller_name": controller_name,
            "controller_type": found_controller_type,
            "controller_code": controller_code,
            "template": template,
            "configs": controller_configs,
            "config_details": config,
            "formatted_output": result,
        }

    else:
        return {
            "action": action,
            "error": "Invalid action. Use 'list' or 'describe'.",
            "formatted_output": "Invalid action. Use 'list' or 'describe'.",
        }


async def modify_controllers(
    client: Any,
    action: Literal["upsert", "delete"],
    target: Literal["controller", "config"],
    controller_type: Literal["directional_trading", "market_making", "generic"] | None = None,
    controller_name: str | None = None,
    controller_code: str | None = None,
    config_name: str | None = None,
    config_data: dict[str, Any] | None = None,
    bot_name: str | None = None,
    confirm_override: bool = False,
) -> dict[str, Any]:
    """
    Create, update, or delete controllers and configurations.

    Args:
        client: Hummingbot API client
        action: "upsert" (create/update) or "delete"
        target: "controller" (template) or "config" (instance)
        controller_type: Type of controller
        controller_name: Name of controller
        controller_code: Code for controller (required for controller upsert)
        config_name: Name of config
        config_data: Configuration data (required for config upsert)
        bot_name: Bot name (for config modification in specific bot)
        confirm_override: Confirm overwriting existing items

    Returns:
        Dictionary containing modification results and message

    Raises:
        ValueError: If required parameters are missing or invalid
    """
    if target == "controller":
        if action == "upsert":
            if not controller_type or not controller_name or not controller_code:
                raise ValueError("controller_type, controller_name, and controller_code are required for controller upsert")

            # Check if controller exists
            controllers = await client.controllers.list_controllers()
            exists = controller_name in controllers.get(controller_type, [])

            if exists and not confirm_override:
                existing_code = await client.controllers.get_controller(controller_type, controller_name)
                return {
                    "action": "upsert",
                    "target": "controller",
                    "exists": True,
                    "controller_name": controller_name,
                    "controller_type": controller_type,
                    "current_code": existing_code,
                    "message": (f"Controller '{controller_name}' already exists and this is the current code: {existing_code}. "
                               f"Set confirm_override=True to update it."),
                }

            result = await client.controllers.create_or_update_controller(
                controller_type, controller_name, controller_code
            )

            return {
                "action": "upsert",
                "target": "controller",
                "exists": exists,
                "controller_name": controller_name,
                "controller_type": controller_type,
                "result": result,
                "message": f"Controller {'updated' if exists else 'created'}: {result}",
            }

        elif action == "delete":
            if not controller_type or not controller_name:
                raise ValueError("controller_type and controller_name are required for controller delete")

            result = await client.controllers.delete_controller(controller_type, controller_name)

            return {
                "action": "delete",
                "target": "controller",
                "controller_name": controller_name,
                "controller_type": controller_type,
                "result": result,
                "message": f"Controller deleted: {result}",
            }

    elif target == "config":
        if action == "upsert":
            if not config_name or not config_data:
                raise ValueError("config_name and config_data are required for config upsert")

            # Extract controller_type and controller_name from config_data
            config_controller_type = config_data.get("controller_type")
            config_controller_name = config_data.get("controller_name")

            if not config_controller_type or not config_controller_name:
                raise ValueError("config_data must include 'controller_type' and 'controller_name'")

            # Validate config first
            await client.controllers.validate_controller_config(config_controller_type, config_controller_name, config_data)

            if bot_name:
                # Modifying config in a specific bot
                if not confirm_override:
                    current_configs = await client.controllers.get_bot_controller_configs(bot_name)
                    config = next((c for c in current_configs if c.get("id") == config_name), None)
                    if config:
                        return {
                            "action": "upsert",
                            "target": "config",
                            "exists": True,
                            "config_name": config_name,
                            "bot_name": bot_name,
                            "current_config": config,
                            "message": (f"Config '{config_name}' already exists in bot '{bot_name}' with data: {config}. "
                                       "Set confirm_override=True to update it."),
                        }
                    else:
                        update_op = await client.controllers.update_bot_controller_config(bot_name, config_name, config_data)
                        return {
                            "action": "upsert",
                            "target": "config",
                            "exists": False,
                            "config_name": config_name,
                            "bot_name": bot_name,
                            "result": update_op,
                            "message": f"Config created in bot '{bot_name}': {update_op}",
                        }
                else:
                    # Ensure config_data has the correct id
                    if "id" not in config_data or config_data["id"] != config_name:
                        config_data["id"] = config_name
                    update_op = await client.controllers.update_bot_controller_config(bot_name, config_name, config_data)
                    return {
                        "action": "upsert",
                        "target": "config",
                        "exists": True,
                        "config_name": config_name,
                        "bot_name": bot_name,
                        "result": update_op,
                        "message": f"Config updated in bot '{bot_name}': {update_op}",
                    }
            else:
                # Modifying global config
                if "id" not in config_data or config_data["id"] != config_name:
                    config_data["id"] = config_name

                controller_configs = await client.controllers.list_controller_configs()
                exists = config_name in [c.get("id") for c in controller_configs]

                if exists and not confirm_override:
                    existing_config = await client.controllers.get_controller_config(config_name)
                    return {
                        "action": "upsert",
                        "target": "config",
                        "exists": True,
                        "config_name": config_name,
                        "current_config": existing_config,
                        "message": (f"Config '{config_name}' already exists with data: {existing_config}. "
                                   "Set confirm_override=True to update it."),
                    }

                result = await client.controllers.create_or_update_controller_config(config_name, config_data)
                return {
                    "action": "upsert",
                    "target": "config",
                    "exists": exists,
                    "config_name": config_name,
                    "result": result,
                    "message": f"Config {'updated' if exists else 'created'}: {result}",
                }

        elif action == "delete":
            if not config_name:
                raise ValueError("config_name is required for config delete")

            result = await client.controllers.delete_controller_config(config_name)
            await client.bot_orchestration.deploy_v2_controllers()

            return {
                "action": "delete",
                "target": "config",
                "config_name": config_name,
                "result": result,
                "message": f"Config deleted: {result}",
            }

    else:
        raise ValueError("Invalid target. Must be 'controller' or 'config'.")


async def deploy_bot(
    client: Any,
    bot_name: str,
    controllers_config: list[str],
    account_name: str | None = "master_account",
    max_global_drawdown_quote: float | None = None,
    max_controller_drawdown_quote: float | None = None,
    image: str = "hummingbot/hummingbot:latest",
) -> dict[str, Any]:
    """
    Deploy a bot with specified controller configurations.

    Args:
        client: Hummingbot API client
        bot_name: Name of the bot to deploy
        controllers_config: List of controller config names
        account_name: Account name to use
        max_global_drawdown_quote: Maximum global drawdown
        max_controller_drawdown_quote: Maximum per-controller drawdown
        image: Docker image to use

    Returns:
        Dictionary containing deployment results
    """
    result = await client.bot_orchestration.deploy_v2_controllers(
        instance_name=bot_name,
        controllers_config=controllers_config,
        credentials_profile=account_name,
        max_global_drawdown_quote=max_global_drawdown_quote,
        max_controller_drawdown_quote=max_controller_drawdown_quote,
        image=image,
    )

    return {
        "bot_name": bot_name,
        "controllers_config": controllers_config,
        "account_name": account_name,
        "image": image,
        "result": result,
        "message": f"Bot Deployment Result: {result}",
    }

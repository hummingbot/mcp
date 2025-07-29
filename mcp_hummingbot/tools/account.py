"""
Account management tools for Hummingbot MCP Server
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from pydantic import BaseModel, Field, field_validator
from mcp.types import Tool
from ..client import hummingbot_client
from ..config.settings import settings
from ..exceptions import ToolError
import logging

logger = logging.getLogger("hummingbot-mcp")


class SetupConnectorRequest(BaseModel):
    """Request model for setting up exchange connectors with progressive disclosure.
    
    This model supports a four-step flow:
    1. No parameters → List available exchanges
    2. Connector only → Show required credential fields  
    3. Connector + credentials, no account → Select account from available accounts
    4. All parameters → Connect the exchange (with override confirmation if needed)
    """
    
    account: Optional[str] = Field(
        default=None,
        description="Account name to add credentials to. If not provided, uses the default account."
    )
    
    connector: Optional[str] = Field(
        default=None,
        description="Exchange connector name (e.g., 'binance', 'coinbase_pro'). Leave empty to list available connectors.",
        examples=["binance", "coinbase_pro", "kraken", "gate_io"]
    )
    
    credentials: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Credentials object with required fields for the connector. Leave empty to see required fields first.",
        examples=[
            {"binance_api_key": "your_api_key", "binance_secret_key": "your_secret"},
            {"coinbase_pro_api_key": "your_key", "coinbase_pro_secret_key": "your_secret", "coinbase_pro_passphrase": "your_passphrase"}
        ]
    )
    
    confirm_override: Optional[bool] = Field(
        default=None,
        description="Explicit confirmation to override existing connector. Required when connector already exists."
    )
    
    @field_validator('connector')
    @classmethod
    def validate_connector_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate connector name format if provided"""
        if v is not None:
            # Convert to lowercase and replace spaces/hyphens with underscores
            v = v.lower().replace(' ', '_').replace('-', '_')
            
            # Basic validation - should be alphanumeric with underscores
            if not v.replace('_', '').isalnum():
                raise ValueError("Connector name should contain only letters, numbers, and underscores")
        
        return v
    
    @field_validator('credentials')
    @classmethod
    def validate_credentials(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate credentials format if provided"""
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError("Credentials must be a dictionary/object")
            
            if not v:  # Empty dict
                raise ValueError("Credentials cannot be empty. Omit the field to see required fields.")
            
            # Check that all values are strings (typical for API credentials)
            # except for force_override which can be boolean
            for key, value in v.items():
                if key == "force_override":
                    if not isinstance(value, bool):
                        raise ValueError("'force_override' must be a boolean (true/false)")
                else:
                    if not isinstance(value, str):
                        raise ValueError(f"Credential '{key}' must be a string")
                    if not value.strip():  # Empty or whitespace-only
                        raise ValueError(f"Credential '{key}' cannot be empty")
        
        return v
    
    def get_account_name(self) -> str:
        """Get account name with fallback to default"""
        return self.account or settings.default_account
    
    def get_flow_stage(self) -> str:
        """Determine which stage of the setup flow we're in"""

        if self.connector is None:
            return "list_exchanges"
        elif self.credentials is None:
            return "show_config"
        elif self.account is None:
            return "select_account"
        else:
            return "connect"
    
    def requires_override_confirmation(self) -> bool:
        """Check if this request needs override confirmation"""
        return (self.credentials is not None and 
                self.confirm_override is None)


async def _check_existing_connector(account_name: str, connector_name: str) -> bool:
    """Check if a connector already exists for the given account"""
    try:
        client = await hummingbot_client.get_client()
        credentials = await client.accounts.list_account_credentials(account_name=account_name)
        
        # Check if the account exists and has the connector
        return connector_name in credentials
    except Exception as e:
        logger.warning(f"Failed to check existing connector: {str(e)}")
        return False


async def setup_connector(request: SetupConnectorRequest) -> Dict[str, Any]:
    """Setup a new exchange connector with credentials using progressive disclosure.
    
    This function handles four different flows based on the provided parameters:
    1. No connector → List available exchanges
    2. Connector only → Show required credential fields  
    3. Connector + credentials, no account → Select account from available accounts
    4. All parameters → Connect the exchange (with override confirmation if needed)
    """
    try:
        client = await hummingbot_client.get_client()
        flow_stage = request.get_flow_stage()
        
        if flow_stage == "select_account":
            # Step 2.5: List available accounts for selection (after connector and credentials are provided)
            accounts = await client.accounts.list_accounts()
            
            return {
                "action": "select_account",
                "message": f"Ready to connect {request.connector}. Please select an account:",
                "connector": request.connector,
                "accounts": accounts,
                "default_account": settings.default_account,
                "next_step": "Call again with 'account' parameter to specify which account to use",
                "example": f"Use account='{settings.default_account}' to use the default account, or choose from the available accounts above"
            }
        
        elif flow_stage == "list_exchanges":
            # Step 1: List available connectors
            connectors = await client.connectors.list_connectors()
            
            # Handle both string and object responses from the API
            connector_names = []
            for c in connectors:
                if isinstance(c, str):
                    connector_names.append(c)
                elif hasattr(c, 'name'):
                    connector_names.append(c.name)
                else:
                    connector_names.append(str(c))
            
            return {
                "action": "list_connectors",
                "message": "Available exchange connectors:",
                "connectors": connector_names,
                "total_connectors": len(connector_names),
                "next_step": "Call again with 'connector' parameter to see required credentials for a specific exchange",
                "example": "Use connector='binance' to see Binance setup requirements"
            }
        
        elif flow_stage == "show_config":
            # Step 2: Show required credential fields for the connector
            try:
                config_fields = await client.connectors.get_config_map(request.connector)
                
                # Build a dictionary from the list of field names
                credentials_dict = {field: f"your_{field}" for field in config_fields}
                
                return {
                    "action": "show_config_map",
                    "connector": request.connector,
                    "required_fields": config_fields,
                    "next_step": "Call again with 'credentials' parameter containing the required fields",
                    "example": f"Use credentials={credentials_dict} to connect"
                }
            except Exception as e:
                raise ToolError(f"Failed to get configuration for connector '{request.connector}': {str(e)}")
        
        elif flow_stage == "connect":
            # Step 3: Actually connect the exchange with provided credentials
            account_name = request.get_account_name()
            
            # Check if connector already exists
            connector_exists = await _check_existing_connector(account_name, request.connector)
            
            if connector_exists and request.requires_override_confirmation():
                return {
                    "action": "requires_confirmation",
                    "message": f"WARNING: Connector '{request.connector}' already exists for account '{account_name}'",
                    "account": account_name,
                    "connector": request.connector,
                    "warning": "Adding credentials will override the existing connector configuration",
                    "next_step": "To proceed with overriding, add 'confirm_override': true to your request",
                    "example": f"Use confirm_override=true along with your credentials to override the existing connector"
                }
            
            if connector_exists and not request.confirm_override:
                return {
                    "action": "override_rejected",
                    "message": f"Cannot override existing connector '{request.connector}' without explicit confirmation",
                    "account": account_name,
                    "connector": request.connector,
                    "next_step": "Set confirm_override=true to override the existing connector"
                }
            
            # Remove force_override from credentials before sending to API
            credentials_to_send = dict(request.credentials)
            if "force_override" in credentials_to_send:
                del credentials_to_send["force_override"]
            
            try:
                await client.accounts.add_credential(
                    account_name=account_name,
                    connector_name=request.connector,
                    credentials=credentials_to_send
                )
                
                action_type = "credentials_overridden" if connector_exists else "credentials_added"
                message_action = "overridden" if connector_exists else "connected"
                
                return {
                    "action": action_type,
                    "message": f"Successfully {message_action} {request.connector} exchange to account '{account_name}'",
                    "account": account_name,
                    "connector": request.connector,
                    "credentials_count": len(credentials_to_send),
                    "was_existing": connector_exists,
                    "next_step": "Exchange is now ready for trading. Use get_account_state to verify the connection."
                }
            except Exception as e:
                raise ToolError(f"Failed to add credentials for {request.connector}: {str(e)}")
        
        else:
            raise ToolError(f"Unknown flow stage: {flow_stage}")
            
    except Exception as e:
        if isinstance(e, ToolError):
            raise
        else:
            logger.error(f"Unexpected error in setup_connector: {str(e)}", exc_info=True)
            raise ToolError(f"Setup connector failed: {str(e)}")

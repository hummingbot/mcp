"""
Gateway CLMM tools for Hummingbot MCP Server

Handles DEX CLMM liquidity operations via Hummingbot Gateway:
- Pool exploration (list pools, get pool info)
- Position management (open, close, collect fees, search positions)
"""
import logging
from typing import Any, Literal
from decimal import Decimal

from pydantic import BaseModel, Field

from hummingbot_mcp.exceptions import ToolError
from hummingbot_mcp.hummingbot_client import hummingbot_client

logger = logging.getLogger("hummingbot-mcp")


def format_pools_as_table(pools: list[dict[str, Any]]) -> str:
    """
    Format pool data as a table string for better LLM processing.

    Columns: address | name | mint_x | mint_y | bin_step | current_price | liquidity | apr | apy | volume_24h | fees_24h
    """
    if not pools:
        return "No pools found."

    def truncate_address(addr: str) -> str:
        """Return full address without truncation"""
        if not addr or addr == "N/A":
            return "N/A"
        return addr

    def format_number(num: Any) -> str:
        """Format number to be more compact"""
        if num is None or num == "N/A":
            return "N/A"
        try:
            num_float = float(num)
            if num_float == 0:
                return "0"
            if num_float >= 1_000_000:
                return f"{num_float/1_000_000:.2f}M"
            elif num_float >= 1_000:
                return f"{num_float/1_000:.2f}K"
            elif num_float >= 1:
                return f"{num_float:.4f}"
            else:
                return f"{num_float:.6f}"
        except (ValueError, TypeError):
            return str(num)

    # Header
    header = "address | name | mint_x | mint_y | bin_step | price | liquidity | apr | apy | volume_24h | fees_24h"
    separator = "-" * 200

    # Format each pool as a row
    rows = []
    for pool in pools:
        row = (
            f"{truncate_address(pool.get('address', 'N/A'))} | "
            f"{pool.get('name', 'N/A')[:12]} | "
            f"{truncate_address(pool.get('mint_x', 'N/A'))} | "
            f"{truncate_address(pool.get('mint_y', 'N/A'))} | "
            f"{pool.get('bin_step', 'N/A')} | "
            f"{format_number(pool.get('current_price'))} | "
            f"{format_number(pool.get('liquidity'))} | "
            f"{format_number(pool.get('apr'))} | "
            f"{format_number(pool.get('apy'))} | "
            f"{format_number(pool.get('volume_24h'))} | "
            f"{format_number(pool.get('fees_24h'))}"
        )
        rows.append(row)

    # Combine everything
    table = f"{header}\n{separator}\n" + "\n".join(rows)
    return table


class GatewayCLMMPoolRequest(BaseModel):
    """Request model for Gateway CLMM pool exploration operations.

    This model supports pool exploration operations:
    - list_pools: Get list of available CLMM pools with filtering/sorting
    - get_pool_info: Get detailed information about a specific pool

    Progressive Flow:
    1. action="list_pools" → Browse available pools with optional filters
    2. action="get_pool_info" + pool_address → Get detailed pool information
    """

    action: Literal["list_pools", "get_pool_info"] = Field(
        description="Action to perform: 'list_pools' (browse pools), 'get_pool_info' (get pool details)"
    )

    # Common parameters
    connector: str = Field(
        description="CLMM connector name (required). Examples: 'meteora', 'raydium', 'uniswap'"
    )

    network: str | None = Field(
        default=None,
        description="Network ID in 'chain-network' format (required for get_pool_info). "
                    "Examples: 'solana-mainnet-beta', 'ethereum-mainnet'"
    )

    # Get pool info parameter
    pool_address: str | None = Field(
        default=None,
        description="Pool contract address (required for get_pool_info action)"
    )

    # List pools parameters
    page: int = Field(
        default=0,
        ge=0,
        description="Page number for list_pools (default: 0)"
    )

    limit: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Results per page for list_pools (default: 50, max: 100)"
    )

    search_term: str | None = Field(
        default=None,
        description="Search term to filter pools by token symbols (e.g., 'SOL', 'USDC')"
    )

    sort_key: str | None = Field(
        default="volume",
        description="Sort by field (volume, tvl, feetvlratio, etc.)"
    )

    order_by: str | None = Field(
        default="desc",
        description="Sort order: 'asc' or 'desc'"
    )

    include_unknown: bool = Field(
        default=True,
        description="Include pools with unverified tokens (default: True)"
    )


class GatewayCLMMPositionRequest(BaseModel):
    """Request model for Gateway CLMM position management operations.

    This model supports position management operations:
    - open_position: Create a new CLMM position with initial liquidity
    - close_position: Close a position completely (removes all liquidity)
    - collect_fees: Collect accumulated fees from a position
    - get_positions: Get all positions owned by a wallet for a specific pool
    - search_positions: Search positions with various filters

    Progressive Flow:
    1. action="search_positions" → Browse existing positions
    2. action="get_positions" + pool_address → Get positions for a specific pool
    3. action="open_position" + parameters → Create new position
    4. action="collect_fees" + position_address → Collect fees
    5. action="close_position" + position_address → Close position
    """

    action: Literal["open_position", "close_position", "collect_fees", "get_positions", "search_positions"] = Field(
        description="Action to perform on CLMM positions"
    )

    # Common parameters
    connector: str | None = Field(
        default=None,
        description="CLMM connector name (required for most actions). Examples: 'meteora', 'raydium'"
    )

    network: str | None = Field(
        default=None,
        description="Network ID in 'chain-network' format (required for most actions). "
                    "Examples: 'solana-mainnet-beta', 'ethereum-mainnet'"
    )

    wallet_address: str | None = Field(
        default=None,
        description="Wallet address (optional, uses default wallet if not provided)"
    )

    # Pool parameters (for open_position, get_positions)
    pool_address: str | None = Field(
        default=None,
        description="Pool contract address (required for open_position and get_positions)"
    )

    # Position parameters (for close_position, collect_fees)
    position_address: str | None = Field(
        default=None,
        description="Position NFT address (required for close_position and collect_fees)"
    )

    # Open position parameters
    lower_price: str | None = Field(
        default=None,
        description="Lower price bound for new position (required for open_position). Example: '150'"
    )

    upper_price: str | None = Field(
        default=None,
        description="Upper price bound for new position (required for open_position). Example: '250'"
    )

    base_token_amount: str | None = Field(
        default=None,
        description="Amount of base token to provide (optional for open_position). Example: '0.01'"
    )

    quote_token_amount: str | None = Field(
        default=None,
        description="Amount of quote token to provide (optional for open_position). Example: '2'"
    )

    slippage_pct: str | None = Field(
        default="1.0",
        description="Maximum slippage percentage (optional for open_position, default: 1.0)"
    )

    extra_params: dict[str, Any] | None = Field(
        default=None,
        description="Additional connector-specific parameters (e.g., {'strategyType': 0} for Meteora)"
    )

    # Search parameters (for search_positions)
    search_network: str | None = Field(
        default=None,
        description="Filter by network for search_positions"
    )

    search_connector: str | None = Field(
        default=None,
        description="Filter by connector for search_positions"
    )

    search_wallet_address: str | None = Field(
        default=None,
        description="Filter by wallet address for search_positions"
    )

    trading_pair: str | None = Field(
        default=None,
        description="Filter by trading pair for search_positions (e.g., 'SOL-USDC')"
    )

    status: Literal["OPEN", "CLOSED"] | None = Field(
        default=None,
        description="Filter by position status for search_positions"
    )

    position_addresses: list[str] | None = Field(
        default=None,
        description="Filter by specific position addresses for search_positions"
    )

    limit: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Maximum number of results for search_positions (default: 50, max: 1000)"
    )

    offset: int = Field(
        default=0,
        ge=0,
        description="Pagination offset for search_positions (default: 0)"
    )

    refresh: bool = Field(
        default=False,
        description="Refresh position data from Gateway before returning (for search_positions)"
    )


async def explore_gateway_clmm_pools(request: GatewayCLMMPoolRequest) -> dict[str, Any]:
    """
    Explore Gateway CLMM pools: list pools and get pool information.

    Actions:
    - list_pools: Get list of available CLMM pools with filtering and sorting
    - get_pool_info: Get detailed information about a specific pool

    Supported CLMM Connectors:
    - meteora (Solana): DLMM pools
    - raydium (Solana): CLMM pools
    - uniswap (Ethereum/EVM): V3 pools
    """
    try:
        client = await hummingbot_client.get_client()

        # ============================================
        # LIST POOLS - Browse available pools
        # ============================================
        if request.action == "list_pools":
            result = await client.gateway_clmm.get_pools(
                connector=request.connector,
                page=request.page,
                limit=request.limit,
                search_term=request.search_term,
                sort_key=request.sort_key,
                order_by=request.order_by,
                include_unknown=request.include_unknown
            )

            # Format pools as table for better LLM processing
            pools = result.get("pools", [])
            formatted_table = format_pools_as_table(pools)

            return {
                "action": "list_pools",
                "connector": request.connector,
                "filters": {
                    "search_term": request.search_term,
                    "sort_key": request.sort_key,
                    "order_by": request.order_by,
                    "include_unknown": request.include_unknown
                },
                "pagination": {
                    "page": request.page,
                    "limit": request.limit,
                    "total": result.get("total", 0)
                },
                "pools_table": formatted_table
            }

        # ============================================
        # GET POOL INFO - Get detailed pool information
        # ============================================
        elif request.action == "get_pool_info":
            # Validate required parameters
            if not request.network:
                raise ToolError("network is required for get_pool_info action")
            if not request.pool_address:
                raise ToolError("pool_address is required for get_pool_info action")

            result = await client.gateway_clmm.get_pool_info(
                connector=request.connector,
                network=request.network,
                pool_address=request.pool_address
            )

            return {
                "action": "get_pool_info",
                "connector": request.connector,
                "network": request.network,
                "pool_address": request.pool_address,
                "result": result
            }

        else:
            raise ToolError(f"Unknown action: {request.action}")

    except Exception as e:
        if isinstance(e, ToolError):
            raise
        else:
            logger.error(f"Error in explore_gateway_clmm_pools: {str(e)}", exc_info=True)
            raise ToolError(f"Gateway CLMM pool exploration failed: {str(e)}")


async def manage_gateway_clmm_positions(request: GatewayCLMMPositionRequest) -> dict[str, Any]:
    """
    Manage Gateway CLMM positions: open, close, collect fees, and search positions.

    Actions:
    - open_position: Create a new CLMM position with initial liquidity
    - close_position: Close a position completely (removes all liquidity)
    - collect_fees: Collect accumulated fees from a position
    - get_positions: Get all positions owned by a wallet for a specific pool
    - search_positions: Search positions with various filters
    """
    try:
        client = await hummingbot_client.get_client()

        # ============================================
        # OPEN POSITION - Create new position
        # ============================================
        if request.action == "open_position":
            # Validate required parameters
            if not request.connector:
                raise ToolError("connector is required for open_position action")
            if not request.network:
                raise ToolError("network is required for open_position action")
            if not request.pool_address:
                raise ToolError("pool_address is required for open_position action")
            if not request.lower_price:
                raise ToolError("lower_price is required for open_position action")
            if not request.upper_price:
                raise ToolError("upper_price is required for open_position action")

            result = await client.gateway_clmm.open_position(
                connector=request.connector,
                network=request.network,
                pool_address=request.pool_address,
                lower_price=Decimal(request.lower_price),
                upper_price=Decimal(request.upper_price),
                base_token_amount=Decimal(request.base_token_amount) if request.base_token_amount else None,
                quote_token_amount=Decimal(request.quote_token_amount) if request.quote_token_amount else None,
                slippage_pct=Decimal(request.slippage_pct or "1.0"),
                wallet_address=request.wallet_address,
                extra_params=request.extra_params
            )

            return {
                "action": "open_position",
                "connector": request.connector,
                "network": request.network,
                "pool_address": request.pool_address,
                "price_range": {
                    "lower_price": request.lower_price,
                    "upper_price": request.upper_price
                },
                "result": result
            }

        # ============================================
        # CLOSE POSITION - Close position completely
        # ============================================
        elif request.action == "close_position":
            # Validate required parameters
            if not request.connector:
                raise ToolError("connector is required for close_position action")
            if not request.network:
                raise ToolError("network is required for close_position action")
            if not request.position_address:
                raise ToolError("position_address is required for close_position action")

            result = await client.gateway_clmm.close_position(
                connector=request.connector,
                network=request.network,
                position_address=request.position_address,
                wallet_address=request.wallet_address
            )

            return {
                "action": "close_position",
                "connector": request.connector,
                "network": request.network,
                "position_address": request.position_address,
                "result": result
            }

        # ============================================
        # COLLECT FEES - Collect accumulated fees
        # ============================================
        elif request.action == "collect_fees":
            # Validate required parameters
            if not request.connector:
                raise ToolError("connector is required for collect_fees action")
            if not request.network:
                raise ToolError("network is required for collect_fees action")
            if not request.position_address:
                raise ToolError("position_address is required for collect_fees action")

            result = await client.gateway_clmm.collect_fees(
                connector=request.connector,
                network=request.network,
                position_address=request.position_address,
                wallet_address=request.wallet_address
            )

            return {
                "action": "collect_fees",
                "connector": request.connector,
                "network": request.network,
                "position_address": request.position_address,
                "result": result
            }

        # ============================================
        # GET POSITIONS - Get positions for a specific pool
        # ============================================
        elif request.action == "get_positions":
            # Validate required parameters
            if not request.connector:
                raise ToolError("connector is required for get_positions action")
            if not request.network:
                raise ToolError("network is required for get_positions action")
            if not request.pool_address:
                raise ToolError("pool_address is required for get_positions action")

            result = await client.gateway_clmm.get_positions_owned(
                connector=request.connector,
                network=request.network,
                pool_address=request.pool_address,
                wallet_address=request.wallet_address
            )

            return {
                "action": "get_positions",
                "connector": request.connector,
                "network": request.network,
                "pool_address": request.pool_address,
                "result": result
            }

        # ============================================
        # SEARCH POSITIONS - Search positions with filters
        # ============================================
        elif request.action == "search_positions":
            # Build search parameters
            search_params = {
                "limit": request.limit,
                "offset": request.offset,
                "refresh": request.refresh
            }

            # Add optional filters
            if request.search_network:
                search_params["network"] = request.search_network
            if request.search_connector:
                search_params["connector"] = request.search_connector
            if request.search_wallet_address:
                search_params["wallet_address"] = request.search_wallet_address
            if request.trading_pair:
                search_params["trading_pair"] = request.trading_pair
            if request.status:
                search_params["status"] = request.status
            if request.position_addresses:
                search_params["position_addresses"] = request.position_addresses

            result = await client.gateway_clmm.search_positions(**search_params)

            return {
                "action": "search_positions",
                "filters": {k: v for k, v in search_params.items() if k not in ["limit", "offset", "refresh"]},
                "pagination": {
                    "limit": search_params["limit"],
                    "offset": search_params["offset"]
                },
                "refresh": search_params["refresh"],
                "result": result
            }

        else:
            raise ToolError(f"Unknown action: {request.action}")

    except Exception as e:
        if isinstance(e, ToolError):
            raise
        else:
            error_message = str(e)
            logger.error(f"Error in manage_gateway_clmm_positions: {error_message}", exc_info=True)

            # Provide more helpful error messages for common Gateway errors
            if "'NoneType' object has no attribute 'get'" in error_message:
                raise ToolError(
                    f"Gateway CLMM operation failed with internal error.\n\n"
                    f"⚠️  Gateway Error: {error_message}\n\n"
                    f"This error typically indicates:\n"
                    f"  1. Insufficient SOL balance for blockchain fees (~0.44 SOL needed for position creation)\n"
                    f"  2. Transaction simulation failure (wallet lacks funds)\n"
                    f"  3. Missing or invalid wallet configuration\n"
                    f"  4. Invalid pool or network parameters\n\n"
                    f"🔍 To diagnose the issue:\n"
                    f"  1. Check Gateway logs: manage_gateway_container(action='get_logs', tail=50)\n"
                    f"  2. Look for 'insufficient lamports' or 'Insufficient funds' messages\n"
                    f"  3. Verify wallet has enough SOL for transaction costs\n\n"
                    f"💰 Common fixes:\n"
                    f"  - Add at least 0.5 SOL to your wallet for position operations\n"
                    f"  - Verify wallet is properly configured in Gateway\n"
                    f"  - Check that the pool address and network are correct"
                )

            # Check for insufficient balance errors
            if "insufficient" in error_message.lower() or "balance" in error_message.lower():
                raise ToolError(
                    f"Gateway CLMM operation failed: Insufficient balance.\n\n"
                    f"Error: {error_message}\n\n"
                    f"💰 Your wallet doesn't have enough funds for this operation.\n"
                    f"   Check Gateway logs for specific balance requirements."
                )

            raise ToolError(f"Gateway CLMM position management failed: {error_message}")

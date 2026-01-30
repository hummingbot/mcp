"""
Gateway CLMM tools for Hummingbot MCP Server

Handles DEX CLMM liquidity operations via Hummingbot Gateway:
- Pool exploration (list pools, get pool info)
- Position management (open, close, collect fees, search positions)
"""
import logging
from decimal import Decimal
from typing import Any

from hummingbot_mcp.exceptions import ToolError
from hummingbot_mcp.formatters.base import format_number, get_field
from hummingbot_mcp.schemas import GatewayCLMMPoolRequest, GatewayCLMMPositionRequest

logger = logging.getLogger("hummingbot-mcp")


def format_pools_as_table(pools: list[dict[str, Any]]) -> str:
    """
    Format pool data as a simplified table string.

    Columns: address | trading_pair | bin_step | current_price | liquidity | base_fee_percentage | apy | volume_24h | fees_24h
    """
    if not pools:
        return "No pools found."

    # Header - simplified columns
    header = "address | trading_pair | bin_step | current_price | liquidity | base_fee_percentage | apy | volume_24h | fees_24h"
    separator = "-" * 200

    # Format each pool as a row
    rows = []
    for pool in pools:
        row = (
            f"{get_field(pool, 'address', default='N/A')} | "
            f"{get_field(pool, 'trading_pair', default='N/A')} | "
            f"{get_field(pool, 'bin_step', default='N/A')} | "
            f"{format_number(get_field(pool, 'current_price', default=None))} | "
            f"{format_number(get_field(pool, 'liquidity', default=None))} | "
            f"{format_number(get_field(pool, 'base_fee_percentage', default=None))} | "
            f"{format_number(get_field(pool, 'apy', default=None))} | "
            f"{format_number(get_field(pool, 'volume_24h', default=None))} | "
            f"{format_number(get_field(pool, 'fees_24h', default=None))}"
        )
        rows.append(row)

    return f"{header}\n{separator}\n" + "\n".join(rows)


def format_pools_as_detailed_table(pools: list[dict[str, Any]]) -> str:
    """
    Format pool data as a detailed table string with exploded volume and fee_tvl_ratio fields.

    Columns: address | trading_pair | mint_x | mint_y | bin_step | current_price | liquidity |
             base_fee_percentage | max_fee_percentage | protocol_fee_percentage | apr | apy |
             volume_hour_1 | volume_hour_12 | volume_hour_24 |
             fee_tvl_ratio_hour_1 | fee_tvl_ratio_hour_12 | fee_tvl_ratio_hour_24
    """
    if not pools:
        return "No pools found."

    # Header - detailed columns
    header = (
        "address | trading_pair | mint_x | mint_y | bin_step | current_price | liquidity | "
        "base_fee_percentage | max_fee_percentage | protocol_fee_percentage | apr | apy | "
        "volume_hour_1 | volume_hour_12 | volume_hour_24 | "
        "fee_tvl_ratio_hour_1 | fee_tvl_ratio_hour_12 | fee_tvl_ratio_hour_24"
    )
    separator = "-" * 300

    # Format each pool as a row
    rows = []
    for pool in pools:
        # Extract nested volume fields
        volume = pool.get('volume', {})
        volume_hour_1 = volume.get('hour_1', 'N/A')
        volume_hour_12 = volume.get('hour_12', 'N/A')
        volume_hour_24 = volume.get('hour_24', 'N/A')

        # Extract nested fee_tvl_ratio fields
        fee_tvl_ratio = pool.get('fee_tvl_ratio', {})
        fee_tvl_ratio_hour_1 = fee_tvl_ratio.get('hour_1', 'N/A')
        fee_tvl_ratio_hour_12 = fee_tvl_ratio.get('hour_12', 'N/A')
        fee_tvl_ratio_hour_24 = fee_tvl_ratio.get('hour_24', 'N/A')

        row = (
            f"{get_field(pool, 'address', default='N/A')} | "
            f"{get_field(pool, 'trading_pair', default='N/A')} | "
            f"{get_field(pool, 'mint_x', default='N/A')} | "
            f"{get_field(pool, 'mint_y', default='N/A')} | "
            f"{get_field(pool, 'bin_step', default='N/A')} | "
            f"{format_number(get_field(pool, 'current_price', default=None))} | "
            f"{format_number(get_field(pool, 'liquidity', default=None))} | "
            f"{format_number(get_field(pool, 'base_fee_percentage', default=None))} | "
            f"{format_number(get_field(pool, 'max_fee_percentage', default=None))} | "
            f"{format_number(get_field(pool, 'protocol_fee_percentage', default=None))} | "
            f"{format_number(get_field(pool, 'apr', default=None))} | "
            f"{format_number(get_field(pool, 'apy', default=None))} | "
            f"{format_number(volume_hour_1)} | "
            f"{format_number(volume_hour_12)} | "
            f"{format_number(volume_hour_24)} | "
            f"{format_number(fee_tvl_ratio_hour_1)} | "
            f"{format_number(fee_tvl_ratio_hour_12)} | "
            f"{format_number(fee_tvl_ratio_hour_24)}"
        )
        rows.append(row)

    return f"{header}\n{separator}\n" + "\n".join(rows)


async def explore_gateway_clmm_pools(client: Any, request: GatewayCLMMPoolRequest) -> dict[str, Any]:
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

        pools = result.get("pools", [])

        # Format as detailed table if detailed mode is enabled
        if request.detailed:
            formatted_table = format_pools_as_detailed_table(pools)
        else:
            # Otherwise format as simplified table
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


async def manage_gateway_clmm_positions(client: Any, request: GatewayCLMMPositionRequest) -> dict[str, Any]:
    """
    Manage Gateway CLMM positions: open, close, collect fees, and get positions.

    Actions:
    - open_position: Create a new CLMM position with initial liquidity
    - close_position: Close a position completely (removes all liquidity)
    - collect_fees: Collect accumulated fees from a position
    - get_positions: Get all positions owned by a wallet for a specific pool (real-time data from blockchain)
    """
    try:
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

        else:
            raise ToolError(f"Unknown action: {request.action}")

    except ToolError:
        raise
    except Exception as e:
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

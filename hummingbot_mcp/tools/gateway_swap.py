"""
Gateway Trading tools for Hummingbot MCP Server

Handles DEX trading operations via Hummingbot Gateway:
- Swap quote/execute (Router: Jupiter, 0x)
- Swap search and status tracking
"""
import logging
from typing import Any, Literal
from decimal import Decimal

from pydantic import BaseModel, Field

from hummingbot_mcp.exceptions import ToolError
from hummingbot_mcp.hummingbot_client import hummingbot_client

logger = logging.getLogger("hummingbot-mcp")


class GatewaySwapRequest(BaseModel):
    """Request model for Gateway swap operations with progressive disclosure.

    This model supports swap operations:
    - quote: Get price quote for a swap
    - execute: Execute a swap transaction
    - search: Search swap history with filters
    - get_status: Get status of a specific swap by transaction hash

    Progressive Flow:
    1. action="quote" → Get price quote before executing
    2. action="execute" → Execute the swap
    3. action="get_status" + tx_hash → Check transaction status
    4. action="search" + filters → Query swap history
    """

    action: Literal["quote", "execute", "search", "get_status"] = Field(
        description="Action to perform: 'quote' (get price), 'execute' (perform swap), "
                    "'search' (query history), 'get_status' (check tx status)"
    )

    # Common swap parameters (required for quote/execute)
    connector: str | None = Field(
        default=None,
        description="DEX router connector (required for quote/execute). "
                    "Examples: 'jupiter' (Solana), '0x' (Ethereum)"
    )

    network: str | None = Field(
        default=None,
        description="Network ID in 'chain-network' format (required for quote/execute). "
                    "Examples: 'solana-mainnet-beta', 'ethereum-mainnet', 'ethereum-base'"
    )

    trading_pair: str | None = Field(
        default=None,
        description="Trading pair in BASE-QUOTE format (required for quote/execute). "
                    "Supports both token symbols and token addresses. "
                    "Examples: 'SOL-USDC', 'ETH-USDT', 'TOKEN_ADDRESS_1-TOKEN_ADDRESS_2', 'TOKEN_ADDRESS_1-USDC'"
    )

    side: Literal["BUY", "SELL"] | None = Field(
        default=None,
        description="Trade side (required for quote/execute): "
                    "'BUY' (buy base with quote) or 'SELL' (sell base for quote)"
    )

    amount: str | None = Field(
        default=None,
        description="Amount to swap (required for quote/execute). "
                    "For BUY: base token amount to receive. For SELL: base token amount to sell. "
                    "Example: '1.5' to buy/sell 1.5 tokens"
    )

    slippage_pct: str | None = Field(
        default="1.0",
        description="Maximum slippage percentage (optional, default: 1.0). "
                    "Example: '1.5' for 1.5% slippage tolerance"
    )

    # Execute-specific parameter
    wallet_address: str | None = Field(
        default=None,
        description="Wallet address for execute action (optional, uses default wallet if not provided)"
    )

    # Get status parameter
    transaction_hash: str | None = Field(
        default=None,
        description="Transaction hash (required for get_status action)"
    )

    # Search parameters (all optional)
    search_connector: str | None = Field(
        default=None,
        description="Filter by connector for search action (e.g., 'jupiter')"
    )

    search_network: str | None = Field(
        default=None,
        description="Filter by network for search action (e.g., 'solana-mainnet-beta')"
    )

    search_wallet_address: str | None = Field(
        default=None,
        description="Filter by wallet address for search action"
    )

    search_trading_pair: str | None = Field(
        default=None,
        description="Filter by trading pair for search action. Supports symbols and addresses "
                    "(e.g., 'SOL-USDC', 'TOKEN_ADDRESS_1-TOKEN_ADDRESS_2')"
    )

    status: Literal["SUBMITTED", "CONFIRMED", "FAILED"] | None = Field(
        default=None,
        description="Filter by transaction status for search action"
    )

    start_time: int | None = Field(
        default=None,
        description="Start timestamp in unix seconds for search action"
    )

    end_time: int | None = Field(
        default=None,
        description="End timestamp in unix seconds for search action"
    )

    limit: int | None = Field(
        default=50,
        ge=1,
        le=1000,
        description="Maximum number of results for search action (default: 50, max: 1000)"
    )

    offset: int | None = Field(
        default=0,
        ge=0,
        description="Pagination offset for search action (default: 0)"
    )


async def manage_gateway_swaps(request: GatewaySwapRequest) -> dict[str, Any]:
    """
    Manage Gateway swap operations: quote, execute, search, and status tracking.

    Actions:
    - quote: Get price quote for a swap before executing
    - execute: Execute a swap transaction on DEX
    - search: Search swap history with various filters
    - get_status: Get status of a specific swap by transaction hash

    Supported DEX Connectors:
    - jupiter (Solana): Router for Solana swaps
    - 0x (Ethereum): Aggregator for EVM chains
    """
    try:
        client = await hummingbot_client.get_client()

        # ============================================
        # QUOTE - Get swap price quote
        # ============================================
        if request.action == "quote":
            # Validate required parameters
            if not request.connector:
                raise ToolError("connector is required for quote action")
            if not request.network:
                raise ToolError("network is required for quote action")
            if not request.trading_pair:
                raise ToolError("trading_pair is required for quote action")
            if not request.side:
                raise ToolError("side is required for quote action (BUY or SELL)")
            if not request.amount:
                raise ToolError("amount is required for quote action")

            # Parse trading pair
            if "-" not in request.trading_pair:
                raise ToolError(f"Invalid trading_pair format. Expected 'BASE-QUOTE', got '{request.trading_pair}'")

            result = await client.gateway_swap.get_swap_quote(
                connector=request.connector,
                network=request.network,
                trading_pair=request.trading_pair,
                side=request.side,
                amount=Decimal(request.amount),
                slippage_pct=Decimal(request.slippage_pct or "1.0")
            )

            return {
                "action": "quote",
                "trading_pair": request.trading_pair,
                "side": request.side,
                "amount": request.amount,
                "result": result
            }

        # ============================================
        # EXECUTE - Execute swap transaction
        # ============================================
        elif request.action == "execute":
            # Validate required parameters
            if not request.connector:
                raise ToolError("connector is required for execute action")
            if not request.network:
                raise ToolError("network is required for execute action")
            if not request.trading_pair:
                raise ToolError("trading_pair is required for execute action")
            if not request.side:
                raise ToolError("side is required for execute action (BUY or SELL)")
            if not request.amount:
                raise ToolError("amount is required for execute action")

            # Parse trading pair
            if "-" not in request.trading_pair:
                raise ToolError(f"Invalid trading_pair format. Expected 'BASE-QUOTE', got '{request.trading_pair}'")

            result = await client.gateway_swap.execute_swap(
                connector=request.connector,
                network=request.network,
                trading_pair=request.trading_pair,
                side=request.side,
                amount=Decimal(request.amount),
                slippage_pct=Decimal(request.slippage_pct or "1.0"),
                wallet_address=request.wallet_address
            )

            return {
                "action": "execute",
                "trading_pair": request.trading_pair,
                "side": request.side,
                "amount": request.amount,
                "result": result
            }

        # ============================================
        # GET STATUS - Get swap status by tx hash
        # ============================================
        elif request.action == "get_status":
            if not request.transaction_hash:
                raise ToolError("transaction_hash is required for get_status action")

            result = await client.gateway_swap.get_swap_status(request.transaction_hash)

            return {
                "action": "get_status",
                "transaction_hash": request.transaction_hash,
                "result": result
            }

        # ============================================
        # SEARCH - Search swap history
        # ============================================
        elif request.action == "search":
            # Build search filters
            search_params = {
                "limit": request.limit or 50,
                "offset": request.offset or 0
            }

            # Add optional filters
            if request.search_network:
                search_params["network"] = request.search_network
            if request.search_connector:
                search_params["connector"] = request.search_connector
            if request.search_wallet_address:
                search_params["wallet_address"] = request.search_wallet_address
            if request.search_trading_pair:
                search_params["trading_pair"] = request.search_trading_pair
            if request.status:
                search_params["status"] = request.status
            if request.start_time:
                search_params["start_time"] = request.start_time
            if request.end_time:
                search_params["end_time"] = request.end_time

            result = await client.gateway_swap.search_swaps(**search_params)

            return {
                "action": "search",
                "filters": {k: v for k, v in search_params.items() if k not in ["limit", "offset"]},
                "pagination": {
                    "limit": search_params["limit"],
                    "offset": search_params["offset"]
                },
                "result": result
            }

        else:
            raise ToolError(f"Unknown action: {request.action}")

    except Exception as e:
        if isinstance(e, ToolError):
            raise
        else:
            logger.error(f"Error in manage_gateway_swaps: {str(e)}", exc_info=True)
            raise ToolError(f"Gateway swap operation failed: {str(e)}")

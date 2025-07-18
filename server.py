import os
import sys
import logging
from typing import Any
from datetime import datetime, timedelta
import asyncio
import json
from enum import Enum

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, CallToolResult
from hummingbot_api_client import HummingbotAPIClient
import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger("hummingbot-mcp")

# Environment configuration
HUMMINGBOT_API_URL = os.getenv("HUMMINGBOT_API_URL", "http://localhost:8000")
HUMMINGBOT_USERNAME = os.getenv("HUMMINGBOT_USERNAME", "admin")
HUMMINGBOT_PASSWORD = os.getenv("HUMMINGBOT_PASSWORD", "admin")

# Initialize API client with retry logic
api_client = None

# Initialize MCP server
server = Server("hummingbot-mcp")


class ToolError(Exception):
    """Custom exception for tool errors"""
    pass


class OrderType(str, Enum):
    """Valid order types"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    LIMIT_MAKER = "LIMIT_MAKER"


class OrderSide(str, Enum):
    """Valid order sides"""
    BUY = "BUY"
    SELL = "SELL"


async def initialize_client() -> HummingbotAPIClient:
    """Initialize API client with retry logic"""
    global api_client
    
    if api_client is not None:
        return api_client
    
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            client = HummingbotAPIClient(
                base_url=HUMMINGBOT_API_URL,
                username=HUMMINGBOT_USERNAME,
                password=HUMMINGBOT_PASSWORD,
                timeout=aiohttp.ClientTimeout(total=30.0)
            )
            
            # Initialize and test connection
            await client.init()
            await client.accounts.list_accounts()
            api_client = client
            logger.info(f"Successfully connected to Hummingbot API at {HUMMINGBOT_API_URL}")
            return client
            
        except Exception as e:
            logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                raise ConnectionError(f"Failed to connect to Hummingbot API after {max_retries} attempts: {e}")


def format_error(error: str) -> TextContent:
    """Format error messages consistently"""
    return TextContent(text=f"Error: {error}")


def format_success(data: Any) -> TextContent:
    """Format successful responses"""
    return TextContent(text=json.dumps(data, indent=2, default=str))


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools"""
    return [
        Tool(
            name="setup_connector",
            description="Setup a new exchange connector with credentials. This tool guides you through the entire process of connecting an exchange.",
            inputSchema={
                "type": "object",
                "properties": {
                    "account": {
                        "type": "string",
                        "description": "Account name to add credentials to (default: master)"
                    },
                    "connector": {
                        "type": "string",
                        "description": "Exchange connector name (e.g., binance, coinbase). Leave empty to list available connectors."
                    },
                    "credentials": {
                        "type": "object",
                        "description": "Credentials object with required fields for the connector. Leave empty to get required fields."
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_account_state",
            description="Get comprehensive account state including balances, positions, and active orders for one or more exchanges.",
            inputSchema={
                "type": "object",
                "properties": {
                    "account": {
                        "type": "string",
                        "description": "Account name (default: master)"
                    },
                    "exchanges": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of exchange names. If empty, returns data for all connected exchanges."
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="place_order",
            description="Place a buy or sell order with smart amount handling (supports USD values).",
            inputSchema={
                "type": "object",
                "properties": {
                    "exchange": {
                        "type": "string",
                        "description": "Exchange name (e.g., binance)"
                    },
                    "trading_pair": {
                        "type": "string",
                        "description": "Trading pair (e.g., BTC-USDT)"
                    },
                    "order_type": {
                        "type": "string",
                        "enum": ["MARKET", "LIMIT", "LIMIT_MAKER"],
                        "description": "Order type"
                    },
                    "side": {
                        "type": "string",
                        "enum": ["BUY", "SELL"],
                        "description": "Order side"
                    },
                    "amount": {
                        "type": "string",
                        "description": "Amount in base currency or USD (e.g., '0.1' or '$100')"
                    },
                    "price": {
                        "type": "number",
                        "description": "Price for limit orders (required for LIMIT and LIMIT_MAKER)"
                    },
                    "account": {
                        "type": "string",
                        "description": "Account name (default: master)"
                    },
                    "check_status": {
                        "type": "boolean",
                        "description": "Wait and check if order was successfully placed (default: true)"
                    }
                },
                "required": ["exchange", "trading_pair", "order_type", "side", "amount"]
            }
        ),
        Tool(
            name="get_market_data",
            description="Get market data including prices, candles, order book, and funding rates.",
            inputSchema={
                "type": "object",
                "properties": {
                    "data_type": {
                        "type": "string",
                        "enum": ["prices", "candles", "order_book", "funding_info"],
                        "description": "Type of market data to retrieve"
                    },
                    "exchange": {
                        "type": "string",
                        "description": "Exchange name"
                    },
                    "trading_pairs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of trading pairs"
                    },
                    "interval": {
                        "type": "string",
                        "description": "Candle interval (1m, 5m, 15m, 1h, 4h, 1d) - for candles only"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days of historical data (for candles) - default: 1"
                    },
                    "depth": {
                        "type": "integer",
                        "description": "Order book depth (default: 10) - for order_book only"
                    }
                },
                "required": ["data_type", "exchange", "trading_pairs"]
            }
        ),
        Tool(
            name="manage_orders",
            description="Manage orders - cancel orders or get order history.",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["cancel", "history"],
                        "description": "Action to perform"
                    },
                    "exchange": {
                        "type": "string",
                        "description": "Exchange name"
                    },
                    "order_id": {
                        "type": "string",
                        "description": "Specific order ID to cancel (for cancel action)"
                    },
                    "trading_pair": {
                        "type": "string",
                        "description": "Trading pair to filter orders"
                    },
                    "cancel_all": {
                        "type": "boolean",
                        "description": "Cancel all orders for the exchange/pair (for cancel action)"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days of history to retrieve (for history action) - default: 7"
                    },
                    "account": {
                        "type": "string",
                        "description": "Account name (default: master)"
                    }
                },
                "required": ["action", "exchange"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> CallToolResult:
    """Handle tool calls"""
    try:
        # Ensure client is initialized
        await initialize_client()
        
        if name == "setup_connector":
            result = await setup_connector(arguments)
        elif name == "get_account_state":
            result = await get_account_state(arguments)
        elif name == "place_order":
            result = await place_order(arguments)
        elif name == "get_market_data":
            result = await get_market_data(arguments)
        elif name == "manage_orders":
            result = await manage_orders(arguments)
        else:
            raise ToolError(f"Unknown tool: {name}")
        
        return CallToolResult(content=[format_success(result)])
    except ConnectionError as e:
        return CallToolResult(content=[format_error(f"Connection error: {str(e)}")], isError=True)
    except ToolError as e:
        return CallToolResult(content=[format_error(str(e))], isError=True)
    except Exception as e:
        logger.error(f"Tool {name} failed: {str(e)}", exc_info=True)
        return CallToolResult(content=[format_error(f"Tool execution failed: {str(e)}")], isError=True)


async def setup_connector(args: dict) -> dict:
    """Setup a new exchange connector"""
    account = args.get("account", DEFAULT_ACCOUNT)
    connector = args.get("connector")
    credentials = args.get("credentials")
    
    client = await initialize_client()
    
    # If no connector specified, list available connectors
    if not connector:
        connectors = await client.connectors.get_connectors()
        return {
            "action": "list_connectors",
            "message": "Available connectors:",
            "connectors": [c.name for c in connectors],
            "next_step": "Specify a connector name to see required credentials"
        }
    
    # If no credentials provided, show required fields
    if not credentials:
        config_map = await client.connectors.get_connector_config_map(connector)
        required_fields = {}
        for key, field in config_map.items():
            if field.required and not field.client_field_data or not field.client_field_data.is_connect_key:
                continue
            required_fields[key] = {
                "type": field.type,
                "description": field.client_field_data.prompt if field.client_field_data else "",
                "required": field.required,
                "is_secure": field.client_field_data.is_secure if field.client_field_data else False
            }
        
        return {
            "action": "show_config_map",
            "connector": connector,
            "required_credentials": required_fields,
            "next_step": "Provide credentials object with these fields to complete setup"
        }
    
    # Add credentials to account
    await client.accounts.add_account_credential(
        account_name=account,
        connector_name=connector,
        credentials=credentials
    )
    
    return {
        "action": "credentials_added",
        "message": f"Successfully added {connector} credentials to account {account}",
        "account": account,
        "connector": connector
    }


async def get_account_state(args: dict) -> dict:
    """Get comprehensive account state"""
    account = args.get("account", DEFAULT_ACCOUNT)
    exchanges = args.get("exchanges", [])
    
    client = await initialize_client()
    
    # Get account credentials to know which exchanges are connected
    account_info = await client.accounts.get_account(account)
    connected_exchanges = list(account_info.credentials.keys())
    
    if not exchanges:
        exchanges = connected_exchanges
    
    result = {
        "account": account,
        "timestamp": datetime.now().isoformat(),
        "exchanges": {}
    }
    
    # Fetch data for each exchange in parallel
    tasks = []
    for exchange in exchanges:
        if exchange not in connected_exchanges:
            result["exchanges"][exchange] = {"error": "Exchange not connected to this account"}
            continue
        
        tasks.append(fetch_exchange_state(account, exchange))
    
    exchange_states = await asyncio.gather(*tasks, return_exceptions=True)
    
    for i, exchange in enumerate(exchanges):
        if exchange in connected_exchanges:
            if isinstance(exchange_states[i - len([e for e in exchanges[:i+1] if e not in connected_exchanges])], Exception):
                result["exchanges"][exchange] = {"error": str(exchange_states[i - len([e for e in exchanges[:i+1] if e not in connected_exchanges])])}
            else:
                result["exchanges"][exchange] = exchange_states[i - len([e for e in exchanges[:i+1] if e not in connected_exchanges])]
    
    return result


async def fetch_exchange_state(account: str, exchange: str) -> dict:
    """Fetch state for a single exchange"""
    # Fetch balances, positions, and orders in parallel
    balances_task = api_client.trading.get_balances(
        account_name=account,
        exchange=exchange
    )
    positions_task = api_client.trading.get_positions(
        account_name=account,
        connectors=[exchange]
    )
    orders_task = api_client.trading.get_orders(
        account_name=account,
        connectors=[exchange],
        status=["OPEN", "PARTIALLY_FILLED"]
    )
    
    balances, positions, orders = await asyncio.gather(
        balances_task, positions_task, orders_task,
        return_exceptions=True
    )
    
    state = {}
    
    # Process balances
    if not isinstance(balances, Exception):
        state["balances"] = {
            bal.asset: {
                "total": float(bal.total_balance),
                "available": float(bal.available_balance),
                "usd_value": float(bal.total_balance * bal.usd_price) if bal.usd_price else None
            }
            for bal in balances
        }
        state["total_usd_value"] = sum(
            b["usd_value"] for b in state["balances"].values() 
            if b["usd_value"] is not None
        )
    else:
        state["balances"] = {"error": str(balances)}
    
    # Process positions
    if not isinstance(positions, Exception):
        state["positions"] = [
            {
                "trading_pair": pos.trading_pair,
                "amount": float(pos.amount),
                "side": pos.side,
                "entry_price": float(pos.entry_price) if pos.entry_price else None,
                "unrealized_pnl": float(pos.unrealized_pnl) if pos.unrealized_pnl else None,
                "realized_pnl": float(pos.realized_pnl) if pos.realized_pnl else None
            }
            for pos in positions
        ]
    else:
        state["positions"] = {"error": str(positions)}
    
    # Process orders
    if not isinstance(orders, Exception):
        state["active_orders"] = [
            {
                "order_id": order.client_order_id,
                "trading_pair": order.trading_pair,
                "side": order.side,
                "type": order.order_type,
                "amount": float(order.amount),
                "price": float(order.price) if order.price else None,
                "filled_amount": float(order.filled_amount) if order.filled_amount else 0,
                "status": order.status,
                "creation_timestamp": order.creation_timestamp
            }
            for order in orders
        ]
        state["active_orders_count"] = len(state["active_orders"])
    else:
        state["active_orders"] = {"error": str(orders)}
    
    return state


async def place_order(args: dict) -> dict:
    """Place an order with smart amount handling"""
    exchange = args["exchange"]
    trading_pair = args["trading_pair"]
    order_type = args["order_type"]
    side = args["side"]
    amount_str = args["amount"]
    price = args.get("price")
    account = args.get("account", DEFAULT_ACCOUNT)
    check_status = args.get("check_status", True)
    
    # Validate limit orders have price
    if order_type in ["LIMIT", "LIMIT_MAKER"] and not price:
        raise ToolError(f"{order_type} orders require a price")
    
    # Parse amount (handle USD notation)
    if amount_str.startswith("$"):
        # USD amount - need to convert to base currency
        usd_amount = float(amount_str[1:])
        
        # Get current price
        prices = await api_client.market_data.get_tickers(
            exchange=exchange,
            trading_pairs=[trading_pair]
        )
        
        if not prices:
            raise ToolError(f"Could not get price for {trading_pair} on {exchange}")
        
        current_price = float(prices[0].last_price)
        amount = usd_amount / current_price
        
        conversion_info = {
            "usd_amount": usd_amount,
            "price_used": current_price,
            "base_amount": amount
        }
    else:
        amount = float(amount_str)
        conversion_info = None
    
    # Get trading rules to validate order
    trading_rules = await api_client.connectors.get_trading_rules(exchange)
    rule = next((r for r in trading_rules if r.trading_pair == trading_pair), None)
    
    if rule:
        # Validate amount
        if rule.min_order_size and amount < rule.min_order_size:
            raise ToolError(f"Order amount {amount} is below minimum {rule.min_order_size}")
        if rule.max_order_size and amount > rule.max_order_size:
            raise ToolError(f"Order amount {amount} is above maximum {rule.max_order_size}")
        
        # Round amount to tick size
        if rule.min_base_amount_increment:
            amount = round(amount / rule.min_base_amount_increment) * rule.min_base_amount_increment
    
    # Place the order
    order_result = await api_client.trading.create_order(
        account_name=account,
        exchange=exchange,
        trading_pair=trading_pair,
        order_type=order_type,
        side=side,
        amount=amount,
        price=price
    )
    
    result = {
        "order_id": order_result.client_order_id,
        "exchange": exchange,
        "trading_pair": trading_pair,
        "side": side,
        "type": order_type,
        "amount": amount,
        "price": price,
        "status": "SUBMITTED"
    }
    
    if conversion_info:
        result["conversion"] = conversion_info
    
    # Check order status if requested
    if check_status:
        await asyncio.sleep(1)  # Wait a moment for order to process
        
        orders = await client.trading.get_orders(
            account_name=account,
            connectors=[exchange],
            order_ids=[order_result.client_order_id]
        )
        
        if orders:
            order = orders[0]
            result["status"] = order.status
            result["filled_amount"] = float(order.filled_amount) if order.filled_amount else 0
            if order.status == "FAILED":
                result["error"] = "Order failed to execute"
    
    return result


async def get_market_data(args: dict) -> dict:
    """Get various types of market data"""
    data_type = args["data_type"]
    exchange = args["exchange"]
    trading_pairs = args["trading_pairs"]
    
    if data_type == "prices":
        tickers = await api_client.market_data.get_tickers(
            exchange=exchange,
            trading_pairs=trading_pairs
        )
        
        return {
            "exchange": exchange,
            "timestamp": datetime.now().isoformat(),
            "prices": {
                ticker.trading_pair: {
                    "last_price": float(ticker.last_price),
                    "best_bid": float(ticker.best_bid),
                    "best_ask": float(ticker.best_ask),
                    "volume_24h": float(ticker.volume_24h) if ticker.volume_24h else None
                }
                for ticker in tickers
            }
        }
    
    elif data_type == "candles":
        interval = args.get("interval", "1h")
        days = args.get("days", 1)
        
        # Start real-time candles (will be cached)
        for pair in trading_pairs:
            try:
                await api_client.market_data.start_candles_stream(
                    exchange=exchange,
                    trading_pair=pair,
                    interval=interval
                )
            except Exception as e:
                logger.warning(f"Could not start candles stream for {pair}: {e}")
        
        # Get historical candles
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        
        candles_data = {}
        for pair in trading_pairs:
            try:
                candles = await api_client.market_data.get_historical_candles(
                    exchange=exchange,
                    trading_pair=pair,
                    interval=interval,
                    start_time=start_time,
                    end_time=end_time
                )
                
                candles_data[pair] = [
                    {
                        "timestamp": candle.timestamp,
                        "open": float(candle.open),
                        "high": float(candle.high),
                        "low": float(candle.low),
                        "close": float(candle.close),
                        "volume": float(candle.volume)
                    }
                    for candle in candles
                ]
            except Exception as e:
                candles_data[pair] = {"error": str(e)}
        
        return {
            "exchange": exchange,
            "interval": interval,
            "days": days,
            "candles": candles_data
        }
    
    elif data_type == "order_book":
        depth = args.get("depth", 10)
        
        order_books = {}
        for pair in trading_pairs:
            try:
                ob = await api_client.market_data.get_order_book_snapshot(
                    exchange=exchange,
                    trading_pair=pair,
                    depth=depth
                )
                
                order_books[pair] = {
                    "timestamp": ob.timestamp,
                    "bids": [
                        {"price": float(bid[0]), "amount": float(bid[1])}
                        for bid in ob.bids[:depth]
                    ],
                    "asks": [
                        {"price": float(ask[0]), "amount": float(ask[1])}
                        for ask in ob.asks[:depth]
                    ],
                    "spread": float(ob.asks[0][0] - ob.bids[0][0]) if ob.bids and ob.asks else None,
                    "mid_price": float((ob.asks[0][0] + ob.bids[0][0]) / 2) if ob.bids and ob.asks else None
                }
            except Exception as e:
                order_books[pair] = {"error": str(e)}
        
        return {
            "exchange": exchange,
            "depth": depth,
            "order_books": order_books
        }
    
    elif data_type == "funding_info":
        funding_info = {}
        for pair in trading_pairs:
            try:
                info = await api_client.market_data.get_funding_info(
                    exchange=exchange,
                    trading_pair=pair
                )
                
                funding_info[pair] = {
                    "rate": float(info.rate) if info.rate else None,
                    "next_funding_time": info.next_funding_time,
                    "timestamp": info.timestamp
                }
            except Exception as e:
                funding_info[pair] = {"error": str(e)}
        
        return {
            "exchange": exchange,
            "funding_info": funding_info
        }
    
    else:
        raise ToolError(f"Unknown data type: {data_type}")


async def manage_orders(args: dict) -> dict:
    """Manage orders - cancel or get history"""
    action = args["action"]
    exchange = args["exchange"]
    account = args.get("account", DEFAULT_ACCOUNT)
    
    if action == "cancel":
        order_id = args.get("order_id")
        trading_pair = args.get("trading_pair")
        cancel_all = args.get("cancel_all", False)
        
        if not order_id and not cancel_all:
            raise ToolError("Either provide order_id or set cancel_all=true")
        
        if cancel_all:
            # Get all active orders
            orders = await client.trading.get_orders(
                account_name=account,
                connectors=[exchange],
                trading_pairs=[trading_pair] if trading_pair else None,
                status=["OPEN", "PARTIALLY_FILLED"]
            )
            
            if not orders:
                return {
                    "action": "cancel_all",
                    "message": "No active orders to cancel",
                    "exchange": exchange,
                    "trading_pair": trading_pair
                }
            
            # Cancel each order
            cancelled = []
            failed = []
            for order in orders:
                try:
                    await client.trading.cancel_order(
                        account_name=account,
                        exchange=exchange,
                        trading_pair=order.trading_pair,
                        order_id=order.client_order_id
                    )
                    cancelled.append(order.client_order_id)
                except Exception as e:
                    failed.append({
                        "order_id": order.client_order_id,
                        "error": str(e)
                    })
            
            return {
                "action": "cancel_all",
                "exchange": exchange,
                "trading_pair": trading_pair,
                "cancelled_count": len(cancelled),
                "cancelled_orders": cancelled,
                "failed_count": len(failed),
                "failed_orders": failed if failed else None
            }
        else:
            # Cancel specific order
            if not trading_pair:
                # Need to get order details first
                orders = await client.trading.get_orders(
                    account_name=account,
                    connectors=[exchange],
                    order_ids=[order_id]
                )
                if not orders:
                    raise ToolError(f"Order {order_id} not found")
                trading_pair = orders[0].trading_pair
            
            await client.trading.cancel_order(
                account_name=account,
                exchange=exchange,
                trading_pair=trading_pair,
                order_id=order_id
            )
            
            return {
                "action": "cancel",
                "message": f"Successfully cancelled order {order_id}",
                "exchange": exchange,
                "trading_pair": trading_pair,
                "order_id": order_id
            }
    
    elif action == "history":
        days = args.get("days", 7)
        trading_pair = args.get("trading_pair")
        
        # Calculate time range
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        
        # Get order history
        orders = await client.trading.get_orders(
            account_name=account,
            connectors=[exchange],
            trading_pairs=[trading_pair] if trading_pair else None,
            start_time=start_time,
            end_time=end_time
        )
        
        # Group orders by status
        orders_by_status = {}
        for order in orders:
            status = order.status
            if status not in orders_by_status:
                orders_by_status[status] = []
            
            orders_by_status[status].append({
                "order_id": order.client_order_id,
                "trading_pair": order.trading_pair,
                "side": order.side,
                "type": order.order_type,
                "amount": float(order.amount),
                "price": float(order.price) if order.price else None,
                "filled_amount": float(order.filled_amount) if order.filled_amount else 0,
                "status": order.status,
                "timestamp": order.creation_timestamp
            })
        
        return {
            "action": "history",
            "exchange": exchange,
            "trading_pair": trading_pair,
            "days": days,
            "total_orders": len(orders),
            "orders_by_status": orders_by_status,
            "summary": {
                status: len(orders_list) 
                for status, orders_list in orders_by_status.items()
            }
        }
    
    else:
        raise ToolError(f"Unknown action: {action}")


async def main():
    """Run the MCP server"""
    logger.info(f"Starting Hummingbot MCP Server")
    logger.info(f"API URL: {HUMMINGBOT_API_URL}")
    logger.info(f"Default Account: {DEFAULT_ACCOUNT}")
    
    # Test API connection
    try:
        accounts = await api_client.accounts.list_accounts()
        logger.info(f"Successfully connected to Hummingbot API. Found {len(accounts)} accounts.")
    except Exception as e:
        logger.error(f"Failed to connect to Hummingbot API: {e}")
        logger.error("Please ensure Hummingbot is running and API credentials are correct.")
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)


if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
Entry point for the Hummingbot MCP Server
"""

import asyncio

from dotenv import load_dotenv

from hummingbot_mcp import main

load_dotenv()

if __name__ == "__main__":
    asyncio.run(main())

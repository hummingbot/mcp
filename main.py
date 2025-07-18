#!/usr/bin/env python3
"""
Entry point for the Hummingbot MCP Server
"""

import asyncio
from dotenv import load_dotenv

# Load environment variables before importing anything else
load_dotenv()

from mcp_hummingbot import main

if __name__ == "__main__":
    asyncio.run(main())
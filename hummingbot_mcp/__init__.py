"""
Hummingbot MCP Server

A professional Model Context Protocol server for Hummingbot API integration.
Enables AI assistants to manage crypto trading across multiple exchanges.
"""

__version__ = "0.1.0"
__author__ = "Federico Cardoso"

from .server import main

__all__ = ["main"]

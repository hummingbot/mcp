"""
Logging configuration for Hummingbot MCP Server
"""

import logging
import sys


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Setup logging configuration"""
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stderr)
        ]
    )
    
    # Create and return logger for this module
    logger = logging.getLogger("hummingbot-mcp")
    logger.setLevel(getattr(logging, level))
    
    return logger
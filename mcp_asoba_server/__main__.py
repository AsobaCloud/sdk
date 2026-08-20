"""Entry point: python -m mcp_asoba_server

Runs the Asoba MCP server over stdio transport.
Requires ASOBA_API_KEY in the environment.
"""

import logging
import sys

from .server import server

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

if __name__ == "__main__":
    server.run(transport="stdio")

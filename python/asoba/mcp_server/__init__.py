"""MCP server exposing the Asoba/Ona Platform SDK as tools.

Install the extra to get the server:
    pip install asoba[mcp]

Run directly (for debugging):
    python -m asoba.mcp_server

Or via uvx (recommended for MCP clients):
    uvx --from asoba[mcp] asoba-mcp-server
"""

__version__ = "1.0.0"


def main():
    from asoba.mcp_server.server import run
    run()

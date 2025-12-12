"""
Minimal FastMCP server stub for repository tooling.

Command to run (from bench root):
  fastmcp run --skip-env fastmcp.json --transport stdio --no-banner
"""

from fastmcp.server.server import FastMCP

server = FastMCP("ferum-repo")


@server.tool()
async def ping() -> str:
	"""Health check tool."""
	return "pong"


if __name__ == "__main__":
	import anyio

	anyio.run(server.run_async)

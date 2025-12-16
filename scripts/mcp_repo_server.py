"""
Minimal FastMCP server stub for repository tooling.

Command to run (from bench root):
  fastmcp run --skip-env fastmcp.json --transport stdio --no-banner
"""

import json
import os
import subprocess
from pathlib import Path
from typing import List, Optional

from fastmcp.server.server import FastMCP

server = FastMCP("ferum-repo")

# Constants
BENCH_ROOT = Path(os.getcwd())
APPS_DIR = BENCH_ROOT / "apps"
LOGS_DIR = BENCH_ROOT / "logs"


@server.tool()
async def ping() -> str:
    """Health check tool."""
    return "pong"


@server.tool()
def list_apps() -> List[str]:
    """Lists all apps installed in the apps/ directory."""
    if not APPS_DIR.exists():
        return []
    return [d.name for d in APPS_DIR.iterdir() if d.is_dir()]


@server.tool()
def find_doctype(doctype_name: str) -> List[str]:
    """
    Finds the file paths for a specific DocType (JSON files).
    Searches within the apps/ directory.
    """
    matches = list(APPS_DIR.rglob(f"{doctype_name}.json"))
    # Filter to ensure it looks like a DocType definition (inside a 'doctype' folder)
    doctype_files = [str(p.relative_to(BENCH_ROOT)) for p in matches if "doctype" in p.parts]
    return doctype_files


@server.tool()
def read_doctype_schema(doctype_name: str) -> str:
    """
    Returns the formatted JSON content of a DocType schema.
    If multiple files match, returns the first one found.
    """
    matches = find_doctype(doctype_name)
    if not matches:
        return f"Error: DocType '{doctype_name}' not found."

    file_path = BENCH_ROOT / matches[0]
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error reading file: {e}"


@server.tool()
def run_bench_command(command: str) -> str:
    """
    Runs specific 'bench' commands safely.
    Allowed commands: migrate, build, clear-cache, restart, version, doctor.
    """
    allowed_commands = ["migrate", "build", "clear-cache", "restart", "version", "doctor"]
    
    parts = command.strip().split()
    if not parts:
        return "Error: No command provided."
    
    action = parts[0]
    if action not in allowed_commands:
        return f"Error: Command '{action}' is not in the allowed list: {', '.join(allowed_commands)}"

    try:
        # We run 'bench' from the shell. Ensure bench is in path or use full path if known.
        # Assuming 'bench' is available in the environment since this is a frappe-bench.
        result = subprocess.run(
            ["bench"] + parts,
            cwd=BENCH_ROOT,
            capture_output=True,
            text=True,
            check=False
        )
        output = f"Stdout:\n{result.stdout}\n"
        if result.stderr:
            output += f"\nStderr:\n{result.stderr}"
        return output
    except Exception as e:
        return f"Error executing bench command: {e}"


@server.tool()
def tail_log(log_file: str, lines: int = 50) -> str:
    """
    Reads the last N lines of a specified log file in the logs/ directory.
    Common logs: web.error.log, web.log, worker.error.log, worker.log, scheduler.error.log
    """
    # Sanitize input to prevent path traversal
    safe_name = os.path.basename(log_file)
    target_path = LOGS_DIR / safe_name
    
    if not target_path.exists():
        available = [f.name for f in LOGS_DIR.glob("*.log")]
        return f"Error: Log file '{safe_name}' not found. Available logs: {', '.join(available)}"

    try:
        # Using tail command via subprocess for efficiency on large files
        result = subprocess.run(
            ["tail", "-n", str(lines), str(target_path)],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except Exception as e:
        return f"Error reading log: {e}"


@server.tool()
def search_code(query: str, app: Optional[str] = None) -> str:
    """
    Searches for a string pattern in the codebase using grep.
    Optionally restricts search to a specific app.
    """
    search_path = APPS_DIR / app if app else APPS_DIR
    
    if not search_path.exists():
        return f"Error: Path {search_path} does not exist."

    try:
        # grep -r "query" path
        # -n for line numbers, -I to ignore binary
        cmd = ["grep", "-rnI", query, str(search_path)]
        
        # Limit output to prevent flooding
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        output = result.stdout
        lines = output.splitlines()
        if len(lines) > 100:
            return "\n".join(lines[:100]) + f"\n... and {len(lines) - 100} more lines."
        return output if output else "No matches found."
    except Exception as e:
        return f"Error searching code: {e}"


if __name__ == "__main__":
    import anyio
    anyio.run(server.run_async)
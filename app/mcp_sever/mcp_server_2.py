import os
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server with configuration
mcp = FastMCP(
    "",
    instructions="",
    host="0.0.0.0", 
    port=8006, 
)


# Get list of files and directories in a specified path
@mcp.tool()
async def get_local_file_list(path: str) -> str:
    """
    Get a list of files and directories in a specified path.

    Args:
        path (str): local directory path to get file list

    Returns:
        str: A string containing the file list separated by newlines
    """
    try:
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist"

        file_list = []

        # Collect file/directory information
        for entry in os.scandir(path):
            stats = entry.stat()
            size = stats.st_size
            modified_time = datetime.fromtimestamp(stats.st_mtime).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            # Convert size unit
            size_str = f"{size:,} bytes"
            if size > 1024 * 1024 * 1024:
                size_str = f"{size/(1024*1024*1024):.2f} GB"
            elif size > 1024 * 1024:
                size_str = f"{size/(1024*1024):.2f} MB"
            elif size > 1024:
                size_str = f"{size/1024:.2f} KB"

            # File/directory distinction
            type_str = "[DIR]" if entry.is_dir() else "[FILE]"

            # Generate result string
            file_info = f"{type_str} {entry.name:<50} {size_str:<15} {modified_time}"
            file_list.append(file_info)

        # Sort and return results
        return "\n".join(sorted(file_list))

    except Exception as e:
        return f"Error: {str(e)}"



if __name__ == "__main__":
    # Start the MCP server with stdio transport
    mcp.run(transport="stdio")

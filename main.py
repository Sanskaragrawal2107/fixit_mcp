import logging
import sys
from fastmcp import FastMCP
import httpx

# Configure logging for production - stderr only for MCP servers
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr,  # Critical: MCP servers must use stderr for logs
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server in stdio mode
mcp = FastMCP(
    name="Fix-OS",
    dependencies=["httpx"],
    on_duplicate_resources="error"
)

# iFixit Constants
BASE_URL = "https://www.ifixit.com/api/2.0"
HEADERS = {
    "User-Agent": "Fix-OS-Hackathon/1.0 (Student Project)",
    "Accept": "application/json"
}

# API Configuration (production-ready)
API_TIMEOUT = 30  # seconds
MAX_RETRIES = 3

@mcp.tool()
async def search_device_manual(device_name: str) -> str:
    """
    Search for a repair guide on iFixit. 
    
    Args:
        device_name: The device name to search for (e.g., 'iPhone 14', 'Toaster')
    
    Returns:
        A list of matching repair guides with metadata, or an error message
    """
    # Input validation
    if not device_name or not device_name.strip():
        logger.warning("Empty device name provided")
        return "Error: Device name cannot be empty"
    
    device_name_clean = device_name.strip()
    url = f"{BASE_URL}/suggest/{device_name_clean}?doctypes=guide&limit=5"
    logger.info(f"Searching for device: {device_name_clean}")
    
    try:
        # Use timeout for production stability
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.get(url, headers=HEADERS)
            response.raise_for_status()  # Raise exception for bad status codes
            
            data = response.json()
            
            # Format results for AI consumption
            results = []
            for item in data.get("results", []):
                guide_info = {
                    "guide_id": item.get("guideid"),
                    "title": item.get("title"),
                    "summary": item.get("summary"),
                    "image_url": item.get("image", {}).get("standard")
                }
                results.append(guide_info)
            
            logger.info(f"Found {len(results)} results for '{device_name_clean}'")
            return str(results)
    
    except httpx.TimeoutException:
        logger.error(f"Timeout while searching for {device_name_clean}")
        return f"Error: Request timed out after {API_TIMEOUT} seconds. Please try again."
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error {e.response.status_code} while searching for {device_name_clean}")
        return f"Error: API returned status {e.response.status_code}"
    except Exception as e:
        logger.error(f"Unexpected error during device search: {type(e).__name__}: {str(e)}")
        return f"Error searching for device: {str(e)}"

@mcp.tool()
async def get_repair_steps(guide_id: int) -> str:
    """
    Get detailed repair steps, tools, and parts for a specific guide.
    
    Args:
        guide_id: The iFixit guide ID (must be a positive integer)
    
    Returns:
        Repair guide data with steps, tools, and parts needed, or an error message
    """
    # Input validation
    if not isinstance(guide_id, int) or guide_id <= 0:
        logger.warning(f"Invalid guide_id provided: {guide_id}")
        return "Error: guide_id must be a positive integer"
    
    url = f"{BASE_URL}/guides/{guide_id}"
    logger.info(f"Fetching repair steps for guide: {guide_id}")
    
    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.get(url, headers=HEADERS)
            response.raise_for_status()  # Raise exception for bad status codes
            
            data = response.json()
            
            # Structure guide data for efficient token usage
            guide_data = {
                "title": data.get("title"),
                "difficulty": data.get("difficulty"),
                "tools_required": [
                    t.get("text") for t in data.get("tools", [])
                    if t.get("text")
                ],
                "parts_required": [
                    p.get("text") for p in data.get("parts", [])
                    if p.get("text")
                ],
                "steps": [
                    {
                        "step_number": step.get("orderby"),
                        "instruction": " ".join([
                            line.get("text_raw") for line in step.get("lines", [])
                            if line.get("text_raw")
                        ]),
                        "image": step.get("media", {}).get("data", [{}])[0].get("standard")
                    }
                    for step in data.get("steps", [])
                ]
            }
            
            logger.info(f"Successfully fetched guide {guide_id} with {len(guide_data.get('steps', []))} steps")
            return str(guide_data)
    
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.warning(f"Guide not found: {guide_id}")
            return f"Error: Guide {guide_id} not found"
        logger.error(f"HTTP error {e.response.status_code} for guide {guide_id}")
        return f"Error: API returned status {e.response.status_code}"
    except httpx.TimeoutException:
        logger.error(f"Timeout while fetching guide {guide_id}")
        return f"Error: Request timed out after {API_TIMEOUT} seconds. Please try again."
    except Exception as e:
        logger.error(f"Unexpected error fetching guide {guide_id}: {type(e).__name__}: {str(e)}")
        return f"Error fetching repair steps: {str(e)}"


def main():
    """Main entry point for the FastMCP server."""
    logger.info("Starting Fix-OS MCP server")
    logger.info("Available tools: search_device_manual, get_repair_steps")
    mcp.run()


if __name__ == "__main__":
    main()
from mcp.server.fastmcp import FastMCP
import httpx

# 1. Initialize FastMCP with dependencies
# This tells the server it depends on 'httpx' for execution
mcp = FastMCP("Fix-OS", dependencies=["httpx"])

# iFixit Constants
BASE_URL = "https://www.ifixit.com/api/2.0"
HEADERS = {
    "User-Agent": "Fix-OS-Hackathon/1.0 (Student Project)",
    "Accept": "application/json"
}

@mcp.tool()
async def search_device_manual(device_name: str) -> str:
    """
    Search for a repair guide on iFixit. 
    Use this when the user mentions a device name (e.g., 'Dell XPS 13', 'Toaster').
    """
    url = f"{BASE_URL}/suggest/{device_name}?doctypes=guide&limit=5"
    
    # BEST PRACTICE: Using Async Client (httpx) to not block the server
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS)
        
        if response.status_code != 200:
            return f"Error connecting to iFixit: {response.status_code}"
        
        data = response.json()
        
        # Format the results for the AI
        results = []
        for item in data.get("results", []):
            results.append({
                "guide_id": item.get("guideid"),
                "title": item.get("title"),
                "summary": item.get("summary"),
                "image_url": item.get("image", {}).get("standard")
            })
            
        return str(results)

@mcp.tool()
async def get_repair_steps(guide_id: int) -> str:
    """
    Get detailed repair steps, tools, and parts for a specific Guide ID.
    Use this after finding the guide_id from the search tool.
    """
    url = f"{BASE_URL}/guides/{guide_id}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS)
        
        if response.status_code != 200:
            return f"Error fetching guide: {response.status_code}"
        
        data = response.json()
        
        # Clean up data to save tokens and give context
        guide_data = {
            "title": data.get("title"),
            "difficulty": data.get("difficulty"),
            "tools_required": [t.get("text") for t in data.get("tools", [])],
            "parts_required": [p.get("text") for p in data.get("parts", [])],
            "steps": [
                {
                    "step_number": step.get("orderby"),
                    "instruction": " ".join([line.get("text_raw") for line in step.get("lines", [])]),
                    "image": step.get("media", {}).get("data", [{}])[0].get("standard")
                }
                for step in data.get("steps", [])
            ]
        }
        
        return str(guide_data)

# Note: No need for 'if __name__ == "__main__"' block when using 'fastmcp dev'
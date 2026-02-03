# Fix-OS MCP Server - Deployment Guide

## Overview
Fix-OS is an MCP (Model Context Protocol) server that provides repair guides and device support information from iFixit. It's designed to work with AI assistants like Claude using the official FastMCP framework.

**Built with:** FastMCP v2.14.5+ | Python 3.11+ | iFixit Public API

## Local Development

### Quick Start
```bash
# Install dependencies
pip install -e .

# Run the development server
fastmcp dev main.py
```

The server will start in development mode with automatic reload. No HTTP server is running - it communicates via stdio.

## Deployment Options

### Option 1: Claude Desktop Integration (Recommended)
This is the preferred way to use Fix-OS with Claude.

**Windows:** Edit `%APPDATA%\Claude\claude_desktop_config.json`
```json
{
  "mcpServers": {
    "fixit": {
      "command": "python",
      "args": ["-m", "main"],
      "env": {}
    }
  }
}
```

**macOS/Linux:** Edit `~/Library/Application\ Support/Claude/claude_desktop_config.json`
```json
{
  "mcpServers": {
    "fixit": {
      "command": "python3",
      "args": ["-m", "main"],
      "env": {}
    }
  }
}
```

After updating the config file, restart Claude Desktop and the tools will be available.

### Option 2: Using FastMCP Configuration File
```bash
# Deploy with the official fastmcp.json config
fastmcp run fastmcp.json

# Or if in the project directory
fastmcp run
```

### Option 3: Direct Python Execution
```bash
# Run the server directly
python main.py

# Server will listen on stdio
```

### Option 4: Docker Deployment
Create a `Dockerfile` in your project:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -e .

# Run the MCP server
CMD ["python", "main.py"]
```

Build and deploy:
```bash
docker build -t fixit-mcp .
docker run -i fixit-mcp
```

## Architecture & Best Practices

### FastMCP Configuration (`fastmcp.json`)
The official configuration file includes:
- **Transport:** stdio (not HTTP)
- **Logging:** INFO level for production
- **Python:** 3.11 requirement
- **Environment:** Production-ready settings

### Deployment Transport
- **stdio** (Standard Input/Output) - Used by MCP for client-server communication
- NOT HTTP/REST API
- Bi-directional communication with clients

## Available Tools

### 1. `search_device_manual`
**Purpose:** Search for repair guides on iFixit

**Input:**
- `device_name` (string): Device name to search for

**Example Input:**
```
"iPhone 14", "MacBook Pro", "Pixel 8"
```

**Output:** List of matching guides with:
- guide_id
- title
- summary
- image_url

### 2. `get_repair_steps`
**Purpose:** Get detailed repair instructions for a specific guide

**Input:**
- `guide_id` (integer): iFixit guide identifier

**Example Input:**
```
147923
```

**Output:** Repair data with:
- title
- difficulty
- tools_required
- parts_required
- steps (with instructions and images)

## Configuration & Environment Variables

### Optional Environment Variables
```bash
# Currently, the server uses hardcoded iFixit API configuration
# Future versions may support:
# - API_BASE_URL (for API proxies)
# - API_TIMEOUT (default: 30 seconds)
```

## Error Handling & Reliability

### Built-in Protections
- **30-second timeout** on all API calls
- **Input validation** for all tool arguments
- **Graceful error handling** with informative error messages
- **Logging** to stderr with timestamps
- **HTTP status code handling** (404, 500, etc.)

### Logging Output
Logs are written to stderr with format:
```
2026-02-03 16:11:08 - __main__ - INFO - Searching for device: iPhone 14
2026-02-03 16:11:10 - __main__ - INFO - Found 5 results for 'iPhone 14'
```

## Troubleshooting

### Issue: "404 Not Found" Errors
**Symptom:** Server returns 404 errors for requests
**Solution:** This was a common issue when running as HTTP. Ensure you're using:
- `python main.py` (stdio mode)
- `fastmcp dev main.py` (development)
- `fastmcp run fastmcp.json` (production)
NOT Uvicorn or other HTTP servers.

### Issue: "Request timed out"
**Solution:** 
- Check internet connectivity to iFixit API
- Verify no firewall blocking `www.ifixit.com`
- Increase timeout in code if needed (API_TIMEOUT variable)

### Issue: "No tools available"
**Symptom:** Connected to server but no tools show up
**Solution:**
- Ensure FastMCP server is fully initialized
- Restart the MCP client (Claude Desktop)
- Check logs for initialization errors

### Issue: "Module not found"
**Solution:**
```bash
pip install -e .
# Verify installation:
python -c "from main import mcp; print('Server ready')"
```

## Performance Considerations

### API Limits
- iFixit API: No documented rate limiting
- Recommended: Cache recent searches client-side

### Timeout Settings
- Default: 30 seconds per request
- Adjust in `API_TIMEOUT` variable if needed

### Resource Usage
- Minimal memory footprint (stdio-based)
- No persistent connections
- Stateless design

## Security & Privacy

### What This Server Does
- Makes read-only requests to iFixit public API
- No authentication required for iFixit API
- No sensitive data stored or transmitted
- User-Agent identifies as "Fix-OS-Hackathon/1.0"

### What This Server Does NOT Do
- Store user data
- Make external calls beyond iFixit
- Require API keys (uses public API)
- Modify or delete data

## Production Deployment Checklist

- [ ] Install all dependencies: `pip install -e .`
- [ ] Test with Claude Desktop setup
- [ ] Verify internet access to iFixit API
- [ ] Check stderr logs for errors
- [ ] Test timeout scenarios
- [ ] Monitor for rate limiting (if needed)
- [ ] Set up log aggregation (if needed)
- [ ] Document any custom timeouts or settings

## Advanced: Custom Deployment

### With Environment Variables
Update `fastmcp.json`:
```json
{
  "deployment": {
    "env": {
      "API_TIMEOUT": "60",
      "LOG_LEVEL": "DEBUG"
    }
  }
}
```

### As a System Service (Linux/macOS)
Create `/etc/systemd/system/fixit-mcp.service`:
```ini
[Unit]
Description=Fix-OS MCP Server
After=network.target

[Service]
Type=simple
User=mcp
WorkingDirectory=/opt/fixit
ExecStart=/usr/bin/python3 main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable fixit-mcp
sudo systemctl start fixit-mcp
```

## Support & Contributing

For issues or feature requests:
1. Check the troubleshooting section
2. Review FastMCP documentation: https://gofastmcp.com
3. Check iFixit API docs: https://www.ifixit.com/api/2.0

## Version History

- **v0.1.0** - Initial release with search and repair steps tools
  - FastMCP v2.14.5+ compatible
  - Production-ready error handling
  - Comprehensive logging


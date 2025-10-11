#!/bin/bash
# Quick test script for MCP server
# This will run the MCP server in the Docker container and see if it starts

echo "Testing PitchScoop MCP Server..."
echo "================================"
echo ""

docker compose -f /Users/allierays/Sites/pitchscoop/docker-compose.yml exec -T api python mcp_server.py &lt;&lt;EOF
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "0.1.0", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0.0"}}}
{"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
EOF

echo ""
echo "================================"
echo "If you saw tool definitions above, the MCP server is working!"

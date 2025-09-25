#!/usr/bin/env python3
"""
import sys
from pathlib import Path

# Add project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

Simple Test Server for CanaryQA MCP Tools (No external dependencies)

This creates a basic HTTP server that exposes the MCP tools via HTTP
so they can be tested in the browser interface.

Run with: python simple_test_server.py
Then open: http://localhost:8000/test.html
"""
import json
import asyncio
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
import threading
from pathlib import Path

# Import our MCP tools
from api.domains.recordings.mcp.mcp_tools import execute_mcp_tool, list_available_tools


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    pass


class MCPTestHandler(SimpleHTTPRequestHandler):
    """HTTP handler that can serve static files and handle MCP API calls."""
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/":
            self.path = "/test.html"
        elif self.path == "/test":
            self.path = "/test.html"
        elif self.path.startswith("/mcp/"):
            self.handle_mcp_get()
            return
        
        # Serve static files
        super().do_GET()
    
    def do_POST(self):
        """Handle POST requests."""
        if self.path.startswith("/mcp/"):
            self.handle_mcp_post()
        else:
            self.send_error(404)
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests (for CORS preflight)."""
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
    
    def send_cors_headers(self):
        """Send CORS headers."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def handle_mcp_get(self):
        """Handle GET requests to MCP endpoints."""
        try:
            if self.path == "/mcp/tools":
                response = {
                    "tools": list_available_tools(),
                    "total": len(list_available_tools())
                }
            elif self.path == "/mcp/health":
                response = {
                    "status": "healthy",
                    "available_tools": len(list_available_tools())
                }
            elif self.path == "/mcp/test":
                # Quick test with proper async handling
                result = self._run_async(execute_mcp_tool("pitches.list_sessions", {}))
                response = {
                    "test": "success",
                    "message": "MCP tools are working",
                    "sample_result": result
                }
            else:
                self.send_error(404)
                return
                
            self.send_json_response(response)
            
        except Exception as e:
            self.send_json_response({"error": str(e)}, 500)
    
    def handle_mcp_post(self):
        """Handle POST requests to MCP endpoints."""
        try:
            if self.path == "/mcp/execute":
                # Read request body
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length).decode('utf-8')
                
                # Parse JSON request
                try:
                    request_data = json.loads(post_data)
                except json.JSONDecodeError:
                    self.send_json_response({"error": "Invalid JSON"}, 400)
                    return
                
                # Validate request
                if "tool" not in request_data or "arguments" not in request_data:
                    self.send_json_response({
                        "error": "Missing 'tool' or 'arguments' in request"
                    }, 400)
                    return
                
                # Execute MCP tool with proper async handling
                result = self._run_async(execute_mcp_tool(
                    request_data["tool"], 
                    request_data["arguments"]
                ))
                
                self.send_json_response(result)
                
            else:
                self.send_error(404)
                
        except Exception as e:
            self.send_json_response({"error": f"Server error: {str(e)}"}, 500)
    
    def send_json_response(self, data, status_code=200):
        """Send a JSON response."""
        response_json = json.dumps(data, indent=2, default=str)
        
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(response_json.encode('utf-8'))
    
    def _run_async(self, coro):
        """Run async coroutine in a safe way that handles event loop issues."""
        try:
            # Try to get the current event loop
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Event loop is closed")
        except RuntimeError:
            # No current event loop or it's closed, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            if loop.is_running():
                # If loop is already running, we need to run in a thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, coro)
                    return future.result()
            else:
                # Loop is not running, we can use it directly
                return loop.run_until_complete(coro)
        except Exception as e:
            # Fallback: create a completely new event loop
            new_loop = asyncio.new_event_loop()
            try:
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()

    def log_message(self, format, *args):
        """Override to provide cleaner logging."""
        print(f"[{self.address_string()}] {format % args}")


def create_test_html():
    """Create a simplified test HTML file if it doesn't exist."""
    html_path = Path("test.html")
    if html_path.exists():
        return
    
    # Copy our existing test interface
    src_path = Path("test_interface.html")
    if src_path.exists():
        html_path.write_text(src_path.read_text())
        print(f"✅ Created {html_path} from existing interface")
    else:
        print(f"⚠️  Could not find test_interface.html")


def run_server(port=8080):  # Use 8080 inside container, 8000 is mapped externally
    """Run the test server."""
    create_test_html()
    
    server_address = ('0.0.0.0', port)  # Bind to all interfaces for Docker
    httpd = ThreadedHTTPServer(server_address, MCPTestHandler)
    
    print(f"🚀 Starting CanaryQA MCP Test Server on port {port}...")
    print(f"📋 Available endpoints:")
    print(f"   • http://localhost:8000/test - Browser test interface (external)")
    print(f"   • http://localhost:8000/mcp/health - Health check")
    print(f"   • http://localhost:8000/mcp/test - Quick MCP test")
    print(f"   • http://localhost:8000/mcp/tools - Available tools")
    print()
    print(f"🎙️  Open http://localhost:8000/test in your browser to test!")
    print(f"📡 Server running inside Docker with Redis and MinIO available")
    print()
    print("Press Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
        httpd.shutdown()


if __name__ == "__main__":
    run_server()
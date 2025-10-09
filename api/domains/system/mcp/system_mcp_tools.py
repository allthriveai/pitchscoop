"""
System Management MCP Tools

These tools help AI assistants onboard users and manage the PitchScoop system.
Used for setup, diagnostics, and system health checks.
"""

import asyncio
import json
import os
import subprocess
import platform
from typing import Dict, Any
from pathlib import Path

# System management MCP tool definitions
SYSTEM_MCP_TOOLS = {
    "system.check_requirements": {
        "description": "Check if Docker and system requirements are installed and available",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
    },
    
    "system.get_status": {
        "description": "Check the current status of PitchScoop services (Docker containers)",
        "inputSchema": {
            "type": "object", 
            "properties": {},
            "additionalProperties": False
        }
    },
    
    "system.start_services": {
        "description": "Start PitchScoop Docker services (equivalent to docker compose up -d)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "rebuild": {
                    "type": "boolean",
                    "description": "Whether to rebuild containers (adds --build flag)",
                    "default": False
                }
            },
            "additionalProperties": False
        }
    },
    
    "system.stop_services": {
        "description": "Stop PitchScoop Docker services",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
    },
    
    "system.generate_config": {
        "description": "Generate MCP configuration for different AI platforms",
        "inputSchema": {
            "type": "object",
            "properties": {
                "platform": {
                    "type": "string",
                    "enum": ["claude-desktop", "chatgpt-mcp", "custom"],
                    "description": "Target platform for MCP configuration"
                },
                "project_path": {
                    "type": "string", 
                    "description": "Absolute path to PitchScoop project directory",
                    "default": "/Users/allierays/Sites/pitchscoop"
                }
            },
            "required": ["platform"],
            "additionalProperties": False
        }
    },
    
    "system.run_diagnostics": {
        "description": "Run comprehensive system diagnostics to troubleshoot issues",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
    },

    "system.get_setup_guide": {
        "description": "Get step-by-step setup instructions for a specific platform",
        "inputSchema": {
            "type": "object",
            "properties": {
                "platform": {
                    "type": "string",
                    "enum": ["claude-desktop", "chatgpt-mcp", "custom", "overview"],
                    "description": "Platform to get setup guide for"
                }
            },
            "required": ["platform"],
            "additionalProperties": False
        }
    }
}


async def execute_system_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a system management MCP tool."""
    
    try:
        if tool_name == "system.check_requirements":
            return await _check_requirements()
        
        elif tool_name == "system.get_status":
            return await _get_status()
            
        elif tool_name == "system.start_services":
            rebuild = arguments.get("rebuild", False)
            return await _start_services(rebuild)
            
        elif tool_name == "system.stop_services":
            return await _stop_services()
            
        elif tool_name == "system.generate_config":
            platform = arguments["platform"]
            project_path = arguments.get("project_path", "/Users/allierays/Sites/pitchscoop")
            return await _generate_config(platform, project_path)
            
        elif tool_name == "system.run_diagnostics":
            return await _run_diagnostics()
            
        elif tool_name == "system.get_setup_guide":
            platform = arguments["platform"]
            return await _get_setup_guide(platform)
            
        else:
            return {
                "success": False,
                "error": f"Unknown system tool: {tool_name}",
                "available_tools": list(SYSTEM_MCP_TOOLS.keys())
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"System tool execution failed: {str(e)}",
            "tool": tool_name,
            "arguments": arguments
        }


async def _check_requirements() -> Dict[str, Any]:
    """Check if Docker and system requirements are available."""
    
    results = {
        "success": True,
        "system": platform.system(),
        "checks": {},
        "overall_status": "checking"
    }
    
    # Check Docker
    try:
        docker_version = subprocess.check_output(
            ["docker", "--version"], 
            stderr=subprocess.STDOUT, 
            text=True
        ).strip()
        results["checks"]["docker"] = {
            "available": True,
            "version": docker_version,
            "status": "✅ Docker found"
        }
    except (subprocess.CalledProcessError, FileNotFoundError):
        results["checks"]["docker"] = {
            "available": False,
            "status": "❌ Docker not found",
            "install_url": "https://docs.docker.com/get-docker/"
        }
        results["success"] = False
    
    # Check Docker Compose
    try:
        compose_version = subprocess.check_output(
            ["docker", "compose", "version"], 
            stderr=subprocess.STDOUT, 
            text=True
        ).strip()
        results["checks"]["docker_compose"] = {
            "available": True,
            "version": compose_version,
            "status": "✅ Docker Compose found"
        }
    except (subprocess.CalledProcessError, FileNotFoundError):
        results["checks"]["docker_compose"] = {
            "available": False,
            "status": "❌ Docker Compose not found",
            "install_url": "https://docs.docker.com/compose/install/"
        }
        results["success"] = False
    
    # Check if project directory exists
    project_dir = Path.cwd()
    docker_compose_file = project_dir / "docker-compose.yml"
    
    results["checks"]["project_structure"] = {
        "project_dir": str(project_dir),
        "docker_compose_exists": docker_compose_file.exists(),
        "status": "✅ Project structure found" if docker_compose_file.exists() else "❌ docker-compose.yml not found"
    }
    
    if not docker_compose_file.exists():
        results["success"] = False
    
    # Set overall status
    if results["success"]:
        results["overall_status"] = "✅ All requirements met"
        results["next_step"] = "Ready to start services with system.start_services"
    else:
        results["overall_status"] = "❌ Missing requirements"
        results["next_step"] = "Install missing requirements before proceeding"
    
    return results


async def _get_status() -> Dict[str, Any]:
    """Get current status of PitchScoop Docker services."""
    
    try:
        # Run docker compose ps to get service status
        result = subprocess.run(
            ["docker", "compose", "ps", "--format", "json"],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": "Could not get service status",
                "stderr": result.stderr
            }
        
        # Parse service status
        services = []
        if result.stdout.strip():
            for line in result.stdout.strip().split('\n'):
                try:
                    service = json.loads(line)
                    services.append({
                        "name": service.get("Service", "unknown"),
                        "state": service.get("State", "unknown"),
                        "status": service.get("Status", "unknown"),
                        "ports": service.get("Publishers", [])
                    })
                except json.JSONDecodeError:
                    continue
        
        # Determine overall status
        if not services:
            overall_status = "❌ No services running"
            next_step = "Start services with system.start_services"
        elif all(s["state"] == "running" for s in services):
            overall_status = "✅ All services running"
            next_step = "Ready for use! Try creating an event."
        else:
            overall_status = "⚠️ Some services not running"
            next_step = "Check logs or restart services"
        
        return {
            "success": True,
            "services": services,
            "overall_status": overall_status,
            "next_step": next_step,
            "service_count": len(services)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get service status: {str(e)}"
        }


async def _start_services(rebuild: bool = False) -> Dict[str, Any]:
    """Start PitchScoop Docker services."""
    
    try:
        cmd = ["docker", "compose", "up", "-d"]
        if rebuild:
            cmd.append("--build")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": "Failed to start services",
                "stderr": result.stderr,
                "stdout": result.stdout
            }
        
        # Wait a moment for services to stabilize
        await asyncio.sleep(3)
        
        # Get updated status
        status = await _get_status()
        
        return {
            "success": True,
            "message": "Services started successfully",
            "rebuild": rebuild,
            "status": status,
            "next_step": "Services are starting up. Try system.get_status to check progress."
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to start services: {str(e)}"
        }


async def _stop_services() -> Dict[str, Any]:
    """Stop PitchScoop Docker services."""
    
    try:
        result = subprocess.run(
            ["docker", "compose", "down"],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": "Failed to stop services",
                "stderr": result.stderr
            }
        
        return {
            "success": True,
            "message": "Services stopped successfully",
            "stdout": result.stdout
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to stop services: {str(e)}"
        }


async def _generate_config(platform: str, project_path: str) -> Dict[str, Any]:
    """Generate MCP configuration for different platforms."""
    
    configs = {
        "claude-desktop": {
            "description": "Configuration for Claude Desktop MCP",
            "config": {
                "mcpServers": {
                    "pitchscoop": {
                        "command": "docker",
                        "args": [
                            "compose",
                            "-f", f"{project_path}/docker-compose.yml", 
                            "exec",
                            "-T",
                            "api",
                            "python",
                            "mcp_server.py"
                        ],
                        "env": {
                            "DOCKER_COMPOSE_PROJECT": "pitchscoop"
                        }
                    }
                }
            },
            "config_file_location": {
                "macOS": "~/Library/Application Support/Claude/claude_desktop_config.json",
                "Windows": "%APPDATA%\\Claude\\claude_desktop_config.json"
            }
        },
        
        "chatgpt-mcp": {
            "description": "Configuration for ChatGPT MCP bridge",
            "config": {
                "mcp_servers": [
                    {
                        "name": "pitchscoop",
                        "command": ["docker", "compose", "-f", f"{project_path}/docker-compose.yml", "exec", "-T", "api", "python", "mcp_server.py"],
                        "env": {"DOCKER_COMPOSE_PROJECT": "pitchscoop"}
                    }
                ]
            },
            "setup_notes": [
                "Requires mcp-chatgpt bridge: https://github.com/wong2/mcp-chatgpt",
                "Install bridge first, then add this configuration",
                "May have compatibility limitations compared to Claude Desktop"
            ]
        },
        
        "custom": {
            "description": "Configuration for custom MCP client",
            "config": {
                "server_command": f"cd {project_path} && docker compose exec -T api python mcp_server.py",
                "transport": "stdio",
                "server_name": "pitchscoop",
                "server_version": "1.0.0"
            },
            "implementation_notes": [
                "Implement MCP protocol client",
                "Connect via stdio transport", 
                "See MCP specification: https://modelcontextprotocol.io/introduction"
            ]
        }
    }
    
    if platform not in configs:
        return {
            "success": False,
            "error": f"Unknown platform: {platform}",
            "available_platforms": list(configs.keys())
        }
    
    config_data = configs[platform]
    
    return {
        "success": True,
        "platform": platform,
        "description": config_data["description"],
        "config": config_data["config"],
        "config_json": json.dumps(config_data["config"], indent=2),
        **{k: v for k, v in config_data.items() if k not in ["config", "description"]}
    }


async def _run_diagnostics() -> Dict[str, Any]:
    """Run comprehensive system diagnostics."""
    
    diagnostics = {
        "success": True,
        "timestamp": str(Path.cwd()),
        "results": {}
    }
    
    # Check requirements
    req_check = await _check_requirements()
    diagnostics["results"]["requirements"] = req_check
    
    # Check service status
    status_check = await _get_status()
    diagnostics["results"]["services"] = status_check
    
    # Check Docker logs for errors
    try:
        logs_result = subprocess.run(
            ["docker", "compose", "logs", "--tail", "10", "api"],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        diagnostics["results"]["recent_logs"] = {
            "success": logs_result.returncode == 0,
            "logs": logs_result.stdout if logs_result.returncode == 0 else logs_result.stderr
        }
    except Exception as e:
        diagnostics["results"]["recent_logs"] = {
            "success": False,
            "error": str(e)
        }
    
    # Overall diagnosis
    if not req_check["success"]:
        diagnostics["diagnosis"] = "❌ Requirements missing - install Docker first"
    elif not status_check.get("services"):
        diagnostics["diagnosis"] = "⚠️ Services not running - try system.start_services"
    elif status_check.get("overall_status", "").startswith("✅"):
        diagnostics["diagnosis"] = "✅ System appears healthy"
    else:
        diagnostics["diagnosis"] = "⚠️ Some issues detected - check service status"
    
    return diagnostics


async def _get_setup_guide(platform: str) -> Dict[str, Any]:
    """Get step-by-step setup guide for a platform."""
    
    guides = {
        "claude-desktop": {
            "title": "Claude Desktop MCP Setup",
            "steps": [
                "1. Install Docker Desktop from https://docs.docker.com/get-docker/",
                "2. Clone/download PitchScoop to your local machine",
                "3. Open terminal in PitchScoop directory",
                "4. Run: system.generate_config with platform='claude-desktop'",
                "5. Copy the generated config to ~/Library/Application Support/Claude/claude_desktop_config.json (macOS)",
                "6. Restart Claude Desktop completely",
                "7. Say 'Help me set up PitchScoop' to start onboarding"
            ]
        },
        
        "chatgpt-mcp": {
            "title": "ChatGPT MCP Bridge Setup", 
            "steps": [
                "1. Install Docker Desktop",
                "2. Install MCP-ChatGPT bridge: npm install -g mcp-chatgpt",
                "3. Clone/download PitchScoop",
                "4. Run: system.generate_config with platform='chatgpt-mcp'",
                "5. Configure the MCP bridge with generated config",
                "6. Connect ChatGPT to the MCP bridge",
                "7. Say 'Set up my pitch competition platform' to start"
            ]
        },
        
        "custom": {
            "title": "Custom MCP Client Setup",
            "steps": [
                "1. Implement MCP protocol client (see https://modelcontextprotocol.io/)",
                "2. Install Docker Desktop",
                "3. Clone/download PitchScoop", 
                "4. Connect to MCP server via stdio transport",
                "5. Command: cd /path/to/pitchscoop && docker compose exec -T api python mcp_server.py",
                "6. Test connection with tools/list method",
                "7. Use tools for pitch competition management"
            ]
        },
        
        "overview": {
            "title": "PitchScoop MCP Overview",
            "description": "PitchScoop is an MCP-first application for AI-powered pitch competitions",
            "key_features": [
                "🎯 Create and manage competitions (hackathons, pitch events)",
                "🎙️ Record and transcribe pitches with AI",
                "📊 AI-powered scoring and analysis",
                "💬 RAG-powered conversations about competition data",
                "🏆 Leaderboards and participant management"
            ],
            "platforms": [
                "Claude Desktop (recommended) - native MCP support", 
                "ChatGPT with MCP bridge - community solution",
                "Custom MCP clients - full protocol implementation"
            ]
        }
    }
    
    if platform not in guides:
        return {
            "success": False,
            "error": f"No guide available for platform: {platform}",
            "available_guides": list(guides.keys())
        }
    
    return {
        "success": True,
        "platform": platform,
        **guides[platform]
    }
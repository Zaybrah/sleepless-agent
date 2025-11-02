"""Web UI server for configuration management."""

from __future__ import annotations

import asyncio
import os
import secrets
import shutil
import signal
import subprocess
import psutil
from pathlib import Path
from typing import Any

import yaml
from starlette.applications import Starlette
from starlette.responses import JSONResponse, HTMLResponse, Response
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import base64

from sleepless_agent.utils.config import get_config, CONFIG_ENV_VAR, DEFAULT_CONFIG_NAME
from sleepless_agent.monitoring.logging import get_logger

logger = get_logger(__name__)

# Basic auth credentials from environment variables
WEBUI_USERNAME = os.environ.get("WEBUI_USERNAME", "admin")
WEBUI_PASSWORD = os.environ.get("WEBUI_PASSWORD", "")  # Empty means no auth

# Process tracking for daemon
DAEMON_PROCESS: subprocess.Popen | None = None
DAEMON_PID_FILE = Path.home() / ".sleepless-agent" / "daemon.pid"


def get_config_path() -> Path:
    """Get the path to the configuration file."""
    config_path_str = os.environ.get(CONFIG_ENV_VAR)
    if config_path_str:
        return Path(config_path_str).expanduser().resolve()
    
    # Use the packaged config.yaml
    from importlib import resources
    config_resource = resources.files("sleepless_agent").joinpath(DEFAULT_CONFIG_NAME)
    
    # Since we can't write to the packaged config, create a user config
    user_config_path = Path.home() / ".sleepless-agent" / "config.yaml"
    if not user_config_path.exists():
        user_config_path.parent.mkdir(parents=True, exist_ok=True)
        # Copy the default config to user config
        with config_resource.open("r") as src:
            user_config_path.write_text(src.read())
    
    return user_config_path


def load_config_file() -> dict[str, Any]:
    """Load the configuration from file."""
    config_path = get_config_path()
    with config_path.open("r") as f:
        return yaml.safe_load(f) or {}


def save_config_file(config_data: dict[str, Any]) -> None:
    """Save the configuration to file."""
    config_path = get_config_path()
    with config_path.open("w") as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)


class BasicAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to handle HTTP Basic Authentication."""
    
    async def dispatch(self, request: Request, call_next):
        # Skip auth if no password is set
        if not WEBUI_PASSWORD:
            return await call_next(request)
        
        # Skip auth for static files
        if request.url.path.startswith("/static"):
            return await call_next(request)
        
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Basic "):
            return Response(
                content="Authentication required",
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="Sleepless Agent WebUI"'}
            )
        
        try:
            # Decode credentials
            credentials = base64.b64decode(auth_header[6:]).decode("utf-8")
            username, password = credentials.split(":", 1)
            
            # Verify credentials using constant-time comparison to prevent timing attacks
            username_match = secrets.compare_digest(username, WEBUI_USERNAME)
            password_match = secrets.compare_digest(password, WEBUI_PASSWORD)
            
            if username_match and password_match:
                return await call_next(request)
        except Exception as e:
            logger.error(f"Auth error: {e}")
        
        # Authentication failed
        return Response(
            content="Invalid credentials",
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Sleepless Agent WebUI"'}
        )


def is_daemon_running() -> tuple[bool, int | None]:
    """Check if the daemon process is running."""
    # First check PID file
    if DAEMON_PID_FILE.exists():
        try:
            pid = int(DAEMON_PID_FILE.read_text().strip())
            if psutil.pid_exists(pid):
                proc = psutil.Process(pid)
                # Verify it's actually our daemon by checking for exact command pattern
                cmdline = proc.cmdline()
                if len(cmdline) >= 2 and cmdline[0].endswith('python') and 'sle' in cmdline[1] and 'daemon' in cmdline:
                    return True, pid
                # Alternative check for direct invocation
                if 'sleepless_agent' in ' '.join(cmdline) and 'daemon' in cmdline:
                    return True, pid
        except (ValueError, psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    # Check if there's a global daemon running by looking for specific command pattern
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline', [])
            if not cmdline:
                continue
            
            # Look for exact 'sle daemon' or 'sleepless-agent daemon' pattern
            cmdline_str = ' '.join(cmdline)
            if ('sle daemon' in cmdline_str or 'sleepless-agent daemon' in cmdline_str or 
                'sleepless_agent.core.daemon' in cmdline_str):
                return True, proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return False, None


def save_daemon_pid(pid: int) -> None:
    """Save the daemon PID to file."""
    DAEMON_PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    DAEMON_PID_FILE.write_text(str(pid))


def clear_daemon_pid() -> None:
    """Clear the daemon PID file."""
    if DAEMON_PID_FILE.exists():
        DAEMON_PID_FILE.unlink()


# Get the directory where this file is located
CURRENT_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(CURRENT_DIR / "templates"))


async def homepage(request):
    """Render the main configuration page."""
    config = load_config_file()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "config": config,
        }
    )


async def files_page(request):
    """Render the file browser page."""
    return templates.TemplateResponse(
        "files.html",
        {
            "request": request,
        }
    )


async def get_config_endpoint(request):
    """API endpoint to get current configuration."""
    try:
        config = load_config_file()
        return JSONResponse({"success": True, "config": config})
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )


async def update_config_endpoint(request):
    """API endpoint to update configuration."""
    try:
        data = await request.json()
        config_data = data.get("config", {})
        
        # Validate the config structure
        if not isinstance(config_data, dict):
            return JSONResponse(
                {"success": False, "error": "Invalid config format"},
                status_code=400
            )
        
        # Save the configuration
        save_config_file(config_data)
        logger.info("Configuration updated successfully")
        
        return JSONResponse({"success": True, "message": "Configuration updated successfully"})
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )


async def get_agent_status(request):
    """API endpoint to get agent daemon status."""
    try:
        running, pid = is_daemon_running()
        return JSONResponse({
            "success": True,
            "running": running,
            "pid": pid
        })
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )


async def start_agent(request):
    """API endpoint to start the agent daemon."""
    global DAEMON_PROCESS
    
    try:
        running, _ = is_daemon_running()
        if running:
            return JSONResponse(
                {"success": False, "error": "Agent is already running"},
                status_code=400
            )
        
        # Create log files for daemon output
        log_dir = DAEMON_PID_FILE.parent
        log_dir.mkdir(parents=True, exist_ok=True)
        stdout_log = log_dir / "daemon_stdout.log"
        stderr_log = log_dir / "daemon_stderr.log"
        
        # Start daemon in detached mode with logging
        DAEMON_PROCESS = subprocess.Popen(
            ["sle", "daemon"],
            stdout=open(stdout_log, 'a'),
            stderr=open(stderr_log, 'a'),
            start_new_session=True
        )
        
        # Give it a moment to start
        await asyncio.sleep(1)
        
        # Verify it started
        running, pid = is_daemon_running()
        if running and pid:
            save_daemon_pid(pid)
            logger.info(f"Agent daemon started with PID {pid}. Logs: {stdout_log}, {stderr_log}")
            return JSONResponse({"success": True, "pid": pid})
        else:
            # Read error logs if start failed
            error_msg = "Failed to start agent"
            if stderr_log.exists():
                try:
                    recent_errors = stderr_log.read_text().strip().split('\n')[-5:]
                    if recent_errors:
                        error_msg += f". Recent errors: {'; '.join(recent_errors)}"
                except Exception:
                    pass
            return JSONResponse(
                {"success": False, "error": error_msg},
                status_code=500
            )
    except Exception as e:
        logger.error(f"Error starting agent: {e}")
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )


async def stop_agent(request):
    """API endpoint to stop the agent daemon."""
    global DAEMON_PROCESS
    
    try:
        running, pid = is_daemon_running()
        if not running:
            return JSONResponse(
                {"success": False, "error": "Agent is not running"},
                status_code=400
            )
        
        # Try to stop the process gracefully
        if pid:
            try:
                proc = psutil.Process(pid)
                proc.terminate()
                
                # Wait for graceful shutdown
                await asyncio.sleep(2)
                
                # Force kill if still running
                if proc.is_running():
                    proc.kill()
                
                clear_daemon_pid()
                logger.info(f"Agent daemon stopped (PID {pid})")
            except psutil.NoSuchProcess:
                clear_daemon_pid()
        
        DAEMON_PROCESS = None
        return JSONResponse({"success": True})
    except Exception as e:
        logger.error(f"Error stopping agent: {e}")
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )


def get_workspace_root() -> Path:
    """Get the workspace root path from configuration."""
    try:
        config = get_config()
        workspace_root = Path(config.agent.workspace_root).expanduser().resolve()
        workspace_root.mkdir(parents=True, exist_ok=True)
        return workspace_root
    except Exception as e:
        logger.error(f"Error getting workspace root: {e}")
        # Fallback to default
        default_workspace = Path("./workspace").expanduser().resolve()
        default_workspace.mkdir(parents=True, exist_ok=True)
        return default_workspace


def is_path_safe(base_path: Path, target_path: Path) -> bool:
    """Check if target_path is within base_path to prevent directory traversal attacks."""
    try:
        # Resolve both paths to absolute paths
        base_resolved = base_path.resolve()
        target_resolved = target_path.resolve()
        # Check if target is within base
        return target_resolved.is_relative_to(base_resolved)
    except (ValueError, OSError):
        return False


async def browse_files(request):
    """API endpoint to browse files and folders in the workspace."""
    try:
        workspace_root = get_workspace_root()
        
        # Get path parameter from query string
        path_param = request.query_params.get("path", "")
        
        if path_param:
            target_path = (workspace_root / path_param).resolve()
        else:
            target_path = workspace_root
        
        # Security check
        if not is_path_safe(workspace_root, target_path):
            return JSONResponse(
                {"success": False, "error": "Access denied: path outside workspace"},
                status_code=403
            )
        
        if not target_path.exists():
            return JSONResponse(
                {"success": False, "error": "Path does not exist"},
                status_code=404
            )
        
        if target_path.is_file():
            # Return file metadata
            return JSONResponse({
                "success": True,
                "type": "file",
                "name": target_path.name,
                "path": str(target_path.relative_to(workspace_root)),
                "size": target_path.stat().st_size,
            })
        else:
            # List directory contents
            items = []
            for item in sorted(target_path.iterdir()):
                try:
                    relative_path = str(item.relative_to(workspace_root))
                    item_data = {
                        "name": item.name,
                        "path": relative_path,
                        "type": "directory" if item.is_dir() else "file",
                    }
                    if item.is_file():
                        item_data["size"] = item.stat().st_size
                    items.append(item_data)
                except (OSError, ValueError):
                    continue
            
            return JSONResponse({
                "success": True,
                "type": "directory",
                "path": str(target_path.relative_to(workspace_root)) if target_path != workspace_root else "",
                "items": items,
            })
    except Exception as e:
        logger.error(f"Error browsing files: {e}")
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )


async def read_file(request):
    """API endpoint to read file contents."""
    try:
        workspace_root = get_workspace_root()
        
        # Get path parameter from query string
        path_param = request.query_params.get("path", "")
        if not path_param:
            return JSONResponse(
                {"success": False, "error": "Path parameter required"},
                status_code=400
            )
        
        target_path = (workspace_root / path_param).resolve()
        
        # Security check
        if not is_path_safe(workspace_root, target_path):
            return JSONResponse(
                {"success": False, "error": "Access denied: path outside workspace"},
                status_code=403
            )
        
        if not target_path.exists():
            return JSONResponse(
                {"success": False, "error": "File does not exist"},
                status_code=404
            )
        
        if not target_path.is_file():
            return JSONResponse(
                {"success": False, "error": "Path is not a file"},
                status_code=400
            )
        
        # Read file content
        try:
            content = target_path.read_text(encoding="utf-8")
            return JSONResponse({
                "success": True,
                "content": content,
                "path": str(target_path.relative_to(workspace_root)),
                "size": target_path.stat().st_size,
            })
        except UnicodeDecodeError:
            # Binary file
            return JSONResponse(
                {"success": False, "error": "File is binary and cannot be edited in the web UI"},
                status_code=400
            )
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )


async def write_file(request):
    """API endpoint to write/update file contents."""
    try:
        workspace_root = get_workspace_root()
        
        data = await request.json()
        path_param = data.get("path", "")
        content = data.get("content", "")
        
        if not path_param:
            return JSONResponse(
                {"success": False, "error": "Path parameter required"},
                status_code=400
            )
        
        target_path = (workspace_root / path_param).resolve()
        
        # Security check
        if not is_path_safe(workspace_root, target_path):
            return JSONResponse(
                {"success": False, "error": "Access denied: path outside workspace"},
                status_code=403
            )
        
        # Create parent directories if they don't exist
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file content
        target_path.write_text(content, encoding="utf-8")
        logger.info(f"File written: {target_path.relative_to(workspace_root)}")
        
        return JSONResponse({
            "success": True,
            "message": "File saved successfully",
            "path": str(target_path.relative_to(workspace_root)),
        })
    except Exception as e:
        logger.error(f"Error writing file: {e}")
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )


async def create_folder(request):
    """API endpoint to create a new folder."""
    try:
        workspace_root = get_workspace_root()
        
        data = await request.json()
        path_param = data.get("path", "")
        
        if not path_param:
            return JSONResponse(
                {"success": False, "error": "Path parameter required"},
                status_code=400
            )
        
        target_path = (workspace_root / path_param).resolve()
        
        # Security check
        if not is_path_safe(workspace_root, target_path):
            return JSONResponse(
                {"success": False, "error": "Access denied: path outside workspace"},
                status_code=403
            )
        
        if target_path.exists():
            return JSONResponse(
                {"success": False, "error": "Path already exists"},
                status_code=400
            )
        
        # Create folder
        target_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Folder created: {target_path.relative_to(workspace_root)}")
        
        return JSONResponse({
            "success": True,
            "message": "Folder created successfully",
            "path": str(target_path.relative_to(workspace_root)),
        })
    except Exception as e:
        logger.error(f"Error creating folder: {e}")
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )


async def delete_path(request):
    """API endpoint to delete a file or folder."""
    try:
        workspace_root = get_workspace_root()
        
        data = await request.json()
        path_param = data.get("path", "")
        
        if not path_param:
            return JSONResponse(
                {"success": False, "error": "Path parameter required"},
                status_code=400
            )
        
        target_path = (workspace_root / path_param).resolve()
        
        # Security check
        if not is_path_safe(workspace_root, target_path):
            return JSONResponse(
                {"success": False, "error": "Access denied: path outside workspace"},
                status_code=403
            )
        
        if not target_path.exists():
            return JSONResponse(
                {"success": False, "error": "Path does not exist"},
                status_code=404
            )
        
        # Don't allow deleting the workspace root itself
        if target_path == workspace_root:
            return JSONResponse(
                {"success": False, "error": "Cannot delete workspace root"},
                status_code=403
            )
        
        # Delete file or folder
        if target_path.is_dir():
            shutil.rmtree(target_path)
            logger.info(f"Folder deleted: {path_param}")
        else:
            target_path.unlink()
            logger.info(f"File deleted: {path_param}")
        
        return JSONResponse({
            "success": True,
            "message": "Deleted successfully",
        })
    except Exception as e:
        logger.error(f"Error deleting path: {e}")
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )


routes = [
    Route("/", homepage),
    Route("/files", files_page),
    Route("/api/config", get_config_endpoint, methods=["GET"]),
    Route("/api/config", update_config_endpoint, methods=["POST"]),
    Route("/api/agent/status", get_agent_status, methods=["GET"]),
    Route("/api/agent/start", start_agent, methods=["POST"]),
    Route("/api/agent/stop", stop_agent, methods=["POST"]),
    Route("/api/files/browse", browse_files, methods=["GET"]),
    Route("/api/files/read", read_file, methods=["GET"]),
    Route("/api/files/write", write_file, methods=["POST"]),
    Route("/api/files/create-folder", create_folder, methods=["POST"]),
    Route("/api/files/delete", delete_path, methods=["POST"]),
    Mount("/static", StaticFiles(directory=str(CURRENT_DIR / "static")), name="static"),
]


# Enable debug mode via environment variable for development
DEBUG_MODE = os.environ.get("SLEEPLESS_WEBUI_DEBUG", "false").lower() == "true"

# Add basic auth middleware
middleware = [
    Middleware(BasicAuthMiddleware)
]

app = Starlette(debug=DEBUG_MODE, routes=routes, middleware=middleware)


def run_server(host: str = "127.0.0.1", port: int = 8080):
    """Run the web UI server."""
    import uvicorn
    
    logger.info(f"Starting web UI server at http://{host}:{port}")
    logger.info(f"Configuration file: {get_config_path()}")
    
    if WEBUI_PASSWORD:
        logger.info(f"Basic authentication enabled (username: {WEBUI_USERNAME})")
    else:
        logger.warning("Basic authentication disabled - set WEBUI_PASSWORD to enable")
    
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_server()

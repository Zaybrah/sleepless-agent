"""Web UI server for configuration management."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from starlette.applications import Starlette
from starlette.responses import JSONResponse, HTMLResponse
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from sleepless_agent.utils.config import get_config, CONFIG_ENV_VAR, DEFAULT_CONFIG_NAME
from sleepless_agent.monitoring.logging import get_logger

logger = get_logger(__name__)


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


routes = [
    Route("/", homepage),
    Route("/api/config", get_config_endpoint, methods=["GET"]),
    Route("/api/config", update_config_endpoint, methods=["POST"]),
    Mount("/static", StaticFiles(directory=str(CURRENT_DIR / "static")), name="static"),
]


# Enable debug mode via environment variable for development
DEBUG_MODE = os.environ.get("SLEEPLESS_WEBUI_DEBUG", "false").lower() == "true"

app = Starlette(debug=DEBUG_MODE, routes=routes)


def run_server(host: str = "127.0.0.1", port: int = 8080):
    """Run the web UI server."""
    import uvicorn
    
    logger.info(f"Starting web UI server at http://{host}:{port}")
    logger.info(f"Configuration file: {get_config_path()}")
    
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_server()

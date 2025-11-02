# Web UI Configuration

The Sleepless Agent includes a web-based configuration interface that makes it easy to manage your agent's settings through a browser.

## Overview

Instead of manually editing the `config.yaml` file, you can use the web UI to:

- View and modify Claude Code settings
- Configure Git integration
- Adjust agent workspace and timeout settings
- Enable/disable multi-agent workflow components
- Toggle auto-generation features

## Starting the Web UI

Launch the web interface using the `webui` command:

```bash
# Start with default settings (http://127.0.0.1:8080)
sle webui

# Specify custom host and port
sle webui --host 0.0.0.0 --port 9000

# Make accessible on your network
sle webui --host 0.0.0.0 --port 8080
```

Once started, open your web browser and navigate to the displayed URL (e.g., `http://127.0.0.1:8080`).

## Configuration Sections

### 🔧 Claude Code Settings

Configure how the agent interacts with Claude Code CLI:

- **Binary Path**: Path to the Claude Code CLI binary (default: `claude`)
- **Model**: Claude model to use (e.g., `claude-sonnet-4-5-20250929`)
- **Day Threshold (%)**: Usage threshold during daytime hours (default: 20%)
- **Night Threshold (%)**: Usage threshold during nighttime hours (default: 80%)
- **Night Start Hour**: When nighttime period begins (default: 1 AM)
- **Night End Hour**: When nighttime period ends (default: 9 AM)

### 🔀 Git Settings

Manage Git integration for automatic version control:

- **Use Remote Repository**: Enable/disable remote repository integration
- **Remote Repository URL**: Your Git repository URL (e.g., `git@github.com:username/repo.git`)
- **Auto Create Repository**: Automatically create the repository if it doesn't exist

### ⚙️ Agent Settings

Core agent configuration:

- **Workspace Root**: Directory for agent workspaces (default: `./workspace`)
- **Task Timeout (seconds)**: Maximum time for a task to run (default: 1800)

### 🤝 Multi-Agent Workflow

Configure the multi-agent system with planner, worker, and evaluator agents:

**Planner Agent:**
- Enable/disable the planner agent
- Max turns for planning phase

**Worker Agent:**
- Enable/disable the worker agent
- Max turns for execution phase

**Evaluator Agent:**
- Enable/disable the evaluator agent
- Max turns for evaluation phase

### 🔄 Auto Generation

Toggle automatic task generation to keep the agent productive during idle time.

## Saving Changes

1. Modify any configuration values in the web UI
2. Click the **💾 Save Configuration** button
3. A success message will confirm the save
4. **Important**: Restart the daemon for changes to take effect

```bash
# If running as a service
sudo systemctl restart sleepless-agent

# If running manually, stop with Ctrl+C and restart
sle daemon
```

## Configuration File Location

The web UI manages the configuration file at:

- User config: `~/.sleepless-agent/config.yaml`
- Environment override: Set `SLEEPLESS_AGENT_CONFIG_FILE` to use a custom location

When you first use the web UI, it automatically creates `~/.sleepless-agent/config.yaml` by copying the default configuration.

## Security Considerations

The web UI binds to `127.0.0.1` (localhost) by default, making it accessible only from the local machine. 

**To make it accessible on your network:**

```bash
sle webui --host 0.0.0.0 --port 8080
```

⚠️ **Warning**: When binding to `0.0.0.0`, anyone on your network can access and modify your agent's configuration. Only use this on trusted networks or implement additional security measures (firewall rules, reverse proxy with authentication, etc.).

## Troubleshooting

### Port Already in Use

If you see an error about the port being in use:

```bash
# Try a different port
sle webui --port 8888
```

### Changes Not Taking Effect

Remember to restart the daemon after saving configuration changes:

```bash
# Stop the current daemon (Ctrl+C if running in terminal)
# Then restart
sle daemon
```

### Configuration File Not Found

The web UI automatically creates `~/.sleepless-agent/config.yaml` if it doesn't exist. If you encounter issues:

1. Check that the directory exists: `ls -la ~/.sleepless-agent/`
2. Verify file permissions: `ls -la ~/.sleepless-agent/config.yaml`
3. Check the logs for error messages

## Tips

- **Use Reload Button**: Click **🔄 Reload** to refresh the UI with current config values
- **Bookmark the URL**: Add it to your bookmarks for quick access
- **Test Changes**: Try changing one setting at a time to verify each change works as expected
- **Check Logs**: Monitor the daemon logs to see configuration changes in action

## Integration with CLI

The web UI complements the command-line interface. You can:

1. Use the web UI to configure settings
2. Use the CLI commands (`sle check`, `sle think`, etc.) to interact with the agent
3. Switch between web UI and manual YAML editing as needed

All methods work with the same underlying configuration file.

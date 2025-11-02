# Docker Setup Guide for Sleepless Agent

This guide covers how to run Sleepless Agent using Docker and Docker Compose.

## Quick Start

### Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- Slack Bot Token and App Token (see main [README.md](../README.md) for setup)
- Claude Code CLI (optional - can be installed in container or mounted from host)

### Using Docker Compose (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/context-machine-lab/sleepless-agent.git
   cd sleepless-agent
   ```

2. **Create and configure `.env` file:**
   ```bash
   cp .env.example .env
   # Edit .env with your Slack tokens
   nano .env
   ```

3. **Start the agent:**
   ```bash
   docker-compose up -d
   ```

4. **View logs:**
   ```bash
   docker-compose logs -f sleepless-agent
   ```

5. **Stop the agent:**
   ```bash
   docker-compose down
   ```

### Using Docker Directly

1. **Build the image:**
   ```bash
   docker build -t sleepless-agent:latest .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name sleepless-agent \
     -v $(pwd)/workspace:/app/workspace \
     --env-file .env \
     sleepless-agent:latest
   ```

3. **View logs:**
   ```bash
   docker logs -f sleepless-agent
   ```

## Configuration

### Environment Variables

All configuration is done through environment variables in the `.env` file:

```bash
# Required
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_APP_TOKEN=xapp-your-token

# Optional
AGENT_WORKSPACE_ROOT=/app/workspace
AGENT_DB_PATH=/app/workspace/data/tasks.db
AGENT_RESULTS_PATH=/app/workspace/data/results
LOG_LEVEL=INFO
GIT_USER_NAME=Sleepless Agent
GIT_USER_EMAIL=agent@sleepless.local
```

### Volumes

The container uses a volume to persist data:

- `./workspace` - Contains all persistent data:
  - `data/` - SQLite database, results, logs, metrics
  - `tasks/` - Individual task workspaces
  - `projects/` - Project workspaces
  - `trash/` - Soft-deleted items

### Claude Code CLI

The Dockerfile attempts to install Claude Code CLI during the build. If this fails due to network/certificate issues, you have several options:

#### Option 1: Install in Running Container
```bash
docker exec -it sleepless-agent /bin/bash
npm install -g @anthropic-ai/claude-code
```

#### Option 2: Mount from Host
If you have Claude Code CLI installed on your host:

```yaml
# In docker-compose.yml
volumes:
  - /usr/local/bin/claude:/usr/local/bin/claude:ro
```

#### Option 3: Use Environment Variable
Set a custom path to Claude Code CLI:

```bash
CLAUDE_CODE_BINARY_PATH=/custom/path/to/claude
```

## Advanced Usage

### Running CLI Commands

Execute CLI commands in the running container:

```bash
# Check status
docker exec sleepless-agent sle check

# View a report
docker exec sleepless-agent sle report 42

# Submit a task
docker exec sleepless-agent sle think "Add new feature" -p my-project
```

### Custom Configuration

Mount a custom `config.yaml`:

```yaml
# In docker-compose.yml
volumes:
  - ./my-config.yaml:/app/src/sleepless_agent/config.yaml:ro
```

### Git Integration

For private Git repositories, mount your SSH keys:

```yaml
# In docker-compose.yml
volumes:
  - ~/.ssh:/root/.ssh:ro
  - ~/.gitconfig:/root/.gitconfig:ro
```

### Using with GitHub CLI

To enable PR automation with GitHub CLI:

1. Uncomment the GitHub CLI installation section in the Dockerfile
2. Mount your GitHub CLI config:
   ```yaml
   volumes:
     - ~/.config/gh:/root/.config/gh:ro
   ```

## Troubleshooting

### Build Failures

**SSL/Certificate Issues:**
If you encounter SSL certificate errors during build:

```bash
# Use the simplified Dockerfile
docker build -f Dockerfile.simple -t sleepless-agent:latest .
```

**Claude Code CLI Installation Failure:**
This is non-fatal. The container will still build. Install Claude Code CLI after container starts (see options above).

### Runtime Issues

**Permission Errors:**
If you encounter permission errors with mounted volumes:

```bash
# Fix ownership on Linux/Mac
sudo chown -R $(id -u):$(id -g) ./workspace
```

**Database Locked:**
If you see "database is locked" errors, ensure only one instance is running:

```bash
docker-compose down
docker-compose up -d
```

### Logs and Debugging

**View detailed logs:**
```bash
docker-compose logs -f --tail=100 sleepless-agent
```

**Access the container:**
```bash
docker exec -it sleepless-agent /bin/bash
```

**Check health status:**
```bash
docker inspect --format='{{.State.Health.Status}}' sleepless-agent
```

## Production Deployment

### Best Practices

1. **Use Docker Secrets** for sensitive data:
   ```yaml
   secrets:
     - slack_bot_token
     - slack_app_token
   ```

2. **Enable auto-restart:**
   ```yaml
   restart: always
   ```

3. **Use named volumes** for better management:
   ```yaml
   volumes:
     - workspace-data:/app/workspace
   ```

4. **Set resource limits:**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 2G
       reservations:
         memory: 512M
   ```

5. **Regular backups:**
   ```bash
   # Backup workspace
   docker exec sleepless-agent tar czf /tmp/backup.tar.gz /app/workspace
   docker cp sleepless-agent:/tmp/backup.tar.gz ./backup-$(date +%Y%m%d).tar.gz
   ```

### Monitoring

Use Docker's built-in monitoring:

```bash
# Resource usage
docker stats sleepless-agent

# Health checks
docker inspect sleepless-agent | jq '.[].State.Health'
```

### Updates

To update to a new version:

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Multi-Architecture Builds

Build for multiple architectures:

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t sleepless-agent:latest .
```

## Docker Hub Deployment

Push to Docker Hub:

```bash
docker tag sleepless-agent:latest yourusername/sleepless-agent:latest
docker push yourusername/sleepless-agent:latest
```

## Support

For issues specific to Docker deployment, please check:
- [Docker Documentation](https://docs.docker.com/)
- [Main README](../README.md)
- [GitHub Issues](https://github.com/context-machine-lab/sleepless-agent/issues)

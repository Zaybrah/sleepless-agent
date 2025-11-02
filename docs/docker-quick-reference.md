# Docker Quick Reference for Sleepless Agent

## Quick Start
```bash
# Start the agent
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the agent
docker-compose down
```

## Common Commands

### Container Management
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View running containers
docker-compose ps

# Remove containers and volumes
docker-compose down -v
```

### Logs and Monitoring
```bash
# View all logs
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail=100

# View logs for specific time
docker-compose logs --since 30m

# Check container health
docker inspect --format='{{.State.Health.Status}}' sleepless-agent

# Monitor resource usage
docker stats sleepless-agent
```

### CLI Commands
```bash
# Execute CLI commands in container
docker exec sleepless-agent sle check
docker exec sleepless-agent sle report 42
docker exec sleepless-agent sle think "Task description" -p project-name

# Access container shell
docker exec -it sleepless-agent /bin/bash

# View Python version
docker exec sleepless-agent python --version

# Check installed packages
docker exec sleepless-agent pip list
```

### Build and Update
```bash
# Rebuild image
docker-compose build

# Rebuild without cache
docker-compose build --no-cache

# Pull latest image (if using pre-built)
docker-compose pull

# Update and restart
docker-compose down
docker-compose build
docker-compose up -d
```

### Database Operations
```bash
# Access SQLite database
docker exec -it sleepless-agent sqlite3 /app/workspace/data/tasks.db

# Backup database
docker exec sleepless-agent sqlite3 /app/workspace/data/tasks.db .dump > backup.sql

# View tasks
docker exec sleepless-agent sqlite3 /app/workspace/data/tasks.db "SELECT id, description, status FROM tasks;"
```

### Volume Management
```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect sleepless-agent_workspace-data

# Backup workspace
docker exec sleepless-agent tar czf /tmp/backup.tar.gz /app/workspace
docker cp sleepless-agent:/tmp/backup.tar.gz ./backup-$(date +%Y%m%d).tar.gz

# Restore workspace
docker cp ./backup.tar.gz sleepless-agent:/tmp/
docker exec sleepless-agent tar xzf /tmp/backup.tar.gz -C /
```

### Troubleshooting
```bash
# View detailed logs
docker logs sleepless-agent --tail=200 --follow

# Check container configuration
docker inspect sleepless-agent

# View environment variables
docker exec sleepless-agent env

# Check network connectivity
docker exec sleepless-agent ping -c 3 google.com

# Test Python imports
docker exec sleepless-agent python -c "from sleepless_agent import __version__; print(__version__)"

# View running processes
docker exec sleepless-agent ps aux

# Check disk usage
docker exec sleepless-agent df -h
```

### Cleanup
```bash
# Remove stopped containers
docker-compose rm

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Clean everything (be careful!)
docker system prune -a --volumes
```

## Environment Variables

View or modify via docker-compose.yml:
```yaml
environment:
  - LOG_LEVEL=DEBUG  # Change to DEBUG for verbose logging
  - GIT_USER_NAME=Your Name
  - GIT_USER_EMAIL=your@email.com
```

Or via .env file:
```bash
LOG_LEVEL=DEBUG
GIT_USER_NAME=Your Name
```

## Port Mapping

If you need to expose ports for monitoring or APIs:
```yaml
# In docker-compose.yml
ports:
  - "8080:8080"  # host:container
```

## Multiple Instances

To run multiple instances:
```bash
# Use different project names
docker-compose -p sleepless-prod up -d
docker-compose -p sleepless-dev up -d

# Or use different compose files
docker-compose -f docker-compose.yml up -d
docker-compose -f docker-compose.dev.yml up -d
```

## Tips

- Always use `docker-compose logs -f` to monitor startup
- Check health status with `docker inspect` after starting
- Back up your workspace directory regularly
- Use named volumes in production for better portability
- Set resource limits in production deployments
- Keep your .env file secure and never commit it to git

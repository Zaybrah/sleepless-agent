# Sleepless Agent Docker Image
# Multi-stage build for optimal image size

# Stage 1: Build Node.js and install Claude Code CLI
FROM node:20-slim AS node-builder

# Install Claude Code CLI globally
# Note: This may fail in corporate environments with proxies/certificates
# If installation fails, you have several options:
#   1. Install after container starts: docker exec sleepless-agent npm install -g @anthropic-ai/claude-code
#   2. Mount from host: -v /usr/local/bin/claude:/usr/local/bin/claude:ro
#   3. Set CLAUDE_CODE_BINARY_PATH environment variable to custom path
RUN npm install -g @anthropic-ai/claude-code 2>&1 || \
    (echo "Warning: Claude Code CLI installation failed." && \
     echo "This is often due to network/certificate issues in corporate environments." && \
     echo "You can install it manually after container starts or mount from host." && \
     echo "See docs/docker.md for detailed instructions.")

# Stage 2: Final application image
FROM python:3.11-slim

LABEL maintainer="Sleepless Agent Maintainers"
LABEL description="24/7 AI agent that maximizes Claude usage via Slack interface"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    gnupg \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Optional: Install GitHub CLI (uncomment if needed for PR automation)
# RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | \
#     dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg && \
#     chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg && \
#     echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | \
#     tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
#     apt-get update && apt-get install -y gh && \
#     rm -rf /var/lib/apt/lists/*

# Copy Node.js and npm from builder stage
COPY --from=node-builder /usr/local/bin/node /usr/local/bin/node
COPY --from=node-builder /usr/local/lib/node_modules /usr/local/lib/node_modules

# Create symlinks for npm and npx
RUN ln -sf /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm && \
    ln -sf /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

# Set working directory
WORKDIR /app

# Copy Python project files
COPY pyproject.toml README.md LICENSE Makefile ./
COPY src/ ./src/

# Install Python dependencies and the application
RUN pip install --no-cache-dir -e .

# Create workspace directories with proper permissions
RUN mkdir -p /app/workspace/data \
             /app/workspace/tasks \
             /app/workspace/projects \
             /app/workspace/trash && \
    chmod -R 755 /app/workspace

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    AGENT_WORKSPACE_ROOT=/app/workspace \
    AGENT_DB_PATH=/app/workspace/data/tasks.db \
    AGENT_RESULTS_PATH=/app/workspace/data/results

# Configure Git with default values (can be overridden via environment variables)
RUN git config --global user.name "Sleepless Agent" && \
    git config --global user.email "agent@sleepless.local"

# Create a non-root user for better security (optional but recommended)
# RUN useradd -m -u 1000 sleepless && \
#     chown -R sleepless:sleepless /app
# USER sleepless

# Volume for persistent data
VOLUME ["/app/workspace"]

# Health check to verify the application can import correctly
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from sleepless_agent import __version__" || exit 1

# Default command to start the daemon
CMD ["sle", "daemon"]

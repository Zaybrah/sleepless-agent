# Z.ai Configuration Guide

Complete guide for configuring Sleepless Agent to use Z.ai's API instead of the standard Claude Code Pro subscription.

## Overview

[Z.ai](https://z.ai) provides access to Claude Code using their GLM models, offering an alternative to Anthropic's Claude Code Pro subscription. This guide shows you how to configure Sleepless Agent to work with Z.ai.

**Benefits of using Z.ai:**
- Access to powerful GLM models (GLM-4.5, GLM-4.6)
- Alternative pricing structure
- Unlimited usage within subscription limits (no daily caps)
- Compatible with existing Claude Code CLI

## Prerequisites

Before starting, you need:

1. **Z.ai Account**: Sign up at [Z.ai Open Platform](https://open.bigmodel.cn/)
2. **API Key**: Create an API key from your Z.ai dashboard
3. **Claude Code CLI**: Already installed as part of Sleepless Agent setup

## Quick Setup

### Option 1: Automated Script (Recommended)

Z.ai provides an automated setup script:

```bash
# Download and run the z.ai configuration script
curl -O "https://cdn.bigmodel.cn/install/claude_code_zai_env.sh"
bash ./claude_code_zai_env.sh
```

This script will automatically configure your `~/.claude/settings.json` file with the necessary environment variables.

### Option 2: Manual Configuration

If you prefer manual setup or need more control:

#### Step 1: Configure Claude Code Settings

Edit or create `~/.claude/settings.json`:

```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "your_zai_api_key_here",
    "ANTHROPIC_BASE_URL": "https://api.z.ai/api/anthropic",
    "API_TIMEOUT_MS": "3000000"
  }
}
```

Replace `your_zai_api_key_here` with your actual Z.ai API key.

#### Step 2: Configure Model Selection (Optional)

To use specific GLM models, add these to your `~/.claude/settings.json`:

```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "your_zai_api_key_here",
    "ANTHROPIC_BASE_URL": "https://api.z.ai/api/anthropic",
    "API_TIMEOUT_MS": "3000000",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "GLM-4.5-Air",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "GLM-4.6",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "GLM-4.6"
  }
}
```

**Available GLM Models:**
- `GLM-4.5-Air` - Fast, lightweight model (similar to Haiku)
- `GLM-4.6` - Powerful model (similar to Sonnet/Opus)

#### Step 3: Disable Usage Monitoring

Since Z.ai doesn't have the same daily usage limits as Claude Code Pro, update your Sleepless Agent configuration:

Edit `config.yaml`:

```yaml
claude_code:
  binary_path: claude
  model: claude-sonnet-4-5-20250929  # This will be mapped to GLM-4.6
  skip_usage_check: true  # Disable usage monitoring for Z.ai
  # ... other settings
```

## Alternative: Environment Variables

Instead of editing `~/.claude/settings.json`, you can set environment variables directly:

### For Linux/macOS

Add to your `~/.bashrc`, `~/.zshrc`, or `~/.profile`:

```bash
# Z.ai Configuration
export ANTHROPIC_AUTH_TOKEN="your_zai_api_key_here"
export ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic"
export API_TIMEOUT_MS="3000000"

# Optional: Specify GLM models
export ANTHROPIC_DEFAULT_HAIKU_MODEL="GLM-4.5-Air"
export ANTHROPIC_DEFAULT_SONNET_MODEL="GLM-4.6"
export ANTHROPIC_DEFAULT_OPUS_MODEL="GLM-4.6"
```

Then reload your shell:
```bash
source ~/.bashrc  # or ~/.zshrc
```

### For Windows

**Command Prompt:**
```cmd
set ANTHROPIC_AUTH_TOKEN=your_zai_api_key_here
set ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
set API_TIMEOUT_MS=3000000
```

**PowerShell:**
```powershell
$env:ANTHROPIC_AUTH_TOKEN="your_zai_api_key_here"
$env:ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic"
$env:API_TIMEOUT_MS="3000000"
```

**Permanent (System Properties):**
1. Open System Properties → Environment Variables
2. Add the variables listed above under User or System variables

## Docker Configuration

If running Sleepless Agent in Docker, add the Z.ai configuration to your `.env` file:

```bash
# Z.ai Configuration (add these to .env)
ANTHROPIC_AUTH_TOKEN=your_zai_api_key_here
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
API_TIMEOUT_MS=3000000
```

Then update `docker-compose.yml` to pass these variables:

```yaml
version: '3.8'

services:
  sleepless-agent:
    image: sleepless-agent:latest
    env_file:
      - .env
    environment:
      - ANTHROPIC_AUTH_TOKEN=${ANTHROPIC_AUTH_TOKEN}
      - ANTHROPIC_BASE_URL=${ANTHROPIC_BASE_URL}
      - API_TIMEOUT_MS=${API_TIMEOUT_MS}
      # ... other environment variables
```

## Advanced Configuration

### Using Claude Code Env (CCE) Tool

The [Claude Code Env tool](https://github.com/vainjs/claude-code-env) allows you to manage multiple API configurations and switch between them easily:

```bash
# Install CCE globally
npm install -g @vainjs/claude-code-env
# or
pnpm add -g @vainjs/claude-code-env

# Add a Z.ai configuration
cce add

# Follow the prompts to enter:
# - Name: z-ai-glm46
# - ANTHROPIC_AUTH_TOKEN: your_zai_api_key
# - ANTHROPIC_BASE_URL: https://api.z.ai/api/anthropic
# - Model: GLM-4.6

# List available configurations
cce list

# Switch to Z.ai configuration
cce use z-ai-glm46

# Switch back to standard Claude
cce use claude-sonnet
```

### Model Selection Strategy

Choose the appropriate GLM model based on your needs:

| GLM Model | Claude Equivalent | Best For | Speed | Cost |
|-----------|-------------------|----------|-------|------|
| GLM-4.5-Air | Claude Haiku | Quick tasks, fast responses | ⚡⚡⚡ | 💰 |
| GLM-4.6 | Claude Sonnet | Balanced tasks, default choice | ⚡⚡ | 💰💰 |
| GLM-4.6 | Claude Opus | Complex reasoning, detailed work | ⚡ | 💰💰💰 |

Update `config.yaml` to specify which model to use:

```yaml
claude_code:
  model: claude-sonnet-4-5-20250929  # Maps to GLM-4.6
  # Change to claude-haiku-* for GLM-4.5-Air
  # Change to claude-opus-* for GLM-4.6 (high quality)
```

## Verification

### Test Claude Code Connection

Verify that Claude Code is correctly configured with Z.ai:

```bash
# Test claude command
claude --version

# Test a simple query
claude "What is 2+2?"

# If successful, you should see a response from the GLM model
```

### Test Sleepless Agent

```bash
# Check daemon status
sle check

# Submit a test thought
sle think "Test Z.ai integration"

# Monitor logs for any errors
tail -f workspace/data/agent.log
```

## Troubleshooting

### Issue: "Authentication failed"

**Solution:**
1. Verify your Z.ai API key is correct
2. Check that `ANTHROPIC_AUTH_TOKEN` is set properly
3. Ensure your Z.ai account has sufficient credits

```bash
# Check environment variable
echo $ANTHROPIC_AUTH_TOKEN

# Re-export if needed
export ANTHROPIC_AUTH_TOKEN="your_correct_api_key"
```

### Issue: "Connection timeout"

**Solution:**
1. Verify `ANTHROPIC_BASE_URL` is set to `https://api.z.ai/api/anthropic`
2. Increase timeout value in settings
3. Check your internet connection

```bash
# Verify base URL
echo $ANTHROPIC_BASE_URL

# Test connectivity
curl -I https://api.z.ai/api/anthropic
```

### Issue: "Model not found"

**Solution:**
1. Ensure you're using the correct GLM model names
2. Check Z.ai documentation for available models
3. Update model mappings in `~/.claude/settings.json`

```bash
# List available models (from Z.ai dashboard)
# Update settings.json with correct model names
```

### Issue: "Usage check errors"

**Solution:**
Make sure `skip_usage_check` is enabled in `config.yaml`:

```yaml
claude_code:
  skip_usage_check: true  # REQUIRED for Z.ai
```

## Migration from Claude Code Pro

If you're migrating from Claude Code Pro to Z.ai:

1. **Backup existing configuration:**
   ```bash
   cp ~/.claude/settings.json ~/.claude/settings.json.backup
   ```

2. **Update configuration** using steps above

3. **Test thoroughly** before committing to production

4. **Monitor costs** - pricing structure may differ

5. **Update documentation** to reflect Z.ai usage

## Security Best Practices

### Protect Your API Key

1. **Never commit API keys to Git:**
   ```bash
   # Add to .gitignore
   echo ".env" >> .gitignore
   echo "config.yaml" >> .gitignore
   ```

2. **Use environment variables:**
   - Store keys in environment variables, not in code
   - Use `.env` files for local development
   - Use secrets management for production

3. **Rotate keys periodically:**
   - Generate new API keys every 90 days
   - Revoke old keys immediately after rotation
   - Update all deployments with new keys

4. **Set restrictive file permissions:**
   ```bash
   chmod 600 ~/.claude/settings.json
   chmod 600 .env
   ```

## Cost Management

### Monitor Usage

1. **Check Z.ai dashboard** regularly for usage metrics
2. **Set up billing alerts** in your Z.ai account
3. **Monitor task completion rates** to optimize costs

### Optimize Costs

```yaml
# Adjust multi-agent workflow to reduce API calls
multi_agent_workflow:
  planner:
    enabled: true
    max_turns: 3  # Reduce from default to save costs
  worker:
    enabled: true
    max_turns: 10  # Adjust based on needs
  evaluator:
    enabled: true
    max_turns: 3
```

### Cost Comparison

| Provider | Pricing Model | Daily Limits | Best For |
|----------|---------------|--------------|----------|
| Claude Code Pro | Subscription (~$20/month) | Yes (usage caps) | Individual developers |
| Z.ai | Pay-per-use / Subscription | No daily caps | Teams, heavy usage |

## Additional Resources

- **[Z.ai Documentation](https://docs.z.ai/)** - Official Z.ai docs
- **[Z.ai Developer Platform](https://open.bigmodel.cn/)** - Create and manage API keys
- **[Claude Code Guide](https://github.com/jezweb/how-to-claude-code)** - General Claude Code documentation
- **[Environment Variables Reference](environment-setup.md)** - Complete environment variable guide

## Getting Help

If you encounter issues:

1. **Check Z.ai Status**: [Z.ai Status Page](https://status.z.ai) (if available)
2. **Review Logs**: `tail -f workspace/data/agent.log`
3. **Community Support**: [Discord](https://discord.gg/74my3Wkn)
4. **GitHub Issues**: [Report issues](https://github.com/context-machine-lab/sleepless-agent/issues)

## Next Steps

After configuring Z.ai:

- [Configure Git Integration](git-integration.md)
- [Set up Slack Bot](slack-setup.md)
- [Configure Web UI](web-ui.md)
- [Deploy to Production](../installation.md#deployment)

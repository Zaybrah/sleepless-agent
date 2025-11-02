# Z.ai Quick Reference

**TL;DR**: Quick setup guide for using Z.ai with Sleepless Agent instead of Claude Code Pro.

## 🚀 5-Minute Setup

### 1. Get API Key
- Sign up at [Z.ai Open Platform](https://open.bigmodel.cn/)
- Create an API key from your dashboard
- Copy the key (starts with your Z.ai credentials)

### 2. Configure Environment

**Option A: Automatic (Recommended)**
```bash
curl -O "https://cdn.bigmodel.cn/install/claude_code_zai_env.sh"
bash ./claude_code_zai_env.sh
```

**Option B: Manual**

Edit `~/.claude/settings.json`:
```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "YOUR_ZAI_API_KEY",
    "ANTHROPIC_BASE_URL": "https://api.z.ai/api/anthropic",
    "API_TIMEOUT_MS": "3000000",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "GLM-4.6"
  }
}
```

### 3. Update Sleepless Agent Config

Edit `config.yaml`:
```yaml
claude_code:
  skip_usage_check: true  # REQUIRED for Z.ai
```

### 4. Test

```bash
# Test Claude Code
claude "Hello, test Z.ai"

# Start Sleepless Agent
sle daemon
```

## 📋 Environment Variables

| Variable | Value | Required |
|----------|-------|----------|
| `ANTHROPIC_AUTH_TOKEN` | Your Z.ai API key | ✅ Yes |
| `ANTHROPIC_BASE_URL` | `https://api.z.ai/api/anthropic` | ✅ Yes |
| `API_TIMEOUT_MS` | `3000000` | ⚠️ Recommended |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | `GLM-4.6` | ⚪ Optional |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | `GLM-4.5-Air` | ⚪ Optional |

## 🎯 GLM Model Selection

| GLM Model | Use Case | Speed | Cost |
|-----------|----------|-------|------|
| GLM-4.5-Air | Quick tasks, fast responses | ⚡⚡⚡ | 💰 |
| GLM-4.6 | Default, balanced performance | ⚡⚡ | 💰💰 |

## 🔧 Config Locations

**Priority Order (highest to lowest):**
1. System environment variables (`export ANTHROPIC_AUTH_TOKEN=...`)
2. `.env` file in project root
3. `~/.claude/settings.json`
4. Sleepless Agent `config.yaml`

## ✅ Verification Checklist

- [ ] Z.ai API key obtained
- [ ] `~/.claude/settings.json` configured OR environment variables set
- [ ] `config.yaml` has `skip_usage_check: true`
- [ ] `claude "test"` works without errors
- [ ] `sle daemon` starts successfully
- [ ] First task completes successfully

## 🚨 Common Issues

### Authentication Failed
```bash
# Check your API key
echo $ANTHROPIC_AUTH_TOKEN

# Verify in settings file
cat ~/.claude/settings.json
```

### Usage Check Errors
```yaml
# Make sure this is set in config.yaml
claude_code:
  skip_usage_check: true  # Must be true for Z.ai
```

### Connection Timeout
```bash
# Test connectivity
curl -I https://api.z.ai/api/anthropic

# Increase timeout in settings.json
"API_TIMEOUT_MS": "3000000"
```

## 📚 Full Documentation

For complete setup instructions, troubleshooting, and advanced configuration:
- **[Complete Z.ai Guide](guides/z-ai-setup.md)** - Full setup guide
- **[Environment Setup](guides/environment-setup.md)** - All environment variables
- **[FAQ](faq.md)** - Common questions about Z.ai and alternative providers

## 💡 Key Differences from Claude Code Pro

| Feature | Claude Code Pro | Z.ai |
|---------|-----------------|------|
| Daily Usage Caps | Yes (limits enforced) | No (based on plan) |
| Models | Claude Haiku/Sonnet/Opus | GLM-4.5-Air, GLM-4.6 |
| Usage Monitoring | Required | Disabled (`skip_usage_check: true`) |
| API Key Location | N/A (uses login) | Environment variable |
| Base URL | Default Anthropic | `https://api.z.ai/api/anthropic` |

## 🔐 Security Reminder

```bash
# Never commit these files
echo ".env" >> .gitignore
echo "config.yaml" >> .gitignore

# Set proper permissions
chmod 600 ~/.claude/settings.json
chmod 600 .env
```

## 🆘 Getting Help

- **Documentation**: [guides/z-ai-setup.md](guides/z-ai-setup.md)
- **Discord**: [Join our community](https://discord.gg/74my3Wkn)
- **Issues**: [GitHub Issues](https://github.com/context-machine-lab/sleepless-agent/issues)
- **Z.ai Docs**: [Z.ai Documentation](https://docs.z.ai/)

---

**Next Steps**: [Configure Slack Integration](guides/slack-setup.md) | [Set up Git](guides/git-integration.md)

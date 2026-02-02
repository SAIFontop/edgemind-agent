# EdgeMind Agent Usage Guide

This guide provides detailed examples and use cases for EdgeMind Agent.

## Table of Contents

1. [Quick Start](#quick-start)
2. [System Analysis](#system-analysis)
3. [Action Planning](#action-planning)
4. [Command Validation](#command-validation)
5. [Advanced Usage](#advanced-usage)
6. [Configuration](#configuration)
7. [Security Best Practices](#security-best-practices)

## Quick Start

### Installation

```bash
# Clone and install
git clone https://github.com/SAIFontop/edgemind-agent.git
cd edgemind-agent
pip install -e .

# Set up your Gemini API key
export GEMINI_API_KEY="your_api_key_here"
```

### First Analysis

```bash
# Check agent status
edgemind-agent status

# Analyze your system
edgemind-agent analyze

# Analyze with AI insights
edgemind-agent analyze --ai
```

## System Analysis

### Basic Analysis

Collect system context without AI:

```bash
edgemind-agent analyze
```

This will collect:
- System information (OS, hostname, CPU, memory)
- Load averages
- Service status
- Recent system logs
- Command execution history

### AI-Powered Analysis

Get AI insights and recommendations:

```bash
edgemind-agent analyze --ai
```

Output includes:
- System health summary
- Identified issues with severity levels
- Recommendations for remediation

### Save Analysis Results

```bash
# Save context and analysis to files
edgemind-agent analyze --ai -o /tmp/system_context.json
```

This creates:
- `system_context.json` - Raw system context
- `system_context_analysis.json` - AI analysis results

### Custom Log Sources

```bash
# Analyze specific log files
edgemind-agent analyze --ai \
  --logs /var/log/syslog,/var/log/auth.log,/var/log/nginx/error.log
```

### Monitor Specific Services

```bash
# Check specific services
edgemind-agent analyze --ai \
  --services ssh,nginx,postgresql,redis
```

## Action Planning

### Create Action Plan

Generate an AI-powered action plan:

```bash
edgemind-agent plan --ai
```

The plan includes:
- Step-by-step actions
- Exact commands to run
- Risk assessment
- Reasoning for each step
- Verification methods

### Review Plan Before Execution

```bash
# Save plan for review
edgemind-agent plan --ai -o /tmp/action_plan.json
```

### Execute Action Plan

**Warning**: Always review the plan before executing!

```bash
# Create and execute plan (requires confirmation for high-risk actions)
edgemind-agent plan --ai --execute
```

## Command Validation

### Validate Single Command

```bash
# Check if a command is allowed
edgemind-agent validate "systemctl status ssh"
```

Output:
```
============================================================
COMMAND VALIDATION
============================================================
Command: systemctl status ssh
Allowed: True
Risk Level: LOW
Reason: Command passed security validation
============================================================
```

### Test Forbidden Commands

```bash
# This will be blocked
edgemind-agent validate "rm -rf /"
```

Output:
```
============================================================
COMMAND VALIDATION
============================================================
Command: rm -rf /
Allowed: False
Risk Level: FORBIDDEN
Reason: Command matches forbidden pattern: ...
============================================================
```

## Advanced Usage

### Verbose Logging

```bash
# Enable debug logging
edgemind-agent -v analyze --ai
```

### Custom API Key

```bash
# Use specific API key
edgemind-agent --api-key "your_key" analyze --ai
```

### Combining Options

```bash
# Full featured analysis
edgemind-agent -v analyze --ai \
  --logs /var/log/syslog,/var/log/auth.log \
  --services ssh,nginx,postgresql \
  -o /tmp/detailed_analysis.json
```

## Configuration

### Environment Variables

Create a `.env` file:

```bash
# Copy example
cp .env.example .env

# Edit with your settings
nano .env
```

Example `.env`:

```bash
GEMINI_API_KEY=your_api_key_here
LOG_LEVEL=INFO
STRICT_MODE=true
DRY_RUN=false
```

### Using Configuration

```bash
# Load from .env file
export $(cat .env | xargs)
edgemind-agent analyze --ai
```

## Security Best Practices

### 1. Always Review Plans

Never execute plans without reviewing them first:

```bash
# Step 1: Create and save plan
edgemind-agent plan --ai -o plan.json

# Step 2: Review plan.json manually

# Step 3: Execute only if safe
edgemind-agent plan --ai --execute
```

### 2. Use Dry Run for Testing

Test commands in dry-run mode (modify code to enable):

```python
from edgemind_agent.execution.gateway import SafeExecutionGateway

gateway = SafeExecutionGateway(dry_run=True)
# Commands will be validated but not executed
```

### 3. Monitor Execution History

```python
from edgemind_agent.execution.gateway import SafeExecutionGateway

gateway = SafeExecutionGateway()
# ... execute commands ...

# Review what was executed
history = gateway.get_execution_history()
stats = gateway.get_statistics()
```

### 4. Whitelist Only Trusted Commands

The security policy uses a strict whitelist by default. Only add commands you trust:

```python
from edgemind_agent.security.policy import SecurityPolicy

policy = SecurityPolicy(strict_mode=True)
# Only whitelisted commands are allowed
```

### 5. Regular Security Audits

```bash
# Check agent status regularly
edgemind-agent status

# Review execution statistics
# Check whitelisted commands count
# Monitor for blocked attempts
```

## Example Workflows

### Workflow 1: System Health Check

```bash
# Daily health check
edgemind-agent analyze --ai -o /var/log/edgemind/daily_check.json

# Review for issues
# Address critical issues manually or with AI guidance
```

### Workflow 2: Service Troubleshooting

```bash
# Analyze specific service
edgemind-agent analyze --ai \
  --services nginx \
  --logs /var/log/nginx/error.log,/var/log/nginx/access.log

# Create remediation plan
edgemind-agent plan --ai
```

### Workflow 3: Security Audit

```bash
# Check authentication logs
edgemind-agent analyze --ai \
  --logs /var/log/auth.log,/var/log/secure \
  --services ssh,fail2ban
```

## Programmatic Usage

### Python API

```python
from edgemind_agent import SystemContextCollector, SecurityPolicy, SafeExecutionGateway
from edgemind_agent.ai.gemini_client import GeminiAIBrain

# Collect system context
collector = SystemContextCollector()
context = collector.collect_all()

# Analyze with AI
ai = GeminiAIBrain(api_key="your_key")
analysis = ai.analyze_system_state(context)

# Create action plan
plan = ai.plan_actions(analysis, context)

# Validate plan
policy = SecurityPolicy(strict_mode=True)
validation = policy.validate_action_plan(plan['plan'])

# Execute if safe
if validation['valid']:
    gateway = SafeExecutionGateway(dry_run=False)
    result = gateway.execute_plan(validation, require_approval=True)
```

## Troubleshooting

### API Key Issues

```bash
# Verify API key is set
echo $GEMINI_API_KEY

# Test with explicit key
edgemind-agent --api-key "your_key" analyze --ai
```

### Permission Issues

```bash
# Some logs require sudo
sudo edgemind-agent analyze --logs /var/log/auth.log
```

### Import Errors

```bash
# Reinstall package
pip install -e . --force-reinstall
```

## Getting Help

```bash
# General help
edgemind-agent --help

# Command-specific help
edgemind-agent analyze --help
edgemind-agent plan --help
edgemind-agent validate --help
```

## Support

For issues or questions:
- GitHub Issues: https://github.com/SAIFontop/edgemind-agent/issues
- Documentation: https://github.com/SAIFontop/edgemind-agent/blob/main/README.md

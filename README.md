# EdgeMind Agent

EdgeMind Agent is a production-ready AI system agent for Raspberry Pi OS that operates as an intelligent decision layer above the operating system. It analyzes system state, diagnoses issues, and plans safe actions using an external Gemini API, while enforcing strict security policies to prevent destructive operations.

## Features

- **CLI-based Interface**: Easy-to-use command-line interface for system analysis and management
- **Context Builder**: Collects comprehensive system state including:
  - System information (platform, CPU, memory, load)
  - System logs from multiple sources
  - Service status (systemd/init services)
  - Command execution history and errors
- **AI Brain Integration**: Uses Google Gemini API for:
  - System state analysis
  - Issue detection and severity assessment
  - Action planning with safety considerations
  - **Note**: AI provides analysis and planning only - it NEVER executes commands directly
- **Strict Security Layer**: 
  - Command whitelist validation
  - Forbidden command/pattern detection
  - Risk level assessment (LOW, MEDIUM, HIGH, CRITICAL, FORBIDDEN)
  - Action plan validation
- **Safe Execution Gateway**:
  - Only executes whitelisted commands
  - Dry-run mode for testing
  - Execution history and audit trail
  - Timeout protection
  - User approval for high-risk operations

## Installation

### Prerequisites

- Python 3.8 or higher
- Raspberry Pi OS (or any Linux distribution)
- Gemini API key (get one from [Google AI Studio](https://makersuite.google.com/app/apikey))

### Install from source

```bash
# Clone the repository
git clone https://github.com/SAIFontop/edgemind-agent.git
cd edgemind-agent

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Configuration

Set up your Gemini API key:

```bash
# Option 1: Environment variable
export GEMINI_API_KEY="your_api_key_here"

# Option 2: Create .env file
cp .env.example .env
# Edit .env and add your API key
```

## Usage

### Basic Commands

#### Analyze System State

Collect and analyze system state without AI:

```bash
edgemind-agent analyze
```

With AI analysis:

```bash
edgemind-agent analyze --ai
```

Save context to file:

```bash
edgemind-agent analyze --ai -o context.json
```

#### Create Action Plan

Create an AI-generated action plan:

```bash
edgemind-agent plan --ai
```

Create and execute the plan (with approval for high-risk commands):

```bash
edgemind-agent plan --ai --execute
```

#### Validate Commands

Check if a command is allowed by the security policy:

```bash
edgemind-agent validate "systemctl status ssh"
edgemind-agent validate "rm -rf /"  # This will be blocked
```

#### Check Agent Status

```bash
edgemind-agent status
```

### Advanced Usage

#### Custom Log Sources and Services

```bash
edgemind-agent analyze --ai \
  --logs /var/log/syslog,/var/log/auth.log \
  --services ssh,nginx,postgresql
```

#### Verbose Logging

```bash
edgemind-agent -v analyze --ai
```

## Architecture

EdgeMind Agent follows a strict separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                     CLI Interface                        │
└─────────────────────────────────────────────────────────┘
                           │
    ┌──────────────────────┼──────────────────────┐
    │                      │                      │
    ▼                      ▼                      ▼
┌─────────┐          ┌──────────┐         ┌──────────────┐
│ Context │          │ AI Brain │         │  Security    │
│ Builder │─────────▶│ (Gemini) │────────▶│  Policy      │
└─────────┘          └──────────┘         └──────────────┘
    │                                              │
    │                                              ▼
    │                                      ┌──────────────┐
    └─────────────────────────────────────▶│  Execution   │
                                            │  Gateway     │
                                            └──────────────┘
                                                   │
                                                   ▼
                                            System Commands
                                           (Whitelisted Only)
```

### Components

1. **Context Collector** (`edgemind_agent/context/collector.py`):
   - Gathers system state, logs, service status
   - Tracks command execution history
   - Provides context summary

2. **AI Brain** (`edgemind_agent/ai/gemini_client.py`):
   - Analyzes system state using Gemini API
   - Identifies issues and severity levels
   - Creates action plans
   - **Does NOT execute commands**

3. **Security Policy** (`edgemind_agent/security/policy.py`):
   - Validates all commands against whitelist
   - Blocks forbidden commands and patterns
   - Assesses risk levels
   - Validates entire action plans

4. **Execution Gateway** (`edgemind_agent/execution/gateway.py`):
   - Executes only validated commands
   - Supports dry-run mode
   - Maintains execution audit trail
   - Enforces timeouts

5. **CLI Interface** (`edgemind_agent/cli/main.py`):
   - User-friendly command-line interface
   - Orchestrates all components
   - Handles user interactions

## Security

EdgeMind Agent implements multiple layers of security:

### Command Whitelist

Only safe, diagnostic commands are whitelisted by default:
- System info: `uname`, `hostname`, `uptime`, `free`, `df`, `ps`, etc.
- Networking: `ping`, `netstat`, `ss`, `ip`, `ifconfig`
- Logs: `journalctl`, `dmesg`, `tail`, `head`, `cat`
- Services: `systemctl status`, `service status`

### Forbidden Commands

Destructive operations are explicitly forbidden:
- File deletion: `rm -rf`, `shred`
- Disk operations: `dd`, `mkfs`, `fdisk`
- System control: `shutdown`, `reboot`, `halt`
- Network disruption: `iptables -F`, `ifconfig down`

### Risk Assessment

All commands are assessed for risk:
- **LOW**: Read-only operations (`ls`, `cat`, `ps`)
- **MEDIUM**: Network/process management (`ping`, `kill`)
- **HIGH**: Commands requiring approval
- **CRITICAL**: High-impact operations
- **FORBIDDEN**: Never allowed

### AI Isolation

The AI brain:
- ✅ Analyzes system state
- ✅ Identifies issues
- ✅ Plans actions
- ❌ **NEVER executes commands directly**
- ❌ **NEVER bypasses security layer**

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests (once implemented)
pytest tests/ -v
```

### Code Style

```bash
# Format code
black edgemind_agent/

# Lint code
flake8 edgemind_agent/
```

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Acknowledgments

- Built with [Google Gemini API](https://ai.google.dev/)
- Designed for Raspberry Pi OS and Linux systems

## Support

For issues, questions, or contributions, please visit:
https://github.com/SAIFontop/edgemind-agent/issues

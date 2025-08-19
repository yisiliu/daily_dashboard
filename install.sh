#!/bin/bash

# Get the absolute path to the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DASHBOARD_SCRIPT="$SCRIPT_DIR/dashboard.py"

echo "🚀 Installing Daily Dashboard..."
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r "$SCRIPT_DIR/requirements.txt" --quiet

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies. Please check requirements.txt"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "📝 Creating .env file from template..."
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
    echo "   ⚠️  Please edit .env file to add your API keys and preferences"
    echo "   Run: nano $SCRIPT_DIR/.env"
    echo ""
fi

# Detect shell and configure
echo "🔧 Configuring terminal auto-start..."

# Detect which shell configuration files exist
SHELL_CONFIGS=()
if [ -f "$HOME/.zshrc" ]; then
    SHELL_CONFIGS+=("$HOME/.zshrc")
fi
if [ -f "$HOME/.bashrc" ]; then
    SHELL_CONFIGS+=("$HOME/.bashrc")
fi
if [ -f "$HOME/.bash_profile" ]; then
    SHELL_CONFIGS+=("$HOME/.bash_profile")
fi

if [ ${#SHELL_CONFIGS[@]} -eq 0 ]; then
    echo "❌ No shell configuration file found (.zshrc, .bashrc, or .bash_profile)"
    echo "   Please manually add this line to your shell config:"
    echo "   python3 '$DASHBOARD_SCRIPT'"
    exit 1
fi

# Add dashboard to shell configs
DASHBOARD_LINE="# Daily Dashboard - Show dashboard on terminal startup
python3 '$DASHBOARD_SCRIPT' 2>/dev/null"

CONFIGURED_COUNT=0
for CONFIG_FILE in "${SHELL_CONFIGS[@]}"; do
    # Check if already configured
    if grep -q "Daily Dashboard" "$CONFIG_FILE" 2>/dev/null; then
        echo "   ✓ Already configured in $CONFIG_FILE"
    else
        # Backup the original file
        cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
        
        # Add dashboard call to shell config
        echo "" >> "$CONFIG_FILE"
        echo "$DASHBOARD_LINE" >> "$CONFIG_FILE"
        echo "   ✓ Added to $CONFIG_FILE"
        CONFIGURED_COUNT=$((CONFIGURED_COUNT + 1))
    fi
done

echo ""
echo "✅ Installation complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Edit your configuration: nano $SCRIPT_DIR/.env"
echo "   2. Test manually: python3 $DASHBOARD_SCRIPT"
echo "   3. Restart terminal to see dashboard on startup"
echo ""
echo "🛠️  Useful commands:"
echo "   python3 $DASHBOARD_SCRIPT           # Run normally (once per day)"
echo "   python3 $DASHBOARD_SCRIPT --debug   # Debug mode (always runs, shows logs)"
echo "   python3 $DASHBOARD_SCRIPT --force   # Force run (ignores daily limit)"
echo ""
echo "🚪 To uninstall:"
echo "   Remove the '# Daily Dashboard' lines from:"
for CONFIG_FILE in "${SHELL_CONFIGS[@]}"; do
    echo "   - $CONFIG_FILE"
done
#!/usr/bin/env bash
# YURO ONE-CLICK LINUX/MACOS INSTALLER
set -euo pipefail

INSTALL_DIR="${HOME}/.local/bin"
CONFIG_DIR="${HOME}/.gemini/config"

echo "============================================================"
echo "              YURO TOOLCHAIN INSTALLER (UNIX)               "
echo "============================================================"

mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR/rules"
mkdir -p "$CONFIG_DIR/skills"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[1/4] Installing CLI tools and shims to $INSTALL_DIR..."
if [ -f "$SCRIPT_DIR/cmd/token-tracker.js" ]; then
    cp "$SCRIPT_DIR/cmd/token-tracker.js" "$INSTALL_DIR/token-tracker.js"
fi

# Create shell wrapper shims
cat << 'EOF' > "$INSTALL_DIR/token-tracker"
#!/usr/bin/env bash
exec node "$HOME/.local/bin/token-tracker.js" "$@"
EOF

cat << 'EOF' > "$INSTALL_DIR/token-scan"
#!/usr/bin/env bash
exec node "$HOME/.local/bin/token-tracker.js" scan "$@"
EOF

cat << 'EOF' > "$INSTALL_DIR/token-audit"
#!/usr/bin/env bash
exec node "$HOME/.local/bin/token-tracker.js" audit "$@"
EOF

cat << 'EOF' > "$INSTALL_DIR/rg-mini"
#!/usr/bin/env bash
exec rg --max-count 20 "$@"
EOF

cat << 'EOF' > "$INSTALL_DIR/fd-mini"
#!/usr/bin/env bash
exec fd --max-results 20 "$@"
EOF

chmod +x "$INSTALL_DIR/token-tracker" "$INSTALL_DIR/token-scan" "$INSTALL_DIR/token-audit" "$INSTALL_DIR/rg-mini" "$INSTALL_DIR/fd-mini"

# Synchronize rules and skills
echo "[2/4] Synchronizing rules and skills to $CONFIG_DIR..."
if [ -d "$SCRIPT_DIR/rules" ]; then
    cp -r "$SCRIPT_DIR/rules/"* "$CONFIG_DIR/rules/"
fi
if [ -d "$SCRIPT_DIR/skills" ]; then
    cp -r "$SCRIPT_DIR/skills/"* "$CONFIG_DIR/skills/"
fi

# Download codebase-memory-mcp if missing
echo "[3/4] Checking codebase-memory-mcp binary..."
if ! command -v codebase-memory-mcp &> /dev/null; then
    OS="$(uname -s)"
    ARCH="$(uname -m)"
    echo "Downloading binary for $OS ($ARCH)..."
    if [ "$OS" = "Darwin" ]; then
        URL="https://github.com/DeusData/codebase-memory-mcp/releases/download/v0.11.0/codebase-memory-mcp-darwin-arm64.tar.gz"
    else
        URL="https://github.com/DeusData/codebase-memory-mcp/releases/download/v0.11.0/codebase-memory-mcp-linux-amd64-portable.tar.gz"
    fi
    curl -sSL "$URL" | tar -xz -C "$INSTALL_DIR" || echo "Warning: Please manually install codebase-memory-mcp."
fi

# PATH Check
echo "[4/4] Checking PATH..."
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo "Note: Please add $INSTALL_DIR to your PATH by adding this to ~/.bashrc or ~/.zshrc:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo "============================================================"
echo "              YURO SETUP COMPLETED SUCCESSFULLY!            "
echo "============================================================"

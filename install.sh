#!/usr/bin/env bash
# YURO TOOLCHAIN INSTALLER (LINUX / MACOS)
# Installs portable core engines: cbm, token-tracker, token-audit, token-scan, rg-mini, fd-mini, and token-save.
set -euo pipefail

INSTALL_DIR="${HOME}/.local/bin"
CONFIG_DIR="${HOME}/.gemini/config"

echo "============================================================"
echo "          YURO TOOLCHAIN INSTALLER (PORTABLE CORE)          "
echo "============================================================"

mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR/rules"
mkdir -p "$CONFIG_DIR/skills"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[1/4] Installing CLI tools and shims to $INSTALL_DIR..."

# Copy JavaScript engine
if [ -f "$SCRIPT_DIR/cmd/token-tracker.js" ]; then
    cp "$SCRIPT_DIR/cmd/token-tracker.js" "$INSTALL_DIR/token-tracker.js"
fi

# 1. token-tracker shims
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

# 2. Bounded search shims (requires ripgrep and fd installed on host)
cat << 'EOF' > "$INSTALL_DIR/rg-mini"
#!/usr/bin/env bash
if ! command -v rg &> /dev/null; then
    echo "Error: ripgrep ('rg') is not installed. Please install it via your package manager." >&2
    exit 1
fi
exec rg --max-count 20 "$@"
EOF

cat << 'EOF' > "$INSTALL_DIR/fd-mini"
#!/usr/bin/env bash
FD_CMD="fd"
if ! command -v fd &> /dev/null; then
    if command -v fdfind &> /dev/null; then
        FD_CMD="fdfind"
    else
        echo "Error: fd ('fd' or 'fdfind') is not installed. Please install it via your package manager." >&2
        exit 1
    fi
fi
exec "$FD_CMD" --max-results 20 "$@"
EOF

# 3. Codebase Memory (cbm) shim
cat << 'EOF' > "$INSTALL_DIR/cbm"
#!/usr/bin/env bash
CBM_BIN="$HOME/.local/bin/codebase-memory-mcp"
if [ ! -f "$CBM_BIN" ]; then
    echo "Error: codebase-memory-mcp binary not found at $CBM_BIN." >&2
    exit 1
fi
exec "$CBM_BIN" "$@"
EOF

cat << 'EOF' > "$INSTALL_DIR/cbm-mini"
#!/usr/bin/env bash
exec "$HOME/.local/bin/cbm" "$@"
EOF

chmod +x "$INSTALL_DIR/token-tracker" \
         "$INSTALL_DIR/token-scan" \
         "$INSTALL_DIR/token-audit" \
         "$INSTALL_DIR/rg-mini" \
         "$INSTALL_DIR/fd-mini" \
         "$INSTALL_DIR/cbm" \
         "$INSTALL_DIR/cbm-mini"

# Synchronize rules and skills
echo "[2/4] Synchronizing rules and skills to $CONFIG_DIR..."
if [ -d "$SCRIPT_DIR/rules" ]; then
    cp -r "$SCRIPT_DIR/rules/"* "$CONFIG_DIR/rules/"
fi
if [ -d "$SCRIPT_DIR/skills" ]; then
    cp -r "$SCRIPT_DIR/skills/"* "$CONFIG_DIR/skills/"
fi

# Download codebase-memory-mcp binary if missing
echo "[3/4] Checking codebase-memory-mcp binary..."
if [ ! -f "$INSTALL_DIR/codebase-memory-mcp" ]; then
    OS="$(uname -s)"
    ARCH="$(uname -m)"
    echo "Downloading binary for $OS ($ARCH)..."
    if [ "$OS" = "Darwin" ]; then
        URL="https://github.com/DeusData/codebase-memory-mcp/releases/download/v0.11.0/codebase-memory-mcp-darwin-arm64.tar.gz"
    else
        URL="https://github.com/DeusData/codebase-memory-mcp/releases/download/v0.11.0/codebase-memory-mcp-linux-amd64-portable.tar.gz"
    fi
    curl -sSL "$URL" | tar -xz -C "$INSTALL_DIR" || echo "Warning: Could not automatically download codebase-memory-mcp. Please install manually."
    if [ -f "$INSTALL_DIR/codebase-memory-mcp" ]; then
        chmod +x "$INSTALL_DIR/codebase-memory-mcp"
    fi
fi

# PATH Check
echo "[4/4] Checking PATH..."
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo "Note: Please add $INSTALL_DIR to your PATH in ~/.bashrc or ~/.zshrc:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo "============================================================"
echo "          YURO PORTABLE SETUP COMPLETED SUCCESSFULLY!       "
echo "============================================================"

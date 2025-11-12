#!/bin/bash
# VS Code Remote Server Launch Script
# Simple alternative to Ansible playbook for quick setup

set -e

VSCODE_PORT="${VSCODE_PORT:-8443}"
VSCODE_DATA_DIR="${VSCODE_DATA_DIR:-$HOME/.local/share/code-server}"
VSCODE_CONFIG_DIR="${VSCODE_CONFIG_DIR:-$HOME/.config/code-server}"
VSCODE_PASSWORD="${VSCODE_PASSWORD:-changeme123}"

echo "========================================="
echo "VS Code Remote Server Setup"
echo "========================================="

# Create directories
echo "[1/5] Creating directories..."
mkdir -p "$VSCODE_DATA_DIR"
mkdir -p "$VSCODE_CONFIG_DIR"

# Install code-server if not present
if ! command -v code-server &> /dev/null; then
    echo "[2/5] Installing code-server..."
    curl -fsSL https://code-server.dev/install.sh | sh
else
    echo "[2/5] code-server already installed, skipping..."
fi

# Create config
echo "[3/5] Creating configuration..."
cat > "$VSCODE_CONFIG_DIR/config.yaml" <<EOF
bind-addr: 0.0.0.0:$VSCODE_PORT
auth: password
password: $VSCODE_PASSWORD
cert: false
user-data-dir: $VSCODE_DATA_DIR
EOF

# Install essential extensions
echo "[4/5] Installing VS Code extensions..."
code-server --install-extension ms-python.python || true
code-server --install-extension ms-toolsai.jupyter || true
code-server --install-extension ms-vscode.cpptools || true
code-server --install-extension golang.go || true
code-server --install-extension rust-lang.rust-analyzer || true

# Start server
echo "[5/5] Starting VS Code Server..."
echo ""
echo "========================================="
echo "VS Code Server Configuration:"
echo "  Port: $VSCODE_PORT"
echo "  Password: $VSCODE_PASSWORD"
echo "  Data Dir: $VSCODE_DATA_DIR"
echo "  Access URL: http://localhost:$VSCODE_PORT"
echo "========================================="
echo ""

# Function to start server
start_vscode_server() {
    local port="${1:-$VSCODE_PORT}"
    code-server --bind-addr "0.0.0.0:$port" --user-data-dir "$VSCODE_DATA_DIR"
}

# Export function for use by other scripts
export -f start_vscode_server

# If script is executed directly (not sourced), start the server
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    start_vscode_server "$VSCODE_PORT"
fi

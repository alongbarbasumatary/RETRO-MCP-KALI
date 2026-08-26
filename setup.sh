#!/bin/bash
# RETRO MCP KALI – Setup Script
# Downloads files from GitHub and installs

set -e

INSTALL_DIR="/opt/retro-mcp-kali"
BIN_DIR="/usr/local/bin"
LAUNCHER="$BIN_DIR/retro-mcp-kali"
REPO_RAW="https://raw.githubusercontent.com/alongbarbasumatary/RETRO-MCP-KALI/main"

echo "[*] Installing RETRO MCP KALI..."

# Create installation directory
mkdir -p "$INSTALL_DIR"

# Download required files from GitHub
echo "[*] Downloading files from GitHub..."
cd "$INSTALL_DIR"
curl -sSL -o backend_api.py "$REPO_RAW/backend_api.py"
curl -sSL -o server.py "$REPO_RAW/server.py"
curl -sSL -o requirements.txt "$REPO_RAW/requirements.txt"

# Install Python dependencies
echo "[*] Installing Python packages..."
pip3 install -r requirements.txt

# Create the launcher script
cat > "$LAUNCHER" << 'EOF'
#!/bin/bash
# RETRO MCP KALI – Launcher
INSTALL_DIR="/opt/retro-mcp-kali"
DEFAULT_API_IP="127.0.0.1"
DEFAULT_API_PORT="5000"
DEFAULT_MCP_HOST="127.0.0.1"
DEFAULT_MCP_PORT="8000"
DEBUG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --api-ip)   API_IP="$2"; shift 2 ;;
        --api-port) API_PORT="$2"; shift 2 ;;
        --mcp-host) MCP_HOST="$2"; shift 2 ;;
        --mcp-port) MCP_PORT="$2"; shift 2 ;;
        --debug)    DEBUG="--debug"; shift ;;
        -h|--help)
            echo "Usage: retro-mcp-kali [OPTIONS]"
            echo "Options:"
            echo "  --api-ip IP      Backend API bind IP (default: 127.0.0.1)"
            echo "  --api-port PORT  Backend API port (default: 5000)"
            echo "  --mcp-host HOST  MCP server bind host (default: 127.0.0.1)"
            echo "  --mcp-port PORT  MCP server port (default: 8000)"
            echo "  --debug          Enable debug logging"
            echo "  -h, --help       Show this help"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

API_IP="${API_IP:-$DEFAULT_API_IP}"
API_PORT="${API_PORT:-$DEFAULT_API_PORT}"
MCP_HOST="${MCP_HOST:-$DEFAULT_MCP_HOST}"
MCP_PORT="${MCP_PORT:-$DEFAULT_MCP_PORT}"

echo "[*] Starting RETRO MCP KALI..."
echo "  Backend API: http://$API_IP:$API_PORT"
echo "  MCP Server:  http://$MCP_HOST:$MCP_PORT/mcp"

cd "$INSTALL_DIR"
python3 backend_api.py --ip "$API_IP" --port "$API_PORT" $DEBUG &
BACKEND_PID=$!
sleep 2
python3 server.py --api "http://$API_IP:$API_PORT" --host "$MCP_HOST" --port "$MCP_PORT" $DEBUG
MCP_EXIT=$?
kill $BACKEND_PID 2>/dev/null || true
exit $MCP_EXIT
EOF

chmod +x "$LAUNCHER"

echo "[+] RETRO MCP KALI installed successfully!"
echo "    Run: retro-mcp-kali"
echo "    Options: retro-mcp-kali --help"

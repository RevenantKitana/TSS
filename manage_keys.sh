#!/usr/bin/env bash
# ==============================================================================
# ZeroTTS Studio - Key & Storage Management Tool (Bash CLI via SSH)
# ==============================================================================

set -e

# Resolve script directory
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# Detect Python interpreter
if [ -f "$DIR/.venv/bin/python" ]; then
    PY="$DIR/.venv/bin/python"
elif [ -f "/home/ubuntu/TSS/.venv/bin/python" ]; then
    PY="/home/ubuntu/TSS/.venv/bin/python"
elif command -v python3 &>/dev/null; then
    PY="python3"
else
    PY="python"
fi

# Execute Python CLI
exec "$PY" "$DIR/webui/manage_keys.py" "$@"

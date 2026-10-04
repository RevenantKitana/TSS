#!/usr/bin/env bash
# ==============================================================================
# ZeroTTS Production Deployment Wrapper
# Calls the comprehensive 1-click install.sh script.
# ==============================================================================

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$DIR/install.sh" ]; then
    exec bash "$DIR/install.sh" "$@"
else
    curl -sSL https://raw.githubusercontent.com/RevenantKitana/TSS/main/install.sh | bash
fi

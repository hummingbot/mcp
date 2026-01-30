#!/bin/bash
# Step 1: Detect operating system and architecture
# Returns JSON with system information

set -e

# Detect OS
OS=$(uname -s | tr '[:upper:]' '[:lower:]')

# Detect architecture
ARCH=$(uname -m)
case "$ARCH" in
    x86_64|amd64) ARCH="amd64" ;;
    aarch64|arm64) ARCH="arm64" ;;
    armv7*|armv8*) ARCH="arm" ;;
    armv*) ARCH="arm" ;;
    *) ARCH="unknown" ;;
esac

# Check disk space (need 2GB minimum)
REQUIRED_MB=2048
if [[ "$OS" == "linux" ]] || [[ "$OS" == "darwin" ]]; then
    AVAILABLE_MB=$(df -m . 2>/dev/null | tail -1 | awk '{print $4}')
else
    AVAILABLE_MB=0
fi

if [[ -n "$AVAILABLE_MB" ]] && [[ $AVAILABLE_MB -ge $REQUIRED_MB ]]; then
    DISK_OK="true"
else
    DISK_OK="false"
fi

# Check if running in container
if [ -f /.dockerenv ] || grep -q docker /proc/1/cgroup 2>/dev/null; then
    IN_CONTAINER="true"
else
    IN_CONTAINER="false"
fi

# Determine if supported
if [[ "$OS" == "linux" ]] || [[ "$OS" == "darwin" ]]; then
    SUPPORTED="true"
else
    SUPPORTED="false"
fi

# Detect package manager (Linux only)
PKG_MANAGER="none"
if [[ "$OS" == "linux" ]]; then
    if command -v apt-get &> /dev/null; then
        PKG_MANAGER="apt-get"
    elif command -v yum &> /dev/null; then
        PKG_MANAGER="yum"
    elif command -v dnf &> /dev/null; then
        PKG_MANAGER="dnf"
    elif command -v apk &> /dev/null; then
        PKG_MANAGER="apk"
    elif command -v pacman &> /dev/null; then
        PKG_MANAGER="pacman"
    fi
elif [[ "$OS" == "darwin" ]]; then
    if command -v brew &> /dev/null; then
        PKG_MANAGER="homebrew"
    fi
fi

cat << EOF
{
    "os": "$OS",
    "arch": "$ARCH",
    "supported": $SUPPORTED,
    "disk_space_mb": ${AVAILABLE_MB:-0},
    "disk_space_ok": $DISK_OK,
    "required_disk_mb": $REQUIRED_MB,
    "in_container": $IN_CONTAINER,
    "package_manager": "$PKG_MANAGER",
    "messages": [
        "Operating System: $OS",
        "Architecture: $ARCH",
        "Disk Space: ${AVAILABLE_MB:-unknown}MB available (${REQUIRED_MB}MB required)",
        $([ "$DISK_OK" = "false" ] && echo "\"WARNING: Insufficient disk space\"," || echo "")
        $([ "$SUPPORTED" = "false" ] && echo "\"WARNING: Unsupported operating system\"," || echo "")
        $([ "$IN_CONTAINER" = "true" ] && echo "\"NOTE: Running inside a container\"," || echo "")
        "Package Manager: $PKG_MANAGER"
    ]
}
EOF

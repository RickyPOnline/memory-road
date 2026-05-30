#!/usr/bin/env bash
# Memory Road · install_substrate.sh
# One-shot install for L0 + L1 + L5 (substrate · chunking · WATCHER).
# Run as root (or with sudo).
set -eu

MR=${MEMORY_ROAD_ROOT:-/opt/memory_road}
DB_DIR=/var/lib/memory_road
LOG_DIR=/var/log/memory_road
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

echo "=== Memory Road · Install Substrate ==="
echo "MR_ROOT=$MR"
echo "DB_DIR=$DB_DIR"
echo "LOG_DIR=$LOG_DIR"
echo "SCRIPT_DIR=$SCRIPT_DIR"
echo ""

# 1. Create dirs
echo "1/5 Creating directories..."
mkdir -p "$MR"/{bin,doctrines,hooks,schema,setup,examples}
mkdir -p "$DB_DIR" "$LOG_DIR"

# 2. Copy code
echo "2/5 Copying code..."
cp -r "$SCRIPT_DIR/bin/"* "$MR/bin/"
cp -r "$SCRIPT_DIR/doctrines/"* "$MR/doctrines/"
cp -r "$SCRIPT_DIR/hooks/"* "$MR/hooks/"
cp -r "$SCRIPT_DIR/schema/"* "$MR/schema/"
chmod +x "$MR"/bin/*.sh "$MR"/hooks/*.sh

# 3. Init DB
echo "3/5 Initializing SQLite DB..."
sqlite3 "$DB_DIR/continuity_kernel.db" < "$MR/schema/kernel_tables.sql"

# 4. Install systemd unit
echo "4/5 Installing systemd unit..."
cp "$SCRIPT_DIR/setup/systemd/continuity-kernel.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable continuity-kernel.service
systemctl start continuity-kernel.service

# 5. Verify
echo "5/5 Verifying..."
sleep 2
if systemctl is-active --quiet continuity-kernel; then
  echo "✅ continuity-kernel.service is ACTIVE"
else
  echo "❌ continuity-kernel.service failed to start"
  systemctl status continuity-kernel --no-pager
  exit 1
fi

echo ""
echo "🟢 SUBSTRATE INSTALL COMPLETE"
echo ""
echo "Next steps:"
echo "  - Fire forward sweeper:  bash $MR/bin/chronicler_forward_sweeper.sh &"
echo "  - Fire rotator:          bash $MR/bin/chronicler_rotator_manager.sh &"
echo "  - Install hooks:         cp $MR/hooks/*.sh ~/.claude/hooks/"
echo "  - Add to settings.json:  see $MR/setup/settings.json.example"
echo "  - Smoke test:            bash $MR/examples/smoke_test.sh"

#!/usr/bin/env bash
# Memory Road · install_hooks.sh
# Safely merges SessionStart + UserPromptSubmit hooks into ~/.claude/settings.json.
# Idempotent · backs up existing settings · uses Python for JSON safety.
set -eu

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
HOOKS_SRC="$SCRIPT_DIR/hooks"
HOOKS_DST="$HOME/.claude/hooks"
SETTINGS="$HOME/.claude/settings.json"
PACKET_PATH=${MEMORY_ROAD_PACKET:-"$HOME/.claude/projects/-root/memory/project_continuity_state.md"}

echo "=== Memory Road · install_hooks.sh ==="
echo "Hooks src: $HOOKS_SRC"
echo "Hooks dst: $HOOKS_DST"
echo "Settings:  $SETTINGS"
echo "Packet:    $PACKET_PATH"
echo ""

# 1. Backup existing settings.json
if [ -f "$SETTINGS" ]; then
  BAK="${SETTINGS}.bak.$(date +%Y%m%d-%H%M%S)"
  cp "$SETTINGS" "$BAK"
  echo "✅ Backup: $BAK"
else
  echo "{}" > "$SETTINGS"
  echo "✅ Created empty $SETTINGS"
fi

# 2. Copy hook scripts
mkdir -p "$HOOKS_DST"
cp "$HOOKS_SRC/inject_continuity_packet.sh" "$HOOKS_DST/"
cp "$HOOKS_SRC/force_memory_use.sh" "$HOOKS_DST/"
chmod +x "$HOOKS_DST"/*.sh
echo "✅ Hook scripts installed in $HOOKS_DST"

# 3. Merge SessionStart + UserPromptSubmit hooks via Python (JSON-safe)
python3 - "$SETTINGS" "$PACKET_PATH" "$HOOKS_DST" <<'PY'
import json, sys, os

settings_path, packet_path, hooks_dst = sys.argv[1], sys.argv[2], sys.argv[3]
with open(settings_path) as f:
    cfg = json.load(f)

cfg.setdefault("hooks", {})

# SessionStart hook · cat the packet on session boot
ss_list = cfg["hooks"].setdefault("SessionStart", [])
ss_cmd = f"cat {packet_path} 2>/dev/null"
ss_exists = any(
    any(sub.get("command", "").startswith("cat") and "project_continuity_state.md" in sub.get("command", "")
        for sub in (entry.get("hooks", []) or []))
    for entry in ss_list if isinstance(entry, dict)
)
if not ss_exists:
    ss_list.append({
        "matcher": "",
        "hooks": [
            {"type": "command", "command": ss_cmd, "timeout": 5}
        ]
    })
    print(f"✅ Added SessionStart hook · cmd: {ss_cmd[:80]}")
else:
    print("⚪ SessionStart hook already present · skipping")

# UserPromptSubmit hooks · inject_continuity_packet.sh + force_memory_use.sh
ups_list = cfg["hooks"].setdefault("UserPromptSubmit", [])
required_cmds = [
    f"bash {hooks_dst}/inject_continuity_packet.sh",
    f"bash {hooks_dst}/force_memory_use.sh",
]
existing_cmds = set()
for entry in ups_list:
    if isinstance(entry, dict):
        for sub in (entry.get("hooks", []) or []):
            existing_cmds.add(sub.get("command", ""))

for cmd in required_cmds:
    if any(cmd in ec or ec.endswith(os.path.basename(cmd.split()[-1])) for ec in existing_cmds):
        print(f"⚪ UserPromptSubmit already has · {cmd[:80]}")
        continue
    # Find first UserPromptSubmit entry · append to its hooks list
    if ups_list and isinstance(ups_list[0], dict):
        ups_list[0].setdefault("hooks", []).append({
            "type": "command", "command": cmd, "timeout": 5
        })
    else:
        ups_list.append({
            "hooks": [{"type": "command", "command": cmd, "timeout": 5}]
        })
    print(f"✅ Added UserPromptSubmit hook · {cmd[:80]}")

with open(settings_path, "w") as f:
    json.dump(cfg, f, indent=4)
print("✅ settings.json updated")
PY

echo ""
echo "🟢 HOOKS INSTALLED"
echo ""
echo "Next steps ·"
echo "  1. Cold-start Claude Code (quit + reopen)"
echo "  2. Send a test prompt"
echo "  3. Verify packet appears in context (look for 'CONTINUITY PACKET' or 'WATCHER')"
echo "  4. If no packet · check ~/.claude/settings.json for SessionStart entry"

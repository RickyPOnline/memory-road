#!/usr/bin/env bash
# Memory Road · Smoke Test
# Validates the entire stack is working end-to-end.
# Exit 0 = all green · exit 1+ = something is broken.
set -u

MR=${MEMORY_ROAD_ROOT:-/opt/memory_road}
DB=${MEMORY_ROAD_DB:-/var/lib/memory_road/continuity_kernel.db}
PACKET=${MEMORY_ROAD_PACKET:-$HOME/.claude/projects/-root/memory/project_continuity_state.md}

PASS=0
FAIL=0

ok()   { echo "✅ $1"; PASS=$((PASS+1)); }
fail() { echo "❌ $1"; FAIL=$((FAIL+1)); }

echo "=== MEMORY ROAD · SMOKE TEST ==="
echo ""

# 1. Substrate alive?
echo "L0 SUBSTRATE ·"
if systemctl is-active --quiet continuity-kernel 2>/dev/null; then
  ok "continuity-kernel.service is active"
else
  # Maybe running as plain process · not systemd
  if pgrep -f continuity_kernel.py >/dev/null; then
    ok "continuity_kernel.py is running (not via systemd)"
  else
    fail "continuity-kernel is NOT running · install/start substrate first"
  fi
fi

# 2. DB exists and has tables?
echo ""
echo "DATABASE ·"
if [ ! -f "$DB" ]; then
  fail "DB file missing: $DB"
else
  ok "DB file exists: $DB ($(du -h $DB | cut -f1))"
  TABLES=$(sqlite3 $DB ".tables" 2>/dev/null | tr -s ' ' '\n' | sort -u | grep -v '^$' | wc -l)
  if [ "$TABLES" -ge 5 ]; then
    ok "$TABLES tables present"
  else
    fail "Only $TABLES tables · expected ≥5 · run schema/kernel_tables.sql"
  fi
fi

# 3. Events being captured?
echo ""
echo "L0 EVENTS ·"
EVENTS=$(sqlite3 $DB "SELECT COUNT(*) FROM events;" 2>/dev/null || echo 0)
if [ "$EVENTS" -gt 0 ]; then
  ok "$EVENTS events captured"
else
  fail "Zero events captured · substrate may not be tailing JSONLs"
fi

# Check if events are FRESH (last 1 hour)
RECENT=$(sqlite3 $DB "SELECT COUNT(*) FROM events WHERE ts > strftime('%s','now') - 3600;" 2>/dev/null || echo 0)
if [ "$RECENT" -gt 0 ]; then
  ok "$RECENT events in last hour (substrate is live)"
else
  fail "Zero events in last hour · substrate not tailing OR agent is idle"
fi

# 4. Episodes chunked?
echo ""
echo "L1 EPISODES (FURROW) ·"
EPISODES=$(sqlite3 $DB "SELECT COUNT(*) FROM episodes_v2;" 2>/dev/null || echo 0)
if [ "$EPISODES" -gt 0 ]; then
  ok "$EPISODES episodes chunked"
else
  fail "Zero episodes · L1 FURROW not running"
fi

# 5. Summaries written?
echo ""
echo "L3 SUMMARIES (CHRONICLER) ·"
SUMMARIES=$(sqlite3 $DB "SELECT COUNT(*) FROM episode_summaries;" 2>/dev/null || echo 0)
MISSING=$(sqlite3 $DB "SELECT COUNT(*) FROM episodes_v2 WHERE id NOT IN (SELECT episode_v2_id FROM episode_summaries);" 2>/dev/null || echo 0)
PCT=0
if [ "$EPISODES" -gt 0 ]; then
  PCT=$(( SUMMARIES * 100 / (SUMMARIES + MISSING) ))
fi
if [ "$SUMMARIES" -gt 0 ]; then
  ok "$SUMMARIES summaries written · $PCT% of episodes covered"
else
  fail "Zero summaries · L3 CHRONICLER not running · fire rotator + forward sweeper"
fi

# 6. Forward sweeper alive?
echo ""
echo "L3 FORWARD SWEEPER ·"
if pgrep -f chronicler_forward_sweeper >/dev/null; then
  ok "Forward sweeper alive"
else
  fail "Forward sweeper NOT running · now-edge will lag"
fi

# 7. WATCHER cortex packet fresh?
echo ""
echo "L5 WATCHER ·"
if [ -f "$PACKET" ]; then
  NOW=$(date +%s)
  MTIME=$(stat -c %Y "$PACKET")
  AGE=$((NOW - MTIME))
  if [ "$AGE" -lt 300 ]; then
    ok "Cortex packet fresh (${AGE}s old)"
  elif [ "$AGE" -lt 600 ]; then
    ok "Cortex packet OK (${AGE}s old · within 10 min)"
  else
    fail "Cortex packet STALE (${AGE}s old · L5 WATCHER may be down)"
  fi
else
  fail "Cortex packet missing: $PACKET"
fi

# 8. HUNTSMAN flagging?
echo ""
echo "L12 HUNTSMAN ·"
HUNTS=$(sqlite3 $DB "SELECT COUNT(*) FROM huntsman_flags WHERE status='open';" 2>/dev/null || echo 0)
if [ "$HUNTS" -gt 0 ]; then
  ok "$HUNTS open unfinished flags"
else
  echo "⚪ HUNTSMAN has 0 flags (run python3 bin/huntsman.py to populate)"
fi

# 9. CARTOGRAPHER clusters?
echo ""
echo "L7 CARTOGRAPHER ·"
CLUSTERS=$(sqlite3 $DB "SELECT COUNT(DISTINCT cluster_id) FROM episode_clusters;" 2>/dev/null || echo 0)
if [ "$CLUSTERS" -gt 0 ]; then
  ok "$CLUSTERS topic clusters discovered"
else
  echo "⚪ CARTOGRAPHER not run yet (python3 bin/cartographer.py to fire)"
fi

# 10. Hooks installed?
echo ""
echo "FORCE-MEMORY-USE HOOKS ·"
if [ -f "$HOME/.claude/hooks/inject_continuity_packet.sh" ]; then
  ok "inject_continuity_packet.sh installed"
else
  fail "inject_continuity_packet.sh NOT installed · run: cp hooks/*.sh ~/.claude/hooks/"
fi
if [ -f "$HOME/.claude/hooks/force_memory_use.sh" ]; then
  ok "force_memory_use.sh installed"
else
  fail "force_memory_use.sh NOT installed · run: cp hooks/*.sh ~/.claude/hooks/"
fi

# 11. Hooks registered in settings.json?
if [ -f "$HOME/.claude/settings.json" ]; then
  if grep -q "inject_continuity_packet" "$HOME/.claude/settings.json"; then
    ok "Hooks registered in settings.json"
  else
    fail "Hooks NOT registered in settings.json · add UserPromptSubmit block from setup/settings.json.example"
  fi
else
  fail "settings.json missing"
fi

echo ""
echo "=== SMOKE TEST RESULT ==="
echo "  PASS: $PASS"
echo "  FAIL: $FAIL"
if [ "$FAIL" -eq 0 ]; then
  echo ""
  echo "🟢 ALL GREEN · Memory Road is operating cleanly."
  exit 0
else
  echo ""
  echo "🔴 $FAIL checks failed · see OPERATIONS.md troubleshooting"
  exit 1
fi

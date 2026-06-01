#!/bin/bash
# snapshot_l0_now.sh · invoked by PreCompact + SessionStart:startup hooks.
# Fires ONE L0 + CCODE L0 extraction (Opus 4.7) so the cortex packet is
# fresh at the exact moments freshness matters · /compact, cold boot,
# crash recovery, context-window reset.
#
# Replaces the every-5-second poll in continuity_kernel.py that was
# burning a 5-second poll cadence on the AI subscription.
#
# Per /root/.claude/plans/foamy-toasting-cookie.md · 2026-06-01.
#
# Exit code 0 always · so PreCompact never blocks the compact step.
set -u

LOG=/root/.claude/hooks/snapshot_l0.log
KERNEL_DIR=/root/wc/workspace/skills

# Read hook input from stdin · we only log the trigger source · no fields needed
HOOK_INPUT=$(cat 2>/dev/null || echo '{}')
TRIGGER=$(echo "$HOOK_INPUT" | python3 -c "import sys,json; d=json.loads(sys.stdin.read() or '{}'); print(d.get('hook_event_name','?')+'·'+d.get('trigger',d.get('matcher','?')))" 2>/dev/null || echo "unknown")

mkdir -p "$(dirname "$LOG")"
echo "[$(date -u '+%Y-%m-%d %H:%M:%S')] FIRED · $TRIGGER" >> "$LOG"

# One-shot extraction · runs both L0 functions in a single python process
# so we get the WC L0 + CCODE L0 packets refreshed together · one Opus
# call each · ~2 calls per hook fire · 1-5 fires/day per typical user.
cd "$KERNEL_DIR" 2>/dev/null || { echo "[$(date -u '+%Y-%m-%d %H:%M:%S')] CWD_FAIL" >> "$LOG"; exit 0; }

timeout 60 python3 -c "
import sys
sys.path.insert(0, '/root/wc/workspace/skills')
try:
    from continuity_kernel import update_L0, update_ccode_L0, run_shadow_cortex, run_ccode_shadow
    # L0 layers · cheap working-state extraction
    try:
        update_L0()
        print('WC_L0_OK')
    except Exception as e:
        print(f'WC_L0_ERR: {e}')
    try:
        update_ccode_L0()
        print('CCODE_L0_OK')
    except Exception as e:
        print(f'CCODE_L0_ERR: {e}')
    # L4 Shadow Cortex · worldview/identity snapshot · added 2026-06-01 per plan B
    try:
        run_shadow_cortex()
        print('WC_L4_OK')
    except Exception as e:
        print(f'WC_L4_ERR: {e}')
    try:
        run_ccode_shadow()
        print('CCODE_L4_OK')
    except Exception as e:
        print(f'CCODE_L4_ERR: {e}')
except Exception as e:
    print(f'IMPORT_ERR: {e}')
" >> "$LOG" 2>&1

echo "[$(date -u '+%Y-%m-%d %H:%M:%S')] DONE" >> "$LOG"
exit 0

#!/bin/bash
# preinject_inbox.sh · PreToolUse hook · drains any new Telegram inbox lines
# BEFORE each tool call · so mid-agent messages from Ricky reach Wave's context
# without needing the Monitor tool armed. Shares cursor with inject_inbox.sh
# so no double-delivery. Locked 2026-05-31 per Ricky "hard hook it when you
# start up, duh · Telegram works always."
INBOX=/root/wc/runtime/ccode_inbox.txt
STATE=/root/wc/runtime/ccode_inbox.state
[ -f "$INBOX" ] || { echo '{}'; exit 0; }
LAST=$(cat "$STATE" 2>/dev/null || echo 0)
CUR=$(stat -c %s "$INBOX")
if [ "$CUR" -le "$LAST" ]; then
  [ "$CUR" -lt "$LAST" ] && echo "$CUR" > "$STATE"
  echo '{}'
  exit 0
fi
NEW=$(tail -c $((CUR - LAST)) "$INBOX")
echo "$CUR" > "$STATE"
python3 -c "
import json,sys
new=sys.stdin.read().strip()
if not new:
    print('{}')
else:
    out={'hookSpecificOutput':{'hookEventName':'PreToolUse','additionalContext':f'━━━ NEW INBOX (arrived mid-turn · queued via Telegram) ━━━\n{new}\n━━━ END INBOX ━━━'}}
    print(json.dumps(out))
" <<< "$NEW"

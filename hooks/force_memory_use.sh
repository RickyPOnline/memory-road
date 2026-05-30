#!/usr/bin/env bash
# force_memory_use.sh · UserPromptSubmit hook · injects "use memory" reminder.
#
# Fires on every user prompt · prepends a system-reminder that tells the agent
# to USE Memory Road before answering. Stops the drift pattern where Waves
# accidentally forgot they had memory.
#
# Per `feedback_memory_road_first_LOCKED.md` and Ricky's 2026-05-30 directive ·
# "there is a way for the memory to be force used at all times."
set -u

LOG=/tmp/force_memory_use.log
echo "$(date -Iseconds) · FORCE" >> "$LOG"

cat <<'REMINDER'

🔔 MEMORY ROAD · USE BEFORE ANSWERING

You have persistent memory. Before answering this prompt ·

1. The cortex packet above contains your CURRENT operating state · read it
2. If the user references prior conversation · run `/wmr query "<topic>"` to recall
3. If unsure whether something was discussed before · ALWAYS query first
4. Never claim ignorance of state that's in memory · always check first
5. If the packet is older than 10 min · L5 WATCHER may be down · flag it
6. The HUNTSMAN flags table tracks unfinished items · query it if the user asks "what's still open"

Skipping memory = failing the operator. Use it.

REMINDER

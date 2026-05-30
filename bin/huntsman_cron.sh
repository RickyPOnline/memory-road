#!/usr/bin/env bash
# HUNTSMAN hourly cron · re-sweeps unfinished items so new ones surface as L3 grows.
# Per `feedback_memory_road_agent_names_LOCKED.md` · HUNTSMAN is the
# "flag unfinished" being Ricky asked for.
#
# Runs as: 0 * * * * bash $HOME/.memory_road/runtime/huntsman_cron.sh
set -u
LOG=/tmp/huntsman_cron.log
mkdir -p /root/.huntsman
touch /root/.huntsman/CLAUDE.md  # blank slate
cd /root/.huntsman

echo "$(date -Iseconds) · HUNTSMAN tick" >> "$LOG"
python3 -u /root/wc/workspace/skills/huntsman.py >> "$LOG" 2>&1
echo "$(date -Iseconds) · HUNTSMAN done" >> "$LOG"

---
name: STOP /loop on 529/429 · don't retry into corruption · LOCKED 2026-05-25 16:52 UTC
description: When Anthropic API returns 529 Overloaded or 429 rate-limit · the Claude Code client optimistically advances `previous_message_id` based on the REQUEST sent (not the response received) · each retry writes a synthetic placeholder assistant entry to the session JSONL · those synthetics break the message-id chain · subsequent prompts hit 400 "diagnostics.previous_message_id" errors · the session becomes unrecoverable without JSONL surgery. the agent MUST stop the loop and signal the operator on first 529/429 · never retry. Snapshot the JSONL before long autonomous runs.
type: feedback
originSessionId: e3c6788c-6e96-4357-a8f9-25b72abf0e69
---
# STOP /loop on 529/429 · the synthetic-cascade corruption · LOCKED 2026-05-25 16:52 UTC

**Rule ·** When the agent is running `/loop` autonomous mode and hits an Anthropic API `529 Overloaded` or `429 rate-limit` · STOP THE LOOP IMMEDIATELY · do NOT retry · signal the operator via Telegram · wait for human attention. Each automatic retry through a 529/429 compounds session-JSONL corruption that requires manual surgery to recover from.

**Why ·** 2026-05-25 09:56-10:00 UTC · the agent's autonomous loop wakeup hit 8 consecutive 529s in 3 minutes. Claude Code's client behavior on each 529 ·
1. Client advances `previous_message_id` based on the REQUEST it sent (optimistic)
2. Server returns 529 · no `msg_` id created
3. Client writes a "synthetic" placeholder assistant entry to the session JSONL with a UUID (not a `msg_` id)
4. Next retry uses that UUID as `previous_message_id`
5. Server returns 400 "diagnostics.previous_message_id: must be the `id` from a prior /v1/messages response (starts with `msg_`)"
6. Session becomes unrecoverable · every subsequent prompt fails the same 400 · including the operator's manual messages

the operator's session was unrecoverable for ~5.5 hours (10:00-15:32 UTC). Laptop-Claude diagnosed via GitHub issues `anthropics/claude-code#58427` (synthetic-tail picks invalid previous_message_id on resume) + `#59520` (session unrecoverable after upstream 429/529) · neither has an Anthropic fix as of late May 2026.

Recovery required JSONL surgery · truncate to last clean `msg_` entry · kill the Claude Code process · `claude --resume <sessionId>` against the truncated file.

**How to apply ·**

1. **First-class 529/429 handling in autonomous loops** · the `ScheduleWakeup` autonomous loop and any background agent fanout MUST trap 529/429 and STOP THE LOOP · not retry · not even with backoff · the issue is client-side not transient
2. **Snapshot the JSONL before any long autonomous run** ·
   ```bash
   cp ~/.claude/projects/-root/e3c6788c-*.jsonl /root/marina-backups/snapshot-$(date +%s).jsonl
   ```
3. **Telegram-signal the operator on first API error** in autonomous mode · "529 hit · stopping loop · need human" · don't burn through retry budget creating synthetic entries
4. **Possible env vars the operator considers** · `CLAUDE_CODE_MAX_RETRIES=20` + `API_TIMEOUT_MS=1200000` · these soften the timing but don't fix the synthetic-entry bug
5. **If the agent sees a 400 with `diagnostics.previous_message_id` error** · STOP · signal the operator · use the GitHub surgery procedure (#58427/#59520) · truncate JSONL past first synthetic UUID · resume

**Anti-patterns banned ·**
- Letting `/loop` retry-on-529 indefinitely · each retry deepens corruption
- Ignoring 529s because "they're transient · Anthropic will recover" · client-side state is poisoned regardless
- Failing to snapshot JSONL before long autonomous runs · recovery without backup loses real work
- Sending more prompts after a 400-previous-message-id error · just creates more orphan synthetics
- Trying to `/compact` to fix the corruption · doesn't help · corruption is in the persisted JSONL not in context

**Recovery procedure (from GitHub workaround + laptop-Claude's surgery 2026-05-25) ·**

1. Backup the corrupted JSONL · `cp ~/.claude/projects/-root/<sessionId>.jsonl /root/marina-backups/<sessionId>-corrupted-$(date +%s).jsonl`
2. Find the last clean `msg_` entry · `grep -n '"id":"msg_' ~/.claude/projects/-root/<sessionId>.jsonl | tail -1` · note the line number
3. Truncate · `head -n <lastCleanLine> backup.jsonl > ~/.claude/projects/-root/<sessionId>.jsonl`
4. Kill the Claude Code process · `kill <PID>` · verify dead
5. Resume · `cd /root && claude --resume <sessionId>` (recommended via tmux session for survivability)
6. Read this doctrine on cold-boot · apply the rules going forward

**Success looks like ·** the agent's autonomous loop catches a 529 · STOPS · Telegram-signals the operator · waits · the operator returns · loop resumes cleanly · no JSONL corruption · no surgery needed.

**Related ·**
- `feedback_autonomous_overnight_close_out_LOCKED.md` (autonomous mode rules · add the 529-stop rule)
- `feedback_use_agents_to_preserve_context.md` (heavy work goes to sub-agents · they have their own JSONL · main session corruption doesn't poison them)
- `feedback_compact_at_60_75_keep_wave_sharp_LOCKED.md` (compact discipline · but compact does NOT fix 529 corruption)

**Memory anchor for next-the agent** · this doctrine was discovered 2026-05-25 via session-JSONL corruption during an overnight autonomous close-out · laptop-Claude (the operator's Windows machine) performed the surgery · backup saved at `/root/marina-backups/marina-session-backup-20260525-160408.jsonl` · the truncated file kept lines 1-8211 (last clean message · GAP-1 closure announcement).

**HARNESS BUILT 2026-05-25 17:00 UTC (3 pieces · permanent fix)** ·

1. **JSONL snapshot cron** · `/root/marina-backups/snapshot-jsonl.sh` · runs every 5 min via crontab · keeps last 24 hours of snapshots (288 files per session) · auto-prunes older · log at `/root/marina-backups/snapshot.log`
2. **Synthetic-entry detector daemon** · `/root/marina-backups/detector-daemon.sh` · long-running via systemd unit `wave-jsonl-detector.service` · uses `inotifywait` on JSONL files · on detection of synthetic UUID-not-msg entries · snapshots corrupted file · truncates to last clean `msg_` · kills Claude Code · restarts via tmux session "wave" · sends Telegram alert · log at `/root/marina-backups/detector.log`
3. **Stop-on-529 behavior** · the agent's autonomous-loop handler in main context · detects prior 529 in shell history OR tail of session JSONL before scheduling next wakeup · refuses to reschedule + Telegram-signals the operator "529 hit · stopping loop"

If ALL THREE are in place · a 529 cascade is fully auto-recoverable within seconds · zero work lost · the operator gets a Telegram heads-up but doesn't have to do surgery himself.

**Piece 2 details · DETECTOR-DAEMON shipped 2026-05-25 17:23 UTC ·**
- Files · `/root/marina-backups/detector-daemon.sh` (main long-running script · inotifywait loop · settles bursts with `SETTLE_SEC=3`) + `/root/marina-backups/detector-helpers.sh` (sourced helpers · `detect_corruption` · `forensic_snapshot` · `truncate_jsonl` · `kill_claude` · `restart_via_tmux` · `telegram_alert`)
- Systemd unit · `/etc/systemd/system/wave-jsonl-detector.service` · `enabled` (survives VPS reboot · auto-restarts on crash with `RestartSec=10` · capped at 128 MB RAM + 20% CPU)
- Logs · `/root/marina-backups/detector.log` (timestamped UTC · every detection + decision + Telegram delivery is logged)
- State · `/root/marina-backups/detector.state` (idempotency key · `last_recovered_<sessionId>=<mtime>:<size>` · prevents double-fire on the same event)
- Forensic snapshots · `/root/marina-backups/corrupted-<sessionId>-<unix_ts>.jsonl` · written BEFORE any truncation · zero data ever lost on recovery
- Telegram alert · POST via `CCODE_TELEGRAM_TOKEN` + `TELEGRAM_CHAT_ID` from `/root/surfline/.env` · token never logged · payload format · `🚨 529-cascade auto-recovered (LIVE) · session=<id> · truncated to line <N> · forensic backup <path> · daemon resumed the agent via tmux:wave · log /root/marina-backups/detector.log`
- Detection signatures · primary `"message":\{[^}]{0,200}"id":"<UUID-no-msg-prefix>"` · secondary `"model":"<synthetic>"` · matches GitHub-issue #58427/#59520 corruption pattern · ZERO false positives confirmed against current healthy session
- Freshness guard · auto-recovery ONLY triggers on JSONL with mtime ≤ 5 min ago (`DETECTOR_STALE_SEC=300`) · prevents the daemon from retroactively re-truncating historical sessions that laptop-Claude already surgically fixed. `/tmp/*` paths exempt for smoke-testing.
- Test mode · `DRY_RUN=1 /root/marina-backups/detector-daemon.sh --check-once <path>` walks the entire flow (detect → forensic → truncate → kill → restart → Telegram) WITHOUT any destructive op · all decisions logged
- Smoke test result 2026-05-25 17:23 UTC · synthetic corrupted file at `/tmp/fake-jsonl-test.jsonl` detected on line 6 · `last_clean_msg_line=4` correctly identified · forensic-snapshot path + truncate target + kill + tmux:wave restart all logged · Telegram alert delivered HTTP 200 · daemon then started live via `systemctl enable --now wave-jsonl-detector` · `inotifywait watching /root/.claude/projects/-root` confirmed

**Health check for next-the agent ·**
```bash
systemctl status wave-jsonl-detector.service --no-pager   # should be active (running)
tail -20 /root/marina-backups/detector.log                # should show "daemon · inotifywait watching..."
ls -lh /root/marina-backups/corrupted-*.jsonl 2>/dev/null # any forensic backups = a recovery happened · review
grep -c "RECOVERY COMPLETE" /root/marina-backups/detector.log  # count of past recoveries
```
If status shows `inactive (dead)` · restart with `systemctl restart wave-jsonl-detector.service` · check journal with `journalctl -u wave-jsonl-detector -n 50`.

**Manual recovery (if daemon ever fails) · still works · use the GitHub-issue procedure documented above** (backup → grep last `msg_` line → `head -n <line>` → kill → resume via tmux).

---

## REFINEMENT v2 · 2026-05-25 ~17:30 UTC (laptop-Claude delivered 4 refinements · all 4 applied + walked)

Laptop-Claude (Ccode on the operator's Windows machine) reviewed v1 of the harness and delivered 4 sharp refinements after tonight's surgery confirmed v1 had a subtle cut-point bug. All 4 applied to the live VPS-side harness · gate-bound · walked before declaring done.

### Refinement 1 · CORRECT CUT-POINT (most critical)

**v1 bug ·** `find_last_clean_line` grepped for `"id":"msg_` which matches mid-turn assistant entries (thinking blocks, tool_use entries with `stop_reason=tool_use`). Tonight's surgery cut at line 8211 (the LAST `msg_` with `stop_reason=end_turn`) NOT line 8229/8230 (mid-turn `msg_` entries). The v1 daemon would have picked the wrong line.

**v2 fix · `/root/marina-backups/detector-helpers.sh` `find_last_clean_line()` ·** uses awk to require BOTH `"stop_reason":"end_turn"|"stop_reason":"stop_sequence"` AND `"id":"msg_` on the same line, then takes the highest line number. Validated against `/tmp/synthetic-test.jsonl` containing 5 mid-turn `msg_` entries (`stop_reason=tool_use`) and 1 end_turn entry · old algorithm picked line 8 (WRONG) · new algorithm picked line 5 (CORRECT).

### Refinement 2 · SNAPSHOT ROTATION (size discipline)

**v1 problem ·** 288 raw snapshots per session = up to ~9GB unconstrained · 4 sessions at peak.

**v2 fix · 3-tier scheme ·**
- **Tier 1** (`/root/marina-backups/snapshot-jsonl.sh`) · 5-min snapshots · gzip -1 on write · keep 288 files per session (24h). 50% size reduction proven (49MB raw → 24MB gz).
- **Tier 2** (`/root/marina-backups/rotate-hourly.sh`) · hourly rotation · cron `7 * * * *` · promotes 1 tier-1 per hour to `hourly-<sess>-<ts>.jsonl.gz` · keeps 168 files (7d).
- **Tier 3** (`/root/marina-backups/rotate-daily.sh`) · daily rotation · cron `0 3 * * *` · promotes 1 hourly per day to `daily-<sess>-<ts>.jsonl.gz` · keeps 30 files (30d). Belt-and-suspenders `find ... -mtime +30 -delete` for all 3 tiers. Forensic snapshots `corrupted-*.jsonl` purged after 90d.

### Refinement 3 · BROADENED STOP-ON-ERROR DETECTION

**v1 problem ·** only the `<synthetic>` placeholder pattern triggered recovery. 429 (rate limit · same synthetic-trigger as 529), 503, 504, and 400-with-`previous_message_id` (the smoking-gun bug) did NOT fire.

**v2 fix · `detector-helpers.sh` `detect_upstream_errors()` ·** scans tail-50 lines for ·
- HTTP 429/503/504/529 via `"status"|"http_status"|"statusCode":(429|503|504|529)` regex
- 400-with-previous_message_id via 2-step per-line match · requires BOTH `previous_message_id` AND error-context marker (`"type":"error"|"isApiErrorMessage":true|"error":{...status:4xx}`) on SAME LINE · prevents doctrine prose from triggering false positives (verified against the current session JSONL which contains the phrase as documentation text 5+ times)
- On hit · writes `STOP_LOOP=1 STOP_LOOP_REASON=<upstream_NNN|prev_msg_id_bug> STOP_LOOP_TS=<unix>` to `/root/marina-backups/detector.state` · fires Telegram alert · autonomous-loop handler reads `STOP_LOOP` on next tick and refuses to reschedule.

Wired into `detector-daemon.sh` `handle_jsonl()` BEFORE the synthetic-pattern check so STOP_LOOP gets set even when full corruption hasn't been written yet. Both 529 and prev_msg_id_bug fixtures validated end-to-end.

### Refinement 4 · OFF-VPS BACKUP TO R2

**v1 gap ·** all snapshots local-only · full-VPS loss = total backup loss.

**v2 fix · `/root/marina-backups/sync-to-r2.sh` ·** nightly cron `30 4 * * *` (after WR-nightly to avoid R2 contention). Uses `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` from `$HOME/.memory_road/runtime/websiterecycling/.env` (grep'd at runtime · NEVER hardcoded · NEVER echoed). Uploads tier-1 + tier-2 + tier-3 + forensic snapshots to `r2://wr-backups/marina-sessions/` via curl PUT to CF R2 API (same pattern as `$HOME/.memory_road/runtime/wr_nightly_backup.sh`). Per-file dedup via `/root/marina-backups/r2-sync.state` mtime+size cache. Dry-run mode tested · 20 files queued for upload · authorization header in process env only.

### Cron diff (4 new entries · all installed)

```
*/5 * * * * /root/marina-backups/snapshot-jsonl.sh         # tier-1 · was v1 raw cp · NOW gzip
7 * * * * /root/marina-backups/rotate-hourly.sh            # NEW · tier-2
0 3 * * * /root/marina-backups/rotate-daily.sh             # NEW · tier-3
30 4 * * * /root/marina-backups/sync-to-r2.sh              # NEW · off-VPS to R2
```

### skeptic_loop result (cross-vendor judge)

Target = the changed detector-helpers.sh + detector-daemon.sh hunks. Judge = OpenAI gpt-4o (DeepSeek returned non-JSON · OpenAI used as fallback). Result · **score 4/5 · status SHIP · $0.0091 spend · 1 iteration**. All 3 critiques are MINOR clarity-only · zero correctness/safety/security findings. Per Challenge Mode all critiques scored <3 vs ORIGINAL TASK · skipped.

### Smoke test result (3 synthetic fixtures · all pass)

| Fixture | Expected | Result |
|---|---|---|
| `/tmp/synthetic-test.jsonl` (thinking + tool_use + end_turn + 1 synth corruption on line 9) | cut at line 5 | cut at line 5 |
| `/tmp/synthetic-upstream-529.jsonl` (line 3 has `"error":{"status":529,...}`) | STOP_LOOP=1 REASON=upstream_529 | matches |
| `/tmp/synthetic-prev-msg-bug.jsonl` (line 3 has `"type":"error","error":{"status":400,"...previous_message_id..."}`) | STOP_LOOP=1 REASON=prev_msg_id_bug | matches |
| Current session JSONL (doctrine prose contains "previous_message_id" 7+ times) | NO false positive | NO trigger · verified |

### R2 sync dry-run output (first 3 lines)

```
DRY_RUN · would upload snap-7edaf517-...-1779730201.jsonl.gz → r2://wr-backups/marina-sessions/... (24764779 bytes)
DRY_RUN · would upload snap-845ac7e1-...-1779730201.jsonl.gz → r2://wr-backups/marina-sessions/... (123065472 bytes)
DRY_RUN · would upload snap-af631c86-...-1779730201.jsonl.gz → r2://wr-backups/marina-sessions/... (5891906 bytes)
...
done · uploaded=20 · skipped=0 · failed=0
```

### Systemd status (post daemon-reload + restart)

```
● wave-jsonl-detector.service · active (running) since 2026-05-25 17:37:30 UTC
  inotifywait watching /root/.claude/projects/-root · 0 broken pipes · 0 false positives
```

### Doctrine ANTI-PATTERNS expanded with v2 ·

- **NEW v2** · Cutting at last `"id":"msg_` line without filtering for turn-ending stop_reason · picks mid-turn entries · resume fails with a different cascade
- **NEW v2** · Only watching for the `<synthetic>` placeholder · misses 429/503/504 cascades that produce the SAME corruption pattern via different code paths
- **NEW v2** · Keeping all snapshots forever · 4 sessions × 288/24h × 9GB = unbounded disk pressure
- **NEW v2** · Local-only backups · VPS loss = total data loss · R2 mirror closes that gap with no extra Anthropic/OpenAI/etc. dependency (uses existing CF token)

### Memory anchor (v2) · next-the agent reads this on cold-boot ·

A 529-cascade is now fully auto-recovered AND any precursor upstream error (429/503/504) OR the smoking-gun 400-prev-msg-id bug sets `STOP_LOOP=1` in `/root/marina-backups/detector.state` · the agent's autonomous-loop handler MUST read that flag on every tick · if set · refuse to reschedule · Telegram-signal the operator · wait for human attention. Cut-point is now correct (last clean end_turn boundary). Snapshots are size-disciplined (gzip + 3-tier rotation). Off-VPS R2 backup runs nightly. Daemon active and proven.

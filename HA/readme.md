## Scenario 1 — Manual mowing (Press "Start Mowing Now" button in dashboard)

1. **Button** calls `script.goat_start_mowing_now`
2. **goat_start_mowing_now** — 5s delay → refresh entity state → weather check
   - If weather blocks or error active → cancel, notify, done
   - If clear:
     - If mode = **Areas** → `shell_command.goat_write_zones` writes zone IDs to `/tmp/goat_zones`
     - Turns on `goat_departure_window_active` + `goat_mowing_session_active`
     - Records `goat_mowing_session_started_at`
     - Calls `goat_open_garage` (opens door, waits up to 1 min, sets `goat_garage_managed_open`)
     - Calls `lawn_mower.start_mowing` → CleanMowerArea reads zone file (or falls back to auto)
     - Notifies (regular)
3. **Mower transitions → mowing**
   - `GOAT - Close Garage When Mowing Starts` fires (because `departure_window_active` = on) → waits 1 min → closes garage → turns off `departure_window_active`
   - `GOAT - Manual Start Detected` does **not** fire — `mowing_session_active` is already on, condition fails
4. **At session_started_at + 95 min** — `GOAT - Open Garage For Expected Return` fires (weekday guard applies) → opens garage, notifies (regular)
5. **Mower transitions → returning** — `GOAT - Open Garage When Returning` fires → opens garage (if not already), sets status "Returning", notifies (regular)
6. **Mower transitions → docked** — `GOAT - Close Garage When Docked` fires → waits 1 min → closes garage → turns off `mowing_session_active`, notifies (regular)
7. **At session_started_at + 100 min** (fallback) — `GOAT - Not Docked Fallback Alert` fires only if still not docked → **critical** notify

**If anything goes wrong mid-session:**
- Error reported → `GOAT - Error After Mowing Started` → opens garage + tries dock → **critical** notify
- Paused 5+ min → `GOAT - Paused Too Long Return To Dock` → docks → **critical** notify

---

## Scenario 2 — Scheduled mowing (Scheduled in Ecovacs App, and days hardcoded in HA; although start time is editable)

1. **Automation: `GOAT - Scheduled Start Gatekeeper`** fires at hardcoded days+time (Sat/Sun/Tue/Thu) if `goat_automation_enabled` = on
2. Calls `script.goat_mowing_start`
3. **goat_mowing_start** — 10s delay → refresh state → weather check
   - If weather blocks → cancel, turns off session flags, notifies (regular), done
   - If clear:
     - Turns on `goat_departure_window_active` + `goat_mowing_session_active`
     - Records `goat_mowing_session_started_at`
     - Calls `goat_open_garage`
     - Notifies "Garage just opened for scheduled mowing start" (regular)
     - **Does not call `lawn_mower.start_mowing`** — the mower starts itself on its own internal schedule
4. **Mower starts on its own → transitions → mowing**
   - `GOAT - Close Garage When Mowing Starts` fires → waits 1 min → closes garage → turns off `departure_window_active`
   - `GOAT - Manual Start Detected` does **not** fire — `mowing_session_active` is already on
5. Steps 4–7 from scenario 1 apply identically from here

---

**Key difference:** Manual uses `goat_start_mowing_now` (calls `start_mowing` explicitly, supports zone mode). Scheduled uses `goat_mowing_start` (opens garage only; mower self-starts on its internal timer). Both converge at the same return/dock sequence.

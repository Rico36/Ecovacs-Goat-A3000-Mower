## Scenario 1 — Manual mowing (Press "Start Mowing Now" in the HA dashboard)

1. **Button** calls `script.goat_start_mowing_now`
2. **goat_start_mowing_now** — 5s delay → refresh entity state → weather check
   - If soil moisture ≥ 55% or rain forecast in next 95 min or mower error → cancel, notify, done
   - If clear:
     - If mode = **Areas** → `shell_command.goat_write_zones` writes zone IDs to `/tmp/goat_zones`
     - Turns on `goat_departure_window_active` + `goat_mowing_session_active`
     - Records `goat_mowing_session_started_at`
     - Calls `goat_open_garage` (opens door, waits up to 1 min, sets `goat_garage_managed_open`)
     - Calls `lawn_mower.start_mowing` → CleanMowerArea reads zone file (or falls back to auto)
     - Notifies (regular)
3. **Mower → mowing**
   - `GOAT - Close Garage When Mowing Starts` fires (because `departure_window_active` = on) → waits 1 min → closes garage → turns off `departure_window_active`
   - `GOAT - Manual Start Detected` does **not** fire — `mowing_session_active` is already on, condition fails
4. **Mower → returning** — `GOAT - Open Garage When Returning` fires → opens garage, sets status "Returning", notifies (regular)
5. **Mower → docked** — `GOAT - Close Garage When Docked` fires → waits 1 min → closes garage → turns off `mowing_session_active` + `goat_makeup_pending`, notifies (regular)
6. **At session_started_at + 120 min** (fallback) — `GOAT - Not Docked Fallback Alert` fires only if still not docked → **critical** notify

**If anything goes wrong mid-session:**
- Error reported → `GOAT - Error After Mowing Started` → opens garage + tries dock → **critical** notify
- Paused 5+ min → `GOAT - Paused Too Long Return To Dock` → docks → **critical** notify

---

## Scenario 2 — Scheduled mowing (HA is the sole scheduler; Ecovacs app schedules deleted)

1. **`GOAT - Scheduled Start Gatekeeper`** fires when `now()` matches `input_datetime.goat_mowing_start_time`
   - Condition: `goat_automation_enabled` = on AND today's `goat_schedule_<weekday>` toggle = on
   - Days are set from the dashboard — 7 green/grey buttons (Mon–Sun), tap to toggle
2. Calls `script.goat_mowing_start`
3. **goat_mowing_start** — 10s delay → refresh state → weather check
   - If soil moisture ≥ 55% or rain forecast in next 95 min or mower error:
     - Cancel, set `goat_makeup_pending` = on, notify "Mowing cancelled — makeup pending" (regular)
   - If clear:
     - If mode = **Areas** → `shell_command.goat_write_zones` writes zone IDs to `/tmp/goat_zones`
     - Turns on `goat_departure_window_active` + `goat_mowing_session_active`
     - Records `goat_mowing_session_started_at`
     - Calls `goat_open_garage`
     - Calls `lawn_mower.start_mowing` → mower starts immediately (no Ecovacs schedule needed)
     - Notifies "Scheduled mowing started" (regular)
4. **Mower → mowing**
   - `GOAT - Manual Start Detected` does **not** fire — `mowing_session_active` is already on
   - `GOAT - Close Garage When Mowing Starts` fires → waits 1 min → closes garage
5. Steps 4–6 from Scenario 1 apply identically from here

**Unauthorized start** (mower starts via physical button or any path outside HA):
- `GOAT - Manual Start Detected` fires (condition: `mowing_session_active` = off)
- Checks weather → if rain forecast → docks + **critical** notify "Mower stopped due to weather"
- If clear → opens garage, sets `mowing_session_active` on, notifies (regular), closes garage after 1 min

---

## Scenario 3 — Makeup mowing (auto-retry after a weather cancellation)

Triggered when a scheduled mow was cancelled and `goat_makeup_pending` = on.

1. **`GOAT - Makeup Day Check`** fires every hour on the hour, 11am–7pm
   - Conditions: `goat_automation_enabled` = on, `goat_makeup_pending` = on,
     `mowing_session_active` = off, today is **not** a scheduled mowing day
     (scheduled days run via the gatekeeper; makeup only fills non-scheduled gaps)
2. Weather check — same conditions as scheduled mow (soil moisture + forecast + error)
   - If still blocked and time is 11am → notify "Makeup mow waiting, will retry hourly" (regular); silent retries each hour after
   - If clear:
     - If mode = **Areas** → writes zone file
     - Turns on `goat_departure_window_active` + `goat_mowing_session_active`
     - Records `goat_mowing_session_started_at`
     - Calls `goat_open_garage`
     - Calls `lawn_mower.start_mowing`
     - Notifies "Makeup mow started" (regular)
3. From here, steps 4–6 from Scenario 1 apply — including clearing `goat_makeup_pending` on dock

**`goat_makeup_pending` lifecycle:**
- Set on: scheduled mow cancelled by weather
- Cleared: any mowing session ends with mower docked (`GOAT - Close Garage When Docked`)
- Also manually toggleable from the dashboard

---

## Weather protection (all scenarios)

Two independent blocking checks run before every mow:

| Check | Source | Block threshold |
|---|---|---|
| Wet grass | `sensor.front_rain_sensor_soil_moisture` | ≥ 55% |
| Rain forecast | PirateWeather (`weather.pirateweather`), next 95 min | precipitation_probability ≥ 40% or condition in rainy/pouring/lightning |

Use `script.goat_test_weather_check` (Developer Tools → Actions) to run a live check — result appears as a persistent notification showing soil moisture, forecast slots, and the go/cancel decision.

---

## Dashboard layout

Three sections in a vertical-stack replacing the old GOAT card:

1. **Entities card** (title: GOAT Mowing Schedule)
   - GOAT Automation Enabled toggle
   - GOAT Status
   - *Scheduled Mowing* section: Start Time · Mow Mode · Zone IDs

2. **7-column button grid** (`custom:button-card`) — Mon Tue Wed Thu Fri Sat Sun
   - Green = scheduled, grey = off; tap to toggle

3. **Entities card** (title: Mowing Run)
   - *Manual Mowing* section: Start Mowing Now button
   - *Session Status* section: Expected Return · Departure Window Active · Mowing Session Active · Makeup Mow Pending · Last Mowing Started · Last Decision

HACS cards required: `custom:button-card`, `custom:template-entity-row`

Full card YAML in `HA/dashboard.yaml`.

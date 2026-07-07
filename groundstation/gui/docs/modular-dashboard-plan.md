# Ground-Station GUI Refactor Plan — Modular Grid Dashboard

## 1. Why / Goal

The Flight-Data UI today is a hardcoded 4-column layout baked into `UIManager._draw_flight_data_ui()`, sized for a fixed 1920×1080 viewport. Every widget is a de-facto singleton: DPG item tags are bare global string literals (`"battery_bar"`, `"xaxis"`, `"accel_series"`, `"subsystem_box_0"`, …), plot state lives in class-body attributes mutated by `@classmethod`s, and telemetry is delivered by a hand-written `UIManager.update_all()` dispatch table that pushes to one named instance of each window. You cannot place a widget twice, move it, resize it, or save a layout — and the serial receiver thread calls `dpg.set_value(...)` directly with no main-thread marshalling (a real bug).

**Goal:** turn the dashboard into a grid of standardized, dynamically-placeable widgets — multiple instances allowed, layouts saved to disk — like a fixed-cell grid dashboard.

## 2. Core design decision

The refactor is **decoupling-first, layout-second**. The real deliverable is three pieces of plumbing:

1. **A thread-safe telemetry bus + main-thread pump** — publishers (the serial thread) only *enqueue*; a per-frame pump drains the queue and invokes subscriber callbacks on the DPG thread. This kills the god-object dispatch table and fixes the cross-thread `dpg.set_value` bug.
2. **A `Widget` base class with per-instance tag namespacing** — every DPG tag flows through `self.tag(name)`, so no two instances can ever collide. This mechanically dissolves every hardcoded-global-tag blocker.
3. **A swappable `LayoutEngine` Protocol** whose default is a true fixed-cell **GridLayoutEngine**, with a DPG-docking engine kept as a de-risking fallback.

Layout is deliberately the *thin, reversible* part. ~70% of the work (bus, instance_id, un-classmethod-ing the plots, thread marshalling) is identical no matter which layout renderer wins, so we build that first and treat the grid renderer as a late, spike-gated phase.

---

## 3. Target architecture

### 3.1 Module / folder layout

```
ui/
  core/                     # domain logic, NO layout/rendering
    bus.py                  # TelemetryBus: topic -> [callback]
    pump.py                 # MainThreadPump: queue drain per frame
    mission_clock.py        # MissionClock: elapsed seconds + reset
    widget_base.py          # Widget ABC + BuildContext
    registry.py             # widget-type registry + factory + meta()
    services.py             # ServiceHub / BuildContext bundle
    serial_service.py       # owns TelemetryReceiver, publishes to bus
  layout/                   # rendering / placement
    layout_engine.py        # LayoutEngine Protocol
    grid_engine.py          # GridLayoutEngine (default)
    dock_engine.py          # DockLayoutEngine (fallback, spike-gated)
    grid_math.py            # PURE functions, unit-testable, no DPG
    layout_store.py         # dashboard JSON load/save
    edit_overlay.py         # Phase-B add/remove/property panel
  windows/                  # each becomes a Widget subclass
    altitude_window.py
    acceleration_window.py
    battery_window.py
    ...
  settings_manager.py       # UNCHANGED singleton (settings.json owner)
  ui_manager.py             # slims to a bootstrap
dashboards/
  flight-default.json       # today's 4-column layout, as a grid
tests/
  test_grid_math.py         # pure math, no viewport
  test_bus.py               # headless fan-out
  test_widget_lifecycle.py  # mount / destroy / tag-uniqueness headless
```

`ui_manager.py` shrinks from a god-object to a bootstrap: create DPG context, keep the GNU Unifont setup and the Escape/exit-callback wiring, build the `ServiceHub`, hand the Flight-Data tab to the active `LayoutEngine`, and own the edit-mode shell. **Delete `ui/windows/accelerometer_window_deprecated.py`** (confirmed zero references).

### 3.2 Base Widget API (`ui/core/widget_base.py`)

```python
class Widget(ABC):
    # --- class-level metadata (drives palette + registry) ---
    TYPE_ID: str          # stable JSON id, e.g. "battery", "altitude", "map"
    DISPLAY_NAME: str     # palette label, e.g. "Battery Voltage"
    DEFAULT_CELLS: tuple[int, int]   # (colspan, rowspan)
    MIN_CELLS: tuple[int, int]
    SINGLETON: bool = False          # True only for SettingsWindow / serial owner

    def __init__(self, iid: str, ctx: BuildContext, config: dict):
        self.iid = iid               # persisted uuid, minted at drop time
        self.ctx = ctx               # bus, settings, mission_clock, serial_service
        self.config = config
        self._subs = []              # subscription tokens, for teardown
        self._root = self.tag("root")

    # THE single source of every DPG tag — nothing else may pass a literal tag
    def tag(self, name: str) -> str:
        return f"{self.TYPE_ID}__{self.iid}__{name}"

    def subscribe(self, topic: str, cb):
        self._subs.append(self.ctx.bus.subscribe(topic, cb))

    # --- lifecycle ---
    @abstractmethod
    def build(self, parent: str, width: int, height: int) -> None:
        """Create dpg.child_window(tag=self._root, parent=parent, ...)
        filling width=-1/height=-1, then subscribe to topics."""

    def on_config_changed(self, config: dict) -> None: ...   # live refresh
    def get_config(self) -> dict: return self.config          # round-trips to JSON

    def destroy(self) -> None:
        for tok in self._subs:
            self.ctx.bus.unsubscribe(tok)
        self._subs.clear()
        dpg.delete_item(self._root)
```

Key contract changes vs. today:
- `build(parent, width, height)` **replaces** `draw_ui(w, h)`. The widget must create its `child_window` with `tag=self._root, parent=parent` and fill the cell (`width=-1, height=-1`); the **grid owns pixel geometry**.
- `destroy()` is **new and load-bearing** — most widgets have no teardown today. Required for add/remove/reload-layout.
- `on_config_changed()` replaces ad-hoc `reload()`.

### 3.3 Data bus (`ui/core/bus.py`, `pump.py`, `services.py`)

`TelemetryBus` is a `topic -> list[callback]` map: `subscribe(topic, cb) -> token`, `unsubscribe(token)`, `publish(topic, payload)`.

**Concrete channels** (derived from the real `FIELDS` in the inventory):

| Channel | Source field / trigger | Primary subscribers |
|---|---|---|
| `tele/temperature` | `temperature` | LastPacket |
| `tele/subsystem_status` | `subsystem_status` | Subsystem, LastPacket |
| `tele/flight_mode` | `flight_mode` | (derives `flight/armed`), LastPacket |
| `tele/low_power_mode` | `low_power_mode` | LastPacket |
| `tele/status_events` | `status_events` | FlightEvents, LastPacket |
| `tele/acceleration` | `acceleration` | Acceleration, LastPacket |
| `tele/height_pressure` | `height_pressure` | Altitude, LastPacket |
| `tele/height_gnss` | `height_gnss` | Altitude, LastPacket |
| `tele/lat_gnss` | `lat_gnss` | (derives `gps/fix`), LastPacket |
| `tele/lon_gnss` | `lon_gnss` | (derives `gps/fix`), LastPacket |
| `tele/battery_voltage` | `battery_voltage` | Battery, LastPacket |
| `tele/rssi` | `rssi` | Connection, LastPacket |
| `tele/time_since_last_packet` | `time_since_last_packet` | Connection, LastPacket |
| `packet/raw` | full decoded dict | LastPacket, ComMonitor |
| `gps/fix` | fires **only** when lat+lon both present | Location, MapView |
| `flight/armed` | bool edge from `flight_mode` (computed centrally) | FlightEvents, plots |
| `mission/reset` | mission clock zeroed | plots, LastPacket, ComMonitor |
| `plot/stop`, `plot/resume`, `plot/reset` | global plot control | Altitude, Acceleration |
| `settings/battery/changed` | `set_section("battery")` | Battery |
| `settings/connection/changed` | `set_section("connection")` | Connection |
| `settings/flight_events/changed` | `set_section("flight_events")` | FlightEvents |
| `settings/commands/changed` | `set_section("commands")` | Commands |

The derived channels (`gps/fix`, `flight/armed`, `mission/reset`) are computed **once, centrally**, so the guards leave the widgets (today `update_gps` does the both-present check and `update_flight_mode` owns the arm/disarm edge state machine).

**Payload** is a small dataclass so plot widgets get mission-elapsed time *without owning a clock*:

```python
@dataclass
class Sample:
    value: object
    wall_t: float      # time.time()
    mission_t: float   # from MissionClock; replaces UIManager's inline elapsed math
```

**Thread marshalling (fixes the confirmed real bug):** `SerialService.on_packet` runs on the `telemetry-rx` daemon thread and **only enqueues** `(topic, sample)` onto a `queue.Queue`. `MainThreadPump.pump()` drains the queue once per rendered frame and invokes callbacks on the DPG thread. `pump.py` replaces the blocking `dpg.start_dearpygui()`:

```python
while dpg.is_dearpygui_running():
    bus.pump()                    # drain queue -> callbacks (main thread)
    dpg.render_dearpygui_frame()
```

**Critical constraint:** publishers only *enqueue*. Item **creation** (edit-mode "add widget") must stay on the main thread. Preserve `UIManager.shutdown()` idempotency and the map/serial thread joins across the loop change.

`BuildContext` bundles `bus`, the `settings` singleton, `mission_clock`, and `serial_service`, handed to every widget factory so widgets **stop importing `UIManager`** (this breaks `CommandsWindow`'s `receiver.controller.controller` hard reference — commands are sent by `iid` via `serial_service`).

### 3.4 Grid layout engine (`ui/layout/`)

`LayoutEngine` Protocol: `load(spec)`, `place(widget, geom)`, `move/resize/remove`, `serialize()`.

`grid_math.py` (pure, unit-testable, no DPG):

```python
@dataclass(frozen=True)
class GridSpec:
    cols: int = 12
    cell_h: int = 80      # fixed pixel row height
    gutter: int = 8
    margin: int = 12

def cell_w(spec, viewport_w):
    return (viewport_w - 2*spec.margin - (spec.cols-1)*spec.gutter) / spec.cols
def cell_to_px(spec, rect, viewport_w): ...   # (col,row,colspan,rowspan) -> (x,y,w,h)
def px_to_cell(spec, x, y, viewport_w): ...    # for snap-to-cell
def first_free_slot(occupancy, span): ...      # placement for "Add widget"
def overlaps(a, b) -> bool: ...
```

**Fluid columns, fixed rows:** `cell_w` recomputes from the live viewport width, so the layout is responsive — this directly fixes the hardcoded 1920×1080 assumption. Row height stays fixed; tall widgets (MapView) span many rows.

`GridLayoutEngine` creates one scrollable canvas `dpg.child_window` per tab (virtual height = `margin + rows*(cell_h+gutter)`). For each widget it creates the root `dpg.child_window(parent=canvas, pos=(x,y), width=w, height=h, tag=widget.tag("root"))`, then calls `widget.build(root, w, h)`. On `dpg.set_viewport_resize_callback` it recomputes `cell_w` and `dpg.configure_item`s every root.

**De-risk:** a week-1 throwaway spike must prove `pos=` on a nested scrollable `child_window` behaves under scroll / DPI / resize **before** committing. If it misbehaves, `dock_engine.py` implements the same Protocol with each widget root as a top-level `dpg.window` under `configure_app(docking=True, docking_space=True)` (verified in DPG 2.2), geometry via `save_init_file`/`load_init_file`. Because `build()` is parent-aware and the Protocol is uniform, switching engines is a one-line bootstrap change with **zero widget edits**.

Both engines expose a **"Lock Layout"** toggle (flip `no_move`/`no_resize` on every root) to freeze the dashboard during flight.

### 3.5 Dashboard JSON schema (`ui/layout/layout_store.py`)

A versioned file under `dashboards/`, **separate from `settings.json`**:

```json
{
  "schema": 1,
  "name": "flight-default",
  "grid": { "cols": 12, "cell_h": 80, "gutter": 8, "margin": 12 },
  "widgets": [
    {
      "type": "altitude",
      "iid": "a1f3c9e2",
      "cell": [0, 0, 6, 5],
      "config": {
        "title": "Altitude",
        "field_a": "height_pressure",
        "field_b": "height_gnss",
        "y_label": "Altitude (m)",
        "coordinated": true
      }
    },
    {
      "type": "battery",
      "iid": "b7d20114",
      "cell": [6, 0, 3, 3],
      "config": { "title": "Main Pack", "thresholds": "settings" }
    },
    {
      "type": "map",
      "iid": "c0e4aa9d",
      "cell": [0, 5, 6, 8],
      "config": { "title": "Map", "lat": 50.59, "lon": 8.70, "zoom": 14,
                  "satellite_mode": false, "traffic_enabled": false }
    }
  ]
}
```

- `cell` is `[col, row, colspan, rowspan]`.
- `iid` is a uuid minted at drop-time and **persisted**, then passed back to the constructor on reload — tags stay stable across save/restore, fixing the non-deterministic `itertools.count()` reset that Location/MapView fall back to.
- The registry **rejects duplicate iids** on load and **drops unknown types with a warning** rather than crashing.
- The active-dashboard path lives in `settings.json` under `dashboard.current`.
- `config` is always the source of truth even if the dock fallback stores geometry in an opaque `.ini`.

Ship `dashboards/flight-default.json` reproducing today's exact 4-column layout as a grid parity target.

### 3.6 Edit mode (phased)

- **Phase A (MVP):** dashboards are hand-editable JSON + a **"Reload Layout"** button that calls `engine.teardown_all()` (`destroy()` every live widget → unsubscribe + delete root) and reloads the file. Multi-instance dashboards work with **zero drag code**.
- **Phase B:** an "Edit" toggle reveals an **"Add Widget"** palette populated from `registry.meta()` (`DISPLAY_NAME` + `DEFAULT_CELLS`); clicking mints a uuid, finds `first_free_slot`, and factory-creates + `build()`s live. A per-cell **✕** calls `widget.destroy()`. A numeric property panel sets `col/row/colspan/rowspan` (DPG has no native `child_window` drag, so MVP edit is snap-to-cell numeric). True mouse-drag with `px_to_cell` snapping is a stretch goal — or exactly where the dock fallback earns its keep (drag/resize free).

### 3.7 How the hardcoded-global-tag multi-instance blocker is fixed

**One mechanical rule, enforced by the base class:** *no literal tag is ever passed to `dpg.add_*` — everything flows through `self.tag(name)`.*

`self.tag("bar")` → `"battery__b7d20114__bar"`. Because `iid` is unique per placement, two instances can never produce the same tag. Concretely this dissolves every confirmed collision:

| Today (global literal) | After |
|---|---|
| `"battery_bar"`, `"battery_min"`… | `battery__{iid}__bar`, `…__min` |
| `"xaxis"`, `"yaxis"`, `"altitude_pressure_series"` | `altitude__{iid}__xaxis`, `…__series_a` |
| `"accel_series"`, `"accel_xaxis"`… | `acceleration__{iid}__series`… |
| `"subsystem_box_0"` (bit index only) | `subsystem__{iid}__box_0` |
| `"rssi_bar"`, `"rssi_warning"`… | `connection__{iid}__bar`… |
| `"monitor_status_label"` | `com_ctl__{iid}__status` |
| `"cfg_bat_min"`, `"settings_status_label"`… | `settings__{iid}__bat_min`… |
| `"time_window_table"`, `"time_window_time_0"` | `time__{iid}__table`, `…__cell_0` |
| `LastPacketWindow.system_status_tags` (class dict) | per-instance dict `{k: self.tag(k)}` |

**Companion fixes that tags alone can't solve:**
1. **Altitude / Acceleration class-body state** (the data lists, `min`/`max`/`current`, `plot_active`) moves into `__init__` as `self.*`, and every `@classmethod` (`draw_ui`, `update_*`, `stop/resume/reset`) becomes an **instance method** — otherwise two instances share one dataset.
2. **`LastPacketWindow.system_status_tags`** class dict becomes per-instance, and the widget gains real update methods that own formatting (moving the `f"{t:.1f} °C"` / `format(status,"03b")` / `"ON"/"OFF"` / `f"{rssi} dBm"` logic out of `UIManager`) and subscribes to `packet/raw`.
3. **`PlotCoordinator`'s class registry** is replaced by bus topics `plot/stop|resume|reset` fanning to subscribed **instances**, with a per-widget `"coordinated"` config flag to opt a plot out of global control.

Result: the commented-out dual MapView/Location and N batteries/altitudes "just work."

---

## 4. Widget migration table

Every widget in the inventory. Grid spans assume a 12-col grid, `cell_h=80px`. Effort is the inventory's own S/M/L.

| # | Current module | New `TYPE_ID` | Per-instance tag fix needed | Subscribes to | Default span `[cols×rows]` | Effort |
|---|---|---|---|---|---|---|
| 1 | `altitude_window.py` (`AltitudeWindow`) | `altitude` | 11 bare tags (`xaxis`,`yaxis`,`altitude_*_series`,`alt_p/g_*`,`alt_btn_stop_resume`) → `self.tag()`; **move all class-body state into `__init__`; un-classmethod all methods**; register instance (not class) for plot control | `tele/height_pressure`, `tele/height_gnss`, `plot/stop`, `plot/resume`, `plot/reset`, `mission/reset` | 6×5 | **M** |
| 2 | `acceleration_window.py` (`AccelerationWindow`) | `acceleration` | 9 `accel_*` tags → `self.tag()`; **class-body state → `__init__`; un-classmethod**; button callbacks bind to `self`, not `PlotCoordinator.toggle/reset_all` | `tele/acceleration`, `plot/*`, `mission/reset`, `flight/armed` (reset on arm) | 6×5 | **M** |
| 3 | `accelerometer_window_deprecated.py` (`AccelerometerWindow`) | — | **DELETE ENTIRELY** — confirmed dead code (zero refs), superseded by #2. No migration. | — | — | **S (delete)** |
| 4 | `battery_window.py` (`BatteryWindow`) | `battery` | 6 tags (`battery_bar/label/warning/min/critical/max`) → `self.tag()`; title from config; add `destroy()` | `tele/battery_voltage`, `settings/battery/changed` | 3×3 | **S** |
| 5 | `connection_window.py` (`ConnectionWindow`) | `connection` | 7 `rssi_*` tags → `self.tag()`; bind bar theme to namespaced bar tag; add `destroy()` | `tele/rssi`, `tele/time_since_last_packet`, `settings/connection/changed` | 3×3 | **S** |
| 6 | `flight_events_window.py` (`FlightEventWindow`) | `flight_events` | Already uses `instance_id` + per-instance state; source `uid` from persisted `iid`, prefix type name; add `destroy()` | `tele/status_events`, `flight/armed` (→`reset()`), `settings/flight_events/changed` | 4×5 | **S** |
| 7 | `last_packet_window.py` (`LastPacketWindow`) | `last_packet` | `system_status_tags` class dict → per-instance `{k: self.tag(k)}`; add real formatting update methods; `destroy()` | `packet/raw` (or the 13 individual `tele/*`), `mission/reset` (optional clear) | 3×5 | **M** |
| 8 | `subsystem_window.py` (`SubsystemWindow`) | `subsystem` | `subsystem_box_{bit}` → `self.tag(f"box_{bit}")`; tag the child_window; SUBSYSTEMS list → config; add `create()/destroy()`; `parent` param | `tele/subsystem_status`, `settings` (optional) | 4×2 | **S** |
| 9 | `time_window.py` (`TimeWindow`) | `time` | `time_window_table` + `time_window_time_{i}` → `self.tag()`; zones → config; add `destroy()` (unbind item_handler_registry) | **none** (pure system clock, self-ticks via visible-handler) | 3×2 | **S** |
| 10 | `commands_window.py` (`CommandsWindow`) | `commands` | Already auto-ID (no literal tags); build themes once in `__init__` + delete in `destroy()`; drop constructor `receiver`, use `ctx.serial_service`; per-instance group filter config; live `settings/commands/changed` refresh | `settings/commands/changed`, `serial/status` (connection state) | 3×6 | **M** |
| 11 | `location_window.py` (`LocationWindow`) | `location` | Already `instance_id`-safe (`loc_*_{uid}`); source `uid` from persisted `iid`, drop `_id_counter`; add `parent` param + `destroy()` | `gps/fix` (both lat+lon present) | 4×2 | **S** |
| 12 | `map_view_window.py` (`MapViewWindow`) | `map` | Tags already namespaced; **fix global arrow-key handler → hover/focus-scoped**; `title` from config replaces `label="Map"`; keep shared disk cache; persist zoom/mode; registry must call `shutdown()` on teardown | `gps/fix` | 6×8 | **M** |
| 13 | `com_monitor.py` (`ComMonitor`) — *disabled* | `com_monitor` | `TABLE_TAG` class literal → `self.tag("table")`; COLUMNS → config; add width/height to `build`; add `reset()/clear()` + row cap + `destroy()`; **re-enable via `packet/raw` subscription** (uncomment its wiring) | `packet/raw`, `mission/reset` | 6×5 | **S** |
| 14 | `com_monitor_controller.py` (`ComMonitorController`) | `com_ctl` | `_TAG_STATUS="monitor_status_label"` → `self.tag("status")`; tag child_window; **publish `packet/raw` via `SerialService` instead of `ui_manager.update_all`**; expose `serial/status`; persist port+baud; `SINGLETON`/single-serial-owner guard | publishes `packet/raw`, `serial/status` | 3×2 | **M** |
| 15 | `settings_window.py` (`SettingsWindow`) | `settings` | All `cfg_*` + `settings_status_label` → `self.tag()`; **mark `SINGLETON=True`** (keep as non-grid tab for MVP — `set_section` whole-section replace = clobber hazard); publish `settings/*/changed` on save instead of `on_saved` callback | — (publishes `settings/*/changed`) | (own tab) | **L** |
| 16 | `telemetry/com_controller.py` (`TelemetryReceiver`) | — (backend, wrapped by `SerialService`) | Not a widget. Add `instance_id`: namespace log filenames (`telemetry_{iid}_{ts}.csv`) + logger; replace single `ui_callback` with bus publish; guard double-open port | — | — | **L** |

---

## 5. Phased roadmap

**Invariant: the app runs after every phase.** Each phase is a strangler-fig step — new machinery is added and *dual-wired* alongside the old path, then the old path is deleted only once the new one is proven at parity.

### Phase 0 — Bus + pump scaffolding (no UI change)
- **Goal:** introduce the core loop change and bus with zero behavioral difference.
- **Tasks:** add `ui/core/bus.py`, `ui/core/pump.py`, `ui/core/services.py` (empty `BuildContext`). Replace `dpg.start_dearpygui()` with the `while dpg.is_dearpygui_running(): bus.pump(); dpg.render_dearpygui_frame()` loop. Re-verify the Escape handler, exit callback, and `shutdown()` idempotency across the loop change. Land `tests/test_bus.py` (headless fan-out, unsubscribe, no viewport).
- **Files:** `ui/core/*` (new), `ui/ui_manager.py`.
- **Commit:** "Add telemetry bus + main-thread pump loop (no consumers yet)."
- **Verify:** app launches, telemetry still updates all windows via the untouched `update_all`; `pytest tests/test_bus.py` green; Escape and window-close still shut down cleanly.

### Phase 1 — SerialService dual-write
- **Goal:** packets flow onto the bus *and* still through `update_all` — nothing consumes the bus yet.
- **Tasks:** add `ui/core/serial_service.py` wrapping `TelemetryReceiver`; in `ComMonitorController.update_ui`, enqueue `tele/<field>` + `packet/raw` samples to the bus queue **and** keep calling `self.ui_manager.update_all(packet)`.
- **Files:** `ui/core/serial_service.py` (new), `ui/windows/com_monitor_controller.py`.
- **Commit:** "SerialService publishes packets to bus (dual-write)."
- **Verify:** attach a debug subscriber that logs `tele/battery_voltage`; confirm it fires on the pump thread (not the serial thread) and the live UI is unchanged.

### Phase 2 — MissionClock + derived channels
- **Goal:** extract mission time and central guards.
- **Tasks:** add `ui/core/mission_clock.py` from `UIManager._mission_start`; compute and publish `gps/fix` (both lat+lon), `flight/armed` (edge), `mission/reset`, and stamp `Sample.mission_t` centrally.
- **Files:** `ui/core/mission_clock.py` (new), `serial_service.py`, `ui_manager.py`.
- **Commit:** "Extract MissionClock + publish derived gps/flight/mission channels."
- **Verify:** debug subscribers confirm `gps/fix` fires only when both fields present and `flight/armed` toggles on the OFF→ON edge exactly once.

### Phase 3 — Prove the pattern on LocationWindow
- **Goal:** first real widget migrated to `Widget` + bus, single-instance.
- **Tasks:** convert `LocationWindow` to a `Widget` subclass (`build`, `subscribe("gps/fix", …)`, `destroy`); construct it via the factory with `iid="main"`; delete its line from `UIManager.update_gps`.
- **Files:** `ui/core/widget_base.py`, `ui/core/registry.py` (new), `ui/windows/location_window.py`, `ui_manager.py`.
- **Commit:** "Migrate LocationWindow to Widget/bus pattern."
- **Verify:** GPS table still updates live; `tests/test_widget_lifecycle.py` proves mount → tag-unique → destroy → unsubscribe headless.

### Phase 4 — Convert the collision-blocked leaves
- **Goal:** migrate the low-risk, tag-collision widgets one commit each.
- **Tasks:** convert **Battery, Connection, Subsystem, LastPacket** to `Widget` subclasses with `self.tag()` and bus subscriptions; move each field's delete out of `update_all` as it moves. Pass `iid="main"` so the single-instance layout still renders in the old hardcoded columns.
- **Files:** the four `ui/windows/*.py`, `ui_manager.py`.
- **Commit (×4):** one per widget, e.g. "Migrate BatteryWindow to Widget/bus."
- **Verify:** after each, the corresponding panel updates live from the bus and no longer from `update_all`; app still runs.

### Phase 5 — Plots, TimeWindow, ComMonitor
- **Goal:** the hard state/classmethod conversions and re-enabling the packet table.
- **Tasks:** convert **Altitude** and **Acceleration** (class-state → `__init__`, `@classmethod` → instance, register instances for `plot/*` topics); replace `PlotCoordinator` with bus topics `plot/stop|resume|reset`. Convert **TimeWindow**. Re-enable **ComMonitor** via `packet/raw` (uncomment its wiring).
- **Files:** `altitude_window.py`, `acceleration_window.py`, `plot_coordinator.py` (remove), `time_window.py`, `com_monitor.py`, `ui_manager.py`.
- **Commit:** grouped per widget.
- **Verify:** Stop/Resume/Reset buttons control only their own plot; arm transition resets plots via `mission/reset`; ComMonitor table populates.

### Phase 6 — Delete dead code
- **Goal:** remove the deprecated gauge.
- **Tasks:** delete `ui/windows/accelerometer_window_deprecated.py`.
- **Commit:** "Remove deprecated AccelerometerWindow (dead code)."
- **Verify:** grep confirms zero references; app runs.

### Phase 7 — Registry + services + Commands decoupling
- **Goal:** widget factory + break `CommandsWindow`'s hard controller reference.
- **Tasks:** finish `registry.py` (`register`, `create`, `meta()`), `serial_service` command send-by-`iid`; convert `CommandsWindow` and `ComMonitorController` to `Widget`s using `ctx.serial_service`; add `serial/status` publishing + single-serial-owner guard.
- **Files:** `ui/core/registry.py`, `serial_service.py`, `commands_window.py`, `com_monitor_controller.py`.
- **Commit:** "Add widget registry; route commands through SerialService."
- **Verify:** commands still send when connected; two `com_ctl` instances rejected by the guard.

### Phase 8 — Grid engine (spike-gated) + parity dashboard
- **Goal:** replace the hardcoded layout with the grid.
- **Tasks:** **Week-1 spike first** — throwaway proof that nested scrollable `child_window` `pos=` behaves under scroll/DPI/resize. Then build `grid_math.py` (+ `tests/test_grid_math.py`), `grid_engine.py`, `layout_store.py`, `dashboards/flight-default.json`. Behind a feature flag, make the Flight-Data tab call `engine.load(default)`. Keep the old `_draw_flight_data_ui` until visual parity is confirmed, **then delete it and the 11 `update_*` methods + `handlers` dict**.
- **Files:** `ui/layout/*` (new), `dashboards/flight-default.json` (new), `ui_manager.py`.
- **Commit:** "Grid layout engine + flight-default dashboard (behind flag)" → then "Remove hardcoded Flight-Data layout."
- **Verify:** side-by-side with the old layout; `pytest tests/test_grid_math.py`; resize the viewport and confirm fluid columns; place a second Battery from JSON and confirm both update independently.

### Phase 9 — Settings via bus
- **Goal:** live settings refresh, remove the hand-wired callback.
- **Tasks:** convert `SettingsWindow` (mark `SINGLETON`, `self.tag()`); on save, publish `settings/*/changed`; Battery/Connection/FlightEvents/Commands self-refresh via `on_config_changed`; delete `UIManager._on_settings_saved`.
- **Files:** `settings_window.py`, `settings_manager` (unchanged core), the four consumer widgets, `ui_manager.py`.
- **Commit:** "Route settings saves through settings/*/changed bus events."
- **Verify:** edit a battery threshold, Save — the panel and any live FlightEvents/Commands refresh **without a UI rebuild** (fixes the current stale-refresh bug).

### Phase 10 — Edit mode + fallback + plot collapse
- **Goal:** interactive dashboards and final cleanups.
- **Tasks:** Phase-B `edit_overlay.py` (Add-Widget palette from `registry.meta()`, per-cell ✕, numeric property panel, Save); build `dock_engine.py` **only if the spike failed**; collapse Altitude + Acceleration into one generic **dual-series time-plot** widget parameterized by two field names (Altitude/Acceleration become saved config instances).
- **Files:** `ui/layout/edit_overlay.py`, optional `dock_engine.py`, a new `timeseries_window.py`.
- **Commit:** grouped.
- **Verify:** add/remove widgets at runtime, Save, restart, layout restores with stable `iid`s; the generic plot renders both an altitude and an acceleration instance from config.

---

## 6. Risks & mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| DPG absolute `pos=` on nested scrollable `child_window` misbehaves under scroll/DPI/resize | Grid engine unusable — the single biggest unknown | **Week-1 throwaway spike gates Phase 8.** `LayoutEngine` Protocol lets us drop in `dock_engine.py` (`configure_app(docking, docking_space)`, verified DPG 2.2) with **zero widget edits** if the spike fails. |
| Core-loop swap (`start_dearpygui` → manual pump) breaks Escape/exit/shutdown | App won't close cleanly, thread leaks | Phase 0 in isolation with explicit re-verification of the Escape handler, exit callback, and `shutdown()` idempotency; keep map/serial thread joins. Alternative: drain the queue from a `set_frame_callback` (lower blast radius) — see open questions. |
| Cross-thread `dpg.set_value` from serial thread (current real bug) | Sporadic crashes/corruption once instances multiply | Enforced by design: publishers **only enqueue**; all `dpg.*` calls happen in `pump()` on the main thread. |
| Un-classmethod-ing Altitude/Acceleration touches shared state subtly | Two plots merge/corrupt data | Convert one plot per commit; unit-test that two instances keep independent series headless. |
| `settings.set_section` whole-section replace → last-save-wins clobber | Two settings editors race, lose edits | Keep `SettingsWindow` `SINGLETON` for MVP (registry refuses a 2nd instance); per-section saves are the follow-up. |
| Two serial owners contend for one COM port (uncaught `SerialException` from a DPG callback) | Crash in a button callback | Single-serial-owner guard in the registry; wrap `start()` so an already-open port raises a caught, widget-local error. |
| High-rate packet bursts outpace frame rate | Queue backlog / lag | Decide drain-all vs. coalesce-latest-per-field per frame (open question); start with drain-all + a bounded queue. |
| Map instances leak `ThreadPoolExecutor` + traffic thread if not torn down | Resource leak on add/remove | Registry tracks every live widget and calls `destroy()`/`shutdown()` on teardown; grid never orphans a root. |
| Non-deterministic `itertools.count()` iids on reload | Saved state keyed to old ids breaks | `iid` is a persisted uuid minted at drop-time, always passed back to the constructor; drop `_id_counter` once every caller passes `iid`. |

## 7. Open questions for the team

1. **Grid vs. docking for v1:** is a true snap-to-cell grid a hard requirement for the first flight, or is free-form docking acceptable if the spike is shaky? Willing to ship the dock engine as the release layout and treat the fixed grid as a follow-up?
2. **Fixed vs. variable row height:** MapView wants ~600px (many rows) while Battery wants ~200px. Accept a uniform `cell_h` with widgets spanning multiple rows, or do you need variable row heights (harder grid math)?
3. **Marshalling mechanism:** manual pump loop (more control, must re-verify Escape/exit/shutdown) vs. draining the queue from a `set_frame_callback` (lower blast radius)? This is the riskiest core-loop decision.
4. **Runtime editing depth:** is numeric/JSON snap-to-cell placement (Phase A + property panel) enough, or is mouse-drag required for v1? Mouse-drag in DPG is hand-rolled and can double the editor effort.
5. **Multi-instance serial ownership:** should the registry forbid a second serial-owner instance outright (single-serial-owner guard)?
6. **SettingsWindow scope:** keep it `SINGLETON` for MVP (because `set_section` clobbers), and defer per-section saves that would make it safely multi-instance?
7. **Protocol investment:** build the `LayoutEngine` Protocol + dock adapter up front as a hedge (~20-line interface + real adapter work), or commit to the grid engine only and accept the rewrite risk?
8. **Back-pressure policy:** drain-all-per-frame vs. coalesce-latest-per-field when packet bursts outpace the frame rate?

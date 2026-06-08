# Karel 2010 — Architecture & Developer Guide

This document describes the internal architecture of `karel2010.py`, the single-file Python port of Karel 2010.

---

## Overview

Karel 2010 is a **single-file tkinter application** (`karel2010.py`, ~2500 lines). It requires Python 3.8+ and optionally numpy + Pillow for Z-buffer rendering.

### Historical context

The original Karel 2010 was written in Delphi with OpenGL (GLScene) for Windows 9x/XP (Mgr. Michal Zeman, Comenius University Bratislava, 2004). The Python port reproduces the core functionality:

- 3D perspective rendering of the room
- Full Karel language interpreter (lexer → parser → AST → interpreter)
- World settings editor with restrictions
- Mission / goal condition system
- XML world file format (`.karxml`)

---

## Module structure

All code lives in `karel2010.py`. The logical modules are:

```
karel2010.py
│
├── Goal condition classes          GoalKarelPos, GoalCellState, GoalSnapshot
├── WorldSettings                   Camera, inventory limits, disabled commands
├── World                           Grid model + Karel state + XML I/O
│
├── Lexer / Parser / Interpreter    tokenize(), Parser, KarelInterpreter
│
├── 3D renderer                     Camera, world_faces(), World3D (tk.Canvas)
│
├── UI panels
│   ├── NavigatorPanel              Camera presets + inventory display
│   ├── ProgramPanel                Syntax-highlighted editor + command list
│   └── ControlPanel                Direct control buttons + command entry
│
├── Dialogs
│   ├── WorldSettingsDialog         6-tab world editor
│   ├── GoalConditionDialog         Sub-dialog for adding mission conditions
│   └── MissionResultDialog         Success/failure popup
│
└── App (tk.Tk)                     Main window, menu, toolbar, threading
```

---

## Data model

### `World`

```python
class World:
    width: int
    height: int
    walls:      list[list[set[str]]]   # walls[y][x] = {'N','E','S','W'}
    bricks:     list[list[int]]         # small bricks at each tile
    big_bricks: list[list[int]]         # big bricks at each tile
    marks:      list[list[bool]]        # mark present at each tile

    karel_x: int
    karel_y: int
    karel_dir: Direction                # NORTH/EAST/SOUTH/WEST

    settings: WorldSettings

    # Runtime inventory (reset on each new run)
    _bricks_left:     int              # -1 = unlimited
    _big_bricks_left: int
    _marks_left:      int

    # Metadata
    title:        str
    intro_html:   str
    success_html: str
    failure_html: str
    program_text: str
    next_level:   str
    prev_level:   str

    # Mission
    goal_conditions: list              # GoalKarelPos | GoalCellState | GoalSnapshot
    mission_eval:    str               # 'on_finish' | 'on_step'
    mission_reset_on_failure: bool
```

Coordinate system: `x=0` at left, `y=0` at bottom.

The height of a tile in "small brick units":
```python
def _height(self, x, y):
    return self.bricks[y][x] + self.big_bricks[y][x] * World.BIG_BRICK_UNITS
    # BIG_BRICK_UNITS = 5
```

### `WorldSettings`

```python
class WorldSettings:
    prog_lang:         str   # 'sk' | 'en' | 'en_pattis' | 'de' | 'fr' | 'it' | 'es'  (per-world)
    brick_limit:       int   # -1 = unlimited
    big_brick_limit:   int
    mark_limit:        int
    disabled_cmds:     set   # token strings, e.g. {'BACK', 'DROP', 'BRICK'}
    disable_procedure: bool
    camera_locked:     bool
    camera_az:         float  # radians
    camera_el:         float
    camera_dist:       float
    max_climb:         int   # max upward step (default 1)
    max_drop:          int   # max downward step (-1 = unlimited)
    max_steps:         int   # forward/back budget from reset (-1 = unlimited)
    max_turns:         int   # turn budget from reset (-1 = unlimited)
    max_brick_height:  int   # max stack height to add bricks (kvader=5; -1 = unlimited)
```

### Movement budget

`World._steps_used` / `_turns_used` increment on each successful move/turn and reset
in `reset_inventory()` (called by `_reset_world`). When `max_steps`/`max_turns` are
exceeded, `World` raises `KarelBudget('steps'|'turns')`:
- During a program run → `interpreter.on_budget` → `App._on_budget` stops the program
  and shows `BudgetDialog` (OK / Reset).
- Direct control (buttons + typed) → caught in `ControlPanel._do` → same dialog.
- `run()` re-raises `KarelBudget` if `on_budget is None`, so the throwaway interpreter
  used for typed commands propagates it out to `_do`.

`max_climb` / `max_drop` / `max_brick_height` are physical limits — the command is
silently skipped (no dialog), consistent with hitting a wall or empty inventory.

---

## Karel language pipeline

```
source text
    │
    ▼
tokenize(src)           → list[Tok]
    │                      each Tok has .t (token type), .v (value), .ln (line)
    ▼
Parser(tokens).parse()  → ProgN (AST root)
    │
    ▼
KarelInterpreter.run(prog)   runs on a daemon thread
    │   calls on_step after each command
    │   calls on_finish / on_error when done
    ▼
World methods are called directly (move_forward, drop_brick, etc.)
```

### Token types

```python
CMD_T   = {'FORWARD','BACK','LEFT','RIGHT','DROP','PICK','DROP_BIG','MARK','CLEAR','SLOWLY','QUICKLY'}
COND_T  = {'WALL','BRICK','FREE','SIGN','TRUE','FALSE'}
CLOSE_T = {'END','END_REPEAT','END_WHILE','END_IF'}
# Plus: BEGIN, PROCEDURE, REPEAT, TIMES, WHILE, NOT, AND, OR, DO, IF, THEN, ELSE,
#       LPAREN '(' , RPAREN ')' , NUM, ID
```

The `KW` dict maps every keyword variant to its token type:
```python
KW = {'dopredu': 'FORWARD', 'forward': 'FORWARD', 'vlavo': 'LEFT', ...}
```

`_KW_REVERSE` maps token types back to keyword lists (used by the syntax highlighter).

### AST nodes

```python
ProgN(procedures, main_stmts)
CmdN(cmd, line)          # FORWARD, LEFT, etc.
CallN(name, line)        # user procedure call
RepN(count, body, line)  # repeat N times
WhileN(cond, body, line)
IfN(cond, then_body, else_body, line)
CondN(cond_type, negated)  # atomic condition
NotN(child)                # not <expr>
AndN(left, right)          # <expr> and <expr>
OrN(left, right)           # <expr> or <expr>
```

### Condition expressions (logical connectives)

Conditions in `if`/`while` are expressions with precedence **NOT > AND > OR**;
parentheses `( )` override it. The parser uses recursive descent:

```
cond     := or_expr
or_expr  := and_expr (OR and_expr)*
and_expr := not_expr (AND not_expr)*
not_expr := NOT not_expr | atom
atom     := '(' or_expr ')' | COND_T
```

`KarelInterpreter._ev(node)` evaluates recursively, short-circuiting via Python
`and`/`or` (atoms have no side effects). Keywords per language: SK `a`/`alebo`,
EN `and`/`or`, DE `und`/`oder`, FR `et`/`ou`, IT `e`/`o`, ES `y`/`o`.

### Interpreter

`KarelInterpreter._cmd(node)`:
1. Checks `disabled_cmds` — raises `KarelError` if the command is forbidden.
2. Calls the corresponding `World` method.
3. Calls `on_step()` callback.
4. Sleeps `self.delay` seconds.

Recursion limit: `MAX_D = 500`.

---

## Threading model

The interpreter runs on a **daemon thread** to avoid blocking the UI.

```python
threading.Thread(target=it.run, args=(prog,), daemon=True).start()
```

Callbacks (`on_finish`, `on_error`) are wrapped with `_safe()`:

```python
def _safe(fn):
    return lambda *a: self._canvas.after(0, lambda: fn(*a))
```

This schedules the callback on the main thread via `tk.after(0, ...)`, which is required on Windows where calling tkinter from a non-main thread silently fails.

`on_step` renders the canvas and updates the inventory display, also scheduled via `after(0, ...)`.

The `_running` flag guards re-entry:
```python
if self._running: return   # don't start a second interpreter
```

---

## 3D renderer

### Z-buffer (numpy path, `_ZBUF = True`)

```
world_faces(w)          →  list of (verts_3d, color, outline, outline_color, normal, priority)
Camera.project(pts3d)   →  screen coords + depth (rz)
Z-buffer compositing    →  numpy array of shape (H, W, 3)
PIL Image + ImageTk     →  displayed on tk.Canvas
```

Back-face culling: faces with `normal` pointing away from the camera are skipped. This correctly hides the exterior of border walls while showing the interior.

Priority system:
- `prio=0` — floor tiles (always rendered first, behind all 3D objects)
- `prio=1` — walls, bricks, Karel (sorted by mean Z depth, painter's algorithm fallback)

### Painter fallback (no numpy)

When numpy is unavailable, faces are sorted by mean Z depth and drawn as `tk.Canvas` polygons. Less accurate but functional.

### Camera

```python
class Camera:
    az:    float   # azimuth (radians)
    el:    float   # elevation (radians)
    dist:  float   # distance from target
    fov:   float   # field of view (degrees)
    target: [x, y, z]  # look-at point
```

The camera uses a spherical coordinate system. Mouse drag events modify `az`, `el`, `dist` and trigger re-render.

---

## UI panels

### `NavigatorPanel`

- Camera preset buttons (8 directions + top)
- Axis display (small 3D widget showing current orientation)
- Inventory display: three `StringVar` labels updated by `update_inventory(world)`
- `set_camera_locked(locked)` disables/enables preset buttons

### `ProgramPanel`

- `tk.Text` editor with the `highlight()` function applied on every keystroke
- Sidebar tree of command categories (click inserts a template)
- `_disabled_cmds: set` — CMD tokens forbidden in this world (from `world.settings.disabled_cmds`)
- `_disable_procedure: bool` — whether procedure definition is forbidden
- `on_procs_update` callback fires whenever parsed procedures change

Key methods:
```python
set_prog_lang(lang)          # _switch_prog_lang + _refresh_cmds_list + _build_filter_tree
set_disabled_cmds(cmds, …)  # updates _disabled_cmds + highlight + _refresh_cmds_list
_effective_disabled()        # returns _disabled_cmds | _LANG_DISABLED[current_prog_lang]
                             # (includes COND tokens like BRICK that have no checkbox)
_refresh_cmds_list()         # refills Listbox using _cmds_list(_effective_disabled())
_on_filter(e)                # fills Listbox for selected filter category, uses _effective_disabled()
```

`_cmds_list(disabled)` and `_cmds_conds(disabled)` both accept an optional set of disabled tokens
and filter them out of the returned list — used by both `_refresh_cmds_list()` and `_on_filter()`.

The `highlight()` function:
```python
def highlight(tw, disabled_cmds=None, disable_procedure=False):
    # Clears all tags, tokenizes text, re-applies colour tags
    # 'disabled' tag = red background for forbidden commands
    # Uses _KW_REVERSE to find all word variants of each token
```

### `WorldSettingsDialog`

- 6 tabs: Language, World, Inventory, Commands, Conditions, Camera
- Commands tab: checkboxes for each CMD token (`_cmd_vars`, `_cmd_cbs`)
  - Only CMD tokens have checkboxes; COND tokens (like BRICK) are controlled via `DISABLED` directive only
- `_on_prog_lang_changed()`: when prog_lang combobox changes —
  1. Updates checkbox labels to primary word of new lang
  2. If new lang has `_LANG_DISABLED` entry: auto-checks those tokens and hides their checkboxes (`grid_remove()`); hides entire group frame if all its tokens are disabled
  3. Switching back to a normal lang restores all checkboxes (`grid()`)

### `ControlPanel`

- Movement / action buttons, each calls `_do(cmd_key)`
- `_do()` checks `disabled_cmds` before calling the `World` method
- `apply_restrictions(settings)` grey-outs forbidden command buttons
- "Príkazovo" tab: `tk.Entry` + `Enter` binding, calls `KarelInterpreter` synchronously
- `_CMD_TO_TOKEN` maps button keys to token names for restriction checking

---

## World file I/O

### Save: `World.to_xml()`

Builds an `xml.etree.ElementTree` tree, serialises to string, pretty-prints via `xml.dom.minidom`.

### Load: `World.from_xml(path_or_string)`

Accepts a file path or an XML string. Parses with `ET.parse()` or `ET.fromstring()`. Handles missing elements gracefully (defaults to empty/None).

### JSON support (legacy)

`World.to_json()` and `World.from_json()` provide basic JSON serialisation (no settings, no mission). Used by the old `.karjson` format.

---

## Mission system

### Goal condition classes

```python
GoalKarelPos.check(world)    →  bool
GoalCellState.check(world)   →  bool
GoalSnapshot.check(world)    →  bool
```

Each class also implements:
- `describe() → str` — human-readable label for the UI list
- `to_xml_el() → ET.Element` — serialisation
- `from_xml_el(el) → GoalCondition` — deserialisation (static)

### Evaluation flow

```
on_finish / on_step callback
    │
    ▼
App._check_mission()             (on_finish mode)
App._check_mission_step()        (on_step mode)
    │
    ▼
all(c.check(world) for c in world.goal_conditions)
    │
    ├─ True  →  MissionResultDialog(success=True, html=success_html)
    │
    └─ False →  if on_finish:
                    MissionResultDialog(success=False, html=failure_html)
                    if reset_on_failure: App._reset_world()
                if on_step:
                    (silent — world still evolving)
```

---

## Language system

### Two independent language settings

| Setting | Stored in | Controls |
|---------|-----------|---------|
| `ui_lang` | `karel.ini [ui] lang` | Menu, toolbar, labels, status messages, **action button display labels** |
| `prog_lang` | `.karxml <settings><prog_lang>` | Karel commands sent to interpreter, commands list in editor |

The split is intentional:
- A teacher sets `ui_lang` once globally (e.g. Slovak). All UI text appears in that language.
- A teacher sets `prog_lang` per world (e.g. English). Students write code in that language.
- Action buttons show **display labels** (GUI lang: "Polož tehlu") but send **commands** (prog lang: "drop" or "poloz") to Karel.

### Interpreter keyword files (`lang/interpreter/*.lng`)

```
# Format: TOKEN = primary_word  alias1  alias2 ...
# Special directives (no TOKEN mapping, processed separately):
NAME     = English (Pattis)       # display name in prog_lang dropdown
DISABLED = BACK RIGHT DROP BRICK  # tokens auto-disabled when this lang is selected

FORWARD  = move  forward  moveforward
LEFT     = turnleft  left
MARK     = putbeeper  put_beeper  mark
```

- **All `.lng` files are loaded and merged** into the global `KW` dict at startup via `_load_all_interpreter_langs()`.
- The interpreter therefore **accepts every language simultaneously** — a student can always type `forward` even in a Slovak-configured world.
- `_LANG_PRIMARY[lang][TOKEN]` = canonical (first) word for that language.
- `_LANG_DISABLED[lang]` = set of TOKEN names that are auto-disabled when this lang is selected (from `DISABLED` directive). May include both CMD tokens and COND tokens (e.g. `BRICK`).
- `_LANG_NAME[lang]` = display name for the prog_lang dropdown (from `NAME` directive). If absent, the language code is used as fallback.
- `_primary_kw(token, lang)` returns the canonical word with EN fallback.
- **Adding a new language** (ES, PL, …) = create `lang/interpreter/xx.lng` with the same TOKEN names and that language's keywords. No code changes needed.

### Currently available languages

| Code | UI (`lang/xx.ini`) | Interpreter (`lang/interpreter/xx.lng`) |
|------|--------------------|-----------------------------------------|
| `sk` | Slovenčina | ✓ |
| `en` | English | ✓ |
| `de` | Deutsch | ✓ |
| `fr` | Français | ✓ |
| `it` | Italiano | ✓ |
| `es` | Español | ✓ |
| `en_pattis` | — (NAME directive in .lng) | ✓ (Pattis mode) |

### Adding a new language

To add e.g. Polish (`pl`):

1. Create `lang/interpreter/pl.lng` with Polish keyword translations.
2. Create `lang/pl.ini` with a `[meta] name = Polski` section plus all other sections (including `[role_dialog]`).
3. Both dropdowns (GUI language in Global Settings, prog language in World Settings) will automatically include the new language on next startup — **no code changes needed**.

> **Important:** Do NOT put `.ini` files for prog-only languages (like `en_pattis`) into `lang/` — `_available_ui_langs()` reads all `lang/*.ini` and would show them in the GUI language dropdown. Use the `NAME` directive in the `.lng` file instead.

### UI string files (`lang/sk.ini`, `lang/en.ini`, `lang/es.ini`, …)

Each file starts with a `[meta]` section used for the language picker display name:

```ini
[meta]
name = Slovenčina
```

INI files with sections:

| Section | Purpose |
|---------|---------|
| `[menu]` | Menu item labels |
| `[toolbar]` | Toolbar button text |
| `[nav]` | Navigator panel labels |
| `[control]` | Direct control panel labels |
| `[status]` | Status bar messages |
| `[action_labels]` | Display text on Karel action buttons (DROP, PICK, …) |
| `[world_settings]` | All labels in WorldSettingsDialog (6 tabs) |
| `[goal_condition]` | All labels in GoalConditionDialog ("Add condition") |
| `[role_dialog]` | RoleDialog — title, role labels, descriptions, buttons |

Loaded by `_load_ui_lang(lang)` into `_ui_strings` flat dict (key = `section.key`).

Available languages are discovered at runtime by `_available_ui_langs()` (scans `lang/*.ini`) and `_available_prog_langs()` (scans `lang/interpreter/*.lng`). The language pickers are `ttk.Combobox` widgets populated dynamically — adding a new language file is sufficient.

### Action buttons

```
_ACTION_TOKEN = {'drop': 'DROP', 'drop_big': 'DROP_BIG', ...}

_prog_btn(action) → (label, command)
  label   = _ui_strings['action_labels.{token}']   # GUI lang — e.g. "Polož tehlu"
  command = _primary_kw(TOKEN, _current_prog_lang)  # prog lang — e.g. "poloz" or "drop"
```

- `_switch_prog_lang(lang)` sets `_current_prog_lang` (no longer loads action labels).
- `ControlPanel.set_prog_lang(lang)` calls `_switch_prog_lang` then rebuilds buttons.
- `ControlPanel.retranslate()` also calls `_rebuild_act_buttons()` so GUI lang change
  immediately updates button display labels.
- `_act_btn_cmds` tracks which cmd keys in `_btn_refs` belong to action buttons (as
  opposed to fixed movement arrows). Keys are cleaned up before each rebuild to avoid
  stale references to destroyed widgets.
- Command restriction checks in `_do()` and `apply_restrictions()` use `KW.get(cmd)`
  (all languages) instead of a hardcoded Slovak-only dict.

### Fallback chain

1. `lang/interpreter/{lang}.lng` → if missing, skips that language
2. `lang/{lang}.ini` → if missing, falls back to `lang/sk.ini`
3. `_fallback_bkw()` → hardcoded SK+EN if `lang/interpreter/` is missing entirely
4. `_T(key)` → returns the key itself if translation is missing

---

## User role system

### Configuration file

```
karel.ini          (next to karel2010.py)
```

```ini
[user]
role = teacher     # student | teacher | admin
```

Read at startup via `_ini_read_role()`. Written via `_ini_write_role()`. Writable check via `_ini_is_writable()` (delegates to `os.access(W_OK)`).

### Role enforcement

`App._role` holds the current role string. `App._apply_role_to_ui()` is called once after `_build_ui()` and again whenever the role changes. It uses `Menu.entryconfigure(index, state=...)` to enable/disable individual menu entries.

| Role | Disabled menu items |
|------|---------------------|
| `student` | Edit → Save world, Edit → Save world as XML, Edit → ⚙ World Settings |
| `teacher` | *(none)* |
| `admin` | *(none — reserved for future global settings)* |

### Changing the role

`App._change_role()` — called from **Settings → Change role...**:
1. Checks `_ini_is_writable()` — shows a warning and returns if not.
2. Opens `RoleDialog` (a `Toplevel` with radio buttons for each role). All strings translated via `_T('role_dialog.*')`.
3. On confirmation writes the new role to `karel.ini` and calls `_apply_role_to_ui()`.

Security is purely OS-level: set the file-system permissions on `karel.ini` to read-only for student accounts.

---

## Key design decisions

### Runs from current position

`App._run()` does **not** call `_reset_world()`. The program executes from wherever Karel currently is. The ↺ Reset button calls `_reset_world()` explicitly.

This allows workflows like:
1. Move Karel manually to an interesting position.
2. Run the program.
3. The program continues from that position.

### Inventory reset

`World.reset_inventory()` copies `settings.*_limit` → `_*_left`. This is called by `App._reset_world()`. It is **not** called by `_run()` — the inventory state persists across runs within a session.

### No implicit auto-reset on open

When a world is opened, `_reset_world()` is called once. Subsequently pressing Run does not reset.

---

## Adding a new command to the language

1. Add keyword variants to `_bkw()` in the `KW` dict:
   ```python
   ('JUMP', ['jump', 'skoc', 'skoč']),
   ```

2. Add the token to `CMD_T`:
   ```python
   CMD_T = {'FORWARD', ..., 'JUMP'}
   ```

3. Implement the `World` method:
   ```python
   def jump(self):
       ...
   ```

4. Handle it in `KarelInterpreter._cmd()`:
   ```python
   elif c == 'JUMP': w.jump()
   ```

5. Add a button to `ControlPanel` and map it in `_CMD_TO_TOKEN`.

6. The `highlight()` function picks up new tokens automatically via `_KW_REVERSE`.

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Python | 3.8+ | Runtime |
| tkinter | stdlib | GUI |
| xml.etree.ElementTree | stdlib | XML I/O |
| threading | stdlib | Interpreter thread |
| numpy | optional | Z-buffer rendering (fast path) |
| Pillow (PIL) | optional | Image compositing for numpy renderer |

Install optional dependencies:
```
pip install pillow numpy
```

Without numpy/Pillow, the app falls back to a painter-algorithm renderer using native `tk.Canvas` polygons.

---

## File listing

| File | Description |
|------|-------------|
| `karel2010.py` | Entire application (~2500 lines) |
| `kar_to_xml.py` | Converts binary `.kar` worlds to `.karxml` |
| `*.karxml` | Predefined worlds (5 converted from original binary format) |
| `*.prg` | Sample Karel programs |
| `Spusti Karel.bat` | Windows launcher |
| `docs/` | This documentation |

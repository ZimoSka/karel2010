# Karel 2010 – Claude pracovné pravidlá a architektúra

---

## ⚠️ Pravidlo: Pred vytvorením nového súboru

Pred vytvorením akéhokoľvek nového súboru do existujúceho priečinka vždy najprv
prečítať VŠETKY miesta v kóde kde sa daný priečinok číta (loadery, glob/listdir
volania) — a až potom rozhodnúť o umiestnení súboru. Nikdy nepredpokladať — overiť kódom.

**Príklad chyby:** `lang/en_pattis.ini` skončil v `lang/` → objavil sa v GUI jazykovom
dropdowne, lebo `_available_ui_langs()` číta všetky `lang/*.ini`. Riešenie: názov
jazyka uložiť priamo do `.lng` súboru cez `NAME` direktívu.

---

## Celková architektúra

**Jedna Python súbor:** `karel2010.py` (~3000 riadkov), tkinter GUI.

```
karel2010.py
├── Dátový model         World, WorldSettings, Direction
├── Goal podmienky       GoalKarelPos, GoalCellState, GoalSnapshot
├── Jazykový systém      _load_all_interpreter_langs(), KW, _LANG_PRIMARY, _LANG_DISABLED, _LANG_NAME
├── Lexer/Parser/AST     tokenize(), Parser, ProgN/CmdN/RepN/WhileN/IfN/CondN
├── Interpreter          KarelInterpreter (beží na daemon threade)
├── 3D renderer          Camera, world_faces(), World3D (tk.Canvas + numpy/PIL)
├── UI panely            NavigatorPanel, ProgramPanel, ControlPanel
├── Dialógy              WorldSettingsDialog, GoalConditionDialog, MissionResultDialog
└── App (tk.Tk)          Hlavné okno, menu, toolbar
```

---

## Dátový model

### `World`
```python
world.width, world.height          # rozmer mriežky
world.bricks[y][x]      : int      # malé tehly (zelené, stackujú sa na vrchu kvadera)
world.big_bricks[y][x]  : int      # kvader/veľká tehla — max 1 per tile (hnedý, =5 malých výškou)
world.marks[y][x]       : bool     # značka pod políčkom
world.walls[y][x]       : set      # {'N','E','S','W'} — steny
world.karel_x, world.karel_y, world.karel_dir  # pozícia a smer Karela
world.settings          : WorldSettings
world.goal_conditions   : list     # GoalKarelPos | GoalCellState | GoalSnapshot
world.mission_eval      : str      # 'on_finish' | 'on_step'
```
**Súradnice:** x=0 vľavo, y=0 dole.

### `WorldSettings`
```python
settings.brick_limit, big_brick_limit, mark_limit  : int  # -1 = neobmedzené
settings.disabled_cmds    : set   # tokeny napr. {'BACK', 'RIGHT'}
settings.disable_procedure: bool
settings.camera_locked    : bool
settings.prog_lang        : str   # 'sk', 'en', 'en_pattis', 'de', ...  — ukladá sa per-svet do .karxml
settings.max_climb        : int   # max výška skoku (default 1)
```

### Sémantika príkazov
- `drop_brick()` / `pick_brick()` — operuje na políčku **PRED** Karelom (`_front()`)
- `drop_big_brick()` — ukladá kvader pred Karelom; max 1 per tile; `check_wall()` vráti True pre kvader
- `pick_big_brick()` / `pick_any_brick()` — len GUI (nie programové); `pick_any_brick` = malá tehla → kvader fallback
- `mark()` / `clear()` — operuje na políčku **POD** Karelom (kde stojí)
- `move_forward()` — skontroluje stenu aj výšku tehiel (`max_climb`)
- `check_wall()` → True ak stena ALEBO kvader pred Karelom
- Rendering: kvader vždy na z=0 (spodok), malé tehly na vrchu kvadera (base_z = big_bricks * BIG_H)

---

## Jazykový systém (KRITICKÉ)

### Dve nezávislé jazykové nastavenia
| Nastavenie | Uloženie | Riadi |
|---|---|---|
| `ui_lang` | `karel.ini [ui] lang` | GUI texty, menu, tlačidlá, hlášky |
| `prog_lang` | `.karxml <settings><prog_lang>` | Kľúčové slová Karlovho jazyka (per-svet) |

### Globálne premenné jazykového systému
```python
KW: dict             # word.lower() → TOKEN  (všetky jazyky naraz, napr. 'dopredu'→'FORWARD')
_LANG_PRIMARY: dict  # lang_code → {TOKEN: primary_word}  (kanonické slovo pre jazyk)
_LANG_DISABLED: dict # lang_code → set of TOKEN names disabled by default  (z DISABLED direktívy)
_LANG_NAME: dict     # lang_code → display name  (z NAME direktívy v .lng)
_ui_strings: dict    # sekcia.kluč → text  (z lang/{ui_lang}.ini)
_current_prog_lang: str  # aktuálne nastavený prog_lang
```

### Súbory jazykového systému
```
lang/
├── sk.ini, en.ini, de.ini, fr.ini, it.ini, es.ini   ← GUI texty (menu, toolbar, dialógy, role_dialog)
│                                                       NEMIEŠAŤ s prog jazykmi — číta _available_ui_langs()
└── interpreter/
    ├── sk.lng, en.lng, de.lng, fr.lng, it.lng, es.lng   ← Karel kľúčové slová
    └── en_pattis.lng                                     ← Pattis štýl (s NAME + DISABLED direktívou)
```

### Formát `.lng` súboru
```
# Komentár
NAME       = English (Pattis)          ← voliteľné: zobrazený názov v dropdowne
DISABLED   = BACK RIGHT DROP DROP_BIG  ← voliteľné: tokeny auto-zakázané pri výbere jazyka
FORWARD    = move  forward  moveforward   ← TOKEN = primárne_slovo  alias1  alias2 ...
LEFT       = turnleft  left
```
- Prvé slovo = primárne (zobrazuje sa na tlačidlách a v šablónach)
- Všetky slová z VŠETKÝCH `.lng` súborov sa zlúčia do `KW` → interpreter akceptuje každý jazyk súčasne

### Dôležité funkcie
```python
_load_all_interpreter_langs()  # číta všetky .lng, plní KW, _LANG_PRIMARY, _LANG_DISABLED, _LANG_NAME
_available_ui_langs()          # číta lang/*.ini → zoznam pre GUI jazykový dropdown
_available_prog_langs()        # číta lang/interpreter/*.lng + _LANG_NAME → zoznam pre prog_lang dropdown
_primary_kw(token, lang)       # primárne slovo tokenu pre daný jazyk (EN fallback)
_T(key)                        # _ui_strings.get(key, key)  — preklad GUI textu
_switch_prog_lang(lang)        # nastaví _current_prog_lang
```

### Pattis režim (`en_pattis`)
- `putbeeper`/`pickbeeper` → **MARK/CLEAR** (kladie značku pod Karela, nie tehlu pred neho)
- `next_to_a_beeper` → **SIGN** (je značka pod Karelom?)
- `front_is_clear` → **FREE**, `front_is_blocked` → **WALL**
- DISABLED: BACK, RIGHT, DROP, DROP_BIG, PICK, BRICK, SLOWLY, QUICKLY

---

## Karel jazyk — pipeline

```
zdrojový text → tokenize() → list[Tok] → Parser.parse() → AST → KarelInterpreter.run()
```

### Token typy
```python
CMD_T  = {'FORWARD','BACK','LEFT','RIGHT','DROP','PICK','DROP_BIG','MARK','CLEAR','SLOWLY','QUICKLY'}
COND_T = {'WALL','BRICK','FREE','SIGN','TRUE','FALSE'}
```

### AST uzly
```python
ProgN(procedures, main_stmts)
CmdN(cmd, line)           # príkaz
CallN(name, line)          # volanie procedúry
RepN(count, body, line)    # opakuj N krat
WhileN(cond, body, line)
IfN(cond, then_body, else_body, line)
CondN(cond_type, negated)
```

### Interpreter
- Beží na **daemon thread** (`threading.Thread(..., daemon=True)`)
- Callbacky (`on_step`, `on_finish`, `on_error`) sa spúšťajú cez `canvas.after(0, ...)` — nutné pre tkinter na Windows
- `KarelInterpreter._cmd(node)` → skontroluje `disabled_cmds` → zavolá `World` metódu → `on_step()` → `sleep(delay)`
- `MAX_D = 500` — limit rekurzie

---

## UI panely

### `ProgramPanel`
- `tk.Text` editor so zvýrazňovaním syntaxe (`highlight()`)
- `_disabled_cmds: set` — zakázané CMD tokeny (z `world.settings.disabled_cmds`)
- `set_prog_lang(lang)` → `_switch_prog_lang()` + `_refresh_cmds_list()` + `_build_filter_tree()`
- `set_disabled_cmds(cmds)` → nastaví `_disabled_cmds` + `highlight()` + `_refresh_cmds_list()`
- `_effective_disabled()` → `_disabled_cmds | _LANG_DISABLED[current_prog_lang]` — kompletná množina vrátane COND tokenov (napr. `BRICK` v Pattis móde, ktorý nemá checkbox)
- `_cmds_list(disabled)` / `_cmds_conds(disabled)` — filtrujú zakázané tokeny zo zoznamu
- `_refresh_cmds_list()` — znovu naplní Listbox cez `_effective_disabled()`
- `_on_filter()` — filter strom (pohyb/štruktúry/podmienky/vlastné), používa `_effective_disabled()`

### `ControlPanel`
- Priame ovládacie tlačidlá volajú `_do(cmd_key)`
- `apply_restrictions(settings)` — sivé tlačidlá pre zakázané príkazy
- `set_prog_lang(lang)` → prebuduje akčné tlačidlá (DROP, PICK, MARK...)

### `WorldSettingsDialog`
- 6 záložiek: Jazyk, Svet, Zásoby, Príkazy, Podmienky, Pohľad
- `_on_prog_lang_changed()` — live update názvov príkazov + skrytie/zobrazenie checkboxov podľa `_LANG_DISABLED`; skryje celú skupinu ak sú všetky tokeny zakázané
- `_cmd_vars: dict` — tok → BooleanVar (iba CMD tokeny, nie COND tokeny ako BRICK)
- `_cmd_cbs: dict` — tok → Checkbutton widget
- COND tokeny (napr. BRICK) sa do `disabled_cmds` dostávajú iba cez `DISABLED` direktívu v `.lng` — nemajú checkbox v UI

---

## Súbor sveta `.karxml`

XML formát. Kľúčové časti:
```xml
<world width="..." height="...">
  <bricks>...</bricks>
  <bigbricks>...</bigbricks>
  <marks>...</marks>
  <walls>...</walls>
  <karel x="..." y="..." dir="NORTH"/>
  <settings>
    <prog_lang>en</prog_lang>
    <disabled_cmds>BACK,RIGHT</disabled_cmds>
    <brick_limit>10</brick_limit>
    ...
  </settings>
  <goal_conditions>...</goal_conditions>
</world>
```

---

## 3D renderer

- **Numpy path** (`_ZBUF=True`): Z-buffer + PIL → `ImageTk` na `tk.Canvas`
- **Fallback** (bez numpy): Painter's algorithm, `tk.Canvas` polygóny
- `world_faces(w)` → zoznam plôch s 3D vrcholmi, farbou, normálou, prioritou
- `Camera`: sférické súradnice (`az`, `el`, `dist`, `fov`, `target`)

---

## Konfigurácia

```
karel.ini  (vedľa karel2010.py)
[ui]
lang = sk          ← GUI jazyk
[user]
role = teacher     ← student | teacher | admin
```

Rola `student` skryje menu položky: Uložiť svet, Uložiť ako XML, Nastavenia sveta.

---

## Pridanie nového príkazu do jazyka

1. Pridať token do `.lng` súborov (napr. `lang/interpreter/sk.lng`)
2. Pridať token do `CMD_T`
3. Implementovať `World.xxx()` metódu
4. Pridať do `KarelInterpreter._cmd()`: `elif c == 'XXX': w.xxx()`
5. Pridať tlačidlo do `ControlPanel`
6. Zvýrazňovač (`highlight()`) a zoznam príkazov (`_cmds_list()`) to zachytia automaticky

## Pridanie nového GUI jazyka

1. Vytvoriť `lang/xx.ini` so sekciami: `[meta]`, `[menu]`, `[toolbar]`, `[nav]`, `[control]`, `[status]`, `[action_labels]`, `[world_settings]`, `[goal_condition]`, `[role_dialog]`
2. Vytvoriť `lang/interpreter/xx.lng` s Karel kľúčovými slovami
3. Oba dropdown sa automaticky doplnia — **žiadna zmena kódu nie je potrebná**

# Karel 2010 – Claude pracovné pravidlá a architektúra

---

## ⚠️ Pravidlo: /compact — nikdy bez povolenia

Príkaz `/compact` nespúšťať automaticky. Vždy sa opýtať používateľa a počkať na jeho súhlas.

**Auto-compact je vypnutý** v `~/.claude.json` cez `autoCompactEnabled: false`.
- POZOR: `settings.json` túto hodnotu ticho ignoruje — patrí do `~/.claude.json`.
- Prejaví sa až po reštarte Claude Code.
- Záloha pôvodného súboru: `~/.claude.json.bak`.

---

## ⚠️ Pravidlo: Dôležité informácie ukladať okamžite do súborov

Ak používateľ povie niečo čo si treba zapamätať (plán, rozhodnutie, pravidlo, architektúra):
- **Okamžite** to zapísať do príslušného `.md` súboru
- Plán vývoja → `PLAN.md`
- Architektonické rozhodnutia / pravidlá → `CLAUDE.md`
- Nikdy nespoliehať na pamäť konverzácie — compact/reset ju zmaže

---

## ⚠️ Pravidlo: Pred vytvorením nového súboru

Pred vytvorením akéhokoľvek nového súboru do existujúceho priečinka vždy najprv
prečítať VŠETKY miesta v kóde kde sa daný priečinok číta (loadery, glob/listdir
volania) — a až potom rozhodnúť o umiestnení súboru. Nikdy nepredpokladať — overiť kódom.

**Príklad chyby:** `lang/en_pattis.ini` skončil v `lang/` → objavil sa v GUI jazykovom
dropdowne, lebo `_available_ui_langs()` číta všetky `lang/*.ini`. Riešenie: názov
jazyka uložiť priamo do `.lng` súboru cez `NAME` direktívu.

---

## ⚠️ Pravidlo: Vždy push hneď po commit

```
git add ... && git commit -m "..." && git push
```

---

## Celková architektúra

**Jeden Python súbor:** `karel2010.py` (~3200 riadkov), tkinter GUI.

```
karel2010.py
├── Dátový model         World, WorldSettings, Direction
├── Goal podmienky       GoalCondition, evaluate_goals()
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
world.goal_conditions   : list[GoalCondition]
world.mission_reset_on_failure : bool
world.title, world.intro_html, world.success_html, world.failure_html : str
world.program_text      : str      # uložený Karel kód v súbore
```
**Súradnice:** x=0 vľavo, y=0 dole.

### `WorldSettings`
```python
settings.brick_limit, big_brick_limit, mark_limit  : int  # -1 = neobmedzené
settings.disabled_cmds    : set   # tokeny napr. {'BACK', 'RIGHT'}
settings.disable_procedure: bool
settings.camera_locked    : bool
settings.camera_az, camera_el, camera_dist : float  # uložený pohľad kamery
settings.prog_lang        : str   # 'sk', 'en', 'en_pattis', 'de', ...  — ukladá sa per-svet do .karxml
settings.max_climb        : int   # max výška výstupu nahor (default 1)
settings.max_drop         : int   # max zoskok nadol (-1 = ∞)
settings.max_steps        : int   # rozpočet krokov od resetu (-1 = ∞)
settings.max_turns        : int   # rozpočet otočení od resetu (-1 = ∞)
settings.max_brick_height : int   # max výška stohu na kladenie tehiel; kvader=5 (-1 = ∞)
```

### Pohybové obmedzenia (rozpočet)
- **Počítadlá** `world._steps_used` / `world._turns_used` — rastú pri úspešnom kroku/otočení, resetujú sa v `reset_inventory()` (volá `_reset_world`)
- **`max_steps`/`max_turns`** — pri vyčerpaní `World` vyhodí `KarelBudget('steps'|'turns')`:
  - počas behu → `interpreter.on_budget` → `App._on_budget` zastaví program + `BudgetDialog` (OK/Reset)
  - priame ovládanie (tlačidlá aj písané) → `ControlPanel._do` zachytí → ten istý dialóg, príkaz sa nevykoná
  - interpreter `run()` re-raisuje `KarelBudget` ak `on_budget is None` (throwaway interpreter v `_do` ho tak prepustí von)
- **`max_climb`/`max_drop`/`max_brick_height`** — fyzické limity, **tichý skip** (ako stena/prázdny inventár), žiadny dialóg
- `_can_step_height(dh)` rieši výstup aj zoskok; `_height_limit_ok(nx,ny,units)` rieši max výšku stohu (kvader = `BIG_BRICK_UNITS`)

### Sémantika príkazov
- `drop_brick()` / `pick_brick()` — operuje na políčku **PRED** Karelom (`_front()`)
- `drop_big_brick()` — ukladá kvader pred Karelom; max 1 per tile; `check_wall()` vráti True pre kvader
- `pick_big_brick()` / `pick_any_brick()` — len GUI (nie programové); `pick_any_brick` = malá tehla → kvader fallback
- `mark()` / `clear()` — operuje na políčku **POD** Karelom (kde stojí)
- `move_forward()` — skontroluje stenu aj výšku tehiel (`max_climb`)
- `check_wall()` → True ak stena ALEBO kvader pred Karelom
- `check_sign()` → True ak značka pod Karelom
- `check_brick()` → True ak aspoň jedna malá tehla pred Karelom
- `_height(x,y)` → `bricks[y][x] + big_bricks[y][x] * 5` (výška v tehlovitých jednotkách)
- Rendering: kvader vždy na z=0 (spodok), malé tehly na vrchu kvadera (base_z = big_bricks * BIG_H)

### Chybové správanie — tichý skip
**Žiadny World príkaz nevyhodí výnimku počas behu programu.** Pri nemožnosti vykonať príkaz sa jednoducho vráti (`return`) a interpreter pokračuje ďalším príkazom. Platí pre:
- `move_forward` / `move_back` — stena alebo príliš vysoká tehla
- `drop_brick` — stena pred Karelom alebo prázdne zásoby
- `drop_big_brick` — stena / prázdne zásoby / políčko už má kvader
- `pick_brick` / `pick_big_brick` — stena alebo žiadna tehla na zdvihnutie
- `mark` — prázdne zásoby značiek

Výnimky (stále hádžu `KarelError`): neznáma procedúra, zakázaný príkaz.
Výnimka `KarelBudget('steps'|'turns')`: vyčerpaný rozpočet pohybu — zastaví program a zobrazí `BudgetDialog` (OK/Reset). Pozri „Pohybové obmedzenia".
Výnimka `KarelLimit('loop'|'recursion')`: nekonečný cyklus (`MAX_OPS`) alebo hlboká rekurzia (`MAX_D`) — zastaví program a zobrazí dialóg (len OK). Pozri „Interpreter".

---

## Systém misií (GoalCondition)

### `GoalCondition`
Jedna podmienka misie. Flat objekt — žiadna hierarchia tried.

```python
GoalCondition(
    check,          # 'karel_pos' | 'cell_state' | 'sign' | 'brick_ahead' | 'wall_ahead' | 'snapshot'
    eval_,          # 'success' | 'failure'  — čo nastane pri splnení
    when,           # 'on_step' | 'on_finish'  — kedy sa vyhodnocuje
    op,             # 'or' | 'and'  — logický operátor voči predchádzajúcej podmienke
    negate,         # bool — neguj výsledok (NOT)
    x, y,           # súradnice (pre karel_pos, cell_state)
    z,              # výška (pre karel_pos: _height(karel_x, karel_y))
    cell_marks,     # bool | None  (pre cell_state)
    cell_bricks,    # int | None   (pre cell_state)
    cell_big_bricks,# int | None   (pre cell_state)
    snap,           # dict         (pre snapshot)
)
```

**Typy podmienok:**
| `check` | Čo kontroluje | Extra polia |
|---|---|---|
| `karel_pos` | Pozícia/výška Karela | `x`, `y`, `z` (None = ľubovoľné) |
| `cell_state` | Stav konkrétneho políčka | `x`, `y`, `cell_marks`, `cell_bricks`, `cell_big_bricks` |
| `sign` | Značka pod Karelom | — |
| `brick_ahead` | Tehla pred Karelom | — |
| `wall_ahead` | Stena pred Karelom | — |
| `snapshot` | Snímok celej miestnosti | `snap` dict |

### `evaluate_goals(world, on_step) → None`
- Vyhodnotí všetky podmienky s `when == on_step` (alebo `on_finish`)
- Skupiny `failure` sa vyhodnotia ako prvé
- Sekvenčné AND/OR v rámci skupiny
- Ak podmienka trigeruje výsledok → `on_step(result)` callback → `MissionResultDialog`

### Logické operátory v zozname
- Prvá podmienka: prefix `'     '` (5 medzier)
- Ďalšie: `' OR '` alebo `'AND '`
- Zobrazuje `_cond_label(idx, cond)` v listboxe WorldSettingsDialog

---

## Stav sveta — _base vs _world

```python
app._base   # World — základ: stav pri nahratí súboru alebo poslednom Save
             # Obsahuje pôvodnú štartovaciu pozíciu Karela
             # Mení sa: pri otvorení súboru, pri Save (uložení), pri WorldSettings Apply
app._world  # World — aktuálny bežiaci stav (Karel sa pohybuje, tehly sa kladú)
```

**Reset (`_reset_world`):**
```python
self._world = self._base.copy()   # deepcopy — Karel sa vráti na štartovaciu pozíciu z _base
self._world.reset_inventory()     # obnoví zásoby podľa settings.brick_limit atď.
```

**WorldSettings Apply:**
- **Nerobí** `_reset_world()` — Karel zostane kde je
- Skopíruje len zmenené polia (`settings`, `goal_conditions`, `title`, `intro_html` atď.) priamo do `_world`
- Aktualizuje `_base = w` (pracovná kópia s novými nastaveniami, pôvodnou štartovacou pozíciou)

**WorldSettings — pozícia Karela:**
- Spinbox zobrazuje štartovaciu pozíciu z `_base` (nie aktuálnu)
- Ak Karel chodil od štartu, zobrazí sa: `ℹ  Štart: ({x},{y})  ×  Karel teraz: ({sx},{sy})`
- Zmeniť štartovaciu pozíciu môže učiteľ manuálne v spinboxe → Apply

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

### Sekcie v `.ini` súboroch (všetkých 6 jazykov)
```
[meta]           name = ...
[menu]           menu položky
[toolbar]        toolbar tlačidlá
[nav]            NavigatorPanel
[control]        ControlPanel
[status]         stavový riadok
[program_panel]  ProgramPanel (filter strom, zoznam príkazov)
[action_labels]  texty na akčných tlačidlách (DROP, PICK, MARK, CLEAR, DROP_BIG)
[world_settings] WorldSettingsDialog — všetky záložky vrátane misie
[goal_condition] GoalConditionDialog
[role_dialog]    RoleDialog
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
# Logické: NOT, AND, OR + LPAREN '(' / RPAREN ')'
```

### AST uzly
```python
ProgN(procedures, main_stmts)
CmdN(cmd, line)           # príkaz
CallN(name, line)         # volanie procedúry
RepN(count, body, line)   # opakuj N krat
WhileN(cond, body, line)
IfN(cond, then_body, else_body, line)
CondN(cond_type, negated) # atóm podmienky
NotN(child)               # nie <expr>
AndN(left, right)         # left a right
OrN(left, right)          # left alebo right
```

### Podmienky — logické spojky
Podmienky v `ak`/`kym` sú výrazy s prioritou **NOT > AND > OR**, zátvorky `( )` ju menia.
```
ak stena alebo znacka potom ...
kym nie stena a nie tehla rob ...
ak (stena alebo tehla) a nie znacka potom ...
```
- Parser: rekurzívny zostup `_or_expr → _and_expr → _not_expr → _atom`
- `_ev(node)` rekurzívne; short-circuit cez Python `and`/`or` (atómy nemajú vedľajšie účinky)
- Kľúčové slová: SK `a`/`alebo`, EN `and`/`or`, DE `und`/`oder`, FR `et`/`ou`, IT `e`/`o`, ES `y`/`o`
- POZOR: `check_free` (volno) a `check_wall` (stena) NIE sú opačné na okraji mriežky —
  `volno` ignoruje okraj, `stena` ho deteguje. Na chôdzu k stene použiť `kym nie stena`.

### Interpreter
- Beží na **daemon thread** (`threading.Thread(..., daemon=True)`)
- Callbacky (`on_step`, `on_finish`, `on_error`, `on_budget`, `on_limit`) sa spúšťajú cez `canvas.after(0, ...)` — nutné pre tkinter na Windows
- `KarelInterpreter._cmd(node)` → skontroluje `disabled_cmds` → zavolá `World` metódu → `on_step()` → `sleep(delay)`
- **Rekurzia** `MAX_D = 1000` úrovní → pri prekročení `KarelLimit('recursion')`.
  Modul pri štarte robí `sys.setrecursionlimit(12000)` + `threading.stack_size(64MB)`,
  aby tých 1000 úrovní (≈3-4 Python rámce/úroveň) bolo reálne dosiahnuteľných pred Python limitom.
- **Ochrana proti nekonečnému cyklu** `MAX_OPS = 100 000` — `_tick()` počíta vykonané
  príkazy (v `_rs` + v `kym`/`opakuj` slučkách, takže aj prázdne telo slučky sa zachytí);
  pri prekročení `KarelLimit('loop')`.
- `KarelLimit` (kind `'loop'|'recursion'`) → `on_limit` → `App._on_limit` zastaví program
  a zobrazí dialóg (len OK). `run()` re-raisuje ak `on_limit is None` (priame ovládanie
  zachytí v `ControlPanel._do`). Rovnaký vzor ako `KarelBudget`.

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
- 6 záložiek: Popis, Miestnosť, Zásoby, Príkazy, Pohľad, Misia
- `_work = app._base.copy()` — pracovná kópia; aplikuje sa až pri OK
- `_on_prog_lang_changed()` — live update názvov príkazov + skrytie/zobrazenie checkboxov podľa `_LANG_DISABLED`
- `_cmd_vars: dict` — tok → BooleanVar (iba CMD tokeny, nie COND tokeny ako BRICK)
- `_cmd_cbs: dict` — tok → Checkbutton widget
- COND tokeny (napr. BRICK) sa do `disabled_cmds` dostávajú iba cez `DISABLED` direktívu v `.lng`
- **Apply** (`_apply()`): patchuje `_world` priamo (bez resetu Karela), uloží `_base = w`
- Záložka Misia: listbox s podmienkami, tlačidlá Pridať/Upraviť/Odstrániť, double-click na úpravu

### `GoalConditionDialog`
- Otvorí sa pri Pridať alebo Upraviť podmienku
- `edit_cond=None` → nová podmienka; `edit_cond=GoalCondition` → úprava existujúcej (predvyplní polia)
- Typ podmienky: radio buttons (6 typov)
  - `karel_pos` — spinboxy X, Y, výška (každý voliteľný)
  - `cell_state` — súradnice + stav značky/tehál
  - `sign` / `brick_ahead` / `wall_ahead` — bez parametrov, iba info text
  - `snapshot` — zachytí aktuálny stav sveta
- Spoločná sekcia: Výsledok (success/failure), Kedy (on_step/on_finish), Operátor (or/and), Negácia

---

## Súbor sveta `.karxml`

Jediný podporovaný formát (`.karjson` sa stále načíta pre spätnu kompatibilitu, ale neukladá sa).

```xml
<world width="..." height="...">
  <karel x="..." y="..." dir="E"/>
  <walls>
    <wall x="0" y="0" side="S"/>
    ...
  </walls>
  <bricks>
    <brick x="3" y="1" count="2"/>
    ...
  </bricks>
  <bigbricks>
    <bigbrick x="2" y="3"/>
    ...
  </bigbricks>
  <marks>
    <mark x="1" y="1"/>
    ...
  </marks>
  <title>Názov sveta</title>
  <intro><![CDATA[<b>HTML zadanie</b>]]></intro>
  <success>Správa pri úspechu</success>
  <failure>Správa pri neúspechu</failure>
  <program>Zacatok\n\nKoniec</program>
  <settings>
    <prog_lang>sk</prog_lang>
    <disabled_cmds>BACK,RIGHT</disabled_cmds>
    <brick_limit>10</brick_limit>
    <big_brick_limit>-1</big_brick_limit>
    <mark_limit>-1</mark_limit>
    <max_climb>1</max_climb>
    <max_drop>-1</max_drop>             <!-- vynechané ak -1 -->
    <max_steps>-1</max_steps>           <!-- vynechané ak -1 -->
    <max_turns>-1</max_turns>           <!-- vynechané ak -1 -->
    <max_brick_height>-1</max_brick_height>  <!-- vynechané ak -1 -->
    <disable_procedure>false</disable_procedure>
    <camera_locked>false</camera_locked>
    <camera_az>...</camera_az>
    <camera_el>...</camera_el>
    <camera_dist>...</camera_dist>
    <mission_reset_on_failure>false</mission_reset_on_failure>
  </settings>
  <mission>
    <condition check="karel_pos" eval="failure" when="on_step" op="or" negate="false" z="1"/>
    <condition check="sign"      eval="success" when="on_step" op="or"/>
    <condition check="snapshot"  eval="success" when="on_finish" op="and"
               karel_x="3" karel_y="1" karel_dir="E"
               bricks="..." marks="..."/>
  </mission>
</world>
```

**Dôležité:** tag je `<mission>`, nie `<goal_conditions>` — `from_xml()` hľadá `mission`.

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

Rola `student` skryje menu položky: Uložiť svet, Nastavenia sveta.

---

## Pridanie nového príkazu do jazyka

1. Pridať token do `.lng` súborov (napr. `lang/interpreter/sk.lng`)
2. Pridať token do `CMD_T`
3. Implementovať `World.xxx()` metódu
4. Pridať do `KarelInterpreter._cmd()`: `elif c == 'XXX': w.xxx()`
5. Pridať tlačidlo do `ControlPanel`
6. Zvýrazňovač (`highlight()`) a zoznam príkazov (`_cmds_list()`) to zachytia automaticky

## Pridanie nového GUI jazyka

1. Vytvoriť `lang/xx.ini` so sekciami: `[meta]`, `[menu]`, `[toolbar]`, `[nav]`, `[control]`, `[status]`, `[program_panel]`, `[action_labels]`, `[world_settings]`, `[goal_condition]`, `[role_dialog]`
2. Vytvoriť `lang/interpreter/xx.lng` s Karel kľúčovými slovami
3. Oba dropdown sa automaticky doplnia — **žiadna zmena kódu nie je potrebná**

## Pridanie nového typu podmienky misie

1. Implementovať logiku v `GoalCondition._check_raw(world)` — nový `elif self.check == 'xxx':`
2. Pridať `describe()` vetvu pre zobrazenie v listboxe
3. Pridať `from_xml()` a `to_xml()` vetvy (ak má extra parametre)
4. V `GoalConditionDialog._build()`: pridať radio button (`type_xxx` kľúč do všetkých `.ini`)
5. V `GoalConditionDialog._switch_type()`: pridať vetvu → `_build_simple_check(t)` alebo vlastná metóda
6. V `GoalConditionDialog._ok()`: pridať vetvu pre vytvorenie `GoalCondition`
7. Pridať `type_xxx` a `type_xxx_desc` do všetkých 6 `lang/*.ini`

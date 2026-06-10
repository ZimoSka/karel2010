# Karel 2010 – Plán vývoja

---

## ✅ Dokončené

### Dátový model a renderer
- Kvader: monolitický renderer, zelené malé tehly na vrchu
- Max 1 kvader per tile; `check_wall()` vracia True pre kvader
- Viacjazyčné kľúčové slová: SK `kvader`, DE `quader`, FR `bloc`, IT `blocco`, ES `bloque`
- GUI: `zdvihni` zdvihne malú tehlu, ak niet → zdvihne kvader (smart pick)
- Pattis režim (`en_pattis`): `putbeeper/pickbeeper` = MARK/CLEAR, `next_to_a_beeper` = SIGN

### Systém misií
- **GoalCondition systém** — flat trieda s check typmi:
  - `karel_pos` — pozícia/výška Karela
  - `cell_state` — stav políčka (značky, tehly)
  - `sign` — značka pod Karelom *(pridané táto session)*
  - `brick_ahead` — tehla pred Karelom *(pridané táto session)*
  - `wall_ahead` — stena pred Karelom *(pridané táto session)*
  - `snapshot` — snímok celej miestnosti
- Per-podmienka: eval (success/failure), when (on_step/on_finish), op (and/or), negate
- `evaluate_goals()` — failure skupina sa vyhodnotí prvá; sekvenčné AND/OR
- `GoalConditionDialog` — editor podmienok s predvyplňovaním pri úprave, double-click
- AND/OR prefix viditeľný v listboxe podmienok
- `sign`/`brick_ahead`/`wall_ahead` dostupné v UI dialógu s info popisom *(táto session)*

### Súborový formát
- Jednotný formát `.karxml` (JSON ukladanie odstránené, spätná kompatibilita zachovaná)

### Správanie Reset / WorldSettings
- `WorldSettingsDialog` Apply — nepúšťa `_reset_world()`, Karel zostane kde je *(táto session)*
- Reset — Karel sa vráti na štartovaciu pozíciu z `_base`, nie na aktuálnu *(táto session)*
- Štartovacia pozícia v dialógu predvyplnená z `_base` (nie z aktuálnej polohy) *(táto session)*
- Hnote: `ℹ  Štart: (x,y)  ×  Karel teraz: (sx,sy)` *(táto session)*

### Preklady
- 6 jazykov (sk/en/de/fr/it/es), 179 kľúčov, všetky zhodné — overené skriptom *(táto session)*

### Editor
- Zvýraznenie komentárov — `//`, `#`, `{ }` v editore
- `zdvihni_kvader` ako programový príkaz

### Jazyk — logické spojky *(táto session)*
- `AND`/`OR`/`NOT` + zátvorky `( )` v podmienkach `ak`/`kym`
- Priorita NOT > AND > OR; rekurzívny parser + `_ev`
- Kľúčové slová vo všetkých 7 jazykoch (SK `a`/`alebo` …)

### Pohybové obmedzenia *(táto session)*
- `max_steps` / `max_turns` — rozpočet krokov/otočení od resetu;
  pri vyčerpaní zastavenie programu + `BudgetDialog` (OK/Reset)
- `max_drop` — max zoskok nadol (-1 = ∞)
- `max_brick_height` — max výška stohu na kladenie tehiel (kvader = 5)
- `max_climb` (už existoval, default 1)
- Priame ovládanie pri vyčerpaní rozpočtu: príkaz sa nevykoná + dialóg
- Ukladá sa do `.karxml`; UI v záložke Pohyb; preklady v 6 jazykoch

### Ochrana proti nekonečnu + rekurzia *(táto session)*
- `MAX_OPS=100 000` — strop príkazov proti nekonečnému cyklu → `KarelLimit('loop')`
- `MAX_D=1000` rekurzia (predtým 500, ale Python limit udieral skôr);
  `sys.setrecursionlimit(12000)` + `threading.stack_size(64MB)` → reálne dosiahnuteľné
- Oba → dialóg len s OK; `on_limit` callback (vzor ako `on_budget`)

### GUI layout
- PanedWindow štruktúra — ťahateľné deliče medzi panelmi *(táto session)*
- Navigator + Ovládanie fixné a vždy celé viditeľné *(táto session)*
- Príkazy + Filter zúžené, scrollovateľné *(táto session)*
- Pravý panel zúžený (~210px), 3D svet dostane väčšinu šírky *(táto session)*
- Tmavá ttk téma (clam) — bez bielych plôch *(táto session)*

### Dokumentácia
- `CLAUDE.md` — kompletná architektúra, pravidlá, GoalCondition, _base vs _world *(táto session)*
- `PLAN.md` — tento súbor *(táto session)*
- Pravidlo: `/compact` nikdy bez povolenia *(táto session)*
- Pravidlo: dôležité info okamžite do `.md` súborov *(táto session)*

---

## 🚀 STRATEGICKÝ SMER: Karel ako webová aplikácia (Docker)

**Rozhodnutie (jún 2026):** Cieľový stav = Karel beží ako **Docker image (Linux)**,
backend v Pythone, frontend (vykresľovanie + UI) vo **webovom prehliadači**.
Používatelia pristupujú cez web, bez inštalácie čohokoľvek.

Blokový editor (Scratch štýl) je **pozastavený** ako samostatný desktop projekt —
vo web frontende sa spraví natívne cez **Blockly** (žiadne pywebview mosty).
Prieskum k Blockly je hotový: custom bloky + vlastný generátor → Karel text →
existujúci interpreter (vzor Otto Blockly / BlocklyDuino).

### Task 1 — Backend do Dockera
- Extrahovať **core** z `karel2010.py` do modulu bez tkinter závislostí:
  World, WorldSettings, GoalCondition, evaluate_goals, tokenize/Parser/AST,
  KarelInterpreter, .karxml I/O, jazykový systém (.lng)
- Desktop tkinter app ďalej funguje — importuje core (žiadna stratená funkčnosť)
- Dockerfile: python slim + web server, mount/volume pre svety

### Task 2 — Integračná vrstva (API)
- Web server (návrh: FastAPI + uvicorn)
- **WebSocket** pre beh programu: server pošle stav sveta po každom kroku
  (ekvivalent `on_step`), klient vykresľuje; Stop/Reset ako správy
- **REST**: zoznam svetov, load/save .karxml, validácia programu, nastavenia
- Session model: každý pripojený žiak má vlastnú inštanciu World + interpreter
- Bezpečnostné stropy už existujú (MAX_OPS, MAX_D, KarelBudget) — kritické pre server!

### Task 3 — Web frontend
- 3D vykresľovanie v prehliadači (návrh: Three.js — kamera, kvadre, tehly, značky)
- Editor programu (CodeMirror + Karel highlighting), panel príkazov, navigátor,
  ovládanie, dialógy (intro/misia/budget/limit)
- i18n — znovu použiť lang/*.ini + lang/interpreter/*.lng (servírovať cez API)
- Neskôr: **Blockly** ako druhý režim editora (prepínač Text ↔ Bloky)

### Rozhodnutia (jún 2026, odsúhlasené)
- **Model zdieľania:** default rola po otvorení = **učiteľ**. Učiteľ pripraví
  svet + zadanie + nastavenia → tlačidlo **„Zdieľaj žiakom"** → vygenerujú sa
  **unikátne persistentné linky** pre žiakov. Link otvorí žiacky mód
  s automaticky natiahnutým svetom; žiak sa k nemu vie kedykoľvek vrátiť.
- **Persistencia:** od začiatku navrhnúť úložisko (assignment = snapshot sveta
  + nastavení; žiacky workspace = program + stav, kľúčované tokenom z linku).
  Na začiatok súborové úložisko (JSON/karxml na disku/volume), DB až keď treba.
- **Repo:** web verzia = **nový git projekt (klon)**, vyvíja sa oddelene.
  Desktop verzia sa mení len on-demand („prihoď aj do desktopu").
- **Stack:** FastAPI + uvicorn, WebSocket, Three.js, CodeMirror. Docker (linux).

---

## 🟡 Stredná priorita (desktop)

| # | Úloha |
|---|-------|
| 1 | **`StopIfCanNotGo`** — Karel sa zastaví namiesto tichého skip pri stene |
| 2 | **Počítadlo efektivity** (CodeHS) — v MissionResult zobraziť „vyriešené na N krokov, M otočení" |
| 3 | **Otočiť logiku zakázaných príkazov** v záložke Príkazy (WorldSettingsDialog): zaškrtnuté = príkaz **viditeľný/povolený** (nie zakázaný) — logickejšie pre učiteľa. Pozor: zmeniť aj ukladanie do `.karxml` (dnes `disabled_cmds`) alebo invertovať len v UI. *(rovnaká zmena aj vo web Karel2030 — viď jeho PLAN U7)* |

## 🟢 Nižšia priorita

| # | Úloha |
|---|-------|
| 3 | **Live syntax validácia** — podčiarknutie chýb priebežne |
| 4 | **Autocomplete** — dopĺňanie kľúčových slov v editore |
| 5 | **História príkazov** — šípky nahor/dole v command boxe |
| 6 | **Gramatika do externého súboru** |
| 7 | **Drag & drop programovanie (Scratch štýl)** — POZASTAVENÉ pre desktop; spraví sa cez Blockly vo web frontende (viď Strategický smer) |
| 8 | **Revalidácia 3D grafiky** — textúry na plochách, animácie pohybu Karela |
| 9 | **Pohľad 1st person** — kamera z očí Karela, pohyb v reálnom čase |

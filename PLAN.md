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

## 🔴 Vyššia priorita

| # | Úloha |
|---|-------|
| 1 | **Logické spojky v jazyku** — `a` / `alebo` (AND/OR) v podmienkach Karel programu |

## 🟡 Stredná priorita

| # | Úloha |
|---|-------|
| 2 | **`GoalKarelNear`** — Karel musí byť v okolí ±1 dlaždice od cieľa |
| 3 | **Pohybové obmedzenia** — max krokov/otočení atď. |
| 4 | **`StopIfCanNotGo`** — Karel sa zastaví namiesto tichého skip pri stene |

## 🟢 Nižšia priorita

| # | Úloha |
|---|-------|
| 5 | **Live syntax validácia** — podčiarknutie chýb priebežne |
| 6 | **Autocomplete** — dopĺňanie kľúčových slov v editore |
| 7 | **História príkazov** — šípky nahor/dole v command boxe |
| 8 | **Gramatika do externého súboru** |
| 9 | **Drag & drop programovanie (Scratch štýl)** — vizuálne bloky namiesto textu; bloky = príkazy/štruktúry, skladajú sa presúvaním |
| 10 | **Karel ako webová aplikácia** — web interface (prehliadač), bez inštalácie Pythonu |
| 11 | **Revalidácia 3D grafiky** — textúry na plochách, animácie pohybu Karela |
| 12 | **Pohľad 1st person** — kamera z očí Karela, pohyb v reálnom čase |

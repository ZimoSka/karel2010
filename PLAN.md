# Karel 2010 – Plán vývoja

---

## ✅ Dokončené

- Kvader: monolitický renderer, zelené malé tehly na vrchu
- Max 1 kvader per tile; `check_wall()` vracia True pre kvader
- Viacjazyčné kľúčové slová: SK `kvader`, DE `quader`, FR `bloc`, IT `blocco`, ES `bloque`
- GUI: `zdvihni` zdvihne malú tehlu, ak niet → zdvihne kvader (smart pick)
- Pattis režim (`en_pattis`): `putbeeper/pickbeeper` = MARK/CLEAR, `next_to_a_beeper` = SIGN
- **GoalCondition systém** — flat trieda s check typmi:
  - `karel_pos` — pozícia/výška Karela
  - `cell_state` — stav políčka (značky, tehly)
  - `sign` — značka pod Karelom
  - `brick_ahead` — tehla pred Karelom
  - `wall_ahead` — stena pred Karelom
  - `snapshot` — snímok celej miestnosti
- Per-podmienka: eval (success/failure), when (on_step/on_finish), op (and/or), negate
- `evaluate_goals()` — failure skupina sa vyhodnotí prvá; sekvenčné AND/OR
- `GoalConditionDialog` — editor podmienok s predvyplňovaním pri úprave
- AND/OR prefix viditeľný v listboxe podmienok
- Jednotný formát `.karxml` (JSON ukladanie odstránené, spätná kompatibilita zachovaná)
- `WorldSettingsDialog` Apply — nepočkáva `_reset_world()`, Karel zostane kde je
- Reset — Karel sa vráti na štartovaciu pozíciu z `_base` (nie na aktuálnu)
- Preklady: 6 jazykov (sk/en/de/fr/it/es), 179 kľúčov, všetky zhodné

---

## 🔴 Vyššia priorita

| # | Úloha |
|---|-------|
| 1 | **Zvýraznenie komentárov** — `//`, `#`, `{ }` v editore bez farby |
| 2 | **Logické spojky v jazyku** — `a` / `alebo` (AND/OR) v podmienkach Karel programu |
| 3 | **`zdvihni_kvader` programovo?** — momentálne GUI only, potvrdiť zámer |

## 🟡 Stredná priorita

| # | Úloha |
|---|-------|
| 4 | **`GoalKarelNear`** — Karel musí byť v okolí ±1 dlaždice od cieľa |
| 5 | **Pohybové obmedzenia** — max krokov/otočení atď. |
| 6 | **`StopIfCanNotGo`** — Karel sa zastaví namiesto tichého skip pri stene |

## 🟢 Nižšia priorita

| # | Úloha |
|---|-------|
| 7 | **Live syntax validácia** — podčiarknutie chýb priebežne |
| 8 | **Autocomplete** — dopĺňanie kľúčových slov v editore |
| 9 | **História príkazov** — šípky nahor/dole v command boxe |
| 10 | **Gramatika do externého súboru** |

# Karel 2010 — Programming Language Reference (All Languages)

This document is the single source of truth for all Karel keyword translations.  
It is written in English and covers all 7 supported keyword sets side by side,  
so a teacher who knows English can find the keywords for any language.

**How it works:** The interpreter accepts *all* keyword variants from *all* languages
simultaneously. A student can write `forward`, `dopredu`, `adelante` or `avanza` in
the same program and Karel will understand all of them. The teacher selects the
*primary* language per world — that determines which words appear on the buttons and
in code templates.

---

## Language codes

| Code | Language | Primary keywords look like |
|------|----------|---------------------------|
| `sk` | Slovak / Slovenčina | `dopredu`, `vlavo`, `opakuj` |
| `en` | English | `forward`, `left`, `repeat` |
| `de` | German / Deutsch | `vorwärts`, `links`, `wiederhole` |
| `fr` | French / Français | `avance`, `gauche`, `répète` |
| `it` | Italian / Italiano | `avanza`, `sinistra`, `ripeti` |
| `es` | Spanish / Español | `adelante`, `izquierda`, `repite` |
| `en_pattis` | English (Pattis 1981) | `move`, `turnleft`, `iterate` |

---

## Commands

### Movement

| Token | SK | EN | DE | FR | IT | ES | Pattis |
|-------|----|----|----|----|----|----|--------|
| FORWARD | `dopredu` | `forward` | `vorwärts` | `avance` | `avanza` | `adelante` | `move` |
| BACK | `dozadu` | `back` | `zurück` | `recule` | `arretra` | `atras` | *(disabled)* |
| LEFT | `vlavo` | `left` | `links` | `gauche` | `sinistra` | `izquierda` | `turnleft` |
| RIGHT | `vpravo` | `right` | `rechts` | `droite` | `destra` | `derecha` | *(disabled)* |

**Aliases accepted (not shown on buttons):**

| Token | Notable aliases |
|-------|----------------|
| FORWARD | SK: `vľavo` · EN: `move`, `moveforward` · DE: `vorwaerts` · FR: `avancer` · ES: `avanza`, `avanzar` |
| BACK | SK: `vzad` · DE: `zurueck` · ES: `atrás`, `retrocede` |
| LEFT | SK: `vľavo`, `dolava`, `doľava` · EN: `turnleft` · DE: — · ES: `gira_izquierda` |
| RIGHT | SK: — · EN: `turnright` · ES: `gira_derecha` |

---

### Bricks (placed and picked up **in front of** Karel)

| Token | SK | EN | DE | FR | IT | ES | Pattis |
|-------|----|----|----|----|----|----|--------|
| DROP | `poloz` | `drop` | `lege` | `pose` | `posa` | `pon` | *(disabled)* |
| PICK | `zdvihni` | `pick` | `hebe` | `prends` | `prendi` | `toma` | *(disabled)* |
| DROP_BIG | `poloz_velku` | `drop_big` | `lege_gross` | `pose_grande` | `posa_grande` | `pon_grande` | *(disabled)* |

**Aliases:** SK: `polož`, `zodvihni`, `poloz_v` · EN: `drop_b`, `dropb` · ES: `poner`, `coloca`, `tomar`, `recoge`

---

### Marks (placed and picked up **under** Karel — on Karel's current tile)

| Token | SK | EN | DE | FR | IT | ES | Pattis |
|-------|----|----|----|----|----|----|--------|
| MARK | `oznac` | `mark` | `markiere` | `marque` | `marca` | `marca` | `putbeeper` |
| CLEAR | `odznac` | `clear` | `lösche` | `efface` | `cancella` | `borra` | `pickbeeper` |

> **Pattis note:** `putbeeper` and `pickbeeper` place/remove a mark on Karel's current
> tile — not a brick in front. This matches the original Pattis semantics where Karel
> interacts with "beepers" at the current corner.

**Aliases:** SK: `označ`, `odznač`, `ocisti`, `čisti` · EN: `unmark` · DE: `loesche` · ES: `marcar`, `borrar`, `desmarca`

---

### Speed

| Token | SK | EN | DE | FR | IT | ES | Pattis |
|-------|----|----|----|----|----|----|--------|
| SLOWLY | `pomaly` | `slowly` | `langsam` | `lentement` | `lentamente` | `despacio` | *(disabled)* |
| QUICKLY | `rychlo` | `quickly` | `schnell` | `vite` | `presto` | `rapido` | *(disabled)* |

**Aliases:** SK: `rýchlo`, `spomal`, `pridaj` · EN: `slow`, `quick` · ES: `lento`, `rápido`, `deprisa`

---

## Conditions

Conditions are used inside `while`, `if`, and can be negated with `not`.

| Token | SK | EN | DE | FR | IT | ES | Pattis | True when… |
|-------|----|----|----|----|----|----|--------|-----------|
| WALL | `stena` | `wall` | `wand` | `mur` | `muro` | `pared` | `front_is_blocked` | Wall or border in front of Karel |
| BRICK | `tehla` | `brick` | `stein` | `brique` | `mattone` | `ladrillo` | *(disabled)* | At least one brick in front |
| FREE | `volno` | `free` | `frei` | `libre` | `libero` | `libre` | `front_is_clear` | No brick in front of Karel |
| SIGN | `znacka` | `sign` | `markierung` | `marqueur` | `segno` | `senal` | `next_to_a_beeper` | Mark on Karel's current tile |
| TRUE | `pravda` | `true` | `wahr` | `vrai` | `vero` | `verdadero` | `true` | Always true |
| FALSE | `nepravda` | `false` | `falsch` | `faux` | `falso` | `falso` | `false` | Always false |

**Aliases:**
- WALL: SK: `je_stena` · EN: `is_wall`, `there_is_wall`, `front_is_blocked`, `frontisblocked` · ES: `hay_pared`, `es_pared`
- BRICK: SK: `je_tehla` · EN: `is_brick`, `there_is_brick` · ES: `hay_ladrillo`, `es_ladrillo`
- FREE: EN: `is_free`, `front_is_clear`, `frontisclear` · ES: `hay_libre`, `es_libre`
- SIGN: SK: `značka`, `je_znacka` · EN: `is_sign`, `next_to_a_beeper`, `nexttoabeeper` · ES: `señal`, `hay_senal`, `hay_señal`

---

## Control structures

### Program block

| Token | SK | EN | DE | FR | IT | ES | Pattis |
|-------|----|----|----|----|----|----|--------|
| BEGIN | `zaciatok` | `begin` | `anfang` | `début` | `inizio` | `inicio` | `begin` |
| END | `koniec` | `end` | `ende` | `fin` | `fine` | `fin` | `end` |

**Aliases:** SK: `začiatok` · FR: `debut`

---

### Procedure definition

| Token | SK | EN | DE | FR | IT | ES | Pattis |
|-------|----|----|----|----|----|----|--------|
| PROCEDURE | `prikaz` | `procedure` | `prozedur` | `procedure` | `procedura` | `instruccion` | `define` |

**Aliases:** SK: `príkaz` · ES: `instrucción`, `procedimiento` · Pattis: `define_new_instruction`

**Syntax (all languages use the same structure):**
```
procedure  Name        ← PROCEDURE token + name
begin                  ← BEGIN token
  ...
end                    ← END token
```

---

### Repeat loop

| Token | SK | EN | DE | FR | IT | ES | Pattis |
|-------|----|----|----|----|----|----|--------|
| REPEAT | `opakuj` | `repeat` | `wiederhole` | `répète` | `ripeti` | `repite` | `iterate` |
| TIMES | `krat` | `times` | `mal` | `fois` | `volte` | `veces` | `times` |
| END (loop) | `koniec` | `end` | `ende` | `fin` | `fine` | `fin` | `end` |

**Aliases:** SK: `krát` · FR: `repete` · ES: `repetir` · Pattis: `repeat`

**Syntax:**
```
repeat  5  times       ← REPEAT + number + TIMES
  forward
end                    ← END
```

---

### While loop

| Token | SK | EN | DE | FR | IT | ES | Pattis |
|-------|----|----|----|----|----|----|--------|
| WHILE | `kym` | `while` | `solange` | `tantque` | `mentre` | `mientras` | `while` |
| NOT | `nie` | `not` | `nicht` | `pas` | `non` | `no` | `not` |
| DO | `rob` | `do` | `tue` | `faire` | `fai` | `haz` | `do` |
| END (while) | `koniec` | `end` | `ende` | `fin` | `fine` | `fin` | `end` |

**Aliases:** SK: `kým` · ES: `hacer`

**Syntax:**
```
while  not wall  do    ← WHILE + [NOT] + condition + DO
  forward
end                    ← END
```

---

### If statement

| Token | SK | EN | DE | FR | IT | ES | Pattis |
|-------|----|----|----|----|----|----|--------|
| IF | `ak` | `if` | `wenn` | `si` | `se` | `si` | `if` |
| THEN | `potom` | `then` | `dann` | `alors` | `allora` | `entonces` | `then` |
| ELSE | `inak` | `else` | `sonst` | `sinon` | `altrimenti` | `sino` | `else` |
| END (if) | `koniec` | `end` | `ende` | `fin` | `fine` | `fin` | `end` |

**Aliases:** SK: `tak` · ES: `si_no`

**Syntax:**
```
if  brick  then        ← IF + condition + THEN
  pick
else                   ← ELSE (optional)
  forward
end                    ← END
```

---

## English (Pattis) mode — complete keyword set

The Pattis mode reproduces Richard Pattis's original 1981 Karel language. It is more
restricted than the standard Karel 2010 language — the following tokens are **disabled**:
`BACK`, `RIGHT`, `DROP`, `DROP_BIG`, `PICK`, `BRICK`, `SLOWLY`, `QUICKLY`.

| Concept | Pattis keyword | Karel 2010 equivalent |
|---------|---------------|----------------------|
| Move forward | `move` | FORWARD |
| Turn left | `turnleft` | LEFT |
| Place mark (at Karel's tile) | `putbeeper` | MARK |
| Remove mark (at Karel's tile) | `pickbeeper` | CLEAR |
| Wall ahead? | `front_is_blocked` | WALL |
| Path clear? | `front_is_clear` | FREE |
| Mark at Karel's tile? | `next_to_a_beeper` | SIGN |
| Repeat loop | `iterate N times` | REPEAT N TIMES |
| Define procedure | `define Name` | PROCEDURE Name |

---

## Full example — same program in all languages

**Task:** Walk Karel forward until a wall, marking each tile.

### Slovak
```
zaciatok
  kym nie stena rob
    oznac
    dopredu
  koniec
  oznac
koniec
```

### English
```
begin
  while not wall do
    mark
    forward
  end
  mark
end
```

### German
```
anfang
  solange nicht wand tue
    markiere
    vorwärts
  ende
  markiere
ende
```

### French
```
début
  tantque pas mur faire
    marque
    avance
  fin
  marque
fin
```

### Italian
```
inizio
  mentre non muro fai
    marca
    avanza
  fine
  marca
fine
```

### Spanish
```
inicio
  mientras no pared haz
    marca
    adelante
  fin
  marca
fin
```

### English (Pattis)
```
begin
  while not front_is_blocked do
    putbeeper
    move
  end
  putbeeper
end
```

---

## Language grammar (formal, language-independent)

```
program      = { procedure } main_block
procedure    = PROCEDURE NAME main_block
main_block   = BEGIN { statement } END
statement    = command
             | REPEAT NUMBER TIMES { statement } END
             | WHILE condition DO { statement } END
             | IF condition THEN { statement } [ ELSE { statement } ] END
             | NAME
command      = FORWARD | BACK | LEFT | RIGHT
             | DROP | PICK | DROP_BIG
             | MARK | CLEAR
             | SLOWLY | QUICKLY
condition    = [ NOT ] ( WALL | BRICK | FREE | SIGN | TRUE | FALSE )
```

The actual keyword used for each token depends on the configured `prog_lang`.
All language variants are accepted simultaneously regardless of the setting.

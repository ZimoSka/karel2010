# Karel Language Reference

Karel programs can be written in **Slovak** or **English** — both keyword sets are fully supported and can even be mixed in the same program.

---

## Program structure

Every Karel program that runs autonomously must have a main block:

```
zaciatok          # begin
  dopredu         # forward
  dopredu
  vlavo           # left
koniec            # end
```

Custom commands (procedures) are defined before or after the main block:

```
prikaz Strana     # procedure Strana
zaciatok
  opakuj 3 krat dopredu koniec
  vlavo
koniec

zaciatok
  opakuj 4 krat Strana koniec
koniec
```

---

## Basic commands

| Slovak | English | Description |
|--------|---------|-------------|
| `dopredu` | `forward` | Move one step forward |
| `dozadu` / `vzad` | `back` | Move one step backward |
| `vlavo` / `vľavo` | `left` | Turn 90° to the left |
| `vpravo` | `right` | Turn 90° to the right |
| `poloz` / `položiť` | `drop` | Place a small brick in front of Karel |
| `zdvihni` / `zodvihni` | `pick` | Pick up a small brick in front of Karel |
| `poloz_velku` / `poloz_v` | `drop_big` / `drop_b` | Place a big brick in front of Karel |
| `oznac` / `označ` | `mark` | Place a mark on the tile Karel stands on |
| `odznac` / `odznač` | `clear` / `unmark` | Remove the mark from Karel's tile |
| `pomaly` | `slowly` / `slow` | Slow Karel's speed down |
| `rychlo` / `rýchlo` | `quickly` / `quick` | Speed Karel up |

### Notes on bricks
- Karel places and picks up bricks **in front of himself**, not on his own tile.
- Karel can climb **at most 1 brick** higher than his current tile. Attempting to climb 2+ bricks raises an error.
- A **big brick** counts as 5 small bricks in height. Karel cannot climb over big bricks.
- Big bricks are typically used as **walls** inside a room.

---

## Control structures

### Procedure definition

```
prikaz MenoPrikazu
zaciatok
  ...
koniec
```

- Procedures can call each other and themselves (recursion).
- The maximum recursion depth is 500 levels.
- No variables exist in the language — recursion depth and brick stacks serve as the "memory".

### Repeat loop

```
opakuj N krat
  ...
koniec
```

`N` must be a literal integer. Example:

```
opakuj 4 krat
  dopredu
  vlavo
koniec
```

### While loop

```
kym podmienka rob
  ...
koniec
```

Example — move forward until a wall is reached:

```
kym nie stena rob
  dopredu
koniec
```

### If statement

```
ak podmienka potom
  ...
inak
  ...
koniec
```

The `inak` / `else` branch is optional:

```
ak tehla potom
  zdvihni
koniec
```

---

## Conditions

| Slovak | English | True when |
|--------|---------|-----------|
| `stena` | `wall` | There is a wall or room border in front of Karel |
| `tehla` | `brick` | There is at least one brick (small or big) in front |
| `volno` | `free` | No brick in front of Karel |
| `znacka` / `značka` | `sign` | Karel is standing on a mark |
| `pravda` | `true` | Always true |
| `nepravda` | `false` | Always false |

Conditions can be negated with `nie` / `not`:

```
kym nie stena rob dopredu koniec
ak nie znacka potom oznac koniec
```

---

## Comments

```
// This is a single-line comment
# Also a single-line comment
{ This is a block comment }
```

---

## Example programs

### Walk in a square

```
prikaz Strana
zaciatok
  opakuj 3 krat dopredu koniec
  vlavo
koniec

zaciatok
  opakuj 4 krat Strana koniec
koniec
```

### Collect all bricks in a row

```
prikaz ZdvihniVsetko
zaciatok
  kym tehla rob zdvihni koniec
koniec

zaciatok
  kym nie stena rob
    ZdvihniVsetko
    dopredu
  koniec
koniec
```

### Solve a maze (right-hand rule)

```
prikaz Krok
zaciatok
  ak stena potom vlavo inak dopredu koniec
koniec

zaciatok
  opakuj 80 krat Krok koniec
koniec
```

### Mark every tile to the wall

```
zaciatok
  kym nie stena rob
    oznac
    dopredu
  koniec
  oznac
koniec
```

### Infinite loop using recursion

```
prikaz Navzdy
zaciatok
  dopredu
  vlavo
  Navzdy
koniec

zaciatok Navzdy koniec
```

> **Note:** Tail recursion like this runs until Karel hits a wall or the recursion limit (500) is reached.

### Move a stack of bricks forward

```
prikaz PreniesStlpik
zaciatok
  kym tehla rob
    zdvihni
    dopredu
    poloz
    dozadu
  koniec
koniec

zaciatok
  PreniesStlpik
koniec
```

---

## Language grammar (simplified)

```
program      = { procedure } main_block
procedure    = 'prikaz' NAME main_block
main_block   = 'zaciatok' { statement } 'koniec'
statement    = command
             | 'opakuj' NUMBER 'krat' { statement } 'koniec'
             | 'kym' condition 'rob' { statement } 'koniec'
             | 'ak' condition 'potom' { statement } [ 'inak' { statement } ] 'koniec'
             | NAME
command      = 'dopredu' | 'dozadu' | 'vlavo' | 'vpravo'
             | 'poloz' | 'zdvihni' | 'poloz_velku'
             | 'oznac' | 'odznac'
             | 'pomaly' | 'rychlo'
condition    = [ 'nie' ] ( 'stena' | 'tehla' | 'volno' | 'znacka' | 'pravda' | 'nepravda' )
```

---

## Pedagogical progression

The Karel language was designed for a specific learning progression:

1. **Direct control** — move Karel with buttons, understand relative orientation (what is "left" when Karel faces different directions?)
2. **Basic sequences** — write short programs using `zaciatok … koniec`
3. **Procedures** — teach Karel new commands (`prikaz … koniec`), decompose problems
4. **Repeat loop** — `opakuj N krat` for when repetition count is known in advance
5. **While loop** — `kym podmienka rob` for unknown repetition counts
6. **If statement** — `ak podmienka potom … inak` for branching
7. **Recursion** — tail recursion as infinite loop; counting bricks as memory

The recommended age group is grades 3–7 of primary school. Karel is intended as a bridge to Logo and later to Pascal/Java.

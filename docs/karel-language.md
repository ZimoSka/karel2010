# Karel Language Reference

Karel programs can be written in **Slovak, English, German, French, Italian, Spanish** or **English (Pattis)** — all keyword sets are fully supported and can even be mixed in the same program. The active language is set per-world by the teacher in World Settings → Language tab (`prog_lang`). The interpreter always accepts all language variants simultaneously.

---

## Program structure

Every Karel program that runs autonomously must have a main block:

```
begin
  forward
  forward
  left
end
```

Custom commands (procedures) are defined before or after the main block:

```
procedure Side
begin
  repeat 3 times forward end
  left
end

begin
  repeat 4 times Side end
end
```

---

## Basic commands

| Slovak | English | Pattis | Description |
|--------|---------|--------|-------------|
| `dopredu` | `forward` / `move` | `move` | Move one step forward |
| `dozadu` / `vzad` | `back` | *(disabled)* | Move one step backward |
| `vlavo` / `vľavo` | `left` / `turnleft` | `turnleft` | Turn 90° to the left |
| `vpravo` | `right` / `turnright` | *(disabled)* | Turn 90° to the right |
| `poloz` | `drop` | *(disabled)* | Place a small brick in front of Karel |
| `zdvihni` / `zodvihni` | `pick` | *(disabled)* | Pick up a small brick in front of Karel |
| `kvader` | `drop_big` / `block` | *(disabled)* | Place a kvader (block) in front of Karel |
| `oznac` | `mark` / `putbeeper` | `putbeeper` | Place a mark on the tile Karel stands on |
| `odznac` | `clear` / `unmark` / `pickbeeper` | `pickbeeper` | Remove the mark from Karel's tile |
| `pomaly` | `slowly` / `slow` | *(disabled)* | Slow Karel's speed down |
| `rychlo` / `rýchlo` | `quickly` / `quick` | *(disabled)* | Speed Karel up |

### Notes on bricks and the kvader (block)

**Small bricks** (`poloz` / `drop`):
- Placed and picked up **in front of** Karel, not on his own tile.
- Multiple small bricks stack on top of each other.
- Karel can climb **at most 1 brick** higher per step.
- Rendered in **green**.

**Kvader** (`kvader` / `drop_big` / `block`):
- Placed **in front of** Karel — equivalent in height to 5 small bricks.
- **Maximum one kvader per tile.**
- Small bricks placed on the same tile stack **on top of** the kvader.
- The `stena` / `wall` condition returns **true** when a kvader is directly in front.
- The `tehla` / `brick` condition also returns **true** for a kvader.
- Karel **cannot climb** over a kvader (too tall).
- Picking up a kvader is only available via GUI (`zdvihni` button or command box) — not in Karel programs.
- Rendered in **brown**, visually distinct from green small bricks.

---

## Control structures

### Procedure definition

```
procedure CommandName
begin
  ...
end
```

- Procedures can call each other and themselves (recursion).
- The maximum recursion depth is 500 levels.
- No variables exist in the language — recursion depth and brick stacks serve as the "memory".

### Repeat loop

```
repeat N times
  ...
end
```

`N` must be a literal integer. Example:

```
repeat 4 times
  forward
  left
end
```

### While loop

```
while condition do
  ...
end
```

Example — move forward until a wall is reached:

```
while not wall do
  forward
end
```

### If statement

```
if condition then
  ...
else
  ...
end
```

The `else` branch is optional:

```
if brick then
  pick
end
```

---

## Conditions

| Slovak | English | Pattis | True when |
|--------|---------|--------|-----------|
| `stena` | `wall` / `front_is_blocked` | `front_is_blocked` | There is a wall or room border in front of Karel |
| `tehla` | `brick` | *(disabled)* | There is at least one brick (small or big) in front |
| `volno` | `free` / `front_is_clear` | `front_is_clear` | No brick in front of Karel |
| `znacka` / `značka` | `sign` / `next_to_a_beeper` | `next_to_a_beeper` | Karel is standing on a mark |
| `pravda` | `true` | `true` | Always true |
| `nepravda` | `false` | `false` | Always false |

Conditions can be negated with `not`:

```
while not wall do forward end
if not sign then mark end
```

---

## English (Pattis) mode

The **English (Pattis)** language variant follows the original 1981 Karel the Robot specification by Richard Pattis. It is intentionally more restricted than the standard Karel 2010 language.

Key differences from standard English:

| Concept | Standard English | Pattis |
|---------|-----------------|--------|
| Move forward | `forward` | `move` |
| Turn left | `left` | `turnleft` |
| Place mark | `mark` | `putbeeper` |
| Remove mark | `clear` | `pickbeeper` |
| Check for wall | `wall` | `front_is_blocked` |
| Check for clear path | `free` | `front_is_clear` |
| Check for mark | `sign` | `next_to_a_beeper` |
| Turn right | `right` | **not available** |
| Move backward | `back` | **not available** |
| Bricks | `drop` / `pick` | **not available** |

In Pattis mode, `putbeeper` and `pickbeeper` place/remove a **mark on the tile Karel is standing on** — not a brick in front of Karel. This matches the original Pattis semantics where Karel interacts with the current corner.

The teacher selects Pattis mode in **World Settings → Language → Programming language = English (Pattis)**. The restricted commands are then hidden from the editor's command list and disabled in both the editor and direct control.

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
procedure Side
begin
  repeat 3 times forward end
  left
end

begin
  repeat 4 times Side end
end
```

### Collect all bricks in a row

```
procedure PickAll
begin
  while brick do pick end
end

begin
  while not wall do
    PickAll
    forward
  end
end
```

### Solve a maze (right-hand rule)

```
procedure Step
begin
  if wall then left else forward end
end

begin
  repeat 80 times Step end
end
```

### Mark every tile to the wall

```
begin
  while not wall do
    mark
    forward
  end
  mark
end
```

### Infinite loop using recursion

```
procedure Forever
begin
  forward
  left
  Forever
end

begin Forever end
```

> **Note:** Tail recursion like this runs until Karel hits a wall or the recursion limit (500) is reached.

### Move a stack of bricks forward

```
procedure MoveStack
begin
  while brick do
    pick
    forward
    drop
    back
  end
end

begin
  MoveStack
end
```

---

## Language grammar (simplified)

```
program      = { procedure } main_block
procedure    = 'procedure' NAME main_block
main_block   = 'begin' { statement } 'end'
statement    = command
             | 'repeat' NUMBER 'times' { statement } 'end'
             | 'while' condition 'do' { statement } 'end'
             | 'if' condition 'then' { statement } [ 'else' { statement } ] 'end'
             | NAME
command      = 'forward' | 'back' | 'left' | 'right'
             | 'drop' | 'pick' | 'drop_big'
             | 'mark' | 'clear'
             | 'slowly' | 'quickly'
condition    = [ 'not' ] ( 'wall' | 'brick' | 'free' | 'sign' | 'true' | 'false' )
```

---

## Pedagogical progression

The Karel language was designed for a specific learning progression:

1. **Direct control** — move Karel with buttons, understand relative orientation (what is "left" when Karel faces different directions?)
2. **Basic sequences** — write short programs using `begin … end`
3. **Procedures** — teach Karel new commands (`procedure … end`), decompose problems
4. **Repeat loop** — `repeat N times` for when repetition count is known in advance
5. **While loop** — `while condition do` for unknown repetition counts
6. **If statement** — `if condition then … else` for branching
7. **Recursion** — tail recursion as infinite loop; counting bricks as memory

The recommended age group is grades 3–7 of primary school. Karel is intended as a bridge to Logo and later to Pascal/Java.

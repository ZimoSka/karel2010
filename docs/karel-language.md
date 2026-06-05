# Karel Language Reference

Karel programs can be written in **Slovak** or **English** — both keyword sets are fully supported and can even be mixed in the same program.

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

| Slovak | English | Description |
|--------|---------|-------------|
| `dopredu` | `forward` | Move one step forward |
| `dozadu` / `vzad` | `back` | Move one step backward |
| `vlavo` / `vľavo` | `left` | Turn 90° to the left |
| `vpravo` | `right` | Turn 90° to the right |
| `poloz` | `drop` | Place a small brick in front of Karel |
| `zdvihni` / `zodvihni` | `pick` | Pick up a small brick in front of Karel |
| `poloz_velku` / `poloz_v` | `drop_big` / `drop_b` | Place a big brick in front of Karel |
| `oznac` | `mark` | Place a mark on the tile Karel stands on |
| `odznac` | `clear` / `unmark` | Remove the mark from Karel's tile |
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

| Slovak | English | True when |
|--------|---------|-----------|
| `stena` | `wall` | There is a wall or room border in front of Karel |
| `tehla` | `brick` | There is at least one brick (small or big) in front |
| `volno` | `free` | No brick in front of Karel |
| `znacka` / `značka` | `sign` | Karel is standing on a mark |
| `pravda` | `true` | Always true |
| `nepravda` | `false` | Always false |

Conditions can be negated with `not`:

```
while not wall do forward end
if not sign then mark end
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

# Karel 2010 — User Guide

Karel 2010 is an educational programming environment for children. Karel is a robot that lives in a 3D room and follows instructions you give it. Your goal is to teach Karel how to solve problems by writing programs in the Karel language.

---

## Getting started

### Starting the application

```
python karel2010.py
```

or double-click **Spusti Karel.bat** on Windows.

### The main window

The window is divided into four main areas:

```
┌─────────────────────────────┬──────────────────┐
│                             │  Camera / Nav    │
│       3D World              │                  │
│       (Karel's room)        ├──────────────────┤
│                             │  Direct control  │
├─────────────────────────────┴──────────────────┤
│              Program editor                    │
└────────────────────────────────────────────────┘
```

| Area | Purpose |
|------|---------|
| **3D World** | The room where Karel lives. Shows Karel, bricks, marks, walls. |
| **Camera / Nav** | Rotate, pan and zoom the 3D view. Shows Karel's inventory. |
| **Direct control** | Move Karel with buttons or by typing commands. |
| **Program editor** | Write and run Karel programs. |

---

## Navigating the 3D view

| Action | How |
|--------|-----|
| Rotate view | Hold left mouse button and drag |
| Pan (move) view | Hold right mouse button and drag |
| Zoom in/out | Mouse scroll wheel |
| Reset to preset view | Click one of the arrow buttons in the Navigator panel |

The **Navigator panel** (top right) shows preset camera angles. Click any arrow to jump to that view. If the teacher has locked the camera, these buttons are disabled.

---

## Direct control

You can control Karel directly without writing a program.

### Using buttons

The **Direct control panel** (bottom right) has buttons for every basic action: move forward, back, turn left/right, place/pick bricks, place/remove marks.

### Typing commands

Switch to the **"Príkazovo"** tab in the Direct control panel. Type any Karel command (e.g. `dopredu`) and press **Enter**. You can also call your own procedures this way — they appear as buttons automatically after you write them in the editor.

---

## Writing and running programs

### The editor

Type your Karel program in the editor at the bottom. Commands are **highlighted automatically**:
- Known commands appear **coloured**.
- Commands forbidden by the teacher appear **red**.
- Comments (`//` or `{ }`) appear greyed out.

### Running a program

1. Write your program in the editor.
2. Click **▶ Spustiť** (Run) in the toolbar.
3. Karel executes each command step by step. Watch the 3D view.
4. To stop early, click **⏹ Stop**.
5. To return Karel to his starting position, click **↺ Reset**.

> **Important:** The program runs **from Karel's current position**, not from the start. If you moved Karel with direct control first, the program continues from there. Use **↺ Reset** to go back to the beginning.

### Speed control

The **Speed slider** in the toolbar controls how fast Karel moves. Slide right for faster, left for slower. You can also use the `pomaly` (slowly) and `rychlo` (quickly) commands inside a program.

### Example programs

The **Examples dropdown** in the toolbar contains ready-made programs. Select one to load it into the editor.

---

## Karel's world

### The room

Karel moves on a grid of tiles. The room is bounded by walls on all four sides. Karel **cannot walk through walls** — attempting to do so raises an error.

### Bricks

- **Small bricks** are placed in front of Karel (`poloz` / `drop`).
- **Big bricks** are placed in front of Karel (`poloz_velku` / `drop_big`). They are taller and Karel cannot climb over them — they act as internal walls.
- Karel can climb **at most 1 small brick** height difference between his tile and the tile in front.
- Karel picks up small bricks with `zdvihni` / `pick`.

### Marks

Marks are flat symbols placed **on Karel's current tile** (`oznac` / `mark`). Karel can remove a mark with `odznac` / `clear`. Marks are useful for leaving a trail or keeping track of visited tiles.

### Inventory

If the teacher has set a limit, Karel starts with a fixed number of bricks or marks. The current inventory is shown in the **Navigator panel**. When the count reaches zero, the corresponding command will fail with an error.

---

## The Karel language — quick reference

### Program skeleton

```
zaciatok
  dopredu
  vlavo
  dopredu
koniec
```

### Custom commands (procedures)

```
prikaz MojPrikaz
zaciatok
  dopredu
  dopredu
koniec

zaciatok
  MojPrikaz
  vlavo
  MojPrikaz
koniec
```

### Repeat loop

```
opakuj 4 krat
  dopredu
  vlavo
koniec
```

### While loop

```
kym nie stena rob
  dopredu
koniec
```

### If statement

```
ak tehla potom
  zdvihni
inak
  dopredu
koniec
```

### All commands

| Command | Effect |
|---------|--------|
| `dopredu` | Move forward |
| `dozadu` | Move backward |
| `vlavo` | Turn left |
| `vpravo` | Turn right |
| `poloz` | Place small brick in front |
| `zdvihni` | Pick up small brick in front |
| `poloz_velku` | Place big brick in front |
| `oznac` | Place mark on current tile |
| `odznac` | Remove mark from current tile |
| `pomaly` | Slow down |
| `rychlo` | Speed up |

### Conditions

| Condition | True when |
|-----------|-----------|
| `stena` | Wall or border in front |
| `tehla` | Any brick in front |
| `volno` | No brick in front |
| `znacka` | Mark on Karel's tile |

All conditions can be negated: `nie stena`, `nie tehla`, etc.

---

## Saving and loading

### Saving a program

`Edit → Save program` saves your `.prg` file.

### Loading a program

`Edit → Open program` loads a `.prg` file into the editor.

### Saving the world

`Edit → Save world as XML` saves the current state of the room (positions of all bricks, marks, Karel) as a `.karxml` file.

### Loading a world

`Edit → Open world` opens a `.karxml` or `.karjson` world file.

---

## Missions

Some worlds have a **mission** — a goal you must achieve. The task description appears in the world title and may be shown as a message when the world loads.

After your program finishes (or during direct control if the teacher chose "after every step"), the simulator checks whether you completed the mission:

- **Success ✓** — a green dialog appears with the success message.
- **Failure ✗** — a red dialog appears with the failure message. If the teacher enabled it, the world automatically resets so you can try again.

---

## Troubleshooting

| Problem | Likely cause | Solution |
|---------|-------------|----------|
| "Karel narazil do steny" | Tried to walk into a wall | Check the path — add a condition check or turn before moving |
| "Karel nevie vylesť" | Tried to climb 2+ bricks at once | Build stairs (1 brick at a time) or remove excess bricks |
| "Príkaz je zakázaný" | Teacher disabled this command | Read the task — you must solve it without that command |
| "Nemáš žiadne tehly" | Brick inventory is empty | You have used all available bricks |
| Program seems stuck | Infinite recursion or very slow | Click ⏹ Stop, check for infinite loops/recursion |
| Run button disabled | Program is still running | Wait for it to finish or click ⏹ Stop |

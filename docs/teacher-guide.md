# Karel 2010 — Teacher Guide

This guide covers everything a teacher needs to create worlds, design missions, and configure the learning environment for students.

---

## Pedagogical background

Karel 2010 is a Python port of the original Karel 3D educational programming environment (Mgr. Michal Zeman, 2004, Comenius University Bratislava). The project continues a tradition started by Richard Pattis (1981) and adapted for Slovak elementary schools by Marián Vittek, Andrej Blaho and colleagues in the late 1980s.

### Recommended age group

- **Grades 3–4**: Direct control only (buttons and typed commands). Focus on spatial orientation, relative movement, basic mouse skills.
- **Grades 4–7**: Programming mode. Sequences, procedures, loops, conditions, and eventually recursion.

Karel is intended as a bridge — it is **not** a replacement for Logo or Pascal. Its purpose is to teach algorithmic thinking before students encounter variables and data types.

### Learning progression

| Stage | Concepts | Tools |
|-------|---------|-------|
| 1 | Spatial orientation, relative movement | Direct control buttons |
| 2 | Sequences | Short programs (`begin … end`) |
| 3 | Procedures / decomposition | `procedure … end` |
| 4 | Counted repetition | `repeat N times` |
| 5 | Condition-based repetition | `while condition do` |
| 6 | Branching | `if condition then … else` |
| 7 | Recursion | Tail recursion, counting with bricks |

A key pedagogical insight from classroom experiments: **`while` is conceptually harder than `repeat`** for younger students. Plan extra time for it.

---

## Creating a world

### World settings dialog

Open via **Edit → ⚙ World Settings...**

The dialog has six tabs:

---

### Tab 1 — Description (Popis)

| Field | Purpose |
|-------|---------|
| **World title** | Short name shown in the window title bar. |
| **Task description** | HTML text shown to the student. Use the B/I/U/H1/H2/H3 toolbar to format. Describe the task, give hints or motivational context. |

The task description is shown to the student in two ways:
- **Automatically** — a dialog pops up when the student opens the world (if the field is not empty).
- **On demand** — the student can re-open it anytime via the **📋 Zadanie** button in the toolbar.

**HTML tips:**
- Use `<b>bold</b>`, `<i>italic</i>`, `<u>underline</u>` for emphasis.
- Use `<h1>`, `<h2>`, `<h3>` for headings.
- Use `<br>` for line breaks.
- You can embed any valid HTML — images, tables, links.

---

### Tab 2 — Room (Miestnosť)

> **Programming language** is also set here — see the *Programming language* section below.

| Field | Purpose |
|-------|---------|
| **Width / Height** | Dimensions of the room grid (3–50 tiles). |
| **Karel X / Y** | Starting position of Karel. Pre-filled from Karel's *current* position, so you can place Karel with direct control first, then save that as the start. |
| **Direction** | Which way Karel faces at the start (N / E / S / W). |

> **Tip:** Arrange bricks, marks and Karel in the 3D view first, then open Settings and click **Apply** — Karel's current position becomes the new starting position.

---

### Tab 3 — Inventory (Zásoby)

Limit how many items Karel starts with. Leave **unlimited (∞)** checked for no restriction.

| Limit | Effect |
|-------|--------|
| **Small bricks** | Number of small bricks Karel can place in total. |
| **Big bricks** | Number of big bricks Karel can place. |
| **Marks** | Number of marks Karel can place. |

The current inventory is shown live in the Navigator panel during the session.

---

### Tab 4 — Commands (Príkazy)

Check any command to **disable** it for this world. Disabled commands:
- Appear **red** in the program editor.
- Raise an error if the student tries to run them.
- Are greyed out in the direct control panel.

Use this to force students to solve problems without certain shortcuts. For example, disable `back` to require planning ahead.

The **"Forbid custom procedures"** checkbox disables `procedure … end` — useful for early stages where you only want `begin … end` programs.

---

### Tab 5 — View (Pohľad)

Check **Lock camera** to prevent students from rotating the 3D view. The camera angle you have set in the 3D window at the moment of clicking Apply is saved and enforced.

Use this to:
- Fix a specific pedagogically useful perspective.
- Simulate a "first-person" view from a specific angle.
- Prevent distraction.

When locked, all camera controls (mouse drag, navigation preset buttons) are disabled for the student.

---

### Tab 6 — Mission (Misia)

Define what the student must achieve. Leave empty for free-form exploration worlds.

#### Evaluation mode

| Mode | Behaviour |
|------|-----------|
| **After program ends** | Check conditions once when the program finishes naturally. Suitable for "write a program that does X". |
| **After every step** | Check after every Karel action, including direct control. The program stops automatically when all conditions are met. Suitable for "guide Karel to position X". |

**Reset on failure** (available in *After program ends* mode): if the student's program does not meet the conditions, the world automatically resets to its initial state. The student's program stays in the editor so they can fix and retry.

#### Adding conditions

Click **＋ Add condition** to define a goal condition. Choose one of three types:

**1. Karel position**
Karel must be at a specific coordinate and/or standing on a specific height of bricks. Check only the fields you want to constrain — unchecked fields are ignored.

| Field | Example | Meaning |
|-------|---------|---------|
| X | 5 | Karel must be in column 5 |
| Y | 3 | Karel must be in row 3 |
| Height | 4 | Karel must be standing on a stack of 4 small bricks |

**2. Cell state**
A specific tile must contain a certain number of bricks or a mark.

| Field | Example | Meaning |
|-------|---------|---------|
| X, Y | 2, 4 | The tile at (2,4) |
| Marks | ✓ checked | The tile must have a mark |
| Small bricks | 3 | The tile must have exactly 3 small bricks |
| Big bricks | 1 | The tile must have exactly 1 big brick |

**3. Room snapshot**
The entire room state (all brick positions and marks) must match a snapshot captured now. Optionally also checks Karel's position and direction.

> **Tip for snapshots:** Set up the room in the desired goal state first (move Karel, place bricks, etc.), then add a snapshot condition. The current state of the room is captured at the moment you click **Add condition**.

#### Multiple conditions

You can add as many conditions as needed. **All conditions must be satisfied simultaneously** for the mission to succeed.

#### Success / failure messages

Enter the text shown to the student after evaluation:

- **Success message**: Shown when all conditions are met (green dialog).
- **Failure message**: Shown when conditions are not met (red dialog).

Both fields support plain text or HTML.

---

## Language settings

Karel 2010 has two independent language settings:

| Setting | Where | Scope | Who changes it |
|---------|-------|-------|----------------|
| **GUI language** | `karel.ini` → `[ui] lang` | All menus, buttons, labels, status messages | Admin via **Settings → Global settings...** |
| **Programming language** | World Settings → Room tab | Karel keywords on direct control buttons; which language students type commands in | Teacher per world |

### GUI language

Changed in **Settings → Global settings...** (admin only). Takes effect immediately — no restart needed. Stored in `karel.ini`:

```ini
[ui]
lang = en
```

Supported values: `sk` (Slovak), `en` (English).

Translation strings are in `lang/sk.ini` and `lang/en.ini`. You can add new languages by creating `lang/xx.ini` with the same keys.

### Programming language

Set per-world in the **Room** tab of World Settings. Affects:
- Labels on the direct control action buttons (*Polož tehlu* vs *Drop brick*)
- Commands sent when those buttons are clicked (`poloz` vs `drop`)

The interpreter always accepts **both** SK and EN keywords — so students can always type either language in the command panel regardless of this setting. The setting only controls the default labels shown in the UI.

Stored in `.karxml`:

```xml
<settings>
  <prog_lang>en</prog_lang>
</settings>
```

---

## User roles

Karel 2010 supports three user roles that restrict what the current user can do. The active role is stored in `karel.ini` (next to `karel2010.py`).

| Role | Permissions |
|------|-------------|
| **Student** | Open worlds; open and save programs. Cannot modify or save worlds. |
| **Teacher** | Everything a student can do, plus: save worlds, open the World Settings editor. |
| **Admin** | Everything a teacher can do, plus: global application settings (future). |

The current role is shown in the window title bar: `Karel 2010  [Učiteľ]`.

### How role security works

There is no password — security is delegated to the operating system. The admin sets the file-system permissions on `karel.ini`:

| OS-level access to `karel.ini` | Effect |
|-------------------------------|--------|
| Read + Write | User can change the role via **Settings → Change role...** |
| Read only | Role is read at startup but cannot be changed from within the app |
| No access / file missing | Defaults to **Student** role |

**Typical classroom setup:**
1. Install Karel 2010 in a folder like `C:\KarelSchool\`.
2. Set the teacher/admin account as the only one with write access to `karel.ini`.
3. Student OS accounts have read-only access to the folder.
4. Create `karel.ini` manually with `role = teacher` — teacher machines have a writable copy, student machines have a read-only copy.

### karel.ini format

```ini
[user]
role = teacher
```

Valid values: `student`, `teacher`, `admin`.

If the file is missing, the app defaults to **Admin** role — so a fresh download works out of the box without any configuration. Restrict access by creating `karel.ini` with `role = student` and setting it read-only for student OS accounts.

---

## Saving the world

`Edit → Save world as XML` saves the complete world to a `.karxml` file, including:
- Room layout (all bricks, marks, walls)
- Karel's starting position and direction
- All settings (inventory limits, disabled commands, camera lock)
- Mission conditions
- Task description HTML
- The current program in the editor

---

## Designing good tasks

Lessons learned from the original 2004 classroom experiment:

1. **Test every task yourself before giving it to students.** Edge cases (e.g. brick stacks at intersections) can create impossible or unexpectedly hard situations.

2. **Sequence commands before conditions.** Students find `repeat` easier than `while`. Introduce them in that order.

3. **`while` needs extra time.** The concept of "repeat while condition is true" is counter-intuitive for many students. Use simple examples: "walk forward until you hit a wall."

4. **Make the task description visual.** Describe the expected room state. Saying "build a wall 5 bricks tall" is clearer than "use the `drop` command 5 times."

5. **Use missions for automatic feedback.** Students benefit enormously from immediate confirmation that their solution is correct. The mission system provides this without teacher intervention.

6. **Enable Reset on failure.** For timed or exam-style tasks, enabling reset prevents students from "editing the answer" after the program runs.

7. **Lock the camera for spatial reasoning tasks.** A fixed perspective forces students to think about Karel's orientation rather than rotating the view to cheat.

---

## Suggested task set

### Direct control tasks

1. Navigate Karel through a maze using only the buttons.
2. Navigate the same maze using only typed commands.
3. Build a column of 5 bricks (Karel stays on top).

### Procedure tasks

4. Teach Karel a `Side` command that walks 3 steps and turns. Use it to walk a square.
5. Teach Karel `WalkAround` — walk around a 6×6 brick house.
6. Teach Karel `HalfTurn` (180°) using only `left`.

### Repeat loop tasks

7. Walk around the room 3 times.
8. Build a staircase — each column one brick taller than the previous.

### While loop tasks

9. Pick up all bricks in a row.
10. Walk to the wall and back.
11. Lower a stack of bricks by 4.

### Condition + recursion tasks

12. Solve a maze using the right-hand rule.
13. Move a stack of bricks one step forward.
14. Pave a floor with marks in a chessboard pattern.

---

## Sample world file

```xml
<world width="12" height="10">
  <karel x="1" y="1" dir="E"/>
  <title>Walk to the wall</title>
  <intro><![CDATA[
    <h2>Task</h2>
    <p>Write a program that moves Karel forward until he reaches the east wall.</p>
    <p>Use the <b>while</b> loop.</p>
  ]]></intro>
  <settings>
    <disabled_cmds>BACK,DROP,DROP_BIG,PICK,MARK,CLEAR</disabled_cmds>
  </settings>
  <mission eval="on_finish" reset_on_failure="true">
    <condition type="karel_pos" x="10" y="1"/>
  </mission>
  <program>begin
  // Write your solution here
end</program>
</world>
```

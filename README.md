# Karel 2010

An educational programming simulator based on Karel the Robot — a Python port of the original project from 2005 (Turbo Pascal/Delphi, by Mgr. Zimo).

## Overview

Karel is a robot that moves around a grid world. Students program it using a simple language (Slovak or English keywords), learning the fundamentals of algorithmic thinking.

Features:
- **3D view** with Z-buffer rendering (perspective projection, mouse control)
- **Program editor** with syntax highlighting and command filter
- **Direct control** of Karel via buttons and typed commands
- **Full interpreter** for the Karel language (procedures, loops, conditionals)
- **XML world format** for saving and loading worlds (`.karxml`)
- **World settings editor** — restrict commands, lock camera, limit brick inventory
- **Mission system** — define goal conditions, evaluate success/failure after the program runs

## Running

```
python karel2010.py
```

or double-click `Spusti Karel.bat`

### Requirements

- Python 3.8+
- `pip install pillow numpy` (for Z-buffer 3D rendering)

Without numpy/Pillow the app falls back to a 2D painter mode.

## The Karel Language

Programs can be written in Slovak or English:

```
zaciatok          # begin
  opakuj 4 krat   # repeat 4 times
    dopredu       # forward
    vlavo         # left
  koniec          # end
koniec
```

**Basic commands:** `dopredu` / `forward`, `dozadu` / `back`, `vlavo` / `left`, `vpravo` / `right`, `poloz` / `drop`, `zdvihni` / `pick`, `poloz_velku` / `drop_big`, `oznac` / `mark`, `odznac` / `clear`

**Conditions:** `stena` / `wall`, `tehla` / `brick`, `znacka` / `sign`, `volno` / `free`

**Defining a custom command:**
```
prikaz MyCommand     # procedure MyCommand
zaciatok             # begin
  dopredu
  dopredu
koniec               # end
```

**Control structures:**
```
opakuj 5 krat ... koniec            # repeat 5 times
kym stena rob ... koniec            # while wall do
ak tehla potom ... inak ... koniec  # if brick then ... else
```

## World File Format (.karxml)

Worlds are stored as XML files. A complete example:

```xml
<world width="10" height="8">
  <karel x="1" y="1" dir="E"/>
  <walls>
    <wall x="0" y="0" side="S"/>
  </walls>
  <bricks>
    <brick x="3" y="1" count="2"/>
  </bricks>
  <bigbricks>
    <bigbrick x="5" y="2" count="1"/>
  </bigbricks>
  <marks>
    <mark x="5" y="0"/>
  </marks>

  <title>My World</title>
  <intro><![CDATA[<p>Task description shown to the student.</p>]]></intro>

  <settings>
    <brick_limit>5</brick_limit>
    <disabled_cmds>BACK</disabled_cmds>
    <camera_locked>true</camera_locked>
  </settings>

  <mission eval="on_finish" reset_on_failure="true">
    <condition type="karel_pos" x="5" y="3"/>
    <condition type="cell_state" x="2" y="2" bricks="3"/>
    <condition type="snapshot">
      <bricks><row>0,0,0,...</row></bricks>
      <marks><row>0,1,0,...</row></marks>
    </condition>
  </mission>

  <program>zaciatok
  dopredu
koniec</program>
</world>
```

**Save/load:** `Edit → Save world as XML` / `Edit → Open world`

## World Settings

Open via `Edit → World Settings...` to configure all world parameters across six tabs:

| Tab | Options |
|-----|---------|
| **Description** | World title; task description / intro text (HTML editor with B/I/U/H1–H3 toolbar) |
| **Room** | Width, height, Karel starting position and direction |
| **Inventory** | Max small bricks / big bricks / marks (or unlimited) |
| **Commands** | Disable specific commands (shown red in editor, buttons greyed out) |
| **View** | Lock camera to a fixed angle |
| **Mission** | Goal conditions, evaluation mode, success/failure messages |

## Mission System

The mission system lets a teacher define what the student must achieve. It is configured in the **Mission** tab of the World Settings dialog.

### Evaluation modes

| Mode | Behaviour |
|------|-----------|
| **After program ends** | Conditions are checked once when the program finishes naturally. |
| **After every step** | Conditions are checked after each Karel action (including direct control). The program stops automatically when all conditions are satisfied. |

**Reset on failure** (available in *After program ends* mode): if the conditions are not met, the world automatically resets to its initial state while the student's program remains in the editor.

### Condition types

| Type | Description |
|------|-------------|
| **Karel position** | Karel must be at a specific X, Y coordinate and/or standing on a stack of a given height. Any combination of X / Y / height can be checked independently. |
| **Cell state** | A specific cell must contain an exact number of small bricks, big bricks, and/or a mark. Multiple cells can be checked with separate conditions. |
| **Room snapshot** | The entire room (bricks, big bricks, marks) must match a snapshot captured at design time. Optionally includes Karel's position and direction. |

All conditions in the list must be satisfied simultaneously for the mission to succeed.

### XML format

```xml
<mission eval="on_finish" reset_on_failure="true">
  <condition type="karel_pos" x="5" y="3"/>
  <condition type="karel_pos" y="2" height="4"/>
  <condition type="cell_state" x="1" y="1" marks="true" bricks="2"/>
  <condition type="snapshot" karel_x="5" karel_y="3" karel_dir="N">
    <bricks>
      <row>0,0,0,2,0</row>
      ...
    </bricks>
    <bigbricks>...</bigbricks>
    <marks>
      <row>0,1,0,0,0</row>
      ...
    </marks>
  </condition>
</mission>
```

## Converting Original Worlds

The script `kar_to_xml.py` converts the original binary `.kar` files to `.karxml`:

```
python kar_to_xml.py
```

> **Note:** The original Karel format does not use internal walls — big bricks serve as walls instead. Border walls and all text content (intro/success/failure messages, embedded programs) are preserved.

## Controls

| Action | How |
|--------|-----|
| Rotate view | Left mouse drag |
| Pan view | Right mouse drag |
| Zoom | Mouse wheel |
| Run program | ▶ button or `Program → Run` |
| Stop | ⏹ button |
| Reset world | ↺ button (returns Karel and world to starting state) |
| Direct control | Bottom-right panel — buttons or type a command + Enter |

## Author

Original: Mgr. Zimo, 2005  
Python port: 2024  
https://github.com/ZimoSka/karel2010

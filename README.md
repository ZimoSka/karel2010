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
opakuj 5 krat ... koniec          # repeat 5 times
kym stena rob ... koniec          # while wall do
ak tehla potom ... inak ... koniec  # if brick then ... else
```

## World File Format (.karxml)

Worlds are stored as XML files:

```xml
<world width="10" height="8">
  <karel x="1" y="1" dir="E"/>
  <walls>
    <wall x="0" y="0" side="S"/>
  </walls>
  <bricks>
    <brick x="3" y="1" count="2"/>
  </bricks>
  <marks>
    <mark x="5" y="0"/>
  </marks>
  <settings>
    <brick_limit>5</brick_limit>
    <disabled_cmds>BACK</disabled_cmds>
    <camera_locked>true</camera_locked>
  </settings>
  <title>My World</title>
  <program>zaciatok
  dopredu
koniec</program>
</world>
```

**Save/load:** `Edit → Save world as XML` / `Edit → Open world`

## World Settings

Open via `Edit → World Settings...` to configure:

| Tab | Options |
|-----|---------|
| **Room** | Width, height, Karel starting position and direction |
| **Inventory** | Max small bricks / big bricks / marks (or unlimited) |
| **Commands** | Disable specific commands (shown red in editor, buttons greyed out) |
| **View** | Lock camera to a fixed angle |

## Converting Original Worlds

The script `kar_to_xml.py` converts the original binary `.kar` files to XML:

```
python kar_to_xml.py
```

> **Note:** Internal walls cannot be fully decoded from the binary format without the original Pascal source. Border walls and all text content (intro/success/failure messages, embedded programs) are preserved.

## Controls

| Action | How |
|--------|-----|
| Rotate view | Left mouse drag |
| Pan view | Right mouse drag |
| Zoom | Mouse wheel |
| Run program | ▶ button or `Program → Run` |
| Stop | ⏹ button |
| Reset Karel | ↺ button (returns to starting position) |
| Direct control | Bottom-right panel — buttons or type a command + Enter |

## Author

Original: Mgr. Zimo, 2005  
Python port: 2024

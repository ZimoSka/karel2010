# Karel World File Format (.karxml)

Karel 2010 worlds are stored as UTF-8 XML files with the `.karxml` extension. This document is the complete format reference.

---

## Root element

```xml
<world width="12" height="10">
  ...
</world>
```

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `width` | int | yes | Room width in tiles (3–50) |
| `height` | int | yes | Room height in tiles (3–50) |

The coordinate system has `x=0` at the **left** and `y=0` at the **bottom**.

---

## Karel's starting position

```xml
<karel x="1" y="1" dir="E"/>
```

| Attribute | Values | Description |
|-----------|--------|-------------|
| `x` | 0 … width-1 | Starting column |
| `y` | 0 … height-1 | Starting row |
| `dir` | `N` `E` `S` `W` | Starting direction (North/East/South/West) |

---

## Walls

Border walls are generated automatically. Internal walls (if any) are listed here.

```xml
<walls>
  <wall x="3" y="2" side="N"/>
  <wall x="3" y="3" side="S"/>
</walls>
```

Each `<wall>` element defines one wall face:

| Attribute | Values | Description |
|-----------|--------|-------------|
| `x` | 0 … width-1 | Tile column |
| `y` | 0 … height-1 | Tile row |
| `side` | `N` `E` `S` `W` | Which face of the tile has the wall |

> **Note:** Walls are always bidirectional — a wall on the North face of tile (x,y) is also stored as a wall on the South face of tile (x, y+1). Both entries must be present. The room border walls are handled internally and are not stored in the file.

> **Design note:** In Karel 2010, internal walls are not used in practice. Big bricks (`<bigbrick>`) serve as walls inside the room.

---

## Small bricks

```xml
<bricks>
  <brick x="3" y="1" count="2"/>
  <brick x="5" y="4" count="1"/>
</bricks>
```

| Attribute | Description |
|-----------|-------------|
| `x`, `y` | Tile coordinate |
| `count` | Number of small bricks stacked on this tile |

---

## Big bricks

```xml
<bigbricks>
  <bigbrick x="5" y="2" count="1"/>
</bigbricks>
```

Each big brick is equivalent to **5 small bricks** in height. Karel cannot climb over big bricks — they act as internal walls.

---

## Marks

```xml
<marks>
  <mark x="2" y="3"/>
  <mark x="7" y="1"/>
</marks>
```

A mark is a flat symbol on the floor of a tile. At most one mark per tile.

---

## World metadata

```xml
<title>My World</title>
<intro><![CDATA[<h2>Task</h2><p>Walk Karel to the wall.</p>]]></intro>
<success><![CDATA[<p>Well done!</p>]]></success>
<failure><![CDATA[<p>Not quite — try again.</p>]]></failure>
<program>zaciatok
  dopredu
koniec</program>
<next_level>level2.karxml</next_level>
<prev_level>level0.karxml</prev_level>
```

| Element | Description |
|---------|-------------|
| `<title>` | Short name shown in the window title bar |
| `<intro>` | HTML shown as the task description (can contain any HTML) |
| `<success>` | HTML shown in the success dialog after mission completion |
| `<failure>` | HTML shown in the failure dialog if mission is not completed |
| `<program>` | Karel program pre-loaded into the editor |
| `<next_level>` | Filename of the next world (for chained levels) |
| `<prev_level>` | Filename of the previous world |

All metadata elements are optional. HTML content should be wrapped in `<![CDATA[ … ]]>` to avoid escaping issues.

---

## World settings

```xml
<settings>
  <prog_lang>en_pattis</prog_lang>
  <brick_limit>5</brick_limit>
  <big_brick_limit>-1</big_brick_limit>
  <mark_limit>10</mark_limit>
  <disabled_cmds>BACK,RIGHT,DROP,DROP_BIG,PICK,BRICK,SLOWLY,QUICKLY</disabled_cmds>
  <disable_procedure>true</disable_procedure>
  <camera_locked>true</camera_locked>
  <camera_az>3.9269908169872414</camera_az>
  <camera_el>0.48869219055841229</camera_el>
  <camera_dist>16.0</camera_dist>
</settings>
```

| Element | Type | Default | Description |
|---------|------|---------|-------------|
| `prog_lang` | string | `sk` | Programming language for this world. Valid values: `sk`, `en`, `en_pattis`, `de`, `fr`, `it`, `es`. Determines which keywords are primary (shown on buttons, used in templates). |
| `brick_limit` | int | -1 | Max small bricks Karel may place. `-1` = unlimited. |
| `big_brick_limit` | int | -1 | Max big bricks. `-1` = unlimited. |
| `mark_limit` | int | -1 | Max marks. `-1` = unlimited. |
| `disabled_cmds` | CSV | (empty) | Comma-separated token names of forbidden commands/conditions. |
| `disable_procedure` | bool | false | If `true`, `prikaz … koniec` syntax is forbidden. |
| `camera_locked` | bool | false | If `true`, the camera is locked. |
| `camera_az` | float | 3.927 | Camera azimuth in radians (only used when locked). |
| `camera_el` | float | 0.489 | Camera elevation in radians (only used when locked). |
| `camera_dist` | float | 16.0 | Camera distance (only used when locked). |

### Valid token names for `disabled_cmds`

Commands: `FORWARD`, `BACK`, `LEFT`, `RIGHT`, `DROP`, `PICK`, `DROP_BIG`, `MARK`, `CLEAR`, `SLOWLY`, `QUICKLY`

Conditions: `BRICK` (disables brick-check condition — used e.g. in Pattis mode where bricks don't exist)

---

## Mission

```xml
<mission eval="on_finish" reset_on_failure="true">
  <condition type="karel_pos" x="5" y="3"/>
  <condition type="cell_state" x="2" y="2" bricks="3" marks="true"/>
  <condition type="snapshot" karel_x="5" karel_y="3" karel_dir="N">
    <bricks>
      <row>0,0,0,0,0,0,0,0,0,0</row>
      <row>0,0,0,0,0,0,0,0,0,0</row>
      ...
    </bricks>
    <bigbricks>
      <row>0,0,0,0,0,0,0,0,0,0</row>
      ...
    </bigbricks>
    <marks>
      <row>0,1,0,0,0,0,0,1,0,0</row>
      ...
    </marks>
  </condition>
</mission>
```

### `<mission>` attributes

| Attribute | Values | Default | Description |
|-----------|--------|---------|-------------|
| `eval` | `on_finish` / `on_step` | `on_finish` | When to evaluate conditions |
| `reset_on_failure` | `true` / `false` | `false` | Reset world on failure (only used when `eval="on_finish"`) |

**`on_finish`** — conditions are checked once when the program ends naturally (not when stopped by the user).

**`on_step`** — conditions are checked after every Karel action including direct control actions. The program stops automatically when all conditions are met. Failure is never reported mid-execution.

### Condition types

#### `karel_pos` — Karel's position

```xml
<condition type="karel_pos" x="5" y="3" height="2"/>
```

| Attribute | Required | Description |
|-----------|----------|-------------|
| `x` | no | Karel must be in this column |
| `y` | no | Karel must be in this row |
| `height` | no | Karel must be standing on this height of small bricks |

Omitted attributes are not checked. At least one must be present.

#### `cell_state` — state of a specific tile

```xml
<condition type="cell_state" x="2" y="2" bricks="3" marks="true" big_bricks="0"/>
```

| Attribute | Required | Description |
|-----------|----------|-------------|
| `x` | yes | Tile column |
| `y` | yes | Tile row |
| `bricks` | no | Required number of small bricks |
| `big_bricks` | no | Required number of big bricks |
| `marks` | no | `true` or `false` — whether a mark must be present |

Omitted attributes are not checked. At least one condition attribute must be present.

#### `snapshot` — full room state

```xml
<condition type="snapshot" karel_x="5" karel_y="3" karel_dir="N">
  <bricks>
    <row>0,0,2,0,0</row>
    <row>0,0,0,0,0</row>
    ...
  </bricks>
  <bigbricks>
    <row>0,1,0,0,0</row>
    ...
  </bigbricks>
  <marks>
    <row>0,0,1,0,0</row>
    ...
  </marks>
</condition>
```

Each `<row>` element contains `width` comma-separated integers (bricks/bigbricks) or 0/1 values (marks), representing one row of tiles from bottom to top.

| Attribute | Required | Description |
|-----------|----------|-------------|
| `karel_x` | no | Karel must be at this column |
| `karel_y` | no | Karel must be at this row |
| `karel_dir` | no | Karel must face this direction (`N`/`E`/`S`/`W`) |

Omit Karel attributes to check only the room state without constraining Karel's position.

---

## Complete example

```xml
<?xml version="1.0" ?>
<world width="12" height="10">

  <karel x="1" y="1" dir="E"/>

  <walls/>

  <bricks>
    <brick x="5" y="1" count="3"/>
  </bricks>

  <bigbricks>
    <bigbrick x="8" y="3" count="1"/>
  </bigbricks>

  <marks>
    <mark x="10" y="1"/>
  </marks>

  <title>Reach the mark</title>
  <intro><![CDATA[
    <h2>Task</h2>
    <p>Walk Karel to the mark at the far end of the room.</p>
    <p>There are some bricks in the way — you may need to climb over them.</p>
  ]]></intro>
  <success><![CDATA[<p><b>Excellent!</b> Karel reached the mark.</p>]]></success>
  <failure><![CDATA[<p>Karel did not reach the mark. Try again!</p>]]></failure>

  <settings>
    <brick_limit>-1</brick_limit>
    <disabled_cmds>BACK,DROP,PICK,DROP_BIG,MARK,CLEAR</disabled_cmds>
    <camera_locked>true</camera_locked>
    <camera_az>3.9269908169872414</camera_az>
    <camera_el>0.48869219055841229</camera_el>
    <camera_dist>14.0</camera_dist>
  </settings>

  <mission eval="on_finish" reset_on_failure="true">
    <condition type="karel_pos" x="10" y="1"/>
  </mission>

  <program>zaciatok
  // Write your solution here
koniec</program>

</world>
```

---

## Differences from the original binary `.kar` format

The original Karel 2010 (Delphi, 2004) stored worlds in a proprietary binary format (`.kar`). The `.karxml` format is a clean re-design for the Python port. Key differences:

| Feature | `.kar` (original) | `.karxml` (Python port) |
|---------|-------------------|------------------------|
| Encoding | Binary (Delphi structures) | UTF-8 XML |
| Human-readable | No | Yes |
| Mission / goal state | Partial (text only) | Full condition system |
| Inventory limits | Yes | Yes |
| Camera lock | Yes | Yes |
| Disabled commands | Yes | Yes |
| Big bricks | Yes | Yes |

The `kar_to_xml.py` converter reads `.kar` files and outputs `.karxml`.

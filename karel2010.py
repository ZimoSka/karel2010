#!/usr/bin/env python3
"""
Karel 2010 – Python port  (3D perspektívny pohľad + multiwindow UI)
Originál: Turbo Pascal/Delphi, Zimo 2010.   Python port: 2024.
Spustenie:  python karel2010.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading, time, re, os, json, math, struct, configparser, html as _html_mod
import xml.etree.ElementTree as ET
from xml.dom import minidom
from enum import Enum
from copy import deepcopy

# Z-buffer renderer — vyžaduje numpy + Pillow (pip install pillow numpy)
try:
    import numpy as np
    from PIL import Image, ImageTk
    _ZBUF = True
except ImportError:
    _ZBUF = False


# =========================================================================
# SVET  /  WORLD MODEL
# =========================================================================

class Direction(Enum):
    NORTH = 0
    EAST  = 1
    SOUTH = 2
    WEST  = 3
    def left(self):     return Direction((self.value-1)%4)
    def right(self):    return Direction((self.value+1)%4)
    def opposite(self): return Direction((self.value+2)%4)
    def to_str(self):
        return {Direction.NORTH:'N',Direction.SOUTH:'S',
                Direction.EAST:'E', Direction.WEST:'W'}[self]
    @staticmethod
    def from_str(s):
        return {'N':Direction.NORTH,'S':Direction.SOUTH,
                'E':Direction.EAST,'W':Direction.WEST,
                'NORTH':Direction.NORTH,'SOUTH':Direction.SOUTH,
                'EAST':Direction.EAST,'WEST':Direction.WEST}[s.upper()]

class KarelError(Exception): pass
class KarelStop(Exception): pass   # tiché zastavenie (napr. narazenie do steny)


# =========================================================================
# PODMIENKY  MISIE  (goal conditions)
# =========================================================================

class GoalCondition:
    """Jedna podmienka misie v plochom zozname s AND/OR operátorom.

    Atribúty:
        check   – 'karel_pos' | 'sign' | 'brick_ahead' | 'wall_ahead' |
                  'cell_state' | 'snapshot'
        eval    – 'success' | 'failure'
        when    – 'on_step' | 'on_finish'
        op      – 'or' | 'and'   (operátor s predchádzajúcou podmienkou rovnakého eval)
        negate  – True → výsledok check() sa neguje
        x, y    – súradnice (pre karel_pos, cell_state)
        z       – výška dlaždice kde Karel stojí (pre karel_pos; None = ignorovať)
        cell_marks, cell_bricks, cell_big_bricks – pre cell_state
        snap    – dict so snapshot dátami (pre snapshot)
    """
    def __init__(self, check, eval_='success', when='on_finish', op='or', negate=False,
                 x=None, y=None, z=None,
                 cell_marks=None, cell_bricks=None, cell_big_bricks=None,
                 snap=None):
        self.check  = check
        self.eval   = eval_
        self.when   = when
        self.op     = op
        self.negate = negate
        self.x = x; self.y = y; self.z = z
        self.cell_marks      = cell_marks
        self.cell_bricks     = cell_bricks
        self.cell_big_bricks = cell_big_bricks
        self.snap = snap   # dict: bricks, big_bricks, marks, karel_x, karel_y, karel_dir

    # --- snapshot helper ---------------------------------------------------
    @staticmethod
    def snapshot_from_world(world, include_karel=False):
        from copy import deepcopy
        s = dict(bricks=deepcopy(world.bricks),
                 big_bricks=deepcopy(world.big_bricks),
                 marks=deepcopy(world.marks))
        if include_karel:
            s['karel_x'] = world.karel_x
            s['karel_y'] = world.karel_y
            s['karel_dir'] = world.karel_dir
        return s

    # --- raw check (bez negate) -------------------------------------------
    def _check_raw(self, world):
        if self.check == 'karel_pos':
            if self.x is not None and world.karel_x != self.x: return False
            if self.y is not None and world.karel_y != self.y: return False
            if self.z is not None and world._height(world.karel_x, world.karel_y) != self.z:
                return False
            return True
        if self.check == 'sign':
            return bool(world.marks[world.karel_y][world.karel_x])
        if self.check == 'brick_ahead':
            nx, ny = world._front()
            if not (0 <= nx < world.width and 0 <= ny < world.height): return False
            return world.bricks[ny][nx] > 0 or world.big_bricks[ny][nx] > 0
        if self.check == 'wall_ahead':
            return world.check_wall()
        if self.check == 'cell_state':
            x, y = self.x, self.y
            if not (0 <= x < world.width and 0 <= y < world.height): return False
            if self.cell_marks is not None and world.marks[y][x] != self.cell_marks: return False
            if self.cell_bricks is not None and world.bricks[y][x] != self.cell_bricks: return False
            if self.cell_big_bricks is not None and world.big_bricks[y][x] != self.cell_big_bricks: return False
            return True
        if self.check == 'snapshot' and self.snap:
            s = self.snap
            if world.bricks != s.get('bricks'): return False
            if world.big_bricks != s.get('big_bricks'): return False
            if world.marks != s.get('marks'): return False
            if s.get('karel_x') is not None and world.karel_x != s['karel_x']: return False
            if s.get('karel_y') is not None and world.karel_y != s['karel_y']: return False
            if s.get('karel_dir') is not None and world.karel_dir != s['karel_dir']: return False
            return True
        return False

    def check_val(self, world):
        val = self._check_raw(world)
        return (not val) if self.negate else val

    # --- popis pre GUI ----------------------------------------------------
    def describe(self):
        neg = '¬' if self.negate else ''
        ev  = '✓' if self.eval == 'success' else '✗'
        wh  = '⚡' if self.when == 'on_step' else '🏁'
        if self.check == 'karel_pos':
            parts = []
            if self.x is not None: parts.append(f"x={self.x}")
            if self.y is not None: parts.append(f"y={self.y}")
            if self.z is not None: parts.append(f"z={self.z}")
            loc = ','.join(parts) if parts else '*'
            return f"{ev}{wh} {neg}Karel@({loc})"
        if self.check == 'sign':        return f"{ev}{wh} {neg}značka pod Karelom"
        if self.check == 'brick_ahead': return f"{ev}{wh} {neg}tehla pred Karelom"
        if self.check == 'wall_ahead':  return f"{ev}{wh} {neg}stena pred Karelom"
        if self.check == 'cell_state':
            p = []
            if self.cell_marks is not None:      p.append('značka' if self.cell_marks else 'bez značky')
            if self.cell_bricks is not None:     p.append(f"{self.cell_bricks}× tehla")
            if self.cell_big_bricks is not None: p.append(f"{self.cell_big_bricks}× kvader")
            return f"{ev}{wh} {neg}políčko({self.x},{self.y}): {', '.join(p)}"
        if self.check == 'snapshot':    return f"{ev}{wh} {neg}snímok miestnosti"
        return f"{ev}{wh} {neg}{self.check}"

    # --- XML --------------------------------------------------------------
    def to_xml_el(self):
        attrs = dict(check=self.check, eval=self.eval, when=self.when, op=self.op)
        if self.negate: attrs['negate'] = 'true'
        if self.x is not None: attrs['x'] = str(self.x)
        if self.y is not None: attrs['y'] = str(self.y)
        if self.z is not None: attrs['z'] = str(self.z)
        if self.cell_marks is not None:      attrs['cell_marks']      = 'true' if self.cell_marks else 'false'
        if self.cell_bricks is not None:     attrs['cell_bricks']     = str(self.cell_bricks)
        if self.cell_big_bricks is not None: attrs['cell_big_bricks'] = str(self.cell_big_bricks)
        el = ET.Element('condition', **attrs)
        if self.check == 'snapshot' and self.snap:
            s = self.snap
            br = ET.SubElement(el, 'bricks')
            for row in s['bricks']:
                ET.SubElement(br, 'row').text = ','.join(map(str, row))
            bb = ET.SubElement(el, 'bigbricks')
            for row in s['big_bricks']:
                ET.SubElement(bb, 'row').text = ','.join(map(str, row))
            mk = ET.SubElement(el, 'marks')
            for row in s['marks']:
                ET.SubElement(mk, 'row').text = ','.join('1' if v else '0' for v in row)
            if s.get('karel_x') is not None:
                el.set('karel_x', str(s['karel_x']))
                el.set('karel_y', str(s['karel_y']))
                el.set('karel_dir', s['karel_dir'].to_str())
        return el

    @staticmethod
    def from_xml_el(el):
        def _gi(a): return int(el.get(a)) if el.get(a) is not None else None
        def _gb(a): v = el.get(a); return (v.lower() == 'true') if v is not None else None
        check  = el.get('check', el.get('type', 'karel_pos'))  # 'type' = starý formát
        eval_  = el.get('eval', 'success')
        when   = el.get('when', 'on_finish')
        op     = el.get('op',   'or')
        negate = el.get('negate', 'false').lower() == 'true'
        c = GoalCondition(check=check, eval_=eval_, when=when, op=op, negate=negate,
                          x=_gi('x'), y=_gi('y'), z=_gi('z'),
                          cell_marks=_gb('cell_marks'),
                          cell_bricks=_gi('cell_bricks'),
                          cell_big_bricks=_gi('cell_big_bricks'))
        # Starý formát kompatibilita
        if check == 'karel_pos' and el.get('height') is not None:
            c.z = int(el.get('height'))
        if check == 'cell_state':
            c.cell_marks      = _gb('marks') if c.cell_marks is None else c.cell_marks
            c.cell_bricks     = _gi('bricks') if c.cell_bricks is None else c.cell_bricks
            c.cell_big_bricks = _gi('big_bricks') if c.cell_big_bricks is None else c.cell_big_bricks
        if check == 'snapshot':
            def _rows(tag):
                return [[int(v) for v in r.text.split(',')] for r in el.findall(f'{tag}/row')]
            def _brows(tag):
                return [[v == '1' for v in r.text.split(',')] for r in el.findall(f'{tag}/row')]
            kx = _gi('karel_x'); ky = _gi('karel_y')
            kd = Direction.from_str(el.get('karel_dir')) if el.get('karel_dir') else None
            br = _rows('bricks'); bb = _rows('bigbricks'); mk = _brows('marks')
            if br and bb and mk:
                c.snap = dict(bricks=br, big_bricks=bb, marks=mk,
                              karel_x=kx, karel_y=ky, karel_dir=kd)
        return c


def evaluate_goals(world, on_step=False):
    """Vyhodnotí podmienky misie. Vracia 'success', 'failure' alebo None.

    Podmienky rovnakého eval sa kombinujú sekvenciálne (zľava doprava)
    operátorom op každej podmienky (okrem prvej).
    Failure sa vyhodnocuje pred success.
    """
    when = 'on_step' if on_step else 'on_finish'
    for eval_type in ('failure', 'success'):
        group = [c for c in world.goal_conditions
                 if c.eval == eval_type and c.when == when]
        if not group:
            continue
        result = None
        for c in group:
            val = c.check_val(world)
            if result is None:
                result = val
            elif c.op == 'and':
                result = result and val
            else:
                result = result or val
        if result:
            return eval_type
    return None


class WorldSettings:
    """Nastavenia obmedzení a reštrikcií sveta — ukladajú sa do .karxml."""
    def __init__(self):
        self.brick_limit      = -1    # max malých tehál pre Karela (-1 = ∞)
        self.big_brick_limit  = -1    # max veľkých tehál (-1 = ∞)
        self.mark_limit       = -1    # max značiek (-1 = ∞)
        # Zakázané príkazy: množina tokenov z CMD_T (napr. {'FORWARD','DROP'})
        self.disabled_cmds    = set()
        # Zakázať definovanie vlastných príkazov ('prikaz … koniec')
        self.disable_procedure = False
        # Max. výška výstupu — o koľko tehiel môže Karel vyskočiť naraz (default 1)
        self.max_climb        = 1
        # Jazyk programovania pre tento svet ('sk' alebo 'en')
        self.prog_lang        = 'sk'
        # Zamknúť pohľad kamery
        self.camera_locked    = False
        self.camera_az        = math.radians(225)
        self.camera_el        = math.radians(28)
        self.camera_dist      = 16.0


class World:
    """Karelova mriežková mapa.  x=0 vľavo, y=0 dole."""
    BIG_BRICK_UNITS = 5   # veľká tehla = 5 malých

    def __init__(self, width=12, height=10):
        self.width=width; self.height=height
        self.walls      = [[set() for _ in range(width)] for _ in range(height)]
        self.bricks     = [[0     for _ in range(width)] for _ in range(height)]
        self.big_bricks = [[0     for _ in range(width)] for _ in range(height)]
        self.marks      = [[False  for _ in range(width)] for _ in range(height)]
        self.karel_x=0; self.karel_y=0; self.karel_dir=Direction.EAST
        self.settings = WorldSettings()
        # Runtime inventár — resetuje sa pri každom reštarte hry
        self._bricks_left     = -1
        self._big_bricks_left = -1
        self._marks_left      = -1
        # Metadáta sveta
        self.title        = ''
        self.intro_html   = ''
        self.success_html = ''
        self.failure_html = ''
        self.program_text = ''
        self.next_level   = ''
        self.prev_level   = ''
        # Misia — podmienky a režim vyhodnocovania
        self.goal_conditions: list    = []   # list[GoalCondition]
        self.mission_reset_on_failure: bool = False
        self._add_border_walls()

    def _add_border_walls(self):
        for x in range(self.width):
            self.walls[0][x].add('S'); self.walls[self.height-1][x].add('N')
        for y in range(self.height):
            self.walls[y][0].add('W'); self.walls[y][self.width-1].add('E')

    def reset_inventory(self):
        """Resetuje inventár podľa nastavení — volať po každom reštarte sveta."""
        self._bricks_left     = self.settings.brick_limit
        self._big_bricks_left = self.settings.big_brick_limit
        self._marks_left      = self.settings.mark_limit

    def inventory_str(self):
        """Vráti (malé, veľké, značky) ako zobraziteľné reťazce."""
        def _s(v): return '∞' if v < 0 else str(v)
        return _s(self._bricks_left), _s(self._big_bricks_left), _s(self._marks_left)

    def resize(self, new_w, new_h):
        """Zmení rozmery sveta; zachová tehly a značky v rámci nových rozmerov."""
        new_walls      = [[set()  for _ in range(new_w)] for _ in range(new_h)]
        new_bricks     = [[0      for _ in range(new_w)] for _ in range(new_h)]
        new_big_bricks = [[0      for _ in range(new_w)] for _ in range(new_h)]
        new_marks      = [[False  for _ in range(new_w)] for _ in range(new_h)]
        for y in range(min(self.height, new_h)):
            for x in range(min(self.width, new_w)):
                # Interné steny (nie na okraji starého sveta)
                if not (x==0 or x==self.width-1 or y==0 or y==self.height-1):
                    new_walls[y][x] = set(self.walls[y][x])
                new_bricks[y][x]     = self.bricks[y][x]
                new_big_bricks[y][x] = self.big_bricks[y][x]
                new_marks[y][x]      = self.marks[y][x]
        self.width=new_w; self.height=new_h
        self.walls=new_walls; self.bricks=new_bricks
        self.big_bricks=new_big_bricks; self.marks=new_marks
        self.karel_x = min(self.karel_x, new_w-1)
        self.karel_y = min(self.karel_y, new_h-1)
        self._add_border_walls()

    def _step(self,x,y,d):
        return (x+1,y) if d==Direction.EAST  else \
               (x-1,y) if d==Direction.WEST  else \
               (x,y+1) if d==Direction.NORTH else (x,y-1)

    def _front(self): return self._step(self.karel_x,self.karel_y,self.karel_dir)

    def add_wall(self,x,y,s):
        self.walls[y][x].add(s)
        opp={'N':'S','S':'N','E':'W','W':'E'}[s]
        nx,ny={'N':(x,y+1),'S':(x,y-1),'E':(x+1,y),'W':(x-1,y)}[s]
        if 0<=nx<self.width and 0<=ny<self.height: self.walls[ny][nx].add(opp)

    def remove_wall(self,x,y,s):
        self.walls[y][x].discard(s)
        opp={'N':'S','S':'N','E':'W','W':'E'}[s]
        nx,ny={'N':(x,y+1),'S':(x,y-1),'E':(x+1,y),'W':(x-1,y)}[s]
        if 0<=nx<self.width and 0<=ny<self.height: self.walls[ny][nx].discard(opp)

    def is_wall_ahead(self):
        return self.karel_dir.to_str() in self.walls[self.karel_y][self.karel_x]

    def _height(self, x, y):
        """Celková výška bunky v jednotkách malých tehál."""
        return self.bricks[y][x] + self.big_bricks[y][x] * self.BIG_BRICK_UNITS

    def move_forward(self):
        if self.is_wall_ahead(): return
        nx,ny = self._front()
        dh = self._height(nx,ny) - self._height(self.karel_x,self.karel_y)
        if dh > self.settings.max_climb: return
        self.karel_x,self.karel_y = nx,ny

    def move_back(self):
        back=self.karel_dir.opposite()
        if back.to_str() in self.walls[self.karel_y][self.karel_x]: return
        bx,by = self._step(self.karel_x,self.karel_y,back)
        dh = self._height(bx,by) - self._height(self.karel_x,self.karel_y)
        if dh > self.settings.max_climb: return
        self.karel_x,self.karel_y = bx,by

    def turn_left(self):  self.karel_dir=self.karel_dir.left()
    def turn_right(self): self.karel_dir=self.karel_dir.right()

    # Tehly/bricks: kladú/dvíhajú sa PRED Karelom; znacka je POD nim
    def drop_brick(self):
        if self.is_wall_ahead(): return
        if self._bricks_left == 0: return
        nx,ny=self._front(); self.bricks[ny][nx]+=1
        if self._bricks_left > 0: self._bricks_left -= 1
    def drop_big_brick(self):
        """Kvader (veľká tehla) — na políčku môže byť max 1 kvader."""
        if self.is_wall_ahead(): return
        if self._big_bricks_left == 0: return
        nx,ny=self._front()
        if self.big_bricks[ny][nx] >= 1: return
        self.big_bricks[ny][nx] = 1
        if self._big_bricks_left > 0: self._big_bricks_left -= 1
    def pick_brick(self):
        if self.is_wall_ahead(): return
        nx,ny=self._front()
        if self.bricks[ny][nx]<=0: return
        self.bricks[ny][nx]-=1
        if self._bricks_left >= 0: self._bricks_left += 1

    def pick_big_brick(self):
        """Zdvihne kvader spred Karela — len cez GUI, nie programovo."""
        if self.is_wall_ahead(): return
        nx,ny=self._front()
        if self.big_bricks[ny][nx]<=0: return
        self.big_bricks[ny][nx]-=1
        if self._big_bricks_left >= 0: self._big_bricks_left += 1

    def pick_any_brick(self):
        """Zdvihne malú tehlu ak je; ak nie, zdvihne kvader. Používa sa len z GUI."""
        nx,ny=self._front()
        if self.bricks[ny][nx] > 0:
            self.pick_brick()
        elif self.big_bricks[ny][nx] > 0:
            self.pick_big_brick()
    def mark(self):
        if not self.marks[self.karel_y][self.karel_x]:
            if self._marks_left == 0: return
            if self._marks_left > 0: self._marks_left -= 1
        self.marks[self.karel_y][self.karel_x]=True
    def clear(self):
        if self.marks[self.karel_y][self.karel_x]:
            if self._marks_left >= 0: self._marks_left += 1
        self.marks[self.karel_y][self.karel_x]=False

    def check_wall(self):
        if self.is_wall_ahead(): return True
        # Kvader pred Karelom — tiež sa správa ako stena
        nx,ny = self._front()
        return (0 <= nx < self.width and 0 <= ny < self.height and
                self.big_bricks[ny][nx] > 0)
    def check_brick(self):
        nx,ny=self._front()
        return (0<=nx<self.width and 0<=ny<self.height and
                (self.bricks[ny][nx]>0 or self.big_bricks[ny][nx]>0))
    def check_free(self):
        nx,ny=self._front()
        return not (0<=nx<self.width and 0<=ny<self.height and
                    (self.bricks[ny][nx]>0 or self.big_bricks[ny][nx]>0))
    def check_sign(self):  return self.marks[self.karel_y][self.karel_x]

    def to_json(self):
        return dict(width=self.width,height=self.height,
                    karel_x=self.karel_x,karel_y=self.karel_y,
                    karel_dir=self.karel_dir.to_str(),
                    walls=[[x,y,s] for y in range(self.height) for x in range(self.width) for s in self.walls[y][x]],
                    bricks=[[x,y,self.bricks[y][x]] for y in range(self.height) for x in range(self.width) if self.bricks[y][x]>0],
                    big_bricks=[[x,y,self.big_bricks[y][x]] for y in range(self.height) for x in range(self.width) if self.big_bricks[y][x]>0],
                    marks=[[x,y] for y in range(self.height) for x in range(self.width) if self.marks[y][x]])
    @staticmethod
    def from_json(d):
        w=World(d['width'],d['height'])
        w.karel_x=d['karel_x']; w.karel_y=d['karel_y']
        w.karel_dir=Direction.from_str(d['karel_dir'])
        for x,y,s in d.get('walls',[]): w.walls[y][x].add(s)
        for x,y,c in d.get('bricks',[]): w.bricks[y][x]=c
        for x,y,c in d.get('big_bricks',[]): w.big_bricks[y][x]=c
        for x,y   in d.get('marks',[]): w.marks[y][x]=True
        return w

    # ---- XML  ---------------------------------------------------------------
    def to_xml(self):
        """Vráti XML reťazec (.karxml formát)."""
        root = ET.Element('world', width=str(self.width), height=str(self.height))
        ET.SubElement(root, 'karel',
                      x=str(self.karel_x), y=str(self.karel_y),
                      dir=self.karel_dir.to_str())
        # steny
        ws = ET.SubElement(root, 'walls')
        for y in range(self.height):
            for x in range(self.width):
                for s in sorted(self.walls[y][x]):
                    ET.SubElement(ws, 'wall', x=str(x), y=str(y), side=s)
        # malé tehly
        br = ET.SubElement(root, 'bricks')
        for y in range(self.height):
            for x in range(self.width):
                if self.bricks[y][x] > 0:
                    ET.SubElement(br, 'brick', x=str(x), y=str(y), count=str(self.bricks[y][x]))
        # veľké tehly
        bb = ET.SubElement(root, 'bigbricks')
        for y in range(self.height):
            for x in range(self.width):
                if self.big_bricks[y][x] > 0:
                    ET.SubElement(bb, 'bigbrick', x=str(x), y=str(y), count=str(self.big_bricks[y][x]))
        # značky
        mk = ET.SubElement(root, 'marks')
        for y in range(self.height):
            for x in range(self.width):
                if self.marks[y][x]:
                    ET.SubElement(mk, 'mark', x=str(x), y=str(y))
        # metadáta
        def _txt(tag, val):
            if val:
                el = ET.SubElement(root, tag)
                el.text = val
        _txt('title',        self.title)
        _txt('intro',        self.intro_html)
        _txt('success',      self.success_html)
        _txt('failure',      self.failure_html)
        _txt('program',      self.program_text)
        _txt('next_level',   self.next_level)
        _txt('prev_level',   self.prev_level)
        # nastavenia sveta
        s = self.settings
        has_settings = (s.brick_limit!=-1 or s.big_brick_limit!=-1 or s.mark_limit!=-1
                        or s.disabled_cmds or s.disable_procedure or s.camera_locked
                        or s.max_climb != 1 or s.prog_lang != 'sk')
        if has_settings:
            st = ET.SubElement(root, 'settings')
            ET.SubElement(st,'max_climb').text        = str(s.max_climb)
            if s.prog_lang != 'sk':
                ET.SubElement(st,'prog_lang').text    = s.prog_lang
            ET.SubElement(st,'brick_limit').text     = str(s.brick_limit)
            ET.SubElement(st,'big_brick_limit').text = str(s.big_brick_limit)
            ET.SubElement(st,'mark_limit').text      = str(s.mark_limit)
            if s.disabled_cmds:
                ET.SubElement(st,'disabled_cmds').text = ','.join(sorted(s.disabled_cmds))
            if s.disable_procedure:
                ET.SubElement(st,'disable_procedure').text = 'true'
            if s.camera_locked:
                ET.SubElement(st,'camera_locked').text = 'true'
                ET.SubElement(st,'camera_az').text    = str(s.camera_az)
                ET.SubElement(st,'camera_el').text    = str(s.camera_el)
                ET.SubElement(st,'camera_dist').text  = str(s.camera_dist)
        # misia — podmienky splnenia
        if self.goal_conditions or self.mission_reset_on_failure:
            miss = ET.SubElement(root, 'mission')
            if self.mission_reset_on_failure:
                miss.set('reset_on_failure', 'true')
            for cond in self.goal_conditions:
                miss.append(cond.to_xml_el())
        # pekné formátovanie
        raw = ET.tostring(root, encoding='unicode')
        dom = minidom.parseString(raw)
        return dom.toprettyxml(indent='  ', encoding=None)

    @staticmethod
    def from_xml(xml_str):
        """Načíta svet z XML reťazca alebo cesty k súboru."""
        if os.path.isfile(xml_str):
            tree = ET.parse(xml_str)
            root = tree.getroot()
        else:
            root = ET.fromstring(xml_str)
        w = World(int(root.get('width')), int(root.get('height')))
        k = root.find('karel')
        if k is not None:
            w.karel_x = int(k.get('x', 0))
            w.karel_y = int(k.get('y', 0))
            w.karel_dir = Direction.from_str(k.get('dir', 'E'))
        for el in root.findall('walls/wall'):
            x, y, s = int(el.get('x')), int(el.get('y')), el.get('side')
            if 0 <= x < w.width and 0 <= y < w.height:
                w.walls[y][x].add(s)
        for el in root.findall('bricks/brick'):
            x, y = int(el.get('x')), int(el.get('y'))
            if 0 <= x < w.width and 0 <= y < w.height:
                w.bricks[y][x] = int(el.get('count', 1))
        for el in root.findall('bigbricks/bigbrick'):
            x, y = int(el.get('x')), int(el.get('y'))
            if 0 <= x < w.width and 0 <= y < w.height:
                w.big_bricks[y][x] = int(el.get('count', 1))
        for el in root.findall('marks/mark'):
            x, y = int(el.get('x')), int(el.get('y'))
            if 0 <= x < w.width and 0 <= y < w.height:
                w.marks[y][x] = True
        def _gtxt(tag): el = root.find(tag); return el.text.strip() if el is not None and el.text else ''
        w.title        = _gtxt('title')
        w.intro_html   = _gtxt('intro')
        w.success_html = _gtxt('success')
        w.failure_html = _gtxt('failure')
        w.program_text = _gtxt('program')
        w.next_level   = _gtxt('next_level')
        w.prev_level   = _gtxt('prev_level')
        # nastavenia
        st = root.find('settings')
        if st is not None:
            def _gi(tag,d):
                el=st.find(tag); return int(el.text) if el is not None and el.text else d
            def _gb(tag):
                el=st.find(tag); return el is not None and (el.text or '').strip().lower()=='true'
            def _gf(tag,d):
                el=st.find(tag); return float(el.text) if el is not None and el.text else d
            w.settings.max_climb       = _gi('max_climb', 1)
            pl_el = st.find('prog_lang')
            w.settings.prog_lang = (pl_el.text.strip().lower()
                                    if pl_el is not None and pl_el.text else 'sk')
            # fallback: ak .lng pre daný jazyk neexistuje, použi sk
            if not os.path.exists(os.path.join(_INTERP_LANG_DIR, f'{w.settings.prog_lang}.lng')):
                w.settings.prog_lang = 'sk'
            w.settings.brick_limit     = _gi('brick_limit',-1)
            w.settings.big_brick_limit = _gi('big_brick_limit',-1)
            w.settings.mark_limit      = _gi('mark_limit',-1)
            dc = st.find('disabled_cmds')
            if dc is not None and dc.text:
                w.settings.disabled_cmds = set(dc.text.strip().split(','))
            w.settings.disable_procedure = _gb('disable_procedure')
            w.settings.camera_locked     = _gb('camera_locked')
            if w.settings.camera_locked:
                w.settings.camera_az   = _gf('camera_az',  math.radians(225))
                w.settings.camera_el   = _gf('camera_el',  math.radians(28))
                w.settings.camera_dist = _gf('camera_dist', 16.0)
        # misia
        miss_el = root.find('mission')
        if miss_el is not None:
            w.mission_reset_on_failure = (miss_el.get('reset_on_failure','') == 'true')
            for cel in miss_el.findall('condition'):
                w.goal_conditions.append(GoalCondition.from_xml_el(cel))
        return w

    def copy(self): return deepcopy(self)


# =========================================================================
# LEXER  +  PARSER  +  INTERPRETER
# =========================================================================

KW: dict = {}            # word.lower() → TOKEN  (všetky jazyky naraz)
_LANG_PRIMARY: dict = {} # lang_code → {TOKEN: primary_word}
_LANG_DISABLED: dict = {} # lang_code → set of TOKEN names disabled by default
_LANG_NAME:     dict = {} # lang_code → display name (z NAME direktívy v .lng)
_INTERP_LANG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'lang', 'interpreter')

def _load_all_interpreter_langs() -> None:
    """Načíta všetky lang/interpreter/*.lng súbory.
    KW sa naplní všetkými kľúčovými slovami zo všetkých jazykov —
    interpreter tak akceptuje ľubovoľný jazyk súčasne.
    _LANG_PRIMARY uloží primárne slovo (prvé) pre každý jazyk a token.
    _LANG_DISABLED uloží set tokenov, ktoré sú v danom jazyku štandardne zakázané."""
    global KW, _LANG_PRIMARY, _LANG_DISABLED, _LANG_NAME
    KW.clear(); _LANG_PRIMARY.clear(); _LANG_DISABLED.clear(); _LANG_NAME.clear()
    if not os.path.isdir(_INTERP_LANG_DIR):
        _fallback_bkw(); return
    for fname in sorted(os.listdir(_INTERP_LANG_DIR)):
        if not fname.endswith('.lng'): continue
        lang = fname[:-4].lower()   # 'sk', 'en', 'de', 'en_pattis', …
        _LANG_PRIMARY[lang] = {}
        path = os.path.join(_INTERP_LANG_DIR, fname)
        try:
            with open(path, encoding='utf-8') as f:
                lines = f.readlines()
        except OSError:
            continue
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'): continue
            if '=' not in line: continue
            token, _, rest = line.partition('=')
            token = token.strip().upper()
            words = rest.split()
            if not words: continue
            if token == 'NAME':
                # Direktíva NAME — zobrazený názov jazyka v dropdowne
                _LANG_NAME[lang] = rest.strip()
                continue
            if token == 'DISABLED':
                # Direktíva DISABLED — tieto tokeny sa pri výbere jazyka automaticky zakážu
                _LANG_DISABLED[lang] = set(w.upper() for w in words)
                continue
            _LANG_PRIMARY[lang][token] = words[0].lower()
            for w in words:
                KW[w.lower()] = token
    # Ak žiadne súbory nenašiel, použi hardcoded zálohu
    if not KW:
        _fallback_bkw()

def _fallback_bkw() -> None:
    """Núdzový fallback — hardcoded SK+EN kľúčové slová ak chýbajú .lng súbory."""
    for t,vs in [
        ('BEGIN',['begin','zaciatok','začiatok']),('END',['end','koniec']),
        ('PROCEDURE',['procedure','prikaz','príkaz']),
        ('REPEAT',['repeat','opakuj']),('TIMES',['times','krat','krát']),
        ('END_REPEAT',['*repeat','*opakuj']),
        ('WHILE',['while','kym','kým']),('NOT',['not','nie']),('DO',['do','rob']),
        ('END_WHILE',['*while','*kym','*kým']),
        ('IF',['if','ak']),('THEN',['then','tak','potom']),
        ('ELSE',['else','inak']),('END_IF',['*if','*ak']),
        ('FORWARD',['forward','dopredu']),('BACK',['back','dozadu','vzad']),
        ('LEFT',['left','vlavo','dolava','vľavo','doľava']),
        ('RIGHT',['right','vpravo','doprava']),
        ('DROP',['drop','poloz','polož']),('PICK',['pick','zdvihni','zodvihni']),
        ('DROP_BIG',['drop_big','drop_b','dropb','poloz_velku','poloz_v','polozv']),
        ('MARK',['mark','oznac','označ']),
        ('CLEAR',['clear','unmark','odznac','ocisti','cisti','odznač','očisti','čisti']),
        ('WALL',['wall','stena','je_stena','is_wall']),
        ('BRICK',['brick','tehla','je_tehla','is_brick']),
        ('FREE',['free','volno','voľno','is_free']),
        ('SIGN',['sign','znacka','značka','je_znacka','is_sign']),
        ('FALSE',['false','nepravda']),('TRUE',['true','pravda']),
        ('SLOWLY',['slowly','slow','pomaly','spomal']),
        ('QUICKLY',['quickly','quick','rychlo','rýchlo','pridaj']),
    ]:
        for v in vs: KW[v] = t
    _LANG_PRIMARY['sk'] = {
        'BEGIN':'zaciatok','END':'koniec','PROCEDURE':'prikaz','REPEAT':'opakuj',
        'TIMES':'krat','END_REPEAT':'*opakuj','WHILE':'kym','NOT':'nie','DO':'rob',
        'END_WHILE':'*kym','IF':'ak','THEN':'potom','ELSE':'inak','END_IF':'*ak',
        'FORWARD':'dopredu','BACK':'dozadu','LEFT':'vlavo','RIGHT':'vpravo',
        'DROP':'poloz','PICK':'zdvihni','DROP_BIG':'poloz_velku',
        'MARK':'oznac','CLEAR':'odznac','WALL':'stena','BRICK':'tehla',
        'FREE':'volno','SIGN':'znacka','FALSE':'nepravda','TRUE':'pravda',
        'SLOWLY':'pomaly','QUICKLY':'rychlo',
    }
    _LANG_PRIMARY['en'] = {
        'BEGIN':'begin','END':'end','PROCEDURE':'procedure','REPEAT':'repeat',
        'TIMES':'times','END_REPEAT':'*repeat','WHILE':'while','NOT':'not','DO':'do',
        'END_WHILE':'*while','IF':'if','THEN':'then','ELSE':'else','END_IF':'*if',
        'FORWARD':'forward','BACK':'back','LEFT':'left','RIGHT':'right',
        'DROP':'drop','PICK':'pick','DROP_BIG':'drop_big',
        'MARK':'mark','CLEAR':'clear','WALL':'wall','BRICK':'brick',
        'FREE':'free','SIGN':'sign','FALSE':'false','TRUE':'true',
        'SLOWLY':'slowly','QUICKLY':'quickly',
    }

_load_all_interpreter_langs()

def _primary_kw(token: str, lang: str) -> str:
    """Vráti primárne kľúčové slovo pre daný token v danom jazyku.
    Fallback: EN, potom lowercase token."""
    return (_LANG_PRIMARY.get(lang, {}).get(token)
            or _LANG_PRIMARY.get('en', {}).get(token)
            or token.lower())

# Spätné mapovanie: token → [varianty slov]  (pre highlighting zakázaných príkazov)
_KW_REVERSE: dict = {}
for _kw, _kt in KW.items():
    _KW_REVERSE.setdefault(_kt, []).append(_kw)

CMD_T={'FORWARD','BACK','LEFT','RIGHT','DROP','PICK','DROP_BIG','MARK','CLEAR','SLOWLY','QUICKLY'}
COND_T={'WALL','BRICK','FREE','SIGN','TRUE','FALSE'}
CLOSE_T={'END','END_REPEAT','END_WHILE','END_IF'}

class Tok:
    __slots__=('t','v','ln')
    def __init__(self,t,v,ln=0): self.t=t;self.v=v;self.ln=ln

def tokenize(src):
    src=re.sub(r'//[^\n]*',' ',src); src=re.sub(r'#[^\n]*',' ',src)
    src=re.sub(r'\{[^}]*\}',' ',src)
    toks=[]; ln=1; i=0; n=len(src)
    while i<n:
        c=src[i]
        if c=='\n': ln+=1;i+=1;continue
        if c.isspace(): i+=1;continue
        if c=='*':
            j=i+1
            while j<n and (src[j].isalpha() or src[j]=='_' or ord(src[j])>127): j+=1
            w=src[i:j].lower(); toks.append(Tok(KW.get(w,'UNK'),src[i:j],ln)); i=j;continue
        if c.isdigit():
            j=i
            while j<n and src[j].isdigit(): j+=1
            toks.append(Tok('NUM',src[i:j],ln)); i=j;continue
        if c.isalpha() or c=='_' or ord(c)>127:
            j=i
            while j<n and (src[j].isalnum() or src[j]=='_' or ord(src[j])>127): j+=1
            w=src[i:j]; toks.append(Tok(KW.get(w.lower(),'ID'),w,ln)); i=j;continue
        i+=1
    toks.append(Tok('EOF','',ln)); return toks

class AN: pass
class ProgN(AN):
    def __init__(self,p,m): self.procedures=p;self.main_stmts=m
class CmdN(AN):
    def __init__(self,c,ln=0): self.cmd=c;self.line=ln
class CallN(AN):
    def __init__(self,n,ln=0): self.name=n;self.line=ln
class RepN(AN):
    def __init__(self,n,b,ln=0): self.count=n;self.body=b;self.line=ln
class WhileN(AN):
    def __init__(self,c,b,ln=0): self.cond=c;self.body=b;self.line=ln
class IfN(AN):
    def __init__(self,c,t,e,ln=0): self.cond=c;self.then_body=t;self.else_body=e;self.line=ln
class CondN(AN):
    def __init__(self,ct,neg=False): self.cond_type=ct;self.negated=neg

class ParseErr(Exception):
    def __init__(self,m,ln=0): super().__init__(f"Riadok {ln}: {m}");self.line=ln

class Parser:
    def __init__(self,toks): self.toks=toks;self.pos=0
    def pk(self): return self.toks[self.pos]
    def eat(self,exp=None):
        t=self.toks[self.pos]
        if exp and t.t!=exp: raise ParseErr(f"Čakal som '{exp}', dostal '{t.t}'('{t.v}')",t.ln)
        self.pos+=1; return t
    def parse(self):
        ps={}; main=None
        while self.pk().t!='EOF':
            t=self.pk()
            if t.t=='PROCEDURE': n,b=self._proc(); ps[n.lower()]=b
            elif t.t=='BEGIN': self.eat(); main=self._stmts()
            if self.pk().t in CLOSE_T: self.eat()
            elif t.t not in ('PROCEDURE','BEGIN'): self.pos+=1
        return ProgN(ps,main or [])
    def _proc(self):
        self.eat('PROCEDURE'); t=self.pk()
        if t.t in ('ID','NUM'): name=self.eat().v
        else: raise ParseErr(f"Čakám meno príkazu",t.ln)
        if self.pk().t=='BEGIN': self.eat()
        body=self._stmts()
        if self.pk().t in CLOSE_T: self.eat()
        return name,body
    def _stmts(self):
        s=[]
        while self.pk().t not in CLOSE_T and self.pk().t not in ('ELSE','EOF'):
            n=self._stmt()
            if n: s.append(n)
        return s
    def _stmt(self):
        t=self.pk()
        if t.t in CMD_T: self.eat(); return CmdN(t.t,t.ln)
        if t.t=='REPEAT': return self._rep()
        if t.t=='WHILE':  return self._whl()
        if t.t=='IF':     return self._if()
        if t.t in ('ID','NUM'): self.eat(); return CallN(t.v,t.ln)
        if t.t=='BEGIN': self.eat(); return None
        self.pos+=1; return None
    def _rep(self):
        t=self.eat('REPEAT'); n=int(self.eat('NUM').v)
        if self.pk().t=='TIMES': self.eat()
        b=self._stmts()
        if self.pk().t in CLOSE_T: self.eat()
        return RepN(n,b,t.ln)
    def _whl(self):
        t=self.eat('WHILE'); c=self._cond()
        if self.pk().t=='DO': self.eat()
        b=self._stmts()
        if self.pk().t in CLOSE_T: self.eat()
        return WhileN(c,b,t.ln)
    def _if(self):
        t=self.eat('IF'); c=self._cond()
        if self.pk().t in ('THEN','BEGIN'): self.eat()
        tb=self._stmts(); eb=[]
        if self.pk().t=='ELSE': self.eat(); eb=self._stmts()
        if self.pk().t in CLOSE_T: self.eat()
        return IfN(c,tb,eb,t.ln)
    def _cond(self):
        neg=False
        if self.pk().t=='NOT': self.eat(); neg=True
        t=self.pk()
        if t.t in COND_T: self.eat(); return CondN(t.t,neg)
        raise ParseErr(f"Podmienka očakávaná, dostal '{t.v}'",t.ln)

def parse(src): return Parser(tokenize(src)).parse()

class StopEx(Exception): pass

class KarelInterpreter:
    MAX_D=500
    def __init__(self,world):
        self.world=world; self.delay=0.25
        self._stop=False; self._d=0; self.procedures={}
        self.on_step=self.on_error=self.on_finish=None
    def stop(self): self._stop=True
    def run(self,prog):
        self._stop=False; self._d=0; self.procedures=prog.procedures
        try:
            self._ex(prog.main_stmts)
            if self.on_finish: self.on_finish(None)
        except StopEx:
            if self.on_finish: self.on_finish("Zastavené.")
        except KarelStop:
            if self.on_finish: self.on_finish(None)   # tiché zastavenie pri stene
        except (KarelError,RecursionError) as e:
            m="Príliš hlboká rekurzia!" if isinstance(e,RecursionError) else str(e)
            if self.on_error: self.on_error(m)
        except Exception as e:
            if self.on_error: self.on_error(f"Chyba: {e}")
    def _ex(self,stmts):
        for s in stmts:
            if self._stop: raise StopEx()
            self._rs(s)
    def _rs(self,s):
        if isinstance(s,CmdN): self._cmd(s)
        elif isinstance(s,CallN): self._call(s.name)
        elif isinstance(s,RepN):
            for _ in range(s.count):
                if self._stop: raise StopEx()
                self._ex(s.body)
        elif isinstance(s,WhileN):
            while self._ev(s.cond):
                if self._stop: raise StopEx()
                self._ex(s.body)
        elif isinstance(s,IfN):
            self._ex(s.then_body if self._ev(s.cond) else s.else_body)
    def _call(self,name):
        self._d+=1
        if self._d>self.MAX_D: raise KarelError("Príliš hlboká rekurzia!")
        try:
            nl=name.lower()
            if nl not in self.procedures: raise KarelError(f"Neznámy príkaz '{name}'")
            self._ex(self.procedures[nl])
        finally: self._d-=1
    def _cmd(self,node):
        w=self.world; c=node.cmd
        if c in w.settings.disabled_cmds:
            raise KarelError(f"Príkaz je zakázaný v tomto svete!")
        if   c=='FORWARD':  w.move_forward()
        elif c=='BACK':     w.move_back()
        elif c=='LEFT':     w.turn_left()
        elif c=='RIGHT':    w.turn_right()
        elif c=='DROP':     w.drop_brick()
        elif c=='PICK':     w.pick_brick()
        elif c=='DROP_BIG': w.drop_big_brick()
        elif c=='MARK':     w.mark()
        elif c=='CLEAR':    w.clear()
        elif c=='SLOWLY':   self.delay=min(self.delay*2,3.0)
        elif c=='QUICKLY':  self.delay=max(self.delay/2,0.02)
        if self.on_step: self.on_step()
        if self.delay>0: time.sleep(self.delay)
    def _ev(self,cond):
        w=self.world; ct=cond.cond_type
        r=(w.check_wall() if ct=='WALL' else w.check_brick() if ct=='BRICK'
           else w.check_free() if ct=='FREE' else w.check_sign() if ct=='SIGN'
           else True if ct=='TRUE' else False)
        return (not r) if cond.negated else r


# =========================================================================
# VSTAVANÝ SVET  +  PRÍKLADY
# =========================================================================

BUILTIN_WORLD={
    "width":10,"height":8,"karel_x":1,"karel_y":1,"karel_dir":"E",
    "walls":[],
    "bricks":[],
    "marks":[]
}

EXAMPLES={
"Prázdny/Empty":"""\
# Karel 2010 – program
# Slovak: zaciatok/koniec, dopredu, vlavo, vpravo, dozadu
#   poloz=pred seba, zdvihni=z pred seba, oznac=pod seba
#   opakuj N krat ... koniec
#   kym podmienka rob ... koniec
#   ak podmienka potom ... inak ... koniec
zaciatok
  dopredu
  dopredu
  vlavo
  dopredu
koniec
""",
"Štvorec/Square":"""\
prikaz Strana
zaciatok
  opakuj 3 krat dopredu koniec
  vlavo
koniec

zaciatok
  opakuj 4 krat Strana koniec
koniec
""",
"Stavanie múru/Build wall":"""\
# Karel stavia múr z tehál pred sebou
zaciatok
  opakuj 4 krat
    poloz
    dopredu
  koniec
koniec
""",
"Zbieranie tehál/Collect":"""\
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
""",
"Samba":"""\
prikaz Samba
zaciatok
  vlavo dopredu vpravo dozadu dopredu vpravo
  opakuj 2 krat dopredu vlavo vpravo koniec
  vlavo dozadu dopredu vlavo dopredu vpravo
  Samba
koniec
Zaciatok Samba Koniec
""",
"Valčík/Waltz":"""\
prikaz Valcik
zaciatok
  opakuj 4 krat
    opakuj 2 krat dopredu koniec
    vlavo
  koniec
koniec
zaciatok opakuj 6 krat Valcik koniec koniec
""",
"Označenie trate/Mark path":"""\
zaciatok
  kym nie stena rob oznac dopredu koniec
  oznac
koniec
""",
"Bludisko/Maze":"""\
prikaz Krok
zaciatok
  ak stena potom vlavo inak dopredu koniec
koniec
zaciatok opakuj 80 krat Krok koniec koniec
""",
}


# =========================================================================
# 3D  PERSPEKTÍVNY  RENDERER
# =========================================================================

def _norm(v):
    l=math.sqrt(sum(x*x for x in v)); return [x/l for x in v] if l>1e-9 else [0,0,1]
def _cross(a,b):
    return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def _dot(a,b): return sum(x*y for x,y in zip(a,b))

# Farby sveta
FC={
    'floor_a':'#0000bb','floor_b':'#0000aa','floor_mark':'#2244cc',
    'grid':'#3344dd',
    'wall':'#dddd00','wall_dark':'#aaaa00','wall_top':'#ffff44',
    'wall_inner':'#888800',
    'brick_top':'#44cc22','brick_s':'#228811','brick_d':'#115500',
    # veľká tehla (kvader) — hnedá, výrazne odlíšená od malých tehál
    'bbrick_top':'#993311','bbrick_s':'#661100','bbrick_d':'#440a00',
    'mark':'#44ff88','mark2':'#ffff44',
    'ground':'#000033',
    'sky':'#000011',
}
WALL_H=1.2; BRICK_H=0.27; FLOOR_T=0.06   # BRICK_H = 2/3 pôvodnej výšky

class Camera:
    def __init__(self):
        self.az=math.radians(225); self.el=math.radians(28)
        self.dist=16.0; self.fov=50; self.target=[5.0,4.0,0.0]
    def set_center(self,w,h): self.target=[w/2,h/2,0.0]
    def _basis(self):
        az,el,r=self.az,self.el,self.dist
        cam=[self.target[0]+r*math.cos(el)*math.cos(az),
             self.target[1]+r*math.cos(el)*math.sin(az),
             self.target[2]+r*math.sin(el)]
        look=_norm([self.target[i]-cam[i] for i in range(3)])
        right=_norm(_cross(look,[0,0,1]))
        up=_cross(right,look)
        return cam,look,right,up
    def project(self,pts3d,cw,ch):
        cam,look,right,up=self._basis()
        f=ch/(2*math.tan(math.radians(self.fov)/2))
        out=[]
        for wx,wy,wz in pts3d:
            dx=wx-cam[0];dy=wy-cam[1];dz=wz-cam[2]
            rx=dx*right[0]+dy*right[1]+dz*right[2]
            ry=dx*up[0]+dy*up[1]+dz*up[2]
            rz=dx*look[0]+dy*look[1]+dz*look[2]
            if rz<0.05: out.append(None); continue
            out.append((cw/2+f*rx/rz, ch/2-f*ry/rz, rz))
        return out


# prio=0 → podlaha (vždy vzadu, vykreslí sa pred 3D objektmi)
# prio=1 → steny, tehly, Karel (depth-sorted)
def _face(pts,col,ol=False,oc='#000000',normal=None,prio=1): return (pts,col,ol,oc,normal,prio)

def world_faces(w):
    """Vráti všetky 3D plochy sveta ako [(verts,color,outline),...]."""
    W,H=w.width,w.height; F=[]

    # Dlaždice / tiles  — jednotná farba, outline = mriežka
    for gy in range(H):
        for gx in range(W):
            x0,y0,x1,y1=gx,gy,gx+1,gy+1
            has_mark = w.marks[gy][gx]
            tile_h   = w._height(gx, gy)
            # Farba podlahy — modrý odtieň len keď je značka BEZ tehál
            c = FC['floor_mark'] if (has_mark and tile_h == 0) else FC['floor_a']
            F.append(_face([(x0,y0,0),(x1,y0,0),(x1,y1,0),(x0,y1,0)],c,True,FC['grid'],None,0))
            if has_mark:
                m  = 0.2
                # Značka sa zobrazí na vrchu stohu tehál — prio=1 ak sú tehly (Z-buffer)
                mz   = tile_h * BRICK_H + 0.015
                mprio = 1 if tile_h > 0 else 0
                F.append(_face([(x0+m,y0+m,mz),(x1-m,y1-m,mz),(x1-m+0.05,y1-m,mz),(x0+m+0.05,y0+m,mz)],FC['mark2'],False,'',None,mprio))
                F.append(_face([(x1-m,y0+m,mz),(x0+m,y1-m,mz),(x0+m,y1-m+0.05,mz),(x1-m,y0+m+0.05,mz)],FC['mark2'],False,'',None,mprio))

    # Steny / walls
    for gy in range(H):
        for gx in range(W):
            x0,y0,x1,y1=gx,gy,gx+1,gy+1
            for side in w.walls[gy][gx]:
                # Normála ukazuje DOVNÚTRA miestnosti — back-face culling skryje stenu
                # keď sa na ňu pozeráme zvonku
                if side=='N':
                    n=(0,-1,0)  # severná stena, interiér smeruje na juh
                    F.append(_face([(x0,y1,0),(x1,y1,0),(x1,y1,WALL_H),(x0,y1,WALL_H)],FC['wall'],False,'',n))
                    F.append(_face([(x0,y1,WALL_H),(x1,y1,WALL_H),(x1,y1-0.06,WALL_H),(x0,y1-0.06,WALL_H)],FC['wall_top'],False,'',n))
                elif side=='S':
                    n=(0,1,0)   # južná stena, interiér smeruje na sever
                    F.append(_face([(x0,y0,0),(x1,y0,0),(x1,y0,WALL_H),(x0,y0,WALL_H)],FC['wall_dark'],False,'',n))
                    F.append(_face([(x0,y0,WALL_H),(x1,y0,WALL_H),(x1,y0+0.06,WALL_H),(x0,y0+0.06,WALL_H)],FC['wall_top'],False,'',n))
                elif side=='E':
                    n=(-1,0,0)  # východná stena, interiér smeruje na západ
                    F.append(_face([(x1,y0,0),(x1,y1,0),(x1,y1,WALL_H),(x1,y0,WALL_H)],FC['wall'],False,'',n))
                    F.append(_face([(x1,y0,WALL_H),(x1,y1,WALL_H),(x1-0.06,y1,WALL_H),(x1-0.06,y0,WALL_H)],FC['wall_top'],False,'',n))
                elif side=='W':
                    n=(1,0,0)   # západná stena, interiér smeruje na východ
                    F.append(_face([(x0,y0,0),(x0,y1,0),(x0,y1,WALL_H),(x0,y0,WALL_H)],FC['wall_dark'],False,'',n))
                    F.append(_face([(x0,y0,WALL_H),(x0,y1,WALL_H),(x0+0.06,y1,WALL_H),(x0+0.06,y0,WALL_H)],FC['wall_top'],False,'',n))

    # Malé tehly / small bricks  — normály = back-face culling, žiadne artefakty
    # Malé tehly sedia NA VRCHU kvadera (ak je prítomný), nie pod ním
    BIG_H = BRICK_H * World.BIG_BRICK_UNITS
    for gy in range(H):
        for gx in range(W):
            n=w.bricks[gy][gx]
            base_z = w.big_bricks[gy][gx] * BIG_H   # 0 ak nie je kvader, BIG_H ak je
            for z in range(n):
                z0 = base_z + z*BRICK_H
                z1 = base_z + (z+1)*BRICK_H
                m=0.07; bx0,bx1,by0,by1=gx+m,gx+1-m,gy+m,gy+1-m
                F.append(_face([(bx0,by0,z1),(bx1,by0,z1),(bx1,by1,z1),(bx0,by1,z1)],FC['brick_top'],True,'#114400',(0,0,1)))
                F.append(_face([(bx0,by0,z0),(bx1,by0,z0),(bx1,by0,z1),(bx0,by0,z1)],FC['brick_s'],True,'#113300',(0,-1,0)))
                F.append(_face([(bx1,by0,z0),(bx1,by1,z0),(bx1,by1,z1),(bx1,by0,z1)],FC['brick_d'],True,'#112200',(1,0,0)))
                F.append(_face([(bx1,by1,z0),(bx0,by1,z0),(bx0,by1,z1),(bx1,by1,z1)],FC['brick_s'],True,'#113300',(0,1,0)))
                F.append(_face([(bx0,by1,z0),(bx0,by0,z0),(bx0,by0,z1),(bx0,by1,z1)],FC['brick_d'],True,'#112200',(-1,0,0)))

    # Kvader (veľká tehla) — renderuje sa ako JEDEN monolitický blok bez vrstiev
    # BIG_H je už definovaný vyššie v sekcii malých tehál
    for gy in range(H):
        for gx in range(W):
            nb = w.big_bricks[gy][gx]
            for z in range(nb):
                z0 = z * BIG_H   # kvader je vždy na dne (malé tehly sú na vrchu)
                z1 = z0 + BIG_H
                m  = 0.05
                bx0,bx1,by0,by1 = gx+m, gx+1-m, gy+m, gy+1-m
                # 4 bočné plochy — celá výška naraz (žiadne vrstvové línie)
                F.append(_face([(bx0,by0,z0),(bx1,by0,z0),(bx1,by0,z1),(bx0,by0,z1)],FC['bbrick_s'],True,'#220500',(0,-1,0)))
                F.append(_face([(bx1,by0,z0),(bx1,by1,z0),(bx1,by1,z1),(bx1,by0,z1)],FC['bbrick_d'],True,'#220500',(1,0,0)))
                F.append(_face([(bx1,by1,z0),(bx0,by1,z0),(bx0,by1,z1),(bx1,by1,z1)],FC['bbrick_s'],True,'#220500',(0,1,0)))
                F.append(_face([(bx0,by1,z0),(bx0,by0,z0),(bx0,by0,z1),(bx0,by1,z1)],FC['bbrick_d'],True,'#220500',(-1,0,0)))
                # Horná plocha
                F.append(_face([(bx0,by0,z1),(bx1,by0,z1),(bx1,by1,z1),(bx0,by1,z1)],FC['bbrick_top'],True,'#330800',(0,0,1)))
    return F


def karel_faces(w):
    """3D humanoidná postavička Karela (tan/béžová farba ako originál)."""
    gx,gy=w.karel_x,w.karel_y; d=w.karel_dir
    zb = w.bricks[gy][gx]*BRICK_H + w.big_bricks[gy][gx]*BRICK_H*World.BIG_BRICK_UNITS
    cx,cy=gx+0.5,gy+0.5

    # Smer dopredu a doprava v súradniciach sveta
    _FW = {Direction.EAST:(1,0), Direction.WEST:(-1,0),
           Direction.NORTH:(0,1), Direction.SOUTH:(0,-1)}
    _RT = {Direction.EAST:(0,1), Direction.WEST:(0,-1),
           Direction.NORTH:(1,0), Direction.SOUTH:(-1,0)}
    FW = _FW[d]
    RT = _RT[d]

    SK='#c8a870'; DK='#a08858'; FC2='#d8b880'; EY='#ffffff'; PU='#003300'

    def w2(fx,ry,z):
        return (cx+fx*FW[0]+ry*RT[0], cy+fx*FW[1]+ry*RT[1], zb+z)

    F=[]
    def box(fx0,ry0,z0,fx1,ry1,z1,top,front,side,back=None):
        if back is None: back=side
        def v(a,b,c): return w2(a,b,c)
        # Normály v lokálnych osiach → transformujeme na svetové súradnice
        nfwd  = (FW[0], FW[1], 0)      # smer dopredu (+fx)
        nbck  = (-FW[0],-FW[1], 0)     # smer dozadu  (-fx)
        nrgt  = (RT[0],  RT[1], 0)     # smer doprava (+ry)
        nlft  = (-RT[0],-RT[1], 0)     # smer doľava  (-ry)
        # top — normála hore
        F.append(_face([v(fx0,ry0,z1),v(fx1,ry0,z1),v(fx1,ry1,z1),v(fx0,ry1,z1)],top,False,'', (0,0,1)))
        # front (fx1 = čelná, smer pohybu)
        F.append(_face([v(fx1,ry0,z0),v(fx1,ry1,z0),v(fx1,ry1,z1),v(fx1,ry0,z1)],front,False,'',nfwd))
        # back (fx0 = zadná)
        F.append(_face([v(fx0,ry0,z0),v(fx0,ry1,z0),v(fx0,ry1,z1),v(fx0,ry0,z1)],back,False,'', nbck))
        # right side (ry1)
        F.append(_face([v(fx0,ry1,z0),v(fx1,ry1,z0),v(fx1,ry1,z1),v(fx0,ry1,z1)],side,False,'',nrgt))
        # left side (ry0)
        F.append(_face([v(fx0,ry0,z0),v(fx1,ry0,z0),v(fx1,ry0,z1),v(fx0,ry0,z1)],DK,False,'',  nlft))

    # Nohy / legs
    box(-0.12,-0.17,0, 0.12,-0.03,0.38, SK,SK,SK,DK)
    box(-0.12, 0.03,0, 0.12, 0.17,0.38, SK,SK,SK,DK)
    # Trup / torso
    box(-0.16,-0.20,0.38, 0.16,0.20,0.86, SK,FC2,DK,DK)
    # Ramená / shoulders (thin)
    box(-0.10,-0.25,0.64, 0.10,-0.20,0.82, SK,DK,DK,DK)
    box(-0.10, 0.20,0.64, 0.10, 0.25,0.82, SK,DK,DK,DK)
    # Hlava / head
    box(-0.14,-0.16,0.86, 0.14,0.16,1.26, SK,FC2,DK,DK)
    # Oči / eyes — rovnaká normála ako čelná strana hlavy
    nfwd=(FW[0],FW[1],0)
    for ry_eye in (-0.08, 0.08):
        er=0.04
        F.append(_face([w2(0.145,ry_eye-er,1.06),w2(0.145,ry_eye+er,1.06),
                        w2(0.145,ry_eye+er,1.14),w2(0.145,ry_eye-er,1.14)],EY,False,'',nfwd))
        pr=0.02
        F.append(_face([w2(0.148,ry_eye-pr,1.08),w2(0.148,ry_eye+pr,1.08),
                        w2(0.148,ry_eye+pr,1.12),w2(0.148,ry_eye-pr,1.12)],PU,False,'',nfwd))
    return F


# =========================================================================
# 3D  CANVAS  (mouse rotate/zoom/pan)
# =========================================================================

class World3D(tk.Canvas):
    def __init__(self,parent,world,**kw):
        super().__init__(parent,bg=FC['sky'],highlightthickness=0,**kw)
        self.world=world; self.cam=Camera()
        self.cam.set_center(world.width,world.height)
        self._ds=None; self._db=None
        self.on_cam_change=None   # nastaví App — po každej zmene kamery
        self.bind('<Configure>',      lambda e:self.render())
        self.bind('<ButtonPress-1>',   self._ds1)
        self.bind('<B1-Motion>',       self._dm1)
        self.bind('<ButtonRelease-1>', lambda e:setattr(self,'_ds',None))
        self.bind('<ButtonPress-3>',   self._ds1)
        self.bind('<B3-Motion>',       self._dm3)
        self.bind('<ButtonRelease-3>', lambda e:setattr(self,'_ds',None))
        self.bind('<MouseWheel>',      self._mw)
        self.bind('<Button-4>',        self._mw)
        self.bind('<Button-5>',        self._mw)

    def set_world(self,w):
        self.world=w; self.cam.set_center(w.width,w.height); self.render()

    def _ds1(self,e): self._ds=(e.x,e.y); self._db=e.num
    def _notify_cam(self):
        if self.on_cam_change: self.on_cam_change()
    def _cam_locked(self):
        return getattr(self.world,'settings',None) and self.world.settings.camera_locked

    def _dm1(self,e):
        if not self._ds: return
        if self._cam_locked(): return
        dx=e.x-self._ds[0]; dy=e.y-self._ds[1]; self._ds=(e.x,e.y)
        self.cam.az-=dx*0.007
        self.cam.el=max(math.radians(4),min(math.radians(82),self.cam.el+dy*0.007))
        self.render(); self._notify_cam()
    def _dm3(self,e):
        if not self._ds: return
        if self._cam_locked(): return
        dx=e.x-self._ds[0]; dy=e.y-self._ds[1]; self._ds=(e.x,e.y)
        _,_,right,up=self.cam._basis()
        s=self.cam.dist*0.0022
        for i in range(3):
            self.cam.target[i]-=dx*right[i]*s
            self.cam.target[i]+=dy*up[i]*s
        self.render(); self._notify_cam()
    def _mw(self,e):
        if self._cam_locked(): return
        f=0.9 if (e.num==4 or getattr(e,'delta',0)>0) else 1.1
        self.cam.dist=max(3,min(80,self.cam.dist*f))
        self.render(); self._notify_cam()

    def render(self):
        cw=self.winfo_width() or 600; ch=self.winfo_height() or 400
        if cw<20 or ch<20: return
        if _ZBUF:
            self._render_zbuf(cw,ch)
        else:
            self._render_painters(cw,ch)

    # ------------------------------------------------------------------
    # Z-BUFFER renderer  (numpy + PIL) — pixel-presný, žiadne artefakty
    # ------------------------------------------------------------------
    def _render_zbuf(self,cw,ch):
        z_buf = np.full((ch,cw), np.inf, dtype=np.float32)
        # BGR canal usporiadanie → RGB pri PIL
        bg = int(FC['sky'][1:3],16), int(FC['sky'][3:5],16), int(FC['sky'][5:7],16)
        c_buf = np.full((ch,cw,3), bg, dtype=np.uint8)

        all_faces  = world_faces(self.world)+karel_faces(self.world)
        cam_pos,_,_,_ = self.cam._basis()
        all_pts    = [p for f,_,_,_,_,_ in all_faces for p in f]
        proj       = self.cam.project(all_pts,cw,ch)

        idx=0
        draw=[]
        for face,col,ol,oc,nrm,prio in all_faces:
            n=len(face); ps=proj[idx:idx+n]; idx+=n
            if nrm is not None:
                fc=[sum(face[i][k] for i in range(n))/n for k in range(3)]
                if sum(nrm[k]*(cam_pos[k]-fc[k]) for k in range(3))<=0: continue
            if any(p is None for p in ps): continue
            pts2  = [(p[0],p[1]) for p in ps]
            deps  = [p[2]         for p in ps]
            avg_d = sum(deps)/n
            cr,cg,cb = int(col[1:3],16),int(col[3:5],16),int(col[5:7],16)
            draw.append((prio, avg_d, pts2, deps, cr,cg,cb, ol,oc))

        # Podlaha vždy vzadu (prio=0), pak 3D objekty depth-sorted
        draw.sort(key=lambda x: (x[0], -x[1]))

        for prio,avg_d,pts2,deps,cr,cg,cb,ol,oc in draw:
            self._rast_poly(pts2,deps,cr,cg,cb,z_buf,c_buf,ch,cw)
            if ol and oc and oc!='':
                # Obrysy — nakreslíme jednopixelové čiary pozdĺž hrán
                ocr,ocg,ocb = int(oc[1:3],16) if len(oc)==7 else (0,0,0), \
                              int(oc[3:5],16) if len(oc)==7 else (0,0,0), \
                              int(oc[5:7],16) if len(oc)==7 else (0,0,0)
                n=len(pts2)
                for i in range(n):
                    x0,y0=pts2[i]; x1,y1=pts2[(i+1)%n]
                    self._rast_line(int(x0),int(y0),int(x1),int(y1),
                                    ocr,ocg,ocb,c_buf,ch,cw)

        img   = Image.fromarray(c_buf,'RGB')
        photo = ImageTk.PhotoImage(img)
        self.delete('all')
        self.create_image(0,0,anchor='nw',image=photo)
        self._photo = photo   # udržať referenciu

    @staticmethod
    def _rast_poly(pts2,deps,cr,cg,cb,z_buf,c_buf,ch,cw):
        """Rasterizuj polygón s Z-buffer testom (triangle fan)."""
        n=len(pts2)
        if n<3: return
        col=np.array([cr,cg,cb],dtype=np.uint8)
        for i in range(1,n-1):
            World3D._rast_tri(
                pts2[0],deps[0], pts2[i],deps[i], pts2[i+1],deps[i+1],
                col, z_buf, c_buf, ch, cw)

    @staticmethod
    def _rast_tri(p0,z0, p1,z1, p2,z2, col, z_buf, c_buf, ch, cw):
        x0,y0=p0; x1,y1=p1; x2,y2=p2
        xmn=max(0,  int(min(x0,x1,x2)))
        xmx=min(cw-1,int(max(x0,x1,x2))+1)
        ymn=max(0,  int(min(y0,y1,y2)))
        ymx=min(ch-1,int(max(y0,y1,y2))+1)
        if xmn>=xmx or ymn>=ymx: return
        denom=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
        if abs(denom)<1e-6: return
        xs=np.arange(xmn,xmx+1,dtype=np.float32)
        ys=np.arange(ymn,ymx+1,dtype=np.float32)
        XX,YY=np.meshgrid(xs,ys)
        w0=((y1-y2)*(XX-x2)+(x2-x1)*(YY-y2))/denom
        w1=((y2-y0)*(XX-x2)+(x0-x2)*(YY-y2))/denom
        w2=1.0-w0-w1
        inside=(w0>=0)&(w1>=0)&(w2>=0)
        Z=w0*z0+w1*z1+w2*z2
        cur_z=z_buf[ymn:ymx+1,xmn:xmx+1]
        upd=inside&(Z<cur_z)
        cur_z[upd]=Z[upd]
        c_buf[ymn:ymx+1,xmn:xmx+1][upd]=col

    @staticmethod
    def _rast_line(x0,y0,x1,y1,cr,cg,cb,c_buf,ch,cw):
        """Bresenham čiara — pre obrysy."""
        col=np.array([cr,cg,cb],dtype=np.uint8)
        dx,dy=abs(x1-x0),abs(y1-y0)
        sx=1 if x0<x1 else -1; sy=1 if y0<y1 else -1
        err=dx-dy
        for _ in range(dx+dy+2):
            if 0<=x0<cw and 0<=y0<ch: c_buf[y0,x0]=col
            if x0==x1 and y0==y1: break
            e2=2*err
            if e2>-dy: err-=dy; x0+=sx
            if e2< dx: err+=dx; y0+=sy

    # ------------------------------------------------------------------
    # Fallback: painter's algorithm (bez numpy/PIL)
    # ------------------------------------------------------------------
    def _render_painters(self,cw,ch):
        self.delete('all')
        all_faces=world_faces(self.world)+karel_faces(self.world)
        cam_pos,_,_,_=self.cam._basis()
        all_pts=[p for face,_,_,_,_,_ in all_faces for p in face]
        proj=self.cam.project(all_pts,cw,ch)
        floor_pass=[]; solid_pass=[]; idx=0
        for face,col,ol,oc,nrm,prio in all_faces:
            n=len(face); ps=proj[idx:idx+n]; idx+=n
            if nrm is not None:
                fc=[sum(face[i][k] for i in range(n))/n for k in range(3)]
                if sum(nrm[k]*(cam_pos[k]-fc[k]) for k in range(3))<=0: continue
            if any(p is None for p in ps): continue
            pts2=[(p[0],p[1]) for p in ps]
            if prio==0: floor_pass.append((pts2,col,ol,oc))
            else:
                dep=sum(p[2] for p in ps)/n
                solid_pass.append((dep,pts2,col,ol,oc))
        for pts2,col,ol,oc in floor_pass:
            flat=[c for pt in pts2 for c in pt]
            if len(flat)>=6:
                self.create_polygon(flat,fill=col,outline=oc if ol else '',width=1 if ol else 0)
        solid_pass.sort(key=lambda x:-x[0])
        for dep,pts2,col,ol,oc in solid_pass:
            flat=[c for pt in pts2 for c in pt]
            if len(flat)>=6:
                self.create_polygon(flat,fill=col,outline=oc if ol else '',width=1 if ol else 0)


# =========================================================================
# NAVIGATOR  PANEL
# =========================================================================

class NavigatorPanel(tk.Frame):
    def __init__(self,parent,cam,on_change=None,**kw):
        super().__init__(parent,bg='#0a0a1c',relief='flat',**kw)
        self.cam=cam; self.on_change=on_change; self._build()

    def _build(self):
        self._nav_title=tk.Label(self,text=_T('nav.title'),bg='#111130',fg='#aaaacc',
                 font=('Arial',9,'bold'),pady=3)
        self._nav_title.pack(fill='x')

        # Inventár — hlavičky
        ifr=tk.Frame(self,bg='#0a0a1c'); ifr.pack(fill='x',padx=2,pady=1)
        self._inv_hdr = []
        for c,(key,fg) in enumerate([('nav.col_item','#8888cc'),('nav.col_left','#88ffcc')]):
            lbl=tk.Label(ifr,text=_T(key),bg='#141430',fg=fg,font=('Arial',7,'bold'),
                     padx=2,relief='flat')
            lbl.grid(row=0,column=c,sticky='ew')
            self._inv_hdr.append((lbl,key))
        ifr.columnconfigure(0,weight=1)   # item stĺpec sa rozťahuje, nie Zostatok
        self._inv_vars=[tk.StringVar(value='∞') for _ in range(3)]
        self._inv_row_lbls=[]
        for r,(key,var) in enumerate(zip(['nav.small_brick','nav.big_brick','nav.mark'],
                                          self._inv_vars),1):
            lbl=tk.Label(ifr,text=_T(key),bg='#0a0a1c',fg='#ccccdd',font=('Arial',7),
                         anchor='w',padx=2)
            lbl.grid(row=r,column=0,sticky='ew')
            tk.Label(ifr,textvariable=var,bg='#0a0a1c',fg='#44ffaa',
                     font=('Arial',8,'bold')).grid(row=r,column=1)
            self._inv_row_lbls.append((lbl,key))

        # Preset tlačidlá pohľadu
        bf=tk.Frame(self,bg='#0a0a1c'); bf.pack(fill='x',padx=2,pady=(1,0))
        self._preset_btns=[]
        self._preset_btn_keys=[]
        for key,az,el in [('nav.view_def',225,28),('nav.view_front',180,20),
                           ('nav.view_top',225,85), ('nav.view_side',135,18)]:
            def mk(a,e):
                def f():
                    self.cam.az=math.radians(a); self.cam.el=math.radians(e)
                    self.render_axes()
                    if self.on_change: self.on_change()
                return f
            b=tk.Button(bf,text=_T(key),command=mk(az,el),bg='#1a1a44',fg='#aaaaff',
                      relief='flat',font=('Arial',7),padx=2,pady=1,
                      cursor='hand2',activebackground='#3333aa',
                      activeforeground='white')
            b.pack(side='left',expand=True,fill='x',padx=1)
            self._preset_btns.append(b)
            self._preset_btn_keys.append(key)

        self.render_axes()

    def retranslate(self):
        """Aktualizuje všetky labely Navigátora po zmene jazyka GUI."""
        self._nav_title.configure(text=_T('nav.title'))
        for lbl,key in self._inv_hdr:
            lbl.configure(text=_T(key))
        for lbl,key in self._inv_row_lbls:
            lbl.configure(text=_T(key))
        for btn,key in zip(self._preset_btns, self._preset_btn_keys):
            btn.configure(text=_T(key))

    def set_camera_locked(self, locked):
        """Zakáže/povolí preset tlačidlá pohľadu."""
        state  = 'disabled' if locked else 'normal'
        fg     = '#444455'  if locked else '#aaaaff'
        cursor = ''         if locked else 'hand2'
        for b in self._preset_btns:
            b.configure(state=state, fg=fg, cursor=cursor)

    def update_inventory(self, world):
        b,bb,m = world.inventory_str()
        self._inv_vars[0].set(b)
        self._inv_vars[1].set(bb)
        self._inv_vars[2].set(m)

    def render_axes(self):
        pass   # os-canvas odstránený


# =========================================================================
# PROGRAM  PANEL  (editor + zoznam príkazov + filter)
# =========================================================================

def _hlidx(src,pos):
    ln=src[:pos].count('\n')+1; col=pos-src[:pos].rfind('\n')-1; return f'{ln}.{col}'

def highlight(tw, disabled_cmds=None, disable_procedure=False):
    src=tw.get('1.0','end')
    for tag in ('kw','cmd','cond','comment','number','disabled'):
        tw.tag_remove(tag,'1.0','end')
    # Komentáre: // jedno-riadkové, # jedno-riadkové, { } blokové
    comment_spans = []
    for m in re.finditer(r'//[^\n]*|#[^\n]*|\{[^}]*\}',src,re.DOTALL):
        tw.tag_add('comment',_hlidx(src,m.start()),_hlidx(src,m.end()))
        comment_spans.append((m.start(),m.end()))
    def _in_comment(pos):
        return any(s<=pos<e for s,e in comment_spans)
    for m in re.finditer(r'\b\d+\b',src):
        if not _in_comment(m.start()):
            tw.tag_add('number',_hlidx(src,m.start()),_hlidx(src,m.end()))
    CTRL={'begin','zaciatok','začiatok','end','koniec','procedure','prikaz','príkaz',
          'repeat','opakuj','times','krat','krát','*repeat','*opakuj',
          'while','kym','kým','do','rob','*while','*kym','*kým',
          'if','ak','then','tak','potom','else','inak','*if','*ak','not','nie'}
    CMDS={'forward','dopredu','back','dozadu','vzad','left','vlavo','dolava',
          'vľavo','doľava','right','vpravo','doprava','drop','poloz','pick',
          'zdvihni','zodvihni','drop_big','poloz_velku','mark','oznac','clear',
          'odznac','ocisti','slowly','pomaly','quickly','rýchlo','pridaj'}
    CONDS={'wall','stena','brick','tehla','free','volno','sign','znacka',
           'true','pravda','false','nepravda'}
    # Zakázané slová (podľa nastavení sveta)
    _dis_words: set = set()
    if disabled_cmds:
        for tok in disabled_cmds:
            _dis_words.update(_KW_REVERSE.get(tok, []))
    if disable_procedure:
        _dis_words.update(_KW_REVERSE.get('PROCEDURE', []))
    for m in re.finditer(r'\*?[\wÀ-ɏ]+',src,re.UNICODE):
        if _in_comment(m.start()): continue   # slová v komentároch sa nefárbia
        wl=m.group(0).lower()
        if wl in _dis_words:
            tw.tag_add('disabled',_hlidx(src,m.start()),_hlidx(src,m.end()))
            continue
        tag=('kw' if wl in CTRL else 'cmd' if wl in CMDS
             else 'cond' if wl in CONDS else None)
        if tag: tw.tag_add(tag,_hlidx(src,m.start()),_hlidx(src,m.end()))


def _cmds_list(disabled=None) -> list:
    """Zoznam základných príkazov v aktuálnom prog_lang (pre filter panel).
    Tokeny v množine disabled sú vynechané."""
    p = _primary_kw; L = _current_prog_lang
    toks = ['FORWARD','BACK','LEFT','RIGHT','DROP','DROP_BIG','PICK',
            'MARK','CLEAR','SLOWLY','QUICKLY']
    return [p(t,L) for t in toks if not (disabled and t in disabled)]

def _cmds_structs() -> list:
    """Zoznam riadiacich štruktúr v aktuálnom prog_lang."""
    p = _primary_kw; L = _current_prog_lang
    rep = p('REPEAT',L); tim = p('TIMES',L); end = p('END',L)
    whl = p('WHILE',L);  cnd = '…';         rob = p('DO',L)
    ifs = p('IF',L);     thn = p('THEN',L); els = p('ELSE',L)
    prc = p('PROCEDURE',L); bgn = p('BEGIN',L)
    return [
        f'{rep} N {tim} ... {end}',
        f'{whl} {cnd} {rob} ... {end}',
        f'{ifs} {cnd} {thn} ... {end}',
        f'{ifs} ... {thn} ... {els} ... {end}',
        f'{prc} Meno\n{bgn}\n\n{end}',
    ]

def _cmds_conds(disabled=None) -> list:
    """Zoznam podmienok v aktuálnom prog_lang. Tokeny v množine disabled sú vynechané."""
    p = _primary_kw; L = _current_prog_lang; n = p('NOT',L)
    d = disabled or set()
    conds = [p(t,L) for t in ['WALL','BRICK','FREE','SIGN','TRUE','FALSE'] if t not in d]
    conds += [f'{n} {p(t,L)}' for t in ['WALL','BRICK'] if t not in d]
    return conds

class ProgramPanel(tk.Frame):
    def __init__(self,parent,**kw):
        super().__init__(parent,bg='#080814',**kw)
        self._user_procs=[]; self.on_procs_update=None
        self._disabled_cmds: set = set()
        self._disable_procedure: bool = False
        self._build()

    def _build(self):
        hdr=tk.Frame(self,bg='#0d1030')
        hdr.pack(fill='x')
        self._hdr_lbl=tk.Label(hdr,text=_T('program_panel.title'),bg='#0d1030',fg='#44ff88',
                 font=('Arial',11,'bold'),pady=4,padx=8)
        self._hdr_lbl.pack(side='left')

        body=tk.Frame(self,bg='#080814'); body.pack(fill='both',expand=True)
        body.columnconfigure(0,weight=5); body.columnconfigure(1,weight=1,minsize=70)
        body.columnconfigure(2,weight=1,minsize=70); body.rowconfigure(0,weight=1)

        # ---- Ľavý: editor ----
        ef=tk.Frame(body,bg='#080814')
        ef.grid(row=0,column=0,sticky='nsew',padx=(3,1),pady=3)
        self.editor=tk.Text(ef,bg='#04040e',fg='#d4d4d4',font=('Consolas',12),
                             insertbackground='white',relief='flat',
                             padx=6,pady=6,undo=True)
        sb=ttk.Scrollbar(ef,command=self.editor.yview)
        self.editor.config(yscrollcommand=sb.set)
        sb.pack(side='right',fill='y'); self.editor.pack(fill='both',expand=True)
        self.editor.tag_configure('kw',foreground='#569cd6',font=('Consolas',12,'bold'))
        self.editor.tag_configure('cmd',foreground='#dcdcaa')
        self.editor.tag_configure('cond',foreground='#4ec9b0')
        self.editor.tag_configure('comment',foreground='#6a9955',font=('Consolas',12,'italic'))
        self.editor.tag_configure('number',foreground='#b5cea8')
        self.editor.tag_configure('disabled',foreground='#ff4444',background='#2a0000',
                                   font=('Consolas',12,'bold'))
        self.editor.bind('<KeyRelease>',lambda e:self.after_idle(self._on_edit))

        # ---- Stred: zoznam príkazov ----
        mf=tk.Frame(body,bg='#080814')
        mf.grid(row=0,column=1,sticky='nsew',padx=1,pady=3)
        self._cmd_list_hdr=tk.Label(mf,text=_T('program_panel.cmd_list_hdr'),
                 bg='#0d1030',fg='#aaaacc',font=('Arial',9,'bold'),pady=2)
        self._cmd_list_hdr.pack(fill='x')
        self._lb=tk.Listbox(mf,bg='#04040e',fg='#dcdcaa',font=('Consolas',10),
                             relief='flat',selectbackground='#2244aa',
                             activestyle='dotbox',exportselection=False,
                             height=4,width=8)
        sc=ttk.Scrollbar(mf,command=self._lb.yview)
        self._lb.config(yscrollcommand=sc.set)
        sc.pack(side='right',fill='y'); self._lb.pack(fill='both',expand=True)
        self._lb.bind('<Double-Button-1>',self._insert)
        self._fill_list(_cmds_list())

        # ---- Pravý: filter strom ----
        rf=tk.Frame(body,bg='#080814')
        rf.grid(row=0,column=2,sticky='nsew',padx=(1,3),pady=3)
        self._filter_hdr=tk.Label(rf,text=_T('program_panel.filter_hdr'),
                 bg='#0d1030',fg='#aaaacc',font=('Arial',9,'bold'),pady=2)
        self._filter_hdr.pack(fill='x')
        style=ttk.Style()
        style.configure('P.Treeview',background='#04040e',
                        foreground='#ccccdd',fieldbackground='#04040e',font=('Arial',9))
        style.map('P.Treeview',background=[('selected','#2244aa')],
                               foreground=[('selected','#ffffff')])
        tv_sc=ttk.Scrollbar(rf,command=lambda *a: self._tv.yview(*a))
        self._tv=ttk.Treeview(rf,show='tree',selectmode='browse',
                               style='P.Treeview',height=4,
                               yscrollcommand=tv_sc.set)
        self._tv.column('#0',width=80,minwidth=40,stretch=True)
        tv_sc.pack(side='right',fill='y')
        self._tv.pack(fill='both',expand=True)
        self._build_filter_tree()
        self._tv.bind('<<TreeviewSelect>>',self._on_filter)

    def _build_filter_tree(self):
        """Vybuduje (alebo prebuduje) strom filtra s aktuálnymi prekladmi."""
        # Zmaž existujúce položky
        for item in self._tv.get_children():
            self._tv.delete(item)
        root=self._tv.insert('','end',text=_T('program_panel.filter_root'),open=True)
        self._sys =self._tv.insert(root,'end',text=_T('program_panel.filter_sys'),open=True)
        self._tmov=self._tv.insert(self._sys,'end',text=_T('program_panel.filter_mov'))
        self._tstr=self._tv.insert(self._sys,'end',text=_T('program_panel.filter_str'))
        self._tcnd=self._tv.insert(self._sys,'end',text=_T('program_panel.filter_cnd'))
        self._tusr=self._tv.insert(root,'end',text=_T('program_panel.filter_usr'),open=True)

    def retranslate(self):
        """Aktualizuje UI labely po zmene jazyka GUI."""
        self._hdr_lbl.configure(text=_T('program_panel.title'))
        self._cmd_list_hdr.configure(text=_T('program_panel.cmd_list_hdr'))
        self._filter_hdr.configure(text=_T('program_panel.filter_hdr'))
        self._build_filter_tree()
        self._fill_list(_cmds_list())

    def set_prog_lang(self, lang: str):
        """Aktualizuje zoznam príkazov a strom filtra pri zmene prog_lang sveta."""
        _switch_prog_lang(lang)   # sám nastaví _current_prog_lang (idempotentné)
        self._refresh_cmds_list()
        self._build_filter_tree()

    def _refresh_cmds_list(self):
        """Znovu naplní zoznam príkazov s ohľadom na aktuálne disabled_cmds."""
        self._fill_list(_cmds_list(self._effective_disabled()))

    def _fill_list(self,items):
        self._lb.delete(0,'end')
        for i in items: self._lb.insert('end',i)

    def _effective_disabled(self) -> set:
        """Vráti úplnú množinu zakázaných tokenov: disabled_cmds zo sveta + DISABLED
        direktíva aktuálneho prog_lang (napr. BRICK pre en_pattis)."""
        return self._disabled_cmds | _LANG_DISABLED.get(_current_prog_lang, set())

    def _on_filter(self,e=None):
        sel=self._tv.selection()
        if not sel: return
        item=sel[0]
        d = self._effective_disabled()
        if item==self._tmov:
            p = _primary_kw; L = _current_prog_lang
            self._fill_list([p(t,L) for t in ['FORWARD','BACK','LEFT','RIGHT'] if t not in d])
        elif item==self._tstr: self._fill_list(_cmds_structs())
        elif item==self._tcnd: self._fill_list(_cmds_conds(d))
        elif item==self._tusr: self._fill_list(self._user_procs)
        else:                  self._fill_list(_cmds_list(d)+_cmds_conds(d))

    def _insert(self,e=None):
        sel=self._lb.curselection()
        if not sel: return
        txt=self._lb.get(sel[0]).split('\n')[0]
        self.editor.insert('insert',txt+'\n')

    def set_disabled_cmds(self, cmds, disable_procedure=False):
        """Nastaví zakázané príkazy, znovu zvýrazní editor a refreshne zoznam príkazov."""
        self._disabled_cmds = set(cmds) if cmds else set()
        self._disable_procedure = disable_procedure
        highlight(self.editor, self._disabled_cmds, self._disable_procedure)
        self._refresh_cmds_list()

    def _on_edit(self):
        """Volá sa pri každom stlačení klávesu — zvýrazni + zisti nové procedúry."""
        highlight(self.editor, self._disabled_cmds, self._disable_procedure)
        src=self.editor.get('1.0','end')
        try:
            prog=parse(src)
            # Procedúra je platná len ak má neprázdnu štruktúru (zaciatok...koniec)
            valid=[n for n,b in prog.procedures.items()]
            self.set_user_procs(valid)
            if self.on_procs_update:
                self.on_procs_update(prog.procedures)
        except Exception:
            pass   # pri neúplnom kóde nemeníme zoznam

    def set_user_procs(self,names):
        self._user_procs=list(names)
        # Aktualizuj podstrom v strome
        for ch in self._tv.get_children(self._tusr): self._tv.delete(ch)
        for n in names: self._tv.insert(self._tusr,'end',text=f'  {n}')
        # Ak je práve aktívny filter "Tvoje príkazy", obnov aj zoznam
        sel=self._tv.selection()
        if sel and sel[0]==self._tusr:
            self._fill_list(self._user_procs)


# =========================================================================
# OVLÁDANIE  KARELA  /  DIRECT CONTROL
# =========================================================================

class ControlPanel(tk.Frame):
    def __init__(self,parent,get_world,on_action=None,get_procs=None,**kw):
        super().__init__(parent,bg='#0a0a1c',**kw)
        self.get_world=get_world; self.on_action=on_action
        self.get_procs=get_procs   # vracia dict procedúr z editora
        self._build()

    def _build(self):
        self._title_lbl=tk.Label(self,text=_T('control.title'),bg='#111130',fg='#aaaacc',
                 font=('Arial',9,'bold'),pady=1)
        self._title_lbl.pack(fill='x')
        self._nb=ttk.Notebook(self); self._nb.pack(fill='both',expand=True,padx=2,pady=1)
        self._t1=tk.Frame(self._nb,bg='#0a0a1c')
        self._t2=tk.Frame(self._nb,bg='#0a0a1c')
        self._nb.add(self._t1,text=_T('control.tab_graphic'))
        self._nb.add(self._t2,text=_T('control.tab_command'))
        self._build_graphic(self._t1); self._build_cmdtab(self._t2)

    def _build_graphic(self,p):
        # ---- Pohybové šípky (ľavý stĺpec) + Akcie (pravý stĺpec) ----
        main=tk.Frame(p,bg='#0a0a1c'); main.pack(fill='both',expand=True,padx=2,pady=2)
        main.columnconfigure(0,weight=0); main.columnconfigure(1,weight=1)
        self._btn_refs: dict = {}   # cmd -> Button widget
        self._btn_bgs:  dict = {}   # cmd -> original bg

        # Pohybové šípky — ikony sú jasné, príkazy sú pevné (interpreter ich aj tak akceptuje obe)
        af=tk.Frame(main,bg='#0a0a1c'); af.grid(row=0,column=0,sticky='n',padx=(0,2))
        def ab(txt,r,c,cmd,bg='#1a2a44'):
            b=tk.Button(af,text=txt,command=lambda:self._do(cmd),
                      bg=bg,fg='white',font=('Arial',11,'bold'),
                      width=2,height=1,relief='flat',cursor='hand2',
                      activebackground='#3355aa',bd=0)
            b.grid(row=r,column=c,padx=1,pady=1)
            self._btn_refs[cmd]=b; self._btn_bgs[cmd]=bg
        ab('▲',0,1,'dopredu','#1a3a1a')
        ab('◀',1,0,'vlavo',  '#2a2a1a')
        self._dir_lbl=tk.Label(af,text='→',fg='#44cc88',bg='#0a0a1c',
                                font=('Arial',12,'bold'),width=2)
        self._dir_lbl.grid(row=1,column=1)
        ab('▶',1,2,'vpravo', '#2a2a1a')
        ab('▼',2,1,'dozadu', '#3a1a1a')

        # Akcie (pravý stĺpec) — label aj príkaz závisia od prog_lang
        self._act_frame = tk.Frame(main,bg='#0a0a1c')
        self._act_frame.grid(row=0,column=1,sticky='nsew')
        self._act_frame.columnconfigure(0,weight=1); self._act_frame.columnconfigure(1,weight=1)
        self._act_btn_specs = [
            # (action_key, bg, row, col)
            ('drop',     '#1a2a3a', 0, 0),
            ('drop_big', '#1a1a3a', 0, 1),
            ('pick',     '#2a1a3a', 1, 0),
            ('mark',     '#1a3a2a', 1, 1),
            ('clear',    '#2a3a1a', 2, 0),
        ]
        self._act_btns: dict = {}   # action_key → Button
        self._act_btn_cmds: set = set()  # cmd kľúče aktuálnych akčných tlačidiel
        self._rebuild_act_buttons()

    def _rebuild_act_buttons(self):
        """Prekreslí akčné tlačidlá podľa aktuálneho prog_lang.
        Staré cmd kľúče sa MUSIA odstrániť z _btn_refs — inak apply_restrictions
        zavolá .configure() na destroyed widgety (crash pri zmene prog_lang)."""
        # 1. Vymaž staré záznamy akčných tlačidiel z btn_refs/btn_bgs
        for old_cmd in self._act_btn_cmds:
            self._btn_refs.pop(old_cmd, None)
            self._btn_bgs.pop(old_cmd, None)
        self._act_btn_cmds.clear()
        # 2. Zničí staré widgety a zresetuj act_btns
        for w in self._act_frame.winfo_children():
            w.destroy()
        self._act_btns.clear()
        # 3. Vytvor nové tlačidlá
        for action, bg, row, col in self._act_btn_specs:
            label, cmd = _prog_btn(action)
            b=tk.Button(self._act_frame, text=label, command=lambda c=cmd: self._do(c),
                      bg=bg, fg='white', font=('Arial',8,'bold'),
                      relief='flat', cursor='hand2', pady=1,
                      activebackground='#334466', bd=0, wraplength=70)
            b.grid(row=row, column=col, sticky='ew', padx=1, pady=1)
            self._btn_refs[cmd] = b; self._btn_bgs[cmd] = bg
            self._act_btns[action] = b
            self._act_btn_cmds.add(cmd)

    def set_prog_lang(self, lang: str):
        """Prepne jazyk akčných tlačidiel podľa prog_lang sveta."""
        _switch_prog_lang(lang)
        self._rebuild_act_buttons()
        self.apply_restrictions(self.get_world().settings if hasattr(self,'get_world') else None)

    def retranslate(self):
        """Aktualizuje všetky UI labely po zmene jazyka GUI."""
        self._title_lbl.configure(text=_T('control.title'))
        self._nb.tab(self._t1, text=_T('control.tab_graphic'))
        self._nb.tab(self._t2, text=_T('control.tab_command'))
        if hasattr(self,'_cmd_prompt_lbl'):
            self._cmd_prompt_lbl.configure(text=_T('control.cmd_prompt'))
        # Labely akčných tlačidiel sledujú GUI jazyk — prekreslíme ich
        self._rebuild_act_buttons()

    def _build_cmdtab(self,p):
        self._cmd_prompt_lbl=tk.Label(p,text=_T('control.cmd_prompt'),bg='#0a0a1c',fg='#8888aa',
                 font=('Arial',8))
        self._cmd_prompt_lbl.pack(anchor='w',padx=6,pady=(6,0))
        self._ent=tk.Entry(p,bg='#04040e',fg='#d4d4d4',font=('Consolas',11),
                            insertbackground='white',relief='flat')
        self._ent.pack(fill='x',padx=6,pady=3)
        self._ent.bind('<Return>',self._exec_typed)
        self._log=tk.Text(p,bg='#04040e',fg='#88aa88',font=('Consolas',10),
                           height=5,state='disabled',relief='flat')
        self._log.pack(fill='both',expand=True,padx=6,pady=(0,4))

    # Priame volania metód Sveta — spoľahlivé, neprechádzajú parserom
    _DIRECT = {
        'dopredu': 'move_forward', 'forward': 'move_forward',
        'dozadu':  'move_back',    'back':    'move_back',
        'vzad':    'move_back',
        'vlavo':   'turn_left',    'left':    'turn_left',
        'dolava':  'turn_left',
        'vpravo':  'turn_right',   'right':   'turn_right',
        'doprava': 'turn_right',
        'poloz':       'drop_brick',     'drop':     'drop_brick',
        'poloz_velku': 'drop_big_brick', 'drop_big': 'drop_big_brick',
        'drop_b':      'drop_big_brick', 'dropb':    'drop_big_brick',
        'zdvihni': 'pick_any_brick', 'pick':   'pick_any_brick',
        'zodvihni':'pick_any_brick',
        'oznac':   'mark',         'mark':    'mark',
        'odznac':  'clear',        'clear':   'clear',
        'ocisti':  'clear',
    }

    def _do(self, cmd):
        if not cmd: return
        w = self.get_world()
        try:
            cmd_key = cmd.lower().strip()
            method = self._DIRECT.get(cmd_key)
            if method:
                # Kontrola zakázaných príkazov aj pri priamom volaní
                tok = KW.get(cmd_key, '')
                if tok and tok in w.settings.disabled_cmds:
                    raise KarelError("Príkaz je zakázaný v tomto svete!")
                getattr(w, method)()
            else:
                prog = parse(f'zaciatok\n  {cmd}\nkoniec')
                if self.get_procs:
                    prog.procedures.update(self.get_procs())
                it = KarelInterpreter(w); it.delay = 0; it.run(prog)
            self._update_dir_label()
            if self.on_action: self.on_action(True, None)
        except (KarelError, Exception) as e:
            if self.on_action: self.on_action(False, str(e))

    def _update_dir_label(self):
        """Aktualizuj šípku smeru Karela v strede kríža."""
        if not hasattr(self,'_dir_lbl'): return
        w = self.get_world()
        arrows = {Direction.NORTH:'↑', Direction.SOUTH:'↓',
                  Direction.EAST:'→',  Direction.WEST:'←'}
        self._dir_lbl.config(text=arrows.get(w.karel_dir,'→'))

    def apply_restrictions(self, settings):
        """Zakáže/povolí tlačidlá podľa nastavení sveta."""
        if not hasattr(self,'_btn_refs'): return
        disabled = settings.disabled_cmds if settings else set()
        for cmd, btn in self._btn_refs.items():
            # KW obsahuje všetky jazyky — tok nájde 'forward' aj 'dopredu' → 'FORWARD'
            tok = KW.get(cmd.lower(), '')
            if tok in disabled:
                btn.configure(state='disabled', bg='#222222', fg='#555555', cursor='')
            else:
                btn.configure(state='normal', bg=self._btn_bgs.get(cmd,'#1a2a3a'),
                              fg='white', cursor='hand2')

    def _exec_typed(self, e=None):
        cmd = self._ent.get().strip()
        if not cmd: return
        self._ent.delete(0, 'end')
        self._logw(f"> {cmd}")
        self._do(cmd)

    def _logw(self,msg):
        self._log.config(state='normal')
        self._log.insert('end',msg+'\n')
        self._log.see('end')
        self._log.config(state='disabled')


# =========================================================================
# EDITOR  NASTAVENÍ  SVETA
# =========================================================================

class GoalConditionDialog(tk.Toplevel):
    """Sub-dialóg: pridanie / editácia jednej podmienky misie."""
    _BG='#0a0a1c'; _FG='#ccccee'; _FG2='#888899'

    def __init__(self, parent, world, edit_cond=None):
        super().__init__(parent)
        self._world     = world
        self._edit_cond = edit_cond   # GoalCondition alebo None (nový)
        self.result     = None
        title_key = 'goal_condition.title_edit' if edit_cond else 'goal_condition.title'
        self.title(_T(title_key))
        self.configure(bg=self._BG)
        self.resizable(False, False)
        self.grab_set(); self.transient(parent)
        self._build()
        self.update_idletasks()
        pw,ph = parent.winfo_width(), parent.winfo_height()
        px,py = parent.winfo_rootx(), parent.winfo_rooty()
        ww,wh = self.winfo_width(), self.winfo_height()
        self.geometry(f'+{px+(pw-ww)//2}+{py+(ph-wh)//2}')

    def _build(self):
        ec = self._edit_cond
        # Typ podmienky
        tf = tk.Frame(self, bg=self._BG, padx=12, pady=8); tf.pack(fill='x')
        tk.Label(tf, text=_T('goal_condition.type_label'), bg=self._BG, fg=self._FG,
                 font=('Arial',9,'bold')).pack(side='left', padx=(0,12))
        _all_types = ('karel_pos','cell_state','sign','brick_ahead','wall_ahead','snapshot')
        default_type = ec.check if ec and ec.check in _all_types else 'karel_pos'
        self._type_var = tk.StringVar(value=default_type)
        for val,lbl in [('karel_pos',   _T('goal_condition.type_karel_pos')),
                        ('cell_state',  _T('goal_condition.type_cell_state')),
                        ('sign',        _T('goal_condition.type_sign')),
                        ('brick_ahead', _T('goal_condition.type_brick_ahead')),
                        ('wall_ahead',  _T('goal_condition.type_wall_ahead')),
                        ('snapshot',    _T('goal_condition.type_snapshot'))]:
            tk.Radiobutton(tf, text=lbl, variable=self._type_var, value=val,
                           bg=self._BG, fg=self._FG, selectcolor='#1a1a44',
                           activebackground=self._BG, font=('Arial',9),
                           command=self._switch_type).pack(side='left', padx=4)
        tk.Frame(self, bg='#334466', height=1).pack(fill='x')
        self._content = tk.Frame(self, bg=self._BG, padx=12, pady=8)
        self._content.pack(fill='both', expand=True)
        tk.Frame(self, bg='#334466', height=1).pack(fill='x')

        # --- Spoločné nastavenia: eval / when / op / negate ------------------
        cf = tk.Frame(self, bg='#0d0d22', padx=12, pady=8); cf.pack(fill='x')

        # riadok 1: výsledok + čas
        r1 = tk.Frame(cf, bg='#0d0d22'); r1.pack(fill='x', pady=(0,4))
        tk.Label(r1, text=_T('goal_condition.lbl_eval'), bg='#0d0d22', fg=self._FG2,
                 font=('Arial',8), width=10, anchor='w').pack(side='left')
        self._eval_var = tk.StringVar(value=ec.eval  if ec else 'success')
        for val, lbl in [('success', _T('goal_condition.eval_success')),
                         ('failure', _T('goal_condition.eval_failure'))]:
            tk.Radiobutton(r1, text=lbl, variable=self._eval_var, value=val,
                           bg='#0d0d22', fg='#88ee88' if val=='success' else '#ee6666',
                           selectcolor='#1a1a44', activebackground='#0d0d22',
                           font=('Arial',9)).pack(side='left', padx=6)

        tk.Frame(r1, bg='#334466', width=1).pack(side='left', fill='y', padx=10)
        tk.Label(r1, text=_T('goal_condition.lbl_when'), bg='#0d0d22', fg=self._FG2,
                 font=('Arial',8), width=5, anchor='w').pack(side='left')
        self._when_var = tk.StringVar(value=ec.when if ec else 'on_finish')
        for val, lbl in [('on_finish', _T('goal_condition.when_finish')),
                         ('on_step',   _T('goal_condition.when_step'))]:
            tk.Radiobutton(r1, text=lbl, variable=self._when_var, value=val,
                           bg='#0d0d22', fg=self._FG,
                           selectcolor='#1a1a44', activebackground='#0d0d22',
                           font=('Arial',9)).pack(side='left', padx=6)

        # riadok 2: operátor + negate
        r2 = tk.Frame(cf, bg='#0d0d22'); r2.pack(fill='x')
        tk.Label(r2, text=_T('goal_condition.lbl_op'), bg='#0d0d22', fg=self._FG2,
                 font=('Arial',8), width=10, anchor='w').pack(side='left')
        self._op_var = tk.StringVar(value=ec.op if ec else 'or')
        for val, lbl in [('or', 'OR'), ('and', 'AND')]:
            tk.Radiobutton(r2, text=lbl, variable=self._op_var, value=val,
                           bg='#0d0d22', fg='#aaaaff',
                           selectcolor='#1a1a44', activebackground='#0d0d22',
                           font=('Consolas',9,'bold')).pack(side='left', padx=6)
        tk.Label(r2, text=_T('goal_condition.op_note'), bg='#0d0d22', fg='#556677',
                 font=('Arial',8,'italic')).pack(side='left', padx=(4,20))

        self._negate_var = tk.BooleanVar(value=ec.negate if ec else False)
        tk.Checkbutton(r2, text=_T('goal_condition.lbl_negate'),
                       variable=self._negate_var,
                       bg='#0d0d22', fg='#ffaa44', selectcolor='#2a1a00',
                       activebackground='#0d0d22', font=('Arial',9)).pack(side='left', padx=6)
        # ---------------------------------------------------------------------

        tk.Frame(self, bg='#334466', height=1).pack(fill='x')
        bf = tk.Frame(self, bg='#111130', pady=6); bf.pack(fill='x')
        tk.Button(bf, text=_T('goal_condition.btn_cancel'), command=self.destroy,
                  bg='#3a1a1a', fg='white', relief='flat', padx=12, pady=4,
                  font=('Arial',9), cursor='hand2').pack(side='right', padx=8)
        btn_lbl = _T('goal_condition.btn_save') if ec else _T('goal_condition.btn_add')
        tk.Button(bf, text=btn_lbl, command=self._ok,
                  bg='#1a4a1a', fg='white', relief='flat', padx=12, pady=4,
                  font=('Arial',9,'bold'), cursor='hand2').pack(side='right', padx=4)
        self._switch_type()

    def _switch_type(self):
        for w in self._content.winfo_children(): w.destroy()
        t = self._type_var.get()
        if   t == 'karel_pos':  self._build_karel_pos()
        elif t == 'cell_state': self._build_cell_state()
        elif t == 'snapshot':   self._build_snapshot()
        else:                   self._build_simple_check(t)

    def _build_simple_check(self, check_type: str):
        p = self._content
        descs = {
            'sign':        _T('goal_condition.type_sign_desc'),
            'brick_ahead': _T('goal_condition.type_brick_ahead_desc'),
            'wall_ahead':  _T('goal_condition.type_wall_ahead_desc'),
        }
        desc = descs.get(check_type, check_type)
        tk.Label(p, text=desc, bg=self._BG, fg=self._FG2,
                 font=('Arial',9,'italic'), wraplength=380,
                 justify='left').pack(anchor='w', pady=12, padx=6)

    def _lbl(self, p, txt, w=14):
        return tk.Label(p, text=txt, bg=self._BG, fg=self._FG,
                        font=('Arial',9), width=w, anchor='w')

    def _build_karel_pos(self):
        p = self._content; wd = self._world; ec = self._edit_cond
        tk.Label(p, text=_T('goal_condition.kp_intro'),
                 bg=self._BG, fg=self._FG2, font=('Arial',8,'italic'),
                 wraplength=380).pack(anchor='w', pady=(0,8))
        # pri editácii pred-vyplníme z existujúcej podmienky, inak z aktuálnej pozície Karela
        self._kp_x_en = tk.BooleanVar(value=ec.x is not None if ec else True)
        self._kp_y_en = tk.BooleanVar(value=ec.y is not None if ec else True)
        self._kp_h_en = tk.BooleanVar(value=ec.z is not None if ec else False)
        self._kp_x    = tk.IntVar(value=ec.x if (ec and ec.x is not None) else wd.karel_x)
        self._kp_y    = tk.IntVar(value=ec.y if (ec and ec.y is not None) else wd.karel_y)
        self._kp_h    = tk.IntVar(value=ec.z if (ec and ec.z is not None) else wd._height(wd.karel_x, wd.karel_y))
        for en_var, val_var, lbl, lo, hi in [
            (self._kp_x_en, self._kp_x, 'X:', 0, wd.width-1),
            (self._kp_y_en, self._kp_y, 'Y:', 0, wd.height-1),
            (self._kp_h_en, self._kp_h, _T('goal_condition.kp_height'), 0, 99),
        ]:
            row = tk.Frame(p, bg=self._BG); row.pack(fill='x', pady=2)
            tk.Checkbutton(row, variable=en_var, bg=self._BG, fg=self._FG,
                           selectcolor='#1a1a44', activebackground=self._BG).pack(side='left')
            self._lbl(row, lbl).pack(side='left')
            ttk.Spinbox(row, textvariable=val_var, from_=lo, to=hi,
                        width=5, font=('Consolas',10)).pack(side='left')

    def _build_cell_state(self):
        p = self._content; wd = self._world; ec = self._edit_cond
        tk.Label(p, text=_T('goal_condition.cs_intro'),
                 bg=self._BG, fg=self._FG2, font=('Arial',8,'italic')).pack(anchor='w', pady=(0,8))
        cr = tk.Frame(p, bg=self._BG); cr.pack(fill='x', pady=2)
        self._cs_x = tk.IntVar(value=ec.x if (ec and ec.x is not None) else wd.karel_x)
        self._cs_y = tk.IntVar(value=ec.y if (ec and ec.y is not None) else wd.karel_y)
        for lbl, var, lo, hi in [('X:', self._cs_x, 0, wd.width-1),
                                   ('Y:', self._cs_y, 0, wd.height-1)]:
            tk.Label(cr, text=lbl, bg=self._BG, fg=self._FG,
                     font=('Arial',9)).pack(side='left', padx=(8,2))
            ttk.Spinbox(cr, textvariable=var, from_=lo, to=hi,
                        width=4, font=('Consolas',10)).pack(side='left', padx=(0,10))
        self._cs_marks_en  = tk.BooleanVar(value=ec.cell_marks      is not None if ec else False)
        self._cs_bricks_en = tk.BooleanVar(value=ec.cell_bricks     is not None if ec else False)
        self._cs_bb_en     = tk.BooleanVar(value=ec.cell_big_bricks is not None if ec else False)
        self._cs_marks  = tk.BooleanVar(value=bool(ec.cell_marks)          if (ec and ec.cell_marks      is not None) else False)
        self._cs_bricks = tk.IntVar(value=ec.cell_bricks                   if (ec and ec.cell_bricks     is not None) else 0)
        self._cs_bb     = tk.IntVar(value=ec.cell_big_bricks               if (ec and ec.cell_big_bricks is not None) else 0)
        # značka
        mr = tk.Frame(p, bg=self._BG); mr.pack(fill='x', pady=2)
        tk.Checkbutton(mr, variable=self._cs_marks_en, bg=self._BG, fg=self._FG,
                       selectcolor='#1a1a44', activebackground=self._BG).pack(side='left')
        self._lbl(mr, _T('goal_condition.cs_mark')).pack(side='left')
        tk.Checkbutton(mr, text=_T('goal_condition.cs_mark_yes'), variable=self._cs_marks,
                       bg=self._BG, fg=self._FG, selectcolor='#1a1a44',
                       activebackground=self._BG, font=('Arial',9)).pack(side='left')
        # tehly
        for en_var, val_var, lbl in [
            (self._cs_bricks_en, self._cs_bricks, _T('goal_condition.cs_bricks')),
            (self._cs_bb_en,     self._cs_bb,     _T('goal_condition.cs_big_bricks')),
        ]:
            row = tk.Frame(p, bg=self._BG); row.pack(fill='x', pady=2)
            tk.Checkbutton(row, variable=en_var, bg=self._BG, fg=self._FG,
                           selectcolor='#1a1a44', activebackground=self._BG).pack(side='left')
            self._lbl(row, lbl, w=18).pack(side='left')
            ttk.Spinbox(row, textvariable=val_var, from_=0, to=99,
                        width=5, font=('Consolas',10)).pack(side='left')

    def _build_snapshot(self):
        p = self._content; wd = self._world; ec = self._edit_cond
        # pri editácii ukážeme štatistiky uloženého snímku, inak aktuálneho sveta
        if ec and ec.snap:
            s = ec.snap
            h = wd.height; w2 = wd.width
            br_c = sum(s['bricks'][y][x]     for y in range(h) for x in range(w2))
            bb_c = sum(s['big_bricks'][y][x] for y in range(h) for x in range(w2))
            mk_c = sum(1 for y in range(h) for x in range(w2) if s['marks'][y][x])
            status_lbl = _T('goal_condition.snap_status_saved')
        else:
            br_c = sum(wd.bricks[y][x]     for y in range(wd.height) for x in range(wd.width))
            bb_c = sum(wd.big_bricks[y][x] for y in range(wd.height) for x in range(wd.width))
            mk_c = sum(1 for y in range(wd.height) for x in range(wd.width) if wd.marks[y][x])
            status_lbl = _T('goal_condition.snap_status')
        tk.Label(p, text=_T('goal_condition.snap_desc').replace('\\n','\n'),
            bg=self._BG, fg=self._FG2, font=('Arial',9,'italic'),
            wraplength=360, justify='left').pack(anchor='w', pady=(0,10))
        tk.Label(p, text=status_lbl.format(br=br_c, bb=bb_c, mk=mk_c),
                 bg='#1a1a33', fg='#88ccff', font=('Consolas',9),
                 padx=10, pady=5).pack(fill='x', pady=(0,8))
        inc_karel = (ec.snap.get('karel_x') is not None) if (ec and ec.snap) else True
        self._snap_karel = tk.BooleanVar(value=inc_karel)
        tk.Checkbutton(p, text=_T('goal_condition.snap_inc_karel'),
                       variable=self._snap_karel,
                       bg=self._BG, fg=self._FG, selectcolor='#1a1a44',
                       activebackground=self._BG, font=('Arial',9)).pack(anchor='w')
        tk.Label(p, text=_T('goal_condition.snap_note'),
                 bg=self._BG, fg='#aaaacc', font=('Arial',8,'italic')).pack(anchor='w', pady=(8,0))

    def _ok(self):
        t = self._type_var.get()
        try:
            if t == 'karel_pos':
                x = int(self._kp_x.get()) if self._kp_x_en.get() else None
                y = int(self._kp_y.get()) if self._kp_y_en.get() else None
                h = int(self._kp_h.get()) if self._kp_h_en.get() else None
                if x is None and y is None and h is None:
                    messagebox.showwarning(_T('goal_condition.warn_title'),
                        _T('goal_condition.warn_no_cond'), parent=self); return
                self.result = GoalCondition('karel_pos', x=x, y=y, z=h,
                    eval_=self._eval_var.get(), when=self._when_var.get(),
                    op=self._op_var.get(), negate=self._negate_var.get())
            elif t == 'cell_state':
                x = int(self._cs_x.get()); y = int(self._cs_y.get())
                marks      = self._cs_marks.get()  if self._cs_marks_en.get()  else None
                bricks     = int(self._cs_bricks.get()) if self._cs_bricks_en.get() else None
                big_bricks = int(self._cs_bb.get())     if self._cs_bb_en.get()     else None
                if marks is None and bricks is None and big_bricks is None:
                    messagebox.showwarning(_T('goal_condition.warn_title'),
                        _T('goal_condition.warn_no_cond'), parent=self); return
                self.result = GoalCondition('cell_state', x=x, y=y,
                    cell_marks=marks, cell_bricks=bricks, cell_big_bricks=big_bricks,
                    eval_=self._eval_var.get(), when=self._when_var.get(),
                    op=self._op_var.get(), negate=self._negate_var.get())
            elif t in ('sign', 'brick_ahead', 'wall_ahead'):
                self.result = GoalCondition(t,
                    eval_=self._eval_var.get(), when=self._when_var.get(),
                    op=self._op_var.get(), negate=self._negate_var.get())
            else:  # snapshot
                self.result = GoalCondition('snapshot',
                    snap=GoalCondition.snapshot_from_world(
                        self._world, include_karel=self._snap_karel.get()),
                    eval_=self._eval_var.get(), when=self._when_var.get(),
                    op=self._op_var.get(), negate=self._negate_var.get())
        except Exception as e:
            messagebox.showerror(_T('goal_condition.err_title'), str(e), parent=self); return
        self.destroy()


class MissionResultDialog(tk.Toplevel):
    """Zobrazí výsledok misie — úspech alebo neúspech."""
    _BG='#0a0a1c'; _FG='#ccccee'

    def __init__(self, app, success: bool, html_msg: str):
        super().__init__(app)
        self.title("Výsledok misie")
        self.configure(bg=self._BG)
        self.resizable(False, False)
        self.grab_set(); self.transient(app)
        self._build(success, html_msg)
        self.update_idletasks()
        pw,ph = app.winfo_width(), app.winfo_height()
        px,py = app.winfo_rootx(), app.winfo_rooty()
        ww,wh = self.winfo_width(), self.winfo_height()
        self.geometry(f'+{px+(pw-ww)//2}+{py+(ph-wh)//2}')

    @staticmethod
    def _strip_html(raw: str) -> str:
        # Odstraň CDATA obal ak existuje
        txt = re.sub(r'<!\[CDATA\[([\s\S]*?)\]\]>', r'\1', raw)
        txt = re.sub(r'<br\s*/?>', '\n', txt, flags=re.IGNORECASE)
        txt = re.sub(r'<[^>]+>', '', txt)
        txt = _html_mod.unescape(txt)
        return txt.strip()

    def _build(self, success: bool, html_msg: str):
        col = '#1a5a1a' if success else '#5a1a1a'
        fg  = '#44ff88' if success else '#ff6666'
        icon = '✓   MISIA SPLNENÁ!' if success else '✗   MISIA NESPLNENÁ'
        hf = tk.Frame(self, bg=col, pady=16, padx=24); hf.pack(fill='x')
        tk.Label(hf, text=icon, bg=col, fg=fg, font=('Arial',16,'bold')).pack()
        txt = (self._strip_html(html_msg) if html_msg else
               ("Všetky podmienky boli splnené." if success
                else "Niektoré podmienky neboli splnené."))
        tf = tk.Frame(self, bg=self._BG, padx=24, pady=14); tf.pack(fill='both', expand=True)
        tk.Label(tf, text=txt, bg=self._BG, fg=self._FG,
                 font=('Arial',10), wraplength=360, justify='left').pack(anchor='w')
        bf = tk.Frame(self, bg='#111130', pady=8); bf.pack(fill='x')
        tk.Button(bf, text='OK', command=self.destroy,
                  bg='#2a5a9a', fg='white', relief='flat', padx=28, pady=5,
                  font=('Arial',10,'bold'), cursor='hand2').pack(side='right', padx=12)


class IntroDialog(tk.Toplevel):
    """Zobrazí úvodné zadanie úlohy (intro_html) pre aktuálny svet."""
    _BG = '#0a0a1c'; _FG = '#ccccee'

    def __init__(self, app, title: str, html_msg: str):
        super().__init__(app)
        self.title("Zadanie úlohy")
        self.configure(bg=self._BG)
        self.resizable(True, True)
        self.transient(app)
        self.grab_set()
        self._build(title, html_msg)
        self.update_idletasks()
        # Vycentruj voči rodičovskému oknu; pevná veľkosť aby sa neorezalo OK tlačidlo
        ww, wh = 500, 400
        pw, ph = app.winfo_width(), app.winfo_height()
        px, py = app.winfo_rootx(), app.winfo_rooty()
        self.geometry(f'{ww}x{wh}+{px+(pw-ww)//2}+{py+(ph-wh)//2}')

    @staticmethod
    def _strip_html(raw: str) -> str:
        # Odstraň CDATA obal ak existuje
        txt = re.sub(r'<!\[CDATA\[([\s\S]*?)\]\]>', r'\1', raw)
        txt = re.sub(r'<br\s*/?>', '\n', txt, flags=re.IGNORECASE)
        txt = re.sub(r'<h[1-6][^>]*>', '\n', txt, flags=re.IGNORECASE)
        txt = re.sub(r'</h[1-6]>', '\n', txt, flags=re.IGNORECASE)
        txt = re.sub(r'<p[^>]*>', '\n', txt, flags=re.IGNORECASE)
        txt = re.sub(r'<[^>]+>', '', txt)
        txt = _html_mod.unescape(txt)
        return re.sub(r'\n{3,}', '\n\n', txt).strip()

    @staticmethod
    def _html_insert(widget, raw: str):
        """Vloží HTML text do tk.Text widgetu so zachovaním bold/italic formátovania."""
        # Odstraň CDATA obal
        html = re.sub(r'<!\[CDATA\[([\s\S]*?)\]\]>', r'\1', raw)
        # Tokenizuj HTML na tagy a text
        TOKEN = re.compile(r'(<[^>]+>|[^<]+)', re.DOTALL)
        bold = italic = False
        buf = []   # (text, bold, italic)
        for m in TOKEN.finditer(html):
            tok = m.group(0)
            if tok.startswith('<'):
                tag = tok.lower().strip('<>/ \t\n\r')
                tag_name = tag.split()[0] if tag else ''
                closing = tok.lstrip('<').startswith('/')
                if tag_name in ('b', 'strong'):
                    bold = not closing
                elif tag_name in ('i', 'em'):
                    italic = not closing
                elif tag_name in ('br',):
                    buf.append(('\n', False, False))
                elif tag_name == 'p' and not closing:
                    buf.append(('\n', False, False))
                elif tag_name in ('h1','h2','h3','h4','h5','h6'):
                    if not closing:
                        buf.append(('\n', True, False))
                    else:
                        buf.append(('\n', False, False))
            else:
                text = _html_mod.unescape(tok)
                if text:
                    buf.append((text, bold, italic))

        # Uprac nadbytočné newline na začiatku prvého segmentu
        if buf and buf[0][0].startswith('\n'):
            buf[0] = (buf[0][0].lstrip('\n'), buf[0][1], buf[0][2])
        # Zapíš do widgetu
        for text, b, i in buf:
            if not text:
                continue
            tag = 'bi' if b and i else ('bold' if b else ('italic' if i else ''))
            if tag:
                widget.insert('end', text, tag)
            else:
                widget.insert('end', text)

    def _build(self, title: str, html_msg: str):
        # Hlavička s názvom sveta
        hf = tk.Frame(self, bg='#111135', pady=12, padx=20)
        hf.pack(fill='x')
        tk.Label(hf, text=title or "Zadanie úlohy", bg='#111135', fg='#44aaff',
                 font=('Arial', 14, 'bold')).pack(anchor='w')

        # Tlačidlo OK — zabalené PRED expand=True framom, inak by sa stratilo pod ním
        bf = tk.Frame(self, bg='#111130', pady=8)
        bf.pack(fill='x', side='bottom')
        tk.Button(bf, text='OK', command=self.destroy,
                  bg='#2a5a9a', fg='white', relief='flat', padx=28, pady=5,
                  font=('Arial', 10, 'bold'), cursor='hand2').pack(side='right', padx=12)
        self.bind('<Return>', lambda _: self.destroy())
        self.bind('<Escape>', lambda _: self.destroy())

        # Telo — Text widget so scrollbarom (expand=True musí byť až po OK frame)
        tf = tk.Frame(self, bg=self._BG, padx=16, pady=10)
        tf.pack(fill='both', expand=True)
        sb = tk.Scrollbar(tf, bg='#222244')
        sb.pack(side='right', fill='y')
        txt_w = tk.Text(tf, wrap='word', bg='#0d0d22', fg=self._FG,
                        font=('Arial', 11), relief='flat', bd=0,
                        yscrollcommand=sb.set, state='normal',
                        padx=10, pady=8, cursor='arrow',
                        selectbackground='#223355')
        txt_w.pack(fill='both', expand=True)
        sb.config(command=txt_w.yview)

        # Fonty pre formátovanie
        txt_w.tag_configure('bold',   font=('Arial', 11, 'bold'))
        txt_w.tag_configure('italic', font=('Arial', 11, 'italic'))
        txt_w.tag_configure('bi',     font=('Arial', 11, 'bold italic'))

        # Vlož obsah s formátovaním
        if html_msg:
            self._html_insert(txt_w, html_msg)
        else:
            txt_w.insert('1.0', "(Žiadne zadanie)")
        txt_w.configure(state='disabled')   # len na čítanie


class WorldSettingsDialog(tk.Toplevel):
    """Modálny dialóg na nastavenie parametrov miestnosti."""
    _BG='#0a0a1c'; _BG2='#111130'; _BG3='#060610'
    _FG='#ccccee'; _FG2='#888899'

    def __init__(self, app):
        super().__init__(app)
        self._app  = app
        self._work = app._base.copy()   # pracovná kópia — aplikuje sa až pri OK
        # Aktuálna poloha Karela (kde sa teraz nachádza, nie štartovacia)
        self._cur_world = app._world
        self._cam  = app._canvas.cam
        self.title(_T('world_settings.title'))
        self.configure(bg=self._BG)
        self.resizable(False, False)
        self.grab_set()
        self.transient(app)
        self._build()
        self.update_idletasks()
        pw,ph = app.winfo_width(), app.winfo_height()
        px,py = app.winfo_rootx(), app.winfo_rooty()
        ww,wh = self.winfo_width(), self.winfo_height()
        self.geometry(f'+{px+(pw-ww)//2}+{py+(ph-wh)//2}')

    # -- helpers --------------------------------------------------------------
    def _lbl(self, p, txt, fg=None, **kw):
        return tk.Label(p, text=txt, bg=self._BG, fg=fg or self._FG,
                        font=('Arial',9), **kw)
    def _sep(self, p):
        tk.Frame(p, bg='#334466', height=1).pack(fill='x', pady=5)
    def _frame(self, p, title):
        return tk.LabelFrame(p, text=f' {title} ', bg=self._BG,
                             fg=self._FG2, font=('Arial',8), bd=1, relief='groove')

    # -- Tab: Popis -----------------------------------------------------------
    def _build_popis(self, p):
        w = self._work
        # Názov sveta
        nf = self._frame(p, _T('world_settings.frame_title')); nf.pack(fill='x', pady=(0,8))
        self._title_var = tk.StringVar(value=w.title)
        tk.Entry(nf, textvariable=self._title_var, bg='#1a1a44', fg='white',
                 font=('Arial',11), insertbackground='white', relief='flat',
                 ).pack(fill='x', padx=8, pady=7)
        # Popis / zadanie úlohy
        df = self._frame(p, _T('world_settings.frame_desc'))
        df.pack(fill='both', expand=True)
        # Toolbar
        tb = tk.Frame(df, bg=self._BG2, padx=4, pady=3); tb.pack(fill='x')
        def _wrap(ot, ct):
            try:
                sel = self._intro_text.get('sel.first','sel.last')
                self._intro_text.delete('sel.first','sel.last')
                self._intro_text.insert('insert', ot+sel+ct)
            except tk.TclError:
                self._intro_text.insert('insert', ot+ct)
            self._intro_text.focus_set()
        for (lbl,ot,ct,fw) in [
            ('B', '<b>','</b>','bold'),
            ('I', '<i>','</i>','italic'),
            ('U', '<u>','</u>','normal'),
        ]:
            tk.Button(tb, text=lbl, width=3,
                      command=lambda o=ot,c=ct:_wrap(o,c),
                      bg='#2a2a55', fg='white', relief='flat',
                      font=('Arial',9,fw), cursor='hand2'
                      ).pack(side='left', padx=(0,2))
        tk.Frame(tb, width=8, bg=self._BG2).pack(side='left')
        for (lbl,ot,ct) in [
            ('H1','<h1>','</h1>'), ('H2','<h2>','</h2>'),
            ('H3','<h3>','</h3>'), ('P','<p>','</p>'),
            ('BR','<br>',''),
        ]:
            tk.Button(tb, text=lbl, width=3,
                      command=lambda o=ot,c=ct:_wrap(o,c),
                      bg='#1a2a44', fg='#88aacc', relief='flat',
                      font=('Arial',8), cursor='hand2'
                      ).pack(side='left', padx=(0,2))
        # Text widget + scrollbar
        tf2 = tk.Frame(df, bg=self._BG); tf2.pack(fill='both', expand=True, padx=4, pady=4)
        self._intro_text = tk.Text(tf2, bg='#0d0d22', fg='#ccccee',
                                   font=('Consolas',10), wrap='word', height=8,
                                   insertbackground='white', relief='flat',
                                   selectbackground='#2a2a55')
        sb = ttk.Scrollbar(tf2, command=self._intro_text.yview)
        self._intro_text.configure(yscrollcommand=sb.set)
        self._intro_text.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')
        self._intro_text.insert('1.0', w.intro_html)

    # -- build ----------------------------------------------------------------
    def _build(self):
        nb = ttk.Notebook(self)
        nb.pack(fill='both', expand=True, padx=8, pady=(8,4))
        tabs = {}
        tab_keys = ['tab_desc','tab_room','tab_inv','tab_cmds','tab_view','tab_mission']
        tab_builders = [self._build_popis, self._build_room, self._build_inventory,
                        self._build_cmds, self._build_camera, self._build_mission]
        self._nb_tabs = []
        for key, builder in zip(tab_keys, tab_builders):
            f = tk.Frame(nb, bg=self._BG, padx=10, pady=8)
            nb.add(f, text=_T(f'world_settings.{key}'))
            self._nb_tabs.append((key, f))
            builder(f)
        # Tlačidlá
        bf = tk.Frame(self, bg=self._BG2, pady=6); bf.pack(fill='x')
        tk.Button(bf, text=_T('world_settings.btn_cancel'), command=self.destroy,
                  bg='#3a1a1a', fg='white', relief='flat', padx=16, pady=4,
                  font=('Arial',10), cursor='hand2',
                  activebackground='#5a2a2a').pack(side='right', padx=8)
        tk.Button(bf, text=_T('world_settings.btn_apply'), command=self._apply,
                  bg='#1a4a1a', fg='white', relief='flat', padx=16, pady=4,
                  font=('Arial',10,'bold'), cursor='hand2',
                  activebackground='#2a6a2a').pack(side='right', padx=4)

    # -- Tab: Miestnosť -------------------------------------------------------
    def _build_room(self, p):
        w    = self._work
        wcur = self._cur_world   # aktuálny stav — odkiaľ Karel teraz je
        # Rozmery
        rf = self._frame(p, _T('world_settings.frame_size')); rf.pack(fill='x', pady=(0,8))
        self._w_var = tk.IntVar(value=w.width)
        self._h_var = tk.IntVar(value=w.height)
        for col,(lbl,var) in enumerate([(_T('world_settings.lbl_width'),self._w_var),(_T('world_settings.lbl_height'),self._h_var)]):
            self._lbl(rf,lbl).grid(row=0,column=col*2,sticky='e',padx=(8,2),pady=6)
            ttk.Spinbox(rf,textvariable=var,from_=3,to=50,
                        width=4,font=('Consolas',11)
                        ).grid(row=0,column=col*2+1,padx=(0,16))
        # Pozícia Karela — predvyplnená z AKTUÁLNEJ polohy (nie zo štartu)
        pf = self._frame(p, _T('world_settings.frame_pos')); pf.pack(fill='x', pady=(0,4))
        self._kx_var = tk.IntVar(value=w.karel_x)
        self._ky_var = tk.IntVar(value=w.karel_y)
        self._lbl(pf,'X:').grid(row=0,column=0,sticky='e',padx=(8,2),pady=6)
        ttk.Spinbox(pf,textvariable=self._kx_var,from_=0,to=w.width-1,
                    width=4,font=('Consolas',11)).grid(row=0,column=1,padx=(0,16))
        self._lbl(pf,'Y:').grid(row=0,column=2,sticky='e',padx=(0,2))
        ttk.Spinbox(pf,textvariable=self._ky_var,from_=0,to=w.height-1,
                    width=4,font=('Consolas',11)).grid(row=0,column=3,padx=(0,8))
        self._hnote = tk.Label(pf,text='',bg=self._BG,fg='#ffaa44',
                               font=('Arial',8,'italic'),anchor='w')
        self._hnote.grid(row=1,column=0,columnspan=4,sticky='ew',padx=8,pady=(0,4))
        if wcur.karel_x != w.karel_x or wcur.karel_y != w.karel_y:
            self._hnote.config(
                text=_T('world_settings.hnote_pos').format(
                    x=w.karel_x, y=w.karel_y,
                    sx=wcur.karel_x, sy=wcur.karel_y))
        self._kx_var.trace_add('write', lambda *a: self._upd_hnote())
        self._ky_var.trace_add('write', lambda *a: self._upd_hnote())
        # Smer
        sf = self._frame(p, _T('world_settings.frame_dir')); sf.pack(fill='x', pady=(0,8))
        self._dir_var = tk.StringVar(value=w.karel_dir.to_str())
        for col,(txt,val) in enumerate([(_T('world_settings.dir_n'),'N'),(_T('world_settings.dir_e'),'E'),
                                         (_T('world_settings.dir_s'),'S'),(_T('world_settings.dir_w'),'W')]):
            tk.Radiobutton(sf,text=txt,variable=self._dir_var,value=val,
                           bg=self._BG,fg=self._FG,selectcolor='#1a1a44',
                           activebackground=self._BG,font=('Arial',9)
                           ).grid(row=0,column=col,padx=8,pady=6)
        # Max. výška výstupu
        cf = self._frame(p, _T('world_settings.frame_move')); cf.pack(fill='x')
        self._max_climb_var = tk.IntVar(value=w.settings.max_climb)
        self._lbl(cf, _T('world_settings.lbl_max_climb')).grid(row=0,column=0,sticky='e',padx=(8,4),pady=6)
        ttk.Spinbox(cf, textvariable=self._max_climb_var, from_=0, to=20,
                    width=4, font=('Consolas',11)).grid(row=0,column=1,sticky='w')
        tk.Label(cf, text=_T('world_settings.lbl_max_climb_note'),
                 bg=self._BG, fg=self._FG2, font=('Arial',8,'italic')
                 ).grid(row=0,column=2,sticky='w',padx=(6,8))
        # Jazyk programovania
        lf = self._frame(p, _T('world_settings.frame_lang')); lf.pack(fill='x')
        prog_langs = _available_prog_langs()   # [(code, name), ...]
        self._prog_lang_codes = [c for c,_ in prog_langs]
        self._prog_lang_var   = tk.StringVar()
        tk.Label(lf, text=_T('world_settings.lbl_prog_lang'),
                 bg=self._BG, fg=self._FG, font=('Arial',9)
                 ).grid(row=0,column=0,sticky='e',padx=(8,4),pady=6)
        cb_prog = ttk.Combobox(lf, textvariable=self._prog_lang_var,
                               values=[n for _,n in prog_langs],
                               state='readonly', width=26, font=('Arial',9))
        cb_prog.grid(row=0,column=1,sticky='w',padx=(0,8),pady=6)
        try:
            cb_prog.current(self._prog_lang_codes.index(w.settings.prog_lang))
        except ValueError:
            cb_prog.current(0)
        # Live update Commands tab pri zmene jazyka
        cb_prog.bind('<<ComboboxSelected>>', lambda e: self._on_prog_lang_changed())

    def _get_prog_lang_code(self) -> str:
        """Vráti aktuálne vybraný kód programovacieho jazyka z Comboboxu."""
        try:
            names = [n for _,n in _available_prog_langs()]
            idx   = names.index(self._prog_lang_var.get())
            return self._prog_lang_codes[idx]
        except (ValueError, IndexError, AttributeError):
            return 'sk'

    def _on_prog_lang_changed(self):
        """Zavolá sa pri zmene Comboboxu prog_lang — live update názvov príkazov.
        Ak vybraný jazyk obsahuje DISABLED direktívu, skryje a zaškrtne dané tokeny."""
        lang = self._get_prog_lang_code()
        disabled = _LANG_DISABLED.get(lang, set())
        for tok, cb in self._cmd_cbs.items():
            cb.configure(text=_primary_kw(tok, lang))
            if tok in disabled:
                var = self._cmd_vars[tok]
                var.set(True)
                cb.grid_remove()          # skryť checkbox
            else:
                cb.grid()                 # zobraziť checkbox (prípadne znova)
        # Skryť celú skupinu ak sú všetky jej tokeny zakázané
        for grp_key, toks in self._cmd_grp_keys:
            frame = next((f for k,f in self._cmd_grp_frames if k==grp_key), None)
            if frame is None: continue
            if disabled and all(t in disabled for t in toks):
                frame.pack_forget()
            else:
                frame.pack(fill='x', pady=(0,4))

    def _upd_hnote(self):
        try:
            x,y = int(self._kx_var.get()), int(self._ky_var.get())
            w = self._cur_world   # výšku tehiel čítame z aktuálneho sveta
            if 0<=x<w.width and 0<=y<w.height:
                h = w._height(x,y)
                if h>0:
                    self._hnote.config(
                        text=_T('world_settings.hnote_stack').format(x=x, y=y, h=h))
                else:
                    self._hnote.config(text='')
        except (ValueError, tk.TclError): pass

    # -- Tab: Zásoby ----------------------------------------------------------
    def _build_inventory(self, p):
        s = self._work.settings
        tk.Label(p,text=_T('world_settings.inv_intro'),
                 bg=self._BG,fg=self._FG2,font=('Arial',9,'italic')
                 ).pack(anchor='w',pady=(0,10))
        self._inv: dict = {}
        for key,label,limit in [
            ('brick',    _T('world_settings.inv_brick'),    s.brick_limit),
            ('big_brick',_T('world_settings.inv_big_brick'),s.big_brick_limit),
            ('mark',     _T('world_settings.inv_mark'),     s.mark_limit),
        ]:
            row = tk.Frame(p,bg=self._BG); row.pack(fill='x',pady=4)
            unl = tk.BooleanVar(value=(limit==-1))
            cnt = tk.IntVar(value=(limit if limit>=0 else 5))
            tk.Label(row,text=label,bg=self._BG,fg=self._FG,
                     font=('Arial',9),width=14,anchor='w').pack(side='left')
            sp = ttk.Spinbox(row,textvariable=cnt,from_=0,to=9999,
                             width=6,font=('Consolas',11))
            sp.pack(side='left',padx=(0,10))
            cb = tk.Checkbutton(row,text=_T('world_settings.inv_unlimited'),variable=unl,
                                bg=self._BG,fg=self._FG,selectcolor='#1a1a44',
                                activebackground=self._BG,font=('Arial',9))
            cb.pack(side='left')
            def _toggle(v=unl,s=sp):
                s.configure(state='disabled' if v.get() else 'normal')
            _toggle()
            unl.trace_add('write', lambda *a,f=_toggle: f())
            self._inv[key] = (unl,cnt)

    # -- Tab: Príkazy ---------------------------------------------------------
    def _build_cmds(self, p):
        s = self._work.settings
        self._cmds_intro_lbl = tk.Label(p,text=_T('world_settings.cmds_intro'),
                 bg=self._BG,fg=self._FG2,font=('Arial',8,'italic'))
        self._cmds_intro_lbl.pack(anchor='w',pady=(0,6))
        self._cmd_vars:     dict = {}   # tok → BooleanVar
        self._cmd_cbs:      dict = {}   # tok → Checkbutton (pre live update textu)
        self._cmd_grp_keys: list = [    # [(grp_T_key, [(TOK,...), ...]), ...]
            ('world_settings.grp_move',   ['FORWARD','BACK','LEFT','RIGHT']),
            ('world_settings.grp_bricks', ['DROP','DROP_BIG','PICK']),
            ('world_settings.grp_marks',  ['MARK','CLEAR']),
            ('world_settings.grp_speed',  ['SLOWLY','QUICKLY']),
        ]
        self._cmd_grp_frames: list = []   # LabelFrame widgety — pre live update titulu
        self._cmds_parent = p             # uschováme pre rebuild (ak by bol potrebný)
        lang = self._get_prog_lang_code()
        for grp_key, toks in self._cmd_grp_keys:
            gf = self._frame(p, _T(grp_key)); gf.pack(fill='x',pady=(0,4))
            self._cmd_grp_frames.append((grp_key, gf))
            for col, tok in enumerate(toks):
                var = tk.BooleanVar(value=(tok in s.disabled_cmds))
                fg  = '#ff6666' if tok in s.disabled_cmds else self._FG
                label = _primary_kw(tok, lang)
                cb = tk.Checkbutton(gf, text=label, variable=var,
                               bg=self._BG, fg=fg, selectcolor='#3a1a1a',
                               activebackground=self._BG, font=('Arial',9))
                cb.grid(row=0, column=col, padx=8, pady=4, sticky='w')
                self._cmd_vars[tok] = var
                self._cmd_cbs[tok]  = cb
        self._sep(p)
        self._proc_var = tk.BooleanVar(value=s.disable_procedure)
        tk.Checkbutton(p,text=_T('world_settings.disable_proc'),
                       variable=self._proc_var,
                       bg=self._BG,fg=self._FG,selectcolor='#3a1a1a',
                       activebackground=self._BG,font=('Arial',9)
                       ).pack(anchor='w',pady=2)

    # -- Tab: Pohľad ----------------------------------------------------------
    def _build_camera(self, p):
        s = self._work.settings
        self._cam_lock_var = tk.BooleanVar(value=s.camera_locked)
        tk.Checkbutton(p,text=_T('world_settings.cam_lock'),
                       variable=self._cam_lock_var,
                       bg=self._BG,fg=self._FG,selectcolor='#1a1a44',
                       activebackground=self._BG,font=('Arial',10)
                       ).pack(anchor='w',pady=(0,10))
        tk.Label(p,text=_T('world_settings.cam_lock_note'),
                 bg=self._BG,fg=self._FG2,font=('Arial',9,'italic'),
                 wraplength=360,justify='left').pack(anchor='w',pady=(0,8))
        cf = tk.Frame(p,bg=self._BG2,padx=10,pady=8); cf.pack(fill='x')
        az_d = round(math.degrees(self._cam.az)%360,1)
        el_d = round(math.degrees(self._cam.el),1)
        for row,(lbl,val) in enumerate([
            (_T('world_settings.cam_az'),   f'{az_d}°'),
            (_T('world_settings.cam_el'),   f'{el_d}°'),
            (_T('world_settings.cam_dist'), f'{round(self._cam.dist,1)}'),
        ]):
            tk.Label(cf,text=lbl,bg=self._BG2,fg=self._FG2,
                     font=('Arial',9),anchor='w').grid(row=row,column=0,sticky='w',pady=2)
            tk.Label(cf,text=val,bg=self._BG2,fg='#44aaff',
                     font=('Consolas',10)).grid(row=row,column=1,sticky='w',padx=14)

    # -- Tab: Misia -----------------------------------------------------------
    def _build_mission(self, p):
        w = self._work
        tk.Label(p, text=_T('world_settings.mission_note'),
                 bg=self._BG, fg=self._FG2, font=('Arial',8,'italic'),
                 wraplength=360, justify='left').pack(anchor='w', pady=(0,6))

        # Reset pri neúspechu
        self._reset_on_failure_var = tk.BooleanVar(value=w.mission_reset_on_failure)
        tk.Checkbutton(p,
            text=_T('world_settings.reset_on_fail'),
            variable=self._reset_on_failure_var,
            bg=self._BG, fg='#ffcc66', selectcolor='#2a2000',
            activebackground=self._BG, font=('Arial',9)
        ).pack(anchor='w', pady=(0,8))

        # Zoznam podmienok
        cf2 = self._frame(p, _T('world_settings.frame_conds'))
        cf2.pack(fill='both', expand=True, pady=(0,4))
        lf = tk.Frame(cf2, bg=self._BG); lf.pack(fill='both', expand=True, padx=8, pady=(6,4))
        self._cond_lb = tk.Listbox(lf, bg='#0d0d22', fg='#ccccee',
                                   selectbackground='#2a2a55', font=('Consolas',9),
                                   height=5, relief='flat', activestyle='dotbox')
        sb2 = ttk.Scrollbar(lf, command=self._cond_lb.yview)
        self._cond_lb.configure(yscrollcommand=sb2.set)
        self._cond_lb.pack(side='left', fill='both', expand=True)
        sb2.pack(side='right', fill='y')

        # Inicializácia zo sveta
        self._goal_conditions: list = list(w.goal_conditions)
        for i, c in enumerate(self._goal_conditions):
            self._cond_lb.insert('end', self._cond_label(i, c))

        self._cond_lb.bind('<Double-Button-1>', lambda e: self._edit_condition())
        bf2 = tk.Frame(cf2, bg=self._BG); bf2.pack(fill='x', padx=8, pady=(0,6))
        tk.Button(bf2, text=_T('world_settings.btn_add_cond'), command=self._add_condition,
                  bg='#1a4a1a', fg='white', relief='flat', padx=8, pady=3,
                  font=('Arial',9), cursor='hand2').pack(side='left', padx=(0,6))
        tk.Button(bf2, text=_T('world_settings.btn_edit_cond'), command=self._edit_condition,
                  bg='#1a2a4a', fg='white', relief='flat', padx=8, pady=3,
                  font=('Arial',9), cursor='hand2').pack(side='left', padx=(0,6))
        tk.Button(bf2, text=_T('world_settings.btn_del_cond'), command=self._remove_condition,
                  bg='#4a1a1a', fg='white', relief='flat', padx=8, pady=3,
                  font=('Arial',9), cursor='hand2').pack(side='left')

        # HTML správy
        mf = self._frame(p, _T('world_settings.frame_msgs')); mf.pack(fill='x', pady=(4,0))
        self._msg_success_var = tk.StringVar(value=w.success_html)
        self._msg_failure_var = tk.StringVar(value=w.failure_html)
        for row2,(lbl,var) in enumerate([
            (_T('world_settings.msg_success'), self._msg_success_var),
            (_T('world_settings.msg_failure'), self._msg_failure_var),
        ]):
            tk.Label(mf, text=lbl, bg=self._BG, fg=self._FG2,
                     font=('Arial',8)).grid(row=row2, column=0, sticky='w', padx=8, pady=3)
            tk.Entry(mf, textvariable=var, bg='#1a1a44', fg='white',
                     font=('Arial',9), insertbackground='white', relief='flat'
                     ).grid(row=row2, column=1, sticky='ew', padx=(0,8), pady=3)
        mf.columnconfigure(1, weight=1)

    def _cond_label(self, idx: int, cond) -> str:
        if idx == 0:
            prefix = '     '
        else:
            op = cond.op.upper()
            prefix = f' {op} ' if op == 'OR' else f'{op} '
        return prefix + cond.describe()

    def _refresh_cond_lb(self):
        """Znovu naplní celý listbox (po zmene poradia alebo op)."""
        self._cond_lb.delete(0, 'end')
        for i, c in enumerate(self._goal_conditions):
            self._cond_lb.insert('end', self._cond_label(i, c))

    def _add_condition(self):
        dlg = GoalConditionDialog(self, self._cur_world)
        self.wait_window(dlg)
        if dlg.result:
            self._goal_conditions.append(dlg.result)
            self._cond_lb.insert('end', self._cond_label(len(self._goal_conditions)-1, dlg.result))

    def _edit_condition(self):
        sel = self._cond_lb.curselection()
        if not sel: return
        idx = sel[0]
        dlg = GoalConditionDialog(self, self._cur_world, edit_cond=self._goal_conditions[idx])
        self.wait_window(dlg)
        if dlg.result:
            self._goal_conditions[idx] = dlg.result
            self._refresh_cond_lb()
            self._cond_lb.selection_set(idx)

    def _remove_condition(self):
        sel = self._cond_lb.curselection()
        if not sel: return
        idx = sel[0]
        self._cond_lb.delete(idx)
        del self._goal_conditions[idx]

    def _upd_reset_cb(self):
        pass   # eval je teraz per-podmienka, reset_cb je vždy aktívny

    # -- Apply ----------------------------------------------------------------
    def _apply(self):
        w = self._work
        s = w.settings
        # 1. Rozmery
        try:   new_w,new_h = max(3,min(50,int(self._w_var.get()))), max(3,min(50,int(self._h_var.get())))
        except (ValueError,tk.TclError): new_w,new_h = w.width,w.height
        if new_w!=w.width or new_h!=w.height:
            w.resize(new_w,new_h)
        # 2. Pozícia a smer Karela
        try:   kx,ky = max(0,min(new_w-1,int(self._kx_var.get()))), max(0,min(new_h-1,int(self._ky_var.get())))
        except (ValueError,tk.TclError): kx,ky = w.karel_x,w.karel_y
        w.karel_x,w.karel_y = kx,ky
        w.karel_dir = Direction.from_str(self._dir_var.get())
        try:   s.max_climb = max(0, int(self._max_climb_var.get()))
        except (ValueError, tk.TclError): s.max_climb = 1
        s.prog_lang = self._get_prog_lang_code()
        # 3. Zásoby
        for key,(unl,cnt) in self._inv.items():
            try:   val = -1 if unl.get() else max(0,int(cnt.get()))
            except (ValueError,tk.TclError): val=-1
            if key=='brick':      s.brick_limit=val
            elif key=='big_brick': s.big_brick_limit=val
            elif key=='mark':     s.mark_limit=val
        # 4. Zakázané príkazy
        s.disabled_cmds      = {t for t,v in self._cmd_vars.items() if v.get()}
        s.disable_procedure  = self._proc_var.get()
        # 5. Pohľad
        s.camera_locked = self._cam_lock_var.get()
        if s.camera_locked:
            s.camera_az,s.camera_el,s.camera_dist = self._cam.az,self._cam.el,self._cam.dist
        # 6. Popis
        w.title      = self._title_var.get().strip()
        w.intro_html = self._intro_text.get('1.0', 'end').rstrip()
        # 7. Misia
        w.goal_conditions          = list(self._goal_conditions)
        w.mission_reset_on_failure = self._reset_on_failure_var.get()
        w.success_html            = self._msg_success_var.get().strip()
        w.failure_html            = self._msg_failure_var.get().strip()
        # Aplikuj na app — bez resetovania Karela
        try:
            app = self._app
            app._base = w          # _base = základ pre Reset (štartová pozícia z nastavení)
            cur = app._world       # aktuálny bežiaci svet — Karel zostane kde je
            s = w.settings
            # Skopíruj len polia ktoré WorldSettings mení; tehly/steny/značky netreba meniť
            cur.settings               = deepcopy(s)
            cur.goal_conditions        = list(w.goal_conditions)
            cur.mission_reset_on_failure = w.mission_reset_on_failure
            cur.success_html           = w.success_html
            cur.failure_html           = w.failure_html
            cur.title                  = w.title
            cur.intro_html             = w.intro_html
            # Resize ak sa zmenili rozmery
            if cur.width != w.width or cur.height != w.height:
                cur.resize(w.width, w.height)
            # Kamera
            if s.camera_locked:
                app._canvas.cam.az   = s.camera_az
                app._canvas.cam.el   = s.camera_el
                app._canvas.cam.dist = s.camera_dist
            app._canvas.render()
            # UI aktualizácia
            app._nav.update_inventory(cur)
            app._nav.set_camera_locked(s.camera_locked)
            app._ctrl.apply_restrictions(s)
            app._ctrl.set_prog_lang(s.prog_lang)
            app._prog.set_prog_lang(s.prog_lang)
            app._prog.set_disabled_cmds(s.disabled_cmds, s.disable_procedure)
            app._world_title_var.set(w.title or "Karlov Svet")
        except Exception as e:
            import traceback
            messagebox.showerror("Chyba pri aplikovaní nastavení", traceback.format_exc())
        finally:
            self.destroy()


# =========================================================================
# HLAVNÁ  APLIKÁCIA
# =========================================================================

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Karel 2010")
        self.geometry("1240x820")
        self.configure(bg='#060610')
        # Tmavá ttk téma — clam umožňuje nastaviť fieldbackground na Treeview
        _s = ttk.Style(self)
        _s.theme_use('clam')
        _s.configure('.',           background='#1a1a33', foreground='#ccccff')
        _s.configure('TScrollbar',  background='#2a2a55', troughcolor='#0a0a1c',
                                    arrowcolor='#8888bb', borderwidth=0)
        _s.configure('TSpinbox',    fieldbackground='#04040e', foreground='#ccccff',
                                    background='#1a1a33', arrowcolor='#8888bb')
        _s.configure('TNotebook',   background='#0a0a1c', borderwidth=0)
        _s.configure('TNotebook.Tab', background='#1a1a33', foreground='#aaaacc',
                                      padding=(8,3))
        _s.map('TNotebook.Tab',     background=[('selected','#2a2a55')],
                                    foreground=[('selected','#ffffff')])
        self._role = _ini_read_role()            # úroveň z karel.ini
        self._base=World.from_json(BUILTIN_WORLD)
        self._world=self._base.copy()
        self._interp=KarelInterpreter(self._world)
        self._running=False
        self._last_procs={}   # procedúry z posledného úspešného parsovania
        self._build_menu(); self._build_ui()
        self._load_ex(list(EXAMPLES.keys())[0])
        self._apply_role_to_ui()                 # skryje/zobrazí položky podľa roly

    # ---- Menu ------------------------------------------------------------
    def _build_menu(self):
        mb=tk.Menu(self,bg='#1a1a33',fg='#ccccff',tearoff=0)
        self.config(menu=mb)
        self._menubar = mb

        def sub(lbl):
            m=tk.Menu(mb,tearoff=0,bg='#1a1a33',fg='#ccccff')
            mb.add_cascade(label=lbl,menu=m)
            return m

        # Edituj — ukladanie sveta a nastavenia vyžadujú rolu teacher+
        e=sub(_T('menu.edit'))
        e.add_command(label=_T('menu.open_program'), command=self._open_prg)
        e.add_command(label=_T('menu.save_program'), command=self._save_prg)
        e.add_separator()
        e.add_command(label=_T('menu.open_world'),   command=self._open_world)
        e.add_command(label=_T('menu.save_world'),   command=self._save_world)
        e.add_separator()
        e.add_command(label=_T('menu.world_settings'), command=self._settings_editor)
        self._menu_edit = e

        p=sub(_T('menu.view'))
        p.add_command(label=_T('menu.reset_view'),
                      command=lambda:[setattr(self._canvas.cam,'az',math.radians(225)),
                                      setattr(self._canvas.cam,'el',math.radians(28)),
                                      self._canvas.render(),
                                      self._nav.render_axes()])

        pr=sub(_T('menu.program'))
        pr.add_command(label=_T('menu.run_menu'),   command=self._run)
        pr.add_command(label=_T('menu.stop_menu'),  command=self._stop)
        pr.add_command(label=_T('menu.reset_menu'), command=self._reset)

        # Nastavenia
        n=sub(_T('menu.settings'))
        n.add_command(label=_T('menu.change_role'),     command=self._change_role)
        n.add_command(label=_T('menu.global_settings'), command=self._global_settings)
        self._menu_nast = n

        h=sub(_T('menu.help'))
        h.add_command(label=_T('menu.about'), command=self._about)

    def _apply_role_to_ui(self):
        """Skryje / zobrazí položky menu podľa aktuálnej roly."""
        role = self._role
        is_teacher = _ROLES.index(role) >= _ROLES.index('teacher')
        is_admin   = role == 'admin'

        e = self._menu_edit
        # Indexy položiek v menu Edituj:
        # 0 Otvoriť program, 1 Uložiť program,
        # 2 separator, 3 Otvoriť svet, 4 Uložiť svet,
        # 5 separator, 6 Uložiť svet ako XML,
        # 7 separator, 8 ⚙ Nastavenia sveta
        teacher_items = [4, 6, 8]
        for idx in teacher_items:
            e.entryconfigure(idx, state='normal' if is_teacher else 'disabled')

        # Globálne nastavenia — len admin (index 1 v menu Nastavenia)
        self._menu_nast.entryconfigure(1, state='normal' if is_admin else 'disabled')

        # Titulok okna — zobrazuje rolu
        lbl = _T(f'role_dialog.label_{role}')
        self.title(f"Karel 2010  [{lbl}]")

    def _retranslate_ui(self):
        """Prekreslí všetky preložiteľné prvky UI po zmene jazyka GUI."""
        # Menu — najjednoduchšie prebudiť celé menu znovu
        self._build_menu()
        self._apply_role_to_ui()
        # Toolbar labely
        self._intro_btn.configure(text=_T('toolbar.task'))
        self._run_btn.configure(text=_T('toolbar.run'))
        self._stop_btn.configure(text=_T('toolbar.stop'))
        self._reset_btn.configure(text=_T('toolbar.reset'))
        self._speed_lbl.configure(text=_T('toolbar.speed'))
        self._examples_lbl.configure(text=_T('toolbar.examples'))
        # Panely
        self._nav.retranslate()
        self._ctrl.retranslate()
        self._prog.retranslate()

    def _global_settings(self):
        """Otvorí dialóg globálnych nastavení (len pre admina)."""
        GlobalSettingsDialog(self)

    def _change_role(self):
        """Zmení rolu v karel.ini ak má používateľ právo zápisu."""
        if not _ini_is_writable():
            messagebox.showwarning("Zmena úrovne",
                "Nemáte právo meniť konfiguráciu.\n"
                "(Súbor karel.ini nie je zapisateľný pre aktuálneho používateľa.)")
            return
        dlg = RoleDialog(self, self._role)
        self.wait_window(dlg)
        if dlg.result and dlg.result != self._role:
            if _ini_write_role(dlg.result):
                self._role = dlg.result
                self._apply_role_to_ui()
                lbl = _T(f'role_dialog.label_{self._role}')
                self._status(f"Úroveň zmenená na: {lbl}", "#44aacc")
            else:
                messagebox.showerror("Chyba", "Nepodarilo sa uložiť karel.ini.")

    # ---- UI Layout -------------------------------------------------------
    def _build_ui(self):
        # Status a toolbar sa packujú pred hlavným panelom (inak by expand=True pohltil status)
        self._stv=tk.StringVar(value="Pripravený / Ready")
        self._stl=tk.Label(self,textvariable=self._stv,bg='#030308',fg='#88cc88',
                            anchor='w',padx=10,pady=2,font=('Consolas',10))
        self._stl.pack(fill='x',side='bottom')

        tb=tk.Frame(self,bg='#111130',pady=4); tb.pack(fill='x',side='top')
        self._build_toolbar(tb)

        # ---- PanedWindow štruktúra ----
        # vpane: horný pás (3D + pravý panel) | dolný pás (program)
        vpane=tk.PanedWindow(self,orient='vertical',bg='#060610',
                             sashwidth=5,sashrelief='flat',sashpad=1)
        vpane.pack(fill='both',expand=True)

        # horný pás: hpane — 3D svet | pravý panel (nav + ovládanie)
        hpane=tk.PanedWindow(vpane,orient='horizontal',bg='#060610',
                             sashwidth=5,sashrelief='flat',sashpad=1)
        self._hpane=hpane

        # 3D svet (ľavý panel)
        wf=tk.Frame(hpane,bg='#000008',bd=1,relief='sunken')
        titlebar=tk.Frame(wf,bg='#000011')
        titlebar.pack(fill='x')
        tk.Label(titlebar,text="Izba1",bg='#000011',fg='#888888',
                 font=('Arial',9)).pack(side='left',padx=8)
        self._world_title_var=tk.StringVar(value="Karlov Svet")
        tk.Label(titlebar,textvariable=self._world_title_var,
                 bg='#000011',fg='#44ff88',
                 font=('Arial',12,'bold')).pack(side='left',padx=20)
        self._canvas=World3D(wf,self._world)
        self._canvas.pack(fill='both',expand=True)
        hpane.add(wf,stretch='always',minsize=180)

        # Pravý panel: Navigator + Ovládanie fixne, vždy celé viditeľné
        rp=tk.Frame(hpane,bg='#0a0a1c')
        self._nav=NavigatorPanel(rp,self._canvas.cam,
                                  on_change=lambda:[self._canvas.render(),self._nav.render_axes()])
        self._nav.pack(fill='x',side='top')
        self._canvas.on_cam_change=self._nav.render_axes
        self._ctrl=ControlPanel(rp,lambda:self._world,
                                 on_action=self._on_direct,
                                 get_procs=lambda:self._last_procs)
        self._ctrl.pack(fill='x',side='top')
        hpane.add(rp,stretch='never',minsize=130)

        vpane.add(hpane,stretch='always',minsize=280)

        # Program panel (dolný pás)
        pf=tk.Frame(vpane,bg='#050510',bd=1,relief='sunken')
        self._prog=ProgramPanel(pf); self._prog.pack(fill='both',expand=True)
        # Keď sa zmení editor, _last_procs sa aktualizuje — Príkazovo má vždy aktuálne procedúry
        self._prog.on_procs_update=lambda p: setattr(self,'_last_procs',p)
        vpane.add(pf,stretch='always',minsize=150)

        # Po vykreslení: nastav delič tak, aby pravý panel bol úzky (~210px)
        # a 3D svet dostal zvyšok. Užívateľ môže delič potom ťahať.
        self.after(80, self._init_right_width)

    def _init_right_width(self):
        try:
            total = self._hpane.winfo_width()
            if total <= 1:
                self.after(80, self._init_right_width); return
            right = 210
            x = max(180, total - right)
            self._hpane.sash_place(0, x, 0)
        except Exception:
            pass

    def _build_toolbar(self,bar):
        def btn(txt,cmd,bg='#2a5a9a'):
            b=tk.Button(bar,text=txt,command=cmd,bg=bg,fg='white',relief='flat',
                      padx=10,pady=4,font=('Arial',10,'bold'),cursor='hand2',
                      activebackground='#4477bb',activeforeground='white',bd=0)
            b.pack(side='left',padx=2); return b
        # Tlačidlo Zadanie — zobrazí intro_html aktuálneho sveta
        self._intro_btn=btn(_T('toolbar.task'), self._show_intro, '#2a4a7a')
        tk.Frame(bar,width=8,bg='#111130').pack(side='left')
        self._run_btn=btn(_T('toolbar.run'),  self._run,  '#1a6a2a')
        self._stop_btn=btn(_T('toolbar.stop'), self._stop, '#6a1a1a')
        self._reset_btn=btn(_T('toolbar.reset'),self._reset,'#4a4a1a')
        tk.Frame(bar,width=14,bg='#111130').pack(side='left')
        self._speed_lbl=tk.Label(bar,text=_T('toolbar.speed'),bg='#111130',fg='#ccc',
                 font=('Arial',10))
        self._speed_lbl.pack(side='left')
        self._spd=tk.DoubleVar(value=0.25)
        ttk.Scale(bar,from_=0.02,to=2.0,orient='horizontal',
                  variable=self._spd,length=100,
                  command=lambda v:setattr(self._interp,'delay',round(2.02-float(v),3))
                  ).pack(side='left',padx=4)
        tk.Frame(bar,width=14,bg='#111130').pack(side='left')
        self._examples_lbl=tk.Label(bar,text=_T('toolbar.examples'),bg='#111130',fg='#ccc',
                 font=('Arial',10))
        self._examples_lbl.pack(side='left')
        self._exv=tk.StringVar()
        cb=ttk.Combobox(bar,textvariable=self._exv,values=list(EXAMPLES.keys()),
                         state='readonly',width=22)
        cb.pack(side='left',padx=4)
        cb.bind('<<ComboboxSelected>>',lambda e:self._load_ex(self._exv.get()))

    # ---- Akcie -----------------------------------------------------------
    def _status(self,msg,col='#88cc88'):
        self._stv.set(msg); self._stl.configure(fg=col)

    def _set_running_ui(self, running: bool):
        """Zapne/vypne Run tlačidlo podľa stavu behu programu."""
        if running:
            self._run_btn.configure(state='disabled', bg='#0d3a0d',
                                    fg='#448844', cursor='')
        else:
            self._run_btn.configure(state='normal', bg='#1a6a2a',
                                    fg='white', cursor='hand2')

    def _load_ex(self,name):
        if name in EXAMPLES:
            self._prog.editor.delete('1.0','end')
            self._prog.editor.insert('1.0',EXAMPLES[name])
            self._exv.set(name); highlight(self._prog.editor)

    def _run(self):
        if self._running: self._status("Už beží!","#ccaa44"); return
        src=self._prog.editor.get('1.0','end')
        try: prog=parse(src)
        except Exception as e: messagebox.showerror("Syntaxová chyba",str(e)); return
        # Kontrola nastavení sveta
        s = self._base.settings
        if s.disable_procedure and prog.procedures:
            messagebox.showerror("Zakázané",
                "Definovanie vlastných príkazov (prikaz … koniec) je v tomto svete zakázané!")
            return
        # Ulož procedúry — dostupné aj v priamom ovládaní
        self._last_procs=prog.procedures
        self._prog.set_user_procs(list(prog.procedures.keys()))
        # Upozornenie ak chýba hlavný blok
        if not prog.main_stmts:
            if prog.procedures:
                messagebox.showinfo("Chýba hlavný blok",
                    "Program obsahuje definície príkazov, ale chýba hlavný blok.\n\n"
                    "Pridaj na koniec:\n\nzaciatok\n  <sem_nazov_prikazu>\nkoniec")
            else:
                messagebox.showwarning("Prázdny program","Program neobsahuje žiadne príkazy.")
            return
        # Neresetujeme svet — program beží z aktuálnej polohy Karela.
        # Reset robí iba tlačidlo ↺.
        self._running=True; self._status("Beží...","#44aacc")
        self._set_running_ui(True)
        it=KarelInterpreter(self._world)
        it.delay=round(2.02-self._spd.get(),3)
        # Callbacky sa volajú cez after() — bezpečné z vlákna interpretera
        def _safe(fn):
            return lambda *a: self._canvas.after(0, lambda: fn(*a))
        it.on_step=self._on_step
        it.on_error=_safe(self._on_err)
        it.on_finish=_safe(self._on_fin)
        self._interp=it
        threading.Thread(target=it.run,args=(prog,),daemon=True).start()

    def _stop(self):
        if self._interp: self._interp.stop()
        self._running=False; self._set_running_ui(False)
        self._status("Zastavené.","#cc8844")

    def _reset(self):
        self._stop(); self._reset_world(); self._status("Reset.","#88cc88")

    def _show_intro(self):
        """Zobrazí úvodné zadanie úlohy (intro_html) aktuálneho sveta."""
        w = self._base
        if not w.intro_html and not w.title:
            self._status("Tento svet nemá žiadne zadanie.", '#888888')
            return
        IntroDialog(self, w.title, w.intro_html)

    def _settings_editor(self):
        WorldSettingsDialog(self)

    def _reset_world(self):
        self._running=False          # poistka — predchádza zaseknutiu po vlákne
        self._world=self._base.copy()
        self._world.reset_inventory()
        if self._interp: self._interp.world=self._world
        self._canvas.set_world(self._world)
        # Zamknutý pohľad
        s = self._base.settings
        if s.camera_locked:
            self._canvas.cam.az   = s.camera_az
            self._canvas.cam.el   = s.camera_el
            self._canvas.cam.dist = s.camera_dist
            self._canvas.render()
        # Inventár, reštrikcie, zvýrazňovanie
        self._nav.update_inventory(self._world)
        self._nav.set_camera_locked(s.camera_locked)
        self._ctrl.apply_restrictions(s)
        self._ctrl.set_prog_lang(s.prog_lang)   # aktualizuje akčné tlačidlá podľa jazyka sveta
        self._prog.set_prog_lang(s.prog_lang)   # aktualizuje zoznam príkazov a filter
        self._prog.set_disabled_cmds(s.disabled_cmds, s.disable_procedure)

    def _on_step(self):
        self._canvas.after(0,self._canvas.render)
        self._canvas.after(0,lambda:self._nav.update_inventory(self._world))
        if self._world.goal_conditions:
            self._canvas.after(0, self._check_mission_step)

    def _on_err(self,m):
        self._running=False
        self._set_running_ui(False)
        self._canvas.render()
        self._status(f"Chyba: {m}","#cc4444")
        messagebox.showerror("Chyba",m)

    def _on_fin(self,m):
        self._running=False
        self._set_running_ui(False)
        self._canvas.render()
        self._status(m if m else "Hotovo! ✓","#cc8844" if m else "#44cc44")
        # Vyhodnotenie misie — len pri prirodzenom skončení (nie Stop)
        if not m and self._world.goal_conditions:
            self._check_mission()

    def _on_direct(self,ok,err=None):
        self._canvas.after(0,self._canvas.render)
        self._nav.update_inventory(self._world)
        if not ok and err:
            self._canvas.after(0,lambda:self._status(f"Chyba: {err}","#cc4444"))
        elif ok and self._world.goal_conditions:
            self._check_mission_step()

    def _check_mission(self):
        """Vyhodnotí on_finish podmienky misie — zobrazí výsledok."""
        w = self._world
        if not w.goal_conditions: return
        result = evaluate_goals(w, on_step=False)
        if result is None: return
        success = (result == 'success')
        if not success and w.mission_reset_on_failure:
            self._reset_world()
        MissionResultDialog(self, success,
                            w.success_html if success else w.failure_html)

    def _check_mission_step(self):
        """Vyhodnotí on_step podmienky po každom kroku."""
        w = self._world
        if not w.goal_conditions: return
        result = evaluate_goals(w, on_step=True)
        if result == 'success':
            if self._interp: self._interp.stop()
            self._running = False
            self._set_running_ui(False)
            self._status("Misia splnená! ✓", "#44cc44")
            MissionResultDialog(self, True, w.success_html)
        elif result == 'failure':
            if self._interp: self._interp.stop()
            self._running = False
            self._set_running_ui(False)
            self._status("Misia nesplnená ✗", "#cc4444")
            if w.mission_reset_on_failure:
                self._reset_world()
            MissionResultDialog(self, False, w.failure_html)

    # ---- Súbory ----------------------------------------------------------
    def _open_prg(self):
        p=filedialog.askopenfilename(title="Otvoriť program",
            filetypes=[("Karel program","*.prg"),("Text","*.txt"),("Všetky","*.*")])
        if not p: return
        try:
            with open(p,encoding='utf-8',errors='replace') as f: src=f.read()
            self._prog.editor.delete('1.0','end')
            self._prog.editor.insert('1.0',src)
            highlight(self._prog.editor); self._status(f"Načítané: {os.path.basename(p)}")
        except Exception as e: messagebox.showerror("Chyba",str(e))

    def _save_prg(self):
        p=filedialog.asksaveasfilename(title="Uložiť program",
            defaultextension='.prg',filetypes=[("Karel program","*.prg"),("Text","*.txt")])
        if not p: return
        try:
            with open(p,'w',encoding='utf-8') as f: f.write(self._prog.editor.get('1.0','end'))
            self._status(f"Uložené: {os.path.basename(p)}")
        except Exception as e: messagebox.showerror("Chyba",str(e))

    def _open_world(self):
        p=filedialog.askopenfilename(title="Otvoriť svet",
            filetypes=[("Karel svet","*.karxml *.karjson *.json"),("Karel XML","*.karxml"),
                       ("Karel JSON (starý formát)","*.karjson *.json"),("Všetky","*.*")])
        if not p: return
        try:
            if p.lower().endswith('.karxml') or p.lower().endswith('.xml'):
                self._base=World.from_xml(p)
            else:
                with open(p,encoding='utf-8') as f: d=json.load(f)
                self._base=World.from_json(d)
            self._reset_world()
            # Ak svet obsahuje program, načítaj ho do editora
            if self._base.program_text:
                self._prog.editor.delete('1.0','end')
                self._prog.editor.insert('1.0', self._base.program_text)
                highlight(self._prog.editor)
            # Nastav titulok sveta
            title = self._base.title or os.path.splitext(os.path.basename(p))[0]
            self._world_title_var.set(title)
            self._status(f"Svet: {os.path.basename(p)}")
            # Automaticky zobraz zadanie úlohy ak existuje
            if self._base.intro_html:
                self.after(200, self._show_intro)
        except Exception as e: messagebox.showerror("Chyba",str(e))

    def _save_world(self):
        p=filedialog.asksaveasfilename(title="Uložiť svet",
            defaultextension='.karxml',filetypes=[("Karel svet","*.karxml"),("Všetky","*.*")])
        if not p: return
        try:
            self._world.program_text = self._prog.editor.get('1.0','end').rstrip()
            xml_str = self._world.to_xml()
            with open(p,'w',encoding='utf-8') as f: f.write(xml_str)
            self._base = self._world.copy()   # uložený stav = nový základ
            self._status(f"Svet uložený: {os.path.basename(p)}")
        except Exception as e: messagebox.showerror("Chyba",str(e))

    def _about(self):
        messagebox.showinfo("Karel 2010",
            "Karel 2010 – Python port\nOriginal: Zimo, 2005\n\n"
            "3D view controls:\n"
            "  Left drag   → rotate\n"
            "  Right drag  → pan\n"
            "  Scroll wheel → zoom\n\n"
            "Bricks: Karel places/picks up in front of himself.\n"
            "Mark: Karel marks the tile he stands on.\n"
            "Karel can climb 1 brick, not 2.\n\n"
            "github.com/ZimoSka/karel2010")


# =========================================================================
# ÚROVNE POUŽÍVATEĽOV  /  USER ROLES
# =========================================================================

# Cesta ku konfiguračnému súboru — vedľa skriptu
_INI_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'karel.ini')

# Poradie úrovní (vyšší index = vyššia úroveň)
_ROLES      = ['student', 'teacher', 'admin']

# -------------------------------------------------------------------------
# JAZYKOVÁ INFRAŠTRUKTÚRA  /  LANGUAGE INFRASTRUCTURE
# -------------------------------------------------------------------------

_LANG_DIR   = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lang')

def _available_ui_langs() -> list:
    """Vráti [(kód, zobrazené_meno), …] pre všetky dostupné jazyky GUI (lang/*.ini).
    Zoradené podľa kódu.  Fallback: [('sk','Slovenčina'),('en','English')]."""
    langs = []
    if os.path.isdir(_LANG_DIR):
        for fname in sorted(os.listdir(_LANG_DIR)):
            if fname.endswith('.ini') and not fname.startswith('_'):
                code = fname[:-4]
                cfg  = configparser.ConfigParser(interpolation=None)
                try:
                    cfg.read(os.path.join(_LANG_DIR, fname), encoding='utf-8')
                    name = cfg.get('meta', 'name', fallback=code)
                except Exception:
                    name = code
                langs.append((code, name))
    return langs or [('sk', 'Slovenčina'), ('en', 'English')]

def _available_prog_langs() -> list:
    """Vráti [(kód, zobrazené_meno), …] pre všetky dostupné programovacie jazyky
    (lang/interpreter/*.lng).  Meno načíta prednostne z _LANG_NAME (direktíva NAME
    v .lng súbore), potom z lang/{kód}.ini [meta] name, inak kód."""
    langs = []
    if os.path.isdir(_INTERP_LANG_DIR):
        for fname in sorted(os.listdir(_INTERP_LANG_DIR)):
            if fname.endswith('.lng'):
                code = fname[:-4]
                # 1) NAME direktíva priamo v .lng súbore
                if code in _LANG_NAME:
                    name = _LANG_NAME[code]
                else:
                    # 2) lang/{kód}.ini [meta] name  (iba ak súbor existuje)
                    ini_path = os.path.join(_LANG_DIR, f'{code}.ini')
                    cfg      = configparser.ConfigParser(interpolation=None)
                    try:
                        cfg.read(ini_path, encoding='utf-8')
                        name = cfg.get('meta', 'name', fallback=code)
                    except Exception:
                        name = code
                langs.append((code, name))
    return langs or [('sk', 'Slovenčina'), ('en', 'English')]

# Aktuálny prekladový slovník — naplní sa pri štarte cez _load_ui_lang()
_ui_strings:        dict = {}
_current_prog_lang: str  = 'sk'

def _load_ui_lang(lang: str = 'sk') -> None:
    """Načíta lang/{lang}.ini do _ui_strings (všetky sekcie okrem action_labels)."""
    global _ui_strings
    path = os.path.join(_LANG_DIR, f'{lang}.ini')
    if not os.path.exists(path):
        path = os.path.join(_LANG_DIR, 'sk.ini')
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.read(path, encoding='utf-8')
    flat: dict = {}
    for sec in cfg.sections():
        for key, val in cfg.items(sec):
            flat[f'{sec}.{key}'] = val.strip()
    _ui_strings = flat

def _T(key: str, **fmt) -> str:
    """Vráti preložený reťazec pre daný kľúč (sekcia.kľúč).
    Ak kľúč neexistuje, vráti samotný kľúč ako fallback."""
    val = _ui_strings.get(key, key)
    if fmt:
        try:
            val = val.format(**fmt)
        except (KeyError, ValueError):
            pass
    return val

# Mapovanie: kľúč akcie (v ControlPanel) → token interpretera
_ACTION_TOKEN = {
    'drop':     'DROP',
    'drop_big': 'DROP_BIG',
    'pick':     'PICK',
    'mark':     'MARK',
    'clear':    'CLEAR',
}

def _switch_prog_lang(lang: str) -> None:
    """Prepne aktuálny programovací jazyk (nastaví _current_prog_lang).
    Labely akčných tlačidiel sledujú GUI jazyk (_ui_strings), nie prog_lang."""
    global _current_prog_lang
    _current_prog_lang = lang

def _prog_btn(action: str) -> tuple:
    """Vráti (display_label, karel_command) pre danú akciu.
    Label pochádza z [action_labels] GUI jazykového súboru (sleduje GUI lang).
    Príkaz je primárne kľúčové slovo z interpreter/*.lng pre aktuálny prog_lang."""
    token = _ACTION_TOKEN.get(action, action.upper())
    # Label = GUI jazyk (action_labels sekcia z _ui_strings)
    label = (_ui_strings.get('action_labels.' + token.lower())
             or _primary_kw(token, _current_prog_lang))
    label = label.replace('\\n', '\n')   # ini ukladá \n ako literal backslash-n
    # Command = programovací jazyk
    cmd   = _primary_kw(token, _current_prog_lang)
    return label, cmd

def _ini_read_ui_lang() -> str:
    """Načíta jazyk UI z karel.ini; fallback 'sk'."""
    cfg = configparser.ConfigParser()
    if os.path.exists(_INI_PATH):
        try:
            cfg.read(_INI_PATH, encoding='utf-8')
            lang = cfg.get('ui', 'lang', fallback='sk').strip().lower()
            if os.path.exists(os.path.join(_LANG_DIR, f'{lang}.ini')):
                return lang
        except Exception:
            pass
    return 'sk'

def _ini_write_ui_lang(lang: str) -> bool:
    """Uloží jazyk UI do karel.ini."""
    cfg = configparser.ConfigParser()
    if os.path.exists(_INI_PATH):
        try:
            cfg.read(_INI_PATH, encoding='utf-8')
        except Exception:
            pass
    if not cfg.has_section('ui'):
        cfg.add_section('ui')
    cfg.set('ui', 'lang', lang)
    try:
        with open(_INI_PATH, 'w', encoding='utf-8') as f:
            cfg.write(f)
        return True
    except (PermissionError, OSError):
        return False

# Načítaj predvolené jazyky okamžite (pred vytvorením App)
_load_ui_lang(_ini_read_ui_lang())
_switch_prog_lang('sk')   # default prog_lang; _reset_world() ho prepíše podľa sveta


def _ini_read_role() -> str:
    """Načíta rolu z karel.ini; ak súbor neexistuje vráti 'admin'."""
    cfg = configparser.ConfigParser()
    if os.path.exists(_INI_PATH):
        try:
            cfg.read(_INI_PATH, encoding='utf-8')
            r = cfg.get('user', 'role', fallback='admin').strip().lower()
            if r in _ROLES:
                return r
        except Exception:
            pass
    return 'admin'

def _ini_write_role(role: str) -> bool:
    """Uloží rolu do karel.ini. Vráti True pri úspechu."""
    cfg = configparser.ConfigParser()
    if os.path.exists(_INI_PATH):
        try:
            cfg.read(_INI_PATH, encoding='utf-8')
        except Exception:
            pass
    if not cfg.has_section('user'):
        cfg.add_section('user')
    cfg.set('user', 'role', role)
    try:
        with open(_INI_PATH, 'w', encoding='utf-8') as f:
            cfg.write(f)
        return True
    except (PermissionError, OSError):
        return False

def _ini_is_writable() -> bool:
    """Vráti True ak má aktuálny OS-používateľ právo meniť karel.ini."""
    if os.path.exists(_INI_PATH):
        return os.access(_INI_PATH, os.W_OK)
    # Súbor ešte neexistuje — skúsime zapísať
    try:
        open(_INI_PATH, 'a').close()
        return True
    except (PermissionError, OSError):
        return False


class GlobalSettingsDialog(tk.Toplevel):
    """Globálne nastavenia aplikácie — dostupné len adminovi."""
    _BG = '#0a0a1c'; _FG = '#ccccee'

    def __init__(self, app):
        super().__init__(app)
        self._app = app
        self.title("Globálne nastavenia")
        self.configure(bg=self._BG)
        self.resizable(False, False)
        self.grab_set(); self.transient(app)
        self._build()
        self.update_idletasks()
        pw, ph = app.winfo_width(), app.winfo_height()
        px, py = app.winfo_rootx(), app.winfo_rooty()
        ww, wh = self.winfo_width(), self.winfo_height()
        self.geometry(f'+{px+(pw-ww)//2}+{py+(ph-wh)//2}')

    def _row(self, parent, label, row):
        tk.Label(parent, text=label, bg=self._BG, fg=self._FG,
                 font=('Arial', 10), anchor='w').grid(
                 row=row, column=0, sticky='w', padx=(16,8), pady=6)

    def _build(self):
        tk.Label(self, text="Globálne nastavenia", bg='#111135', fg='#44aaff',
                 font=('Arial', 13, 'bold'), pady=10).pack(fill='x', padx=0)

        gf = tk.Frame(self, bg=self._BG); gf.pack(fill='both', padx=8, pady=8)

        # --- Jazyk GUI ---
        self._row(gf, "Jazyk rozhrania (GUI):", 0)
        ui_langs = _available_ui_langs()   # [(code, name), ...]
        cur_ui   = _ini_read_ui_lang()
        self._ui_lang_codes  = [c for c,_ in ui_langs]
        self._ui_lang_var    = tk.StringVar()
        cb_ui = ttk.Combobox(gf, textvariable=self._ui_lang_var,
                             values=[n for _,n in ui_langs],
                             state='readonly', width=22, font=('Arial', 10))
        cb_ui.grid(row=0, column=1, sticky='w', padx=8, pady=6)
        # nastav aktuálnu hodnotu
        try:
            cb_ui.current(self._ui_lang_codes.index(cur_ui))
        except ValueError:
            cb_ui.current(0)

        # --- Oddeľovač ---
        tk.Frame(gf, bg='#333355', height=1).grid(
            row=1, column=0, columnspan=2, sticky='ew', padx=8, pady=4)

        # --- Info ---
        tk.Label(gf, text="Zmena jazyka GUI sa prejaví okamžite.\n"
                           "Jazyk programovania sa nastavuje per-svet\nv záložke Miestnosť editora sveta.",
                 bg=self._BG, fg='#6666aa', font=('Arial', 9),
                 justify='left').grid(row=2, column=0, columnspan=2, sticky='w', padx=16, pady=(0,8))

        # --- Tlačidlá ---
        bf = tk.Frame(self, bg='#111130', pady=8); bf.pack(fill='x', side='bottom')
        tk.Button(bf, text='OK', width=10, command=self._apply,
                  bg='#2a5a9a', fg='white', relief='flat',
                  activebackground='#4477bb').pack(side='right', padx=8)
        tk.Button(bf, text='Zrušiť', width=10, command=self.destroy,
                  bg='#3a3a55', fg='white', relief='flat',
                  activebackground='#555577').pack(side='right', padx=4)
        self.bind('<Return>', lambda _: self._apply())
        self.bind('<Escape>', lambda _: self.destroy())

    def _apply(self):
        # Combobox zobrazuje meno — potrebujeme kód
        idx = 0
        try:
            from_langs = _available_ui_langs()
            names = [n for _,n in from_langs]
            idx = names.index(self._ui_lang_var.get())
            new_lang = from_langs[idx][0]
        except (ValueError, IndexError):
            new_lang = 'sk'
        old_lang = _ini_read_ui_lang()
        if new_lang != old_lang:
            if not _ini_is_writable():
                messagebox.showwarning("Chyba",
                    "Nemáte právo meniť konfiguráciu (karel.ini nie je zapisateľný).")
                return
            _ini_write_ui_lang(new_lang)
            _load_ui_lang(new_lang)
            self._app._retranslate_ui()
        self.destroy()


class RoleDialog(tk.Toplevel):
    """Dialóg na zmenu úrovne používateľa."""
    def __init__(self, parent, current_role: str):
        super().__init__(parent)
        self.title(_T('role_dialog.title'))
        self.configure(bg='#1a1a33')
        self.resizable(False, False)
        self.grab_set()
        self.result = None

        tk.Label(self, text=_T('role_dialog.select'), bg='#1a1a33', fg='#ccccff',
                 font=('Arial', 11)).pack(padx=20, pady=(16, 8))

        self._var = tk.StringVar(value=current_role)
        for r in _ROLES:
            rb = tk.Radiobutton(self, text=_T(f'role_dialog.label_{r}'),
                                variable=self._var, value=r,
                                bg='#1a1a33', fg='#ccccff', selectcolor='#333366',
                                activebackground='#1a1a33', activeforeground='#ffffff',
                                font=('Arial', 10))
            rb.pack(anchor='w', padx=30, pady=2)

        # Popisy úrovní
        descs = {r: _T(f'role_dialog.desc_{r}') for r in _ROLES}
        self._desc_var = tk.StringVar()
        self._var.trace_add('write', lambda *_: self._upd_desc(descs))
        self._upd_desc(descs)
        tk.Label(self, textvariable=self._desc_var, bg='#1a1a33', fg='#8888bb',
                 font=('Arial', 9), wraplength=280, justify='left').pack(
                 padx=20, pady=(6, 0))

        bf = tk.Frame(self, bg='#1a1a33')
        bf.pack(pady=14)
        tk.Button(bf, text=_T('role_dialog.btn_ok'), width=10, command=self._ok,
                  bg='#2a5a9a', fg='white', relief='flat',
                  activebackground='#4477bb').pack(side='left', padx=6)
        tk.Button(bf, text=_T('role_dialog.btn_cancel'), width=10, command=self.destroy,
                  bg='#3a3a55', fg='white', relief='flat',
                  activebackground='#555577').pack(side='left', padx=6)
        self.bind('<Return>', lambda _: self._ok())
        self.bind('<Escape>', lambda _: self.destroy())

    def _upd_desc(self, descs):
        self._desc_var.set(descs.get(self._var.get(), ''))

    def _ok(self):
        self.result = self._var.get()
        self.destroy()


# =========================================================================
if __name__=='__main__':
    App().mainloop()

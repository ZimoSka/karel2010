#!/usr/bin/env python3
"""
Konvertor binárnych .kar súborov (Karel 2010 / Delphi) do XML formátu .karxml

Prepísaný na základe Delphi zdrojového kódu (uMain.pas, Karel.pas).

Binárny formát .kar:
  Pre verziu > 0 (všetky moderné súbory):
    int32 × 4 : 0, 0, version, 0
    int32      : mi = High(Square)  = width  - 1
    int32      : mj = High(Square[0]) = height - 1
    int32      : dim (počet dummys, ignorujeme)
    int32      : Kar.RelPos.X  (relatívna pozícia, os. stred = Max.X = width//2)
    int32      : Kar.RelPos.Y
    byte       : Kar.RelAngle (0=NORTH,1=WEST,2=SOUTH,3=EAST — Delphi Y=0 je hore)
    Grid:
      for i in range(width):
        for j in range(height):
          int32 mk  (-1 = prázdna bunka)
          for k in range(mk+1): TObjects[40 bytes]
    int32+chars: intro HTML  (start.htm)
    int32+chars: success HTML (end0.htm)
    int32+chars: failure HTML (badend0.htm)
    int32+chars: program text
    ... (podmienky cieľov, nastavenia — momentálne preskakujeme)

  Pre verziu 0 (staré súbory):
    int32: mi, int32: mj, int32: dim — potom rovnaký formát bez version bloku

TObjects record (Delphi, zarovnaný na 8 bajtov):
  offset  0: Name   String[20] = 21 bajtov
  offset 21: Typ    ObjectType =  1 bajt  (0=SmallBrick,1=LargeBrick,2=oMark,3=None)
  offset 22: (2 bajty padding pre zarovnanie Double na 8)
  offset 24: Height Double     =  8 bajtov
  offset 32: BrickH Integer   =  4 bajty
  offset 36: ObjectN Integer  =  4 bajty
  TOTAL    = 40 bajtov

Súradnice:
  Delphi: RelPos.X/Y je relatívna (stred = 0). Y=0 je vizuálne HORE.
  karxml: x=0 vľavo, y=0 DOLE — čiže treba y-flip.
  karxml_x = RelPos.X + Max.X
  karxml_y = (height-1) - (RelPos.Y + Max.Y)
  Pre objekty v Square[i][j]: karxml_x=i, karxml_y=(height-1)-j
"""

import struct
import re
import sys
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom

# ─── Konštanty TObjects ──────────────────────────────────────────────────────
TOBJECTS_SIZE   = 40   # veľkosť záznamu v bajtoch
TYP_OFFSET      = 21   # offset poľa Typ v zázname
OT_SMALL = 0; OT_LARGE = 1; OT_MARK = 2; OT_NONE = 3

DIR_MAP = {0: 'N', 1: 'W', 2: 'S', 3: 'E'}   # Delphi RelAngle → karxml dir


# ─── Pomocná trieda na čítanie binárnych dát ─────────────────────────────────
class Reader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos  = 0

    def i32(self) -> int:
        v = struct.unpack_from('<i', self.data, self.pos)[0]; self.pos += 4; return v

    def u8(self) -> int:
        v = self.data[self.pos]; self.pos += 1; return v

    def tobject_type(self) -> int:
        """Prečíta TObjects record (40 bajtov), vráti hodnotu Typ."""
        typ = self.data[self.pos + TYP_OFFSET]
        self.pos += TOBJECTS_SIZE
        return typ

    def string_block(self) -> str:
        """Číta int32 length + znaky, dekóduje cp1250."""
        n = self.i32()
        if n <= 0 or self.pos + n > len(self.data):
            return ''
        raw = self.data[self.pos:self.pos + n]
        self.pos += n
        return raw.decode('cp1250', errors='replace')

    def ok(self, need: int = 1) -> bool:
        return self.pos + need <= len(self.data)

    def skip(self, n: int):
        self.pos += n


# ─── Hlavná extrakcia ─────────────────────────────────────────────────────────
def extract_kar(path: str) -> dict:
    data = open(path, 'rb').read()
    r    = Reader(data)

    # — Verzia a rozmery —
    v0 = r.i32(); v1 = r.i32(); v2 = r.i32()
    if v0 != 0 or v1 != 0:
        # Verzia 0: prvé tri int sú mi, mj, dim
        vers = 0
        mi, mj = v0, v1
        _ = v2          # dim
    else:
        # Moderný formát: 0, 0, version, 0, mi, mj, dim
        vers = v2
        r.i32()         # štvrtá nula
        mi  = r.i32()
        mj  = r.i32()
        r.i32()         # dim

    width  = mi + 1
    height = mj + 1
    max_x  = width  // 2
    max_y  = height // 2

    # — Karel pozícia a smer —
    rel_x   = r.i32()
    rel_y   = r.i32()
    rel_ang = r.u8()    # RelAngle : 0..3, sizeof = 1 bajt

    # Konverzia súradníc: Delphi Y=0 hore → karxml Y=0 dole
    karel_x   = max(0, min(width  - 1, rel_x + max_x))
    karel_y   = max(0, min(height - 1, (height - 1) - (rel_y + max_y)))
    karel_dir = DIR_MAP.get(rel_ang % 4, 'E')

    # — Grid: Square[0..mi][0..mj] —
    bricks     = {}    # (x,y) → count
    big_bricks = {}    # (x,y) → count
    marks      = set() # (x,y)

    for i in range(width):
        for j in range(height):
            if not r.ok(4):
                break
            mk = r.i32()    # High(Square[i,j]); -1 = prázdna bunka
            for k in range(mk + 1):
                if not r.ok(TOBJECTS_SIZE):
                    break
                typ = r.tobject_type()
                # y-flip: delphi j → karxml y
                kx, ky = i, (height - 1) - j
                if typ == OT_SMALL:
                    bricks[(kx, ky)]     = bricks.get((kx, ky), 0) + 1
                elif typ == OT_LARGE:
                    big_bricks[(kx, ky)] = big_bricks.get((kx, ky), 0) + 1
                elif typ == OT_MARK:
                    marks.add((kx, ky))

    # — Textové bloky —
    intro   = r.string_block() if r.ok(4) else ''  # start.htm
    success = r.string_block() if r.ok(4) else ''  # end0.htm
    failure = r.string_block() if r.ok(4) else ''  # badend0.htm
    program = r.string_block() if r.ok(4) else ''  # program text

    # Extrakcia čistého HTML body (ak je v obsahu celá HTML stránka)
    def _body(html: str) -> str:
        m = re.search(r'<body[^>]*>([\s\S]*?)</body>', html, re.IGNORECASE)
        return m.group(1).strip() if m else html.strip()

    title = os.path.splitext(os.path.basename(path))[0]

    return dict(
        width=width, height=height, vers=vers,
        karel_x=karel_x, karel_y=karel_y, karel_dir=karel_dir,
        bricks=bricks, big_bricks=big_bricks, marks=marks,
        intro=_body(intro), success=_body(success), failure=_body(failure),
        program=program.strip(),
        title=title,
    )


# ─── Generovanie XML ──────────────────────────────────────────────────────────
def to_xml(d: dict) -> str:
    root = ET.Element('world', width=str(d['width']), height=str(d['height']))

    ET.SubElement(root, 'karel',
                  x=str(d['karel_x']), y=str(d['karel_y']), dir=d['karel_dir'])

    # Steny — len okrajové (vnútorné steny v .kar neexistujú; veľké tehly slúžia ako steny)
    ws = ET.SubElement(root, 'walls')
    for x in range(d['width']):
        ET.SubElement(ws, 'wall', x=str(x), y='0',             side='S')
        ET.SubElement(ws, 'wall', x=str(x), y=str(d['height']-1), side='N')
    for y in range(d['height']):
        ET.SubElement(ws, 'wall', x='0',              y=str(y), side='W')
        ET.SubElement(ws, 'wall', x=str(d['width']-1), y=str(y), side='E')

    # Malé tehly
    br = ET.SubElement(root, 'bricks')
    for (x, y), cnt in sorted(d['bricks'].items()):
        ET.SubElement(br, 'brick', x=str(x), y=str(y), count=str(cnt))

    # Kvader (veľká tehla)
    bb = ET.SubElement(root, 'bigbricks')
    for (x, y), cnt in sorted(d['big_bricks'].items()):
        ET.SubElement(bb, 'bigbrick', x=str(x), y=str(y), count=str(min(cnt, 1)))

    # Značky
    mk = ET.SubElement(root, 'marks')
    for (x, y) in sorted(d['marks']):
        ET.SubElement(mk, 'mark', x=str(x), y=str(y))

    def _add(tag, val):
        if val and val.strip():
            el = ET.SubElement(root, tag)
            el.text = val

    _add('title',   d.get('title', ''))
    _add('intro',   d.get('intro',   ''))
    _add('success', d.get('success', ''))
    _add('failure', d.get('failure', ''))
    _add('program', d.get('program', ''))

    raw = ET.tostring(root, encoding='unicode')
    dom = minidom.parseString(raw)
    return dom.toprettyxml(indent='  ', encoding=None)


# ─── Hlavný program ───────────────────────────────────────────────────────────
def convert_file(kar_path: str):
    xml_path = os.path.splitext(kar_path)[0] + '.karxml'
    print(f'Konvertujem: {kar_path}')
    try:
        d = extract_kar(kar_path)
        xml_str = to_xml(d)
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(xml_str)
        nb = sum(d['bricks'].values())
        nbb = sum(d['big_bricks'].values())
        nm  = len(d['marks'])
        print(f'  OK  vers={d["vers"]}  '
              f'{d["width"]}x{d["height"]}  '
              f'Karel=({d["karel_x"]},{d["karel_y"]},{d["karel_dir"]})  '
              f'bricks={nb}  big={nbb}  marks={nm}')
    except Exception as e:
        print(f'  CHYBA: {e}')
        import traceback; traceback.print_exc()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        files = sys.argv[1:]
    else:
        folder = os.path.dirname(os.path.abspath(__file__))
        files  = [os.path.join(folder, f) for f in os.listdir(folder)
                  if f.lower().endswith('.kar')]

    if not files:
        print('Nenašli sa žiadne .kar súbory v aktuálnom priečinku.')
        print('Použitie: python kar_to_xml.py  alebo  python kar_to_xml.py subor.kar')
    else:
        for f in files:
            convert_file(f)
        print(f'\nHotovo — spracovaných {len(files)} súborov.')

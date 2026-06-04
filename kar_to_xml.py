#!/usr/bin/env python3
"""
Konvertor binárnych .kar súborov (Karel 2010 / Delphi) do XML formátu .karxml
Autor: generované pomocou Claude pre zimo, 2024

Spustenie:
  python kar_to_xml.py              -- konvertuje všetky .kar v aktuálnom priečinku
  python kar_to_xml.py súbor.kar    -- konvertuje konkrétny súbor
"""

import struct, re, sys, os
import xml.etree.ElementTree as ET
from xml.dom import minidom


# ──────────────────────────────────────────────────────────────────────────────
#  POMOCNÉ FUNKCIE
# ──────────────────────────────────────────────────────────────────────────────

def read_int32(data, offset):
    return struct.unpack_from('<i', data, offset)[0]

def clamp_coord(val, size):
    """Opraví prípadne záporné alebo príliš veľké koordináty."""
    if 0 <= val < size:
        return val
    # Pokus o korekciu záporných hodnôt (Delphi mohol uložiť inak)
    corrected = val % size
    if 0 <= corrected < size:
        return corrected
    return 0


# ──────────────────────────────────────────────────────────────────────────────
#  EXTRAKCIA OBSAHU Z BINÁRNEHO .kar SÚBORU
# ──────────────────────────────────────────────────────────────────────────────

def extract_kar(path):
    """
    Načíta .kar súbor a vráti dict so všetkými dekódovateľnými dátami.

    Formát hlavičky (5 × int32 = 20 bajtov):
      offset  0: šírka sveta (w)
      offset  4: výška sveta (h)
      offset  8: počet stien - 1 (alebo iná hodnota v niektorých verziách)
      offset 12: x-pozícia Karla (kx)
      offset 16: y-pozícia Karla (ky)
    Nasleduje 1 bajt: smer Karla (0=N, 1=E, 2=S, 3=W)

    Smer Karla v Delphi verzii:
      0 = NORTH (Sever)
      1 = EAST  (Východ)
      2 = SOUTH (Juh)
      3 = WEST  (Západ)
    """
    data = open(path, 'rb').read()

    w   = read_int32(data, 0)
    h   = read_int32(data, 4)
    kx  = read_int32(data, 12)
    ky  = read_int32(data, 16)
    kdir_byte = data[20] if len(data) > 20 else 1

    # Oprava koordinátov
    kx = clamp_coord(kx, w)
    ky = clamp_coord(ky, h)

    dir_map = {0: 'N', 1: 'E', 2: 'S', 3: 'W'}
    kdir = dir_map.get(kdir_byte % 4, 'E')

    # Dekódovanie textových sekcií (CP1250 / Windows-1250)
    text = data.decode('cp1250', errors='replace')

    # HTML správy: intro (štart), success (úspech), failure (neúspech)
    # Formát A: <body...>...</body>  (staršia verzia)
    html_blocks = re.findall(r'<body[\s\S]*?</body>', text, re.IGNORECASE)
    # Formát B: celé <html>...</html> stránky (novšia verzia)
    html_pages = re.findall(r'<html[\s\S]*?</html>', text, re.IGNORECASE)

    if html_blocks:
        intro   = html_blocks[0].strip()
        success = html_blocks[1].strip() if len(html_blocks) > 1 else ''
        failure = html_blocks[2].strip() if len(html_blocks) > 2 else ''
    elif html_pages:
        intro   = html_pages[0].strip()
        success = html_pages[1].strip() if len(html_pages) > 1 else ''
        failure = html_pages[2].strip() if len(html_pages) > 2 else ''
    else:
        intro = success = failure = ''

    # Program (zaciatok...Koniec)
    prog_match = re.search(r'[Zz]a[čc]iatok[\s\S]*?[Kk]oniec', text, re.DOTALL)
    program = prog_match.group(0).strip() if prog_match else 'zaciatok\n\nkoniec'

    # Navigácia: cesty k ďalšej a predchádzajúcej úrovni
    # Hľadáme Pascal-štýl length-prefixed strings na konci súboru
    nav_raw = re.findall(
        rb'[A-Za-z]:\\[^\x00-\x1f\xff]{4,60}\.(?:kar|prg|KAR|PRG)', data)
    nav = [n.decode('cp1250', errors='replace').replace('\\\\','\\') for n in nav_raw]
    next_level = nav[0] if nav else ''
    prev_level = nav[1] if len(nav) > 1 else ''

    # Steny — pokusom dekódovať z wall-objektov (d0 3f 01 00 VMT pattern)
    # POZNÁMKA: Dekódovanie binárnych stien je neúplné — pohladajte .pas zdrojový kód
    walls = _decode_walls(data, w, h)

    return dict(
        width=w, height=h, karel_x=kx, karel_y=ky, karel_dir=kdir,
        walls=walls, bricks=[], big_bricks=[], marks=[],
        intro=intro, success=success, failure=failure,
        program=program, next_level=next_level, prev_level=prev_level,
        title=os.path.splitext(os.path.basename(path))[0]
    )


def _decode_walls(data, w, h):
    """
    Dekódovanie stien z binárnych dát.

    Bez .pas zdrojového kódu sa nedá plne dekódovať štruktúra vnútorných stien.
    Vrátime iba okrajové steny (tie sú vždy prítomné v každom svete).

    Vnútorné steny treba doplniť manuálne v aplikácii Karel 2010.
    """
    walls = []
    # Okrajové steny — vždy prítomné v každom svete
    for x in range(w):
        walls.append((x, 0,   'S'))   # spodná hranica
        walls.append((x, h-1, 'N'))   # horná hranica
    for y in range(h):
        walls.append((0,   y, 'W'))   # ľavá hranica
        walls.append((w-1, y, 'E'))   # pravá hranica
    return walls


# ──────────────────────────────────────────────────────────────────────────────
#  GENEROVANIE XML
# ──────────────────────────────────────────────────────────────────────────────

def kar_data_to_xml(d):
    """Skonvertuje dekódované .kar dáta do XML reťazca."""
    root = ET.Element('world',
                      width=str(d['width']),
                      height=str(d['height']))
    ET.SubElement(root, 'karel',
                  x=str(d['karel_x']),
                  y=str(d['karel_y']),
                  dir=d['karel_dir'])

    # Steny — deduplikácia
    ws = ET.SubElement(root, 'walls')
    seen_walls = set()
    for entry in d['walls']:
        x, y, s = entry
        key = (x, y, s)
        if key not in seen_walls:
            seen_walls.add(key)
            ET.SubElement(ws, 'wall', x=str(x), y=str(y), side=s)

    # Tehly
    br = ET.SubElement(root, 'bricks')
    for x, y, cnt in d.get('bricks', []):
        ET.SubElement(br, 'brick', x=str(x), y=str(y), count=str(cnt))

    # Veľké tehly
    bb = ET.SubElement(root, 'bigbricks')
    for x, y, cnt in d.get('big_bricks', []):
        ET.SubElement(bb, 'bigbrick', x=str(x), y=str(y), count=str(cnt))

    # Značky
    mk = ET.SubElement(root, 'marks')
    for x, y in d.get('marks', []):
        ET.SubElement(mk, 'mark', x=str(x), y=str(y))

    # Metadáta
    def _add(tag, val):
        if val and val.strip():
            el = ET.SubElement(root, tag)
            el.text = val
    _add('title',      d.get('title', ''))
    _add('intro',      d.get('intro', ''))
    _add('success',    d.get('success', ''))
    _add('failure',    d.get('failure', ''))
    _add('program',    d.get('program', ''))
    _add('next_level', d.get('next_level', ''))
    _add('prev_level', d.get('prev_level', ''))

    raw = ET.tostring(root, encoding='unicode')
    dom = minidom.parseString(raw)
    return dom.toprettyxml(indent='  ', encoding=None)


# ──────────────────────────────────────────────────────────────────────────────
#  HLAVNÝ PROGRAM
# ──────────────────────────────────────────────────────────────────────────────

def convert_file(kar_path):
    xml_path = os.path.splitext(kar_path)[0] + '.karxml'
    print(f'Konvertujem: {kar_path}  ->  {xml_path}')
    try:
        d = extract_kar(kar_path)
        xml_str = kar_data_to_xml(d)
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(xml_str)
        print(f'  OK — w={d["width"]} h={d["height"]} '
              f'kx={d["karel_x"]} ky={d["karel_y"]} dir={d["karel_dir"]} '
              f'walls={len([e for e in d["walls"]])}')
    except Exception as e:
        print(f'  CHYBA: {e}')
        import traceback; traceback.print_exc()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        files = sys.argv[1:]
    else:
        folder = os.path.dirname(os.path.abspath(__file__))
        files = [os.path.join(folder, f) for f in os.listdir(folder)
                 if f.lower().endswith('.kar')]

    if not files:
        print('Nenašli sa žiadne .kar súbory.')
    else:
        for f in files:
            convert_file(f)
        print(f'\nHotovo — skonvertovaných {len(files)} súborov.')

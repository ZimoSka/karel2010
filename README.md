# Karel 2010

Vzdelávací programovací simulátor Karel the Robot — Python port originálneho projektu z roku 2005 (Turbo Pascal/Delphi, autor: Mgr. Zimo).

## Popis

Karel je robot pohybujúci sa po mriežkovom svete. Žiaci ho programujú pomocou jednoduchého jazyka (slovensky alebo anglicky), čím sa učia základy algoritmického myslenia.

Aplikácia obsahuje:
- **3D pohľad** so Z-buffer renderingom (perspektívna projekcia, ovládanie myšou)
- **Editor programov** s farebným zvýrazňovaním syntaxe a filtrom príkazov
- **Priame ovládanie** Karla tlačidlami a textovými príkazmi
- **Interpreter** celého jazyka Karel (procedúry, opakovanie, podmienky)
- **XML formát** pre ukladanie a načítanie svetov (`.karxml`)

## Spustenie

```
python karel2010.py
```

alebo dvojklikom na `Spusti Karel.bat`

### Požiadavky

- Python 3.8+
- `pip install pillow numpy` (pre Z-buffer 3D rendering)

Bez numpy/Pillow aplikácia beží v záložnom 2D painter móde.

## Jazyk Karel

```
zaciatok
  opakuj 4 krat
    dopredu
    vlavo
  koniec
koniec
```

Základné príkazy: `dopredu`, `dozadu`, `vlavo`, `vpravo`, `poloz`, `zdvihni`, `poloz_velku`, `oznac`, `odznac`

Podmienky: `stena`, `tehla`, `znacka`, `volno`

Definícia vlastného príkazu:
```
prikaz MojPrikaz
zaciatok
  dopredu
  dopredu
koniec
```

## Formát svetov (.karxml)

Svety sa ukladajú ako XML súbory. Príklad:

```xml
<world width="10" height="8">
  <karel x="1" y="1" dir="E"/>
  <walls>
    <wall x="0" y="0" side="S"/>
    ...
  </walls>
  <bricks>
    <brick x="3" y="1" count="2"/>
  </bricks>
  <marks>
    <mark x="5" y="0"/>
  </marks>
  <title>Môj svet</title>
  <program>zaciatok
  dopredu
koniec</program>
</world>
```

## Konverzia pôvodných svetov

Skript `kar_to_xml.py` konvertuje pôvodné binárne `.kar` súbory do XML formátu:

```
python kar_to_xml.py
```

## Autor

Originál: Mgr. Zimo, 2005  
Python port: 2024

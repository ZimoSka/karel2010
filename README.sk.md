# Karel 2010

> 🇬🇧 [English version / Anglická verzia](README.md)

Výukový programovací simulátor postavený na koncepte robota Karla — Python port pôvodného projektu z roku 2005 (Turbo Pascal/Delphi, Mgr. Zimo).

## Prehľad

Karel je robot, ktorý sa pohybuje v mriežkovom svete. Žiaci ho programujú jednoduchým jazykom (slovenské alebo anglické kľúčové slová) a učia sa tak základy algoritmického myslenia.

Vlastnosti:
- **3D pohľad** s Z-buffer renderovaním (perspektívna projekcia, ovládanie myšou)
- **Editor programov** so zvýrazňovaním syntaxe a filtrom príkazov
- **Priame ovládanie** Karla tlačidlami aj písanými príkazmi
- **Plnohodnotný interpreter** jazyka Karel (procedúry, cykly, podmienky)
- **XML formát svetov** na ukladanie a načítavanie (`.karxml`)
- **Editor nastavení sveta** — zakázané príkazy, zámok kamery, limity inventára
- **Systém misií** — definuj cieľové podmienky, vyhodnoť úspech/neúspech po skončení programu

## Spustenie

```
python karel2010.py
```

alebo dvakrát klikni na `Spusti Karel.bat`

### Požiadavky

- Python 3.8+
- `pip install pillow numpy` (pre Z-buffer 3D renderovanie)

Bez numpy/Pillow aplikácia použije záložný 2D painter režim.

## Jazyk Karel

Programy môžu byť písané v slovenčine alebo angličtine:

```
zaciatok
  opakuj 4 krat
    dopredu
    vlavo
  koniec
koniec
```

**Základné príkazy:** `dopredu`, `dozadu`, `vlavo`, `vpravo`, `poloz`, `zdvihni`, `poloz_velku`, `oznac`, `odznac`

**Podmienky:** `stena`, `tehla`, `znacka`, `volno`

**Definovanie vlastného príkazu:**
```
prikaz MojPrikaz
zaciatok
  dopredu
  dopredu
koniec
```

**Riadiace štruktúry:**
```
opakuj 5 krat ... koniec
kym nie stena rob ... koniec
ak tehla potom ... inak ... koniec
```

## Formát súborov svetov (.karxml)

Svety sú uložené ako XML súbory. Úplný príklad:

```xml
<world width="10" height="8">
  <karel x="1" y="1" dir="E"/>
  <bricks>
    <brick x="3" y="1" count="2"/>
  </bricks>
  <bigbricks>
    <bigbrick x="5" y="2" count="1"/>
  </bigbricks>
  <marks>
    <mark x="5" y="0"/>
  </marks>

  <title>Môj svet</title>
  <intro><![CDATA[<p>Popis úlohy pre žiaka.</p>]]></intro>

  <settings>
    <brick_limit>5</brick_limit>
    <disabled_cmds>BACK</disabled_cmds>
    <camera_locked>true</camera_locked>
  </settings>

  <mission eval="on_finish" reset_on_failure="true">
    <condition type="karel_pos" x="5" y="3"/>
    <condition type="cell_state" x="2" y="2" bricks="3"/>
  </mission>

  <program>zaciatok
  dopredu
koniec</program>
</world>
```

**Uloženie/načítanie:** `Edituj → Uložiť svet ako XML` / `Edituj → Otvoriť svet`

## Nastavenia sveta

Otvor cez `Edituj → Nastavenia sveta...` na nastavenie všetkých parametrov sveta v šiestich záložkách:

| Záložka | Možnosti |
|---------|---------|
| **Popis** | Názov sveta; popis/zadanie úlohy (HTML editor s panelom B/I/U/H1–H3) |
| **Miestnosť** | Šírka, výška, štartovacia pozícia a smer Karla |
| **Zásoby** | Max. malých tehál / veľkých tehál / značiek (alebo neobmedzene) |
| **Príkazy** | Zakázanie konkrétnych príkazov (červené v editore, sivé tlačidlá) |
| **Pohľad** | Zamknutie kamery na pevný uhol |
| **Misia** | Cieľové podmienky, režim vyhodnocovania, správy pre žiaka |

## Úrovne používateľov

Aktívna úroveň je uložená v `karel.ini` (vedľa skriptu). Bezpečnosť je na úrovni OS — kto má právo zápisu do tohto súboru, môže meniť úroveň.

| Úroveň | Čo môže robiť |
|--------|--------------|
| **Žiak** | Otváranie svetov; písanie a ukladanie programov |
| **Učiteľ** | Navyše: ukladanie svetov, editor nastavení sveta |
| **Admin** | Navyše: globálne nastavenia aplikácie (rezervované) |

Aktuálna úroveň sa zobrazuje v titulku okna. Zmeníte ju cez **Nastavenia → Zmeniť úroveň...** (dostupné len ak má aktuálny OS-používateľ právo zápisu do `karel.ini`). Ak `karel.ini` chýba, aplikácia štartuje ako **Admin** — čerstvé stiahnutie funguje bez konfigurácie.

```ini
; karel.ini
[user]
role = teacher
```

---

## Systém misií

Systém misií umožňuje učiteľovi definovať, čo musí žiak dosiahnuť. Konfiguruje sa v záložke **Misia** dialógu Nastavení sveta.

### Režimy vyhodnocovania

| Režim | Správanie |
|-------|-----------|
| **Po skončení programu** | Podmienky sa skontrolujú raz po prirodzenom skončení programu. |
| **Po každom kroku** | Podmienky sa kontrolujú po každej akcii Karla (vrátane priameho ovládania). Program sa automaticky zastaví pri splnení všetkých podmienok. |

**Reset pri neúspechu** (dostupné v režime *Po skončení programu*): ak podmienky nie sú splnené, svet sa automaticky resetuje do počiatočného stavu — program žiaka zostane v editore.

### Typy podmienok

| Typ | Popis |
|-----|-------|
| **Poloha Karla** | Karel musí byť na konkrétnych súradniciach X, Y a/alebo stáť na stohu danej výšky. |
| **Stav políčka** | Konkrétne políčko musí obsahovať presný počet malých tehál, veľkých tehál a/alebo značku. |
| **Snímok miestnosti** | Celá miestnosť (tehly, veľké tehly, značky) musí zodpovedať snímku zachytenému pri tvorbe sveta. Voliteľne vrátane polohy Karla. |

Všetky podmienky v zozname musia byť splnené súčasne.

## Konverzia pôvodných svetov

Skript `kar_to_xml.py` konvertuje pôvodné binárne `.kar` súbory na `.karxml`:

```
python kar_to_xml.py
```

> **Poznámka:** Pôvodný formát Karel nepoužíva vnútorné steny — namiesto nich slúžia veľké tehly. Okrajové steny a všetok textový obsah (úvodné texty, správy o úspechu/neúspechu, vložené programy) sú zachované.

## Ovládanie

| Akcia | Ako |
|-------|-----|
| Otočenie pohľadu | Ťahanie ľavým tlačidlom myši |
| Posun pohľadu | Ťahanie pravým tlačidlom myši |
| Priblíženie/oddialenie | Koliesko myši |
| Spustenie programu | Tlačidlo ▶ alebo `Program → Spustiť` |
| Zastavenie | Tlačidlo ⏹ |
| Reset sveta | Tlačidlo ↺ (vráti Karla a svet do počiatočného stavu) |
| Priame ovládanie | Panel vpravo dole — tlačidlá alebo napísanie príkazu + Enter |

## Dokumentácia

### Slovenčina

| Dokument | Komu | Popis |
|----------|------|-------|
| [docs/sk/navod-pre-ziakov.md](docs/sk/navod-pre-ziakov.md) | Žiaci | Popis rozhrania, rýchla referencia jazyka, riešenie problémov |
| [docs/sk/navod-pre-ucitelov.md](docs/sk/navod-pre-ucitelov.md) | Učitelia | Tvorba svetov, navrhovanie misií, pedagogická postupnosť |
| [docs/sk/jazyk-karla.md](docs/sk/jazyk-karla.md) | Všetci | Kompletná referencia jazyka Karel s príkladmi |

### English (technická dokumentácia)

| Document | Audience | Description |
|----------|----------|-------------|
| [docs/karxml-format.md](docs/karxml-format.md) | World authors | Full `.karxml` file format specification |
| [docs/architecture.md](docs/architecture.md) | Developers | Code architecture, data model, renderer, threading |

## Pozadie projektu

Karel 2010 je Python port pôvodného výukového programovacieho prostredia, ktoré vzniklo ako diplomová práca na Fakulte matematiky, fyziky a informatiky Univerzity Komenského v Bratislave (Mgr. Michal Zeman, 2004).

Koncept robota Karla pochádza od Richarda Pattisa (*Karel the Robot: A Gentle Introduction to the Art of Programming*, 1981) a bol prispôsobený pre slovenské základné školy v 80. rokoch Mariánom Vittekom, Andrejom Blahom a ďalšími. Karel 2010 pokračuje v tejto tradícii s moderným 3D rozhraním a konfigurovateľným systémom misií.

## Autor

Pôvodný projekt: Mgr. Zimo, 2005  
Python port: 2024  
https://github.com/ZimoSka/karel2010

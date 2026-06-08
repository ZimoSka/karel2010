# Karel 2010 — Návod pre žiakov

Karel 2010 je výukové programovacie prostredie pre deti. Karel je robot, ktorý žije v 3D miestnosti a plní príkazy, ktoré mu zadáš. Tvojou úlohou je naučiť Karla riešiť problémy písaním programov v jazyku Karel.

---

## Spustenie

```
python karel2010.py
```

alebo dvakrát klikni na **Spusti Karel.bat** vo Windows.

---

## Hlavné okno

Okno je rozdelené do štyroch oblastí:

```
┌─────────────────────────────┬──────────────────┐
│                             │  Kamera / Nav    │
│       3D Miestnosť          │                  │
│       (Karlov svet)         ├──────────────────┤
│                             │  Priame ovládanie│
├─────────────────────────────┴──────────────────┤
│              Editor programu                   │
└────────────────────────────────────────────────┘
```

| Oblasť | Účel |
|--------|------|
| **3D Miestnosť** | Miestnosť kde žije Karel. Zobrazuje Karla, tehly, značky, steny. |
| **Kamera / Nav** | Otáčanie, posun a zoom 3D pohľadu. Zobrazuje inventár Karla. |
| **Priame ovládanie** | Pohyb Karla tlačidlami alebo písaním príkazov. |
| **Editor programu** | Písanie a spúšťanie programov. |

---

## Ovládanie 3D pohľadu

| Akcia | Ako |
|-------|-----|
| Otočenie pohľadu | Ľavé tlačidlo myši + ťahanie |
| Posun pohľadu | Pravé tlačidlo myši + ťahanie |
| Priblíženie/oddialenie | Koliesko myši |
| Skok na predvolený pohľad | Kliknutie na šípky v paneli navigátora |

Panel **Navigátor** (vpravo hore) obsahuje predvolené uhly kamery. Ak učiteľ zamkol kameru, tieto tlačidlá sú vypnuté.

---

## Priame ovládanie

Karla môžeš ovládať priamo bez písania programu.

### Pomocou tlačidiel

Panel **Priame ovládanie** (vpravo dole) má tlačidlá pre každú základnú akciu: pohyb dopredu, dozadu, otočenie vľavo/vpravo, kladenie/dvíhanie tehál, kladenie/odstraňovanie značiek.

### Písaním príkazov

Prepni sa na záložku **„Príkazovo"** v paneli priameho ovládania. Napíš ľubovoľný príkaz Karla (napr. `dopredu`) a stlač **Enter**. Takto môžeš volať aj vlastné procedúry — po napísaní v editore sa objavia automaticky ako tlačidlá.

---

## Písanie a spúšťanie programov

### Editor

Programy píš v editore na spodku okna. Príkazy sa **automaticky zvýrazňujú farbou**:
- Známe príkazy sú **farebné**.
- Príkazy zakázané učiteľom sú **červené**.
- Komentáre (`//` alebo `{ }`) sú sivé.

### Zadanie úlohy

Klikni na **📋 Zadanie** v paneli nástrojov — zobrazí sa popis úlohy pre aktuálny svet. Ak svet obsahuje zadanie, zobrazí sa automaticky aj pri jeho otvorení.

### Spustenie programu

1. Napíš program do editora.
2. Klikni na **▶ Spustiť** v paneli nástrojov.
3. Karel vykonáva príkazy krok za krokom. Sleduj 3D pohľad.
4. Na predčasné zastavenie klikni na **⏹ Stop**.
5. Na návrat Karla na štartovaciu pozíciu klikni na **↺ Reset**.

> **Dôležité:** Program beží **z aktuálnej polohy Karla**, nie od začiatku. Ak si Karla pred tým presunul priamym ovládaním, program pokračuje odtiaľ. Na návrat na začiatok použi **↺ Reset**.

### Rýchlosť

**Posuvník rýchlosti** v paneli nástrojov ovláda rýchlosť Karla. Dopravo = rýchlejšie, doľava = pomalšie. V programe môžeš tiež použiť príkazy `pomaly` a `rychlo`.

---

## Karlov svet

### Miestnosť

Karel sa pohybuje na mriežke políčok. Miestnosť je ohraničená stenami zo všetkých štyroch strán. Karel **nemôže prejsť cez stenu** — pri pokuse nastane chyba.

### Tehly

- **Malé tehly** sa kladú pred Karla (`poloz`).
- **Veľké tehly** sa kladú pred Karla (`poloz_velku`). Sú vyššie a Karel cez ne nemôže prejsť — slúžia ako vnútorné steny.
- Karel môže vyjsť **najviac o 1 malú tehlu** vyššie ako je jeho aktuálne políčko.
- Malé tehly sa dvíhajú príkazom `zdvihni`.

### Značky

Značky sú ploché symboly, ktoré Karel kladie **na políčko kde stojí** (`oznac`). Odstrániť ich môže príkazom `odznac`. Značky sa hodia na označovanie navštívených políčok alebo na zanechávanie stopy.

### Inventár

Ak učiteľ nastavil obmedzenie, Karel začína s daným počtom tehál alebo značiek. Aktuálny inventár je zobrazený v paneli **Navigátor**. Keď počet klesne na nulu, daný príkaz skončí chybou.

### Rozpočet krokov a otočení

Učiteľ môže obmedziť **počet krokov** alebo **otočení**, ktoré máš k dispozícii
(počíta sa od posledného **Resetu**). Keď ich minieš, program sa zastaví a objaví sa
okno s tlačidlami **OK** a **Reset**. Vtedy treba úlohu vyriešiť **úspornejšie** —
menej krokov, šikovnejšia cesta. To isté platí pri ovládaní tlačidlami.

---

## Jazyk Karel — rýchla referencia

### Kostra programu

```
zaciatok
  dopredu
  vlavo
  dopredu
koniec
```

### Vlastné príkazy (procedúry)

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

### Cyklus opakuj

```
opakuj 4 krat
  dopredu
  vlavo
koniec
```

### Cyklus kým

```
kym nie stena rob
  dopredu
koniec
```

### Podmienka ak

```
ak tehla potom
  zdvihni
inak
  dopredu
koniec
```

### Všetky príkazy

| Príkaz | Čo robí |
|--------|---------|
| `dopredu` | Pohyb dopredu |
| `dozadu` | Pohyb dozadu |
| `vlavo` | Otočenie doľava |
| `vpravo` | Otočenie doprava |
| `poloz` | Položenie malej tehly pred Karla |
| `zdvihni` | Zdvihnutie malej tehly pred Karlom |
| `poloz_velku` | Položenie veľkej tehly pred Karla |
| `oznac` | Položenie značky na aktuálne políčko |
| `odznac` | Odstránenie značky z aktuálneho políčka |
| `pomaly` | Spomalenie |
| `rychlo` | Zrýchlenie |

### Podmienky

| Podmienka | Pravda keď |
|-----------|-----------|
| `stena` | Pred Karlom je stena alebo okraj |
| `tehla` | Pred Karlom je akákoľvek tehla |
| `volno` | Pred Karlom nie je tehla |
| `znacka` | Na políčku Karla je značka |

### Spájanie podmienok (`nie`, `a`, `alebo`)

Podmienku môžeš **negovať** slovom `nie` a viac podmienok **spojiť** spojkami
`a` (musia platiť obe) a `alebo` (stačí jedna). Na zoskupenie použi zátvorky `( )`.

```
ak stena alebo znacka potom vlavo koniec
kym nie stena a nie tehla rob dopredu koniec
ak (stena alebo tehla) a nie znacka potom dozadu koniec
```

Najskôr platí `nie`, potom `a`, nakoniec `alebo` — ako v matematike „krát pred plus".
Zátvorkami toto poradie zmeníš.

> **Tip:** Na chôdzu až k stene použi `kym nie stena` (nie `kym volno`) —
> `volno` totiž nereaguje na okraj miestnosti.

---

## Ukladanie a načítavanie

### Uloženie programu

`Edituj → Uložiť program` uloží tvoj `.prg` súbor.

### Načítanie programu

`Edituj → Otvoriť program` načíta `.prg` súbor do editora.

### Uloženie sveta

`Edituj → Uložiť svet ako XML` uloží aktuálny stav miestnosti (polohy tehál, značiek, Karla) ako `.karxml` súbor.

### Načítanie sveta

`Edituj → Otvoriť svet` otvorí `.karxml` alebo `.karjson` súbor sveta.

---

## Misie

Niektoré svety majú **misiu** — cieľ, ktorý musíš splniť. Popis úlohy je v názve sveta a môže sa zobraziť aj ako správa pri načítaní sveta.

Po skončení programu (alebo počas priameho ovládania, ak učiteľ zvolil „po každom kroku") simulátor skontroluje, či si misiu splnil:

- **Úspech ✓** — objaví sa zelený dialóg so správou o úspechu.
- **Neúspech ✗** — objaví sa červený dialóg so správou o neúspechu. Ak učiteľ povolil reset, svet sa automaticky vráti do pôvodného stavu a môžeš skúsiť znova.

---

## Úrovne používateľov a obmedzený režim

Karel 2010 môže bežať v troch režimoch podľa toho, čo nastavil učiteľ. Aktuálny režim je zobrazený v titulku okna.

| Režim | Čo môžeš robiť |
|-------|---------------|
| **Žiak** | Otváranie svetov; písanie a ukladanie programov. Niektoré položky menu môžu byť sivé. |
| **Učiteľ** | Navyše: ukladanie svetov, editor nastavení sveta. |
| **Admin** | Navyše: globálne nastavenia aplikácie. |

Ak je nejaká položka menu sivá, nemáš potrebnú úroveň prístupu. Požiadaj učiteľa alebo správcu systému.

---

## Riešenie problémov

| Problém | Pravdepodobná príčina | Riešenie |
|---------|----------------------|---------|
| „Karel narazil do steny" | Pokus o chôdzu cez stenu | Skontroluj cestu — pridaj kontrolu podmienky alebo otočenie pred pohybom |
| „Karel nevie vylesť" | Pokus o výstup na 2+ tehly naraz | Stav schody (po 1 tehle) alebo odober prebytočné tehly |
| „Príkaz je zakázaný" | Učiteľ zakázal tento príkaz | Prečítaj zadanie — musíš úlohu vyriešiť bez tohto príkazu |
| „Nemáš žiadne tehly" | Inventár tehál je prázdny | Spotreboval si všetky dostupné tehly |
| Program akoby zamrzol | Nekonečná rekurzia alebo veľmi pomalý chod | Klikni ⏹ Stop, skontroluj nekonečné slučky/rekurziu |
| Tlačidlo Spustiť je sivé | Program stále beží | Počkaj na dokončenie alebo klikni ⏹ Stop |

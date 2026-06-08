# Referencia jazyka Karel

Programy pre Karla môžete písať v **slovenčine** alebo v angličtine — obe sady kľúčových slov sú plne podporované a dajú sa aj kombinovať v jednom programe.

---

## Štruktúra programu

Každý program, ktorý Karel vykonáva automaticky, musí mať hlavný blok:

```
zaciatok
  dopredu
  dopredu
  vlavo
koniec
```

Vlastné príkazy (procedúry) sa definujú pred alebo za hlavným blokom:

```
prikaz Strana
zaciatok
  opakuj 3 krat dopredu koniec
  vlavo
koniec

zaciatok
  opakuj 4 krat Strana koniec
koniec
```

---

## Základné príkazy

| Slovensky | Anglicky | Popis |
|-----------|---------|-------|
| `dopredu` | `forward` | Pohyb o krok dopredu |
| `dozadu` / `vzad` | `back` | Pohyb o krok dozadu |
| `vlavo` / `vľavo` | `left` | Otočenie o 90° doľava |
| `vpravo` | `right` | Otočenie o 90° doprava |
| `poloz` / `položiť` | `drop` | Položenie malej tehly pred Karla |
| `zdvihni` / `zodvihni` | `pick` | Zdvihnutie malej tehly pred Karlom |
| `poloz_velku` / `poloz_v` | `drop_big` | Položenie veľkej tehly pred Karla |
| `oznac` / `označ` | `mark` | Položenie značky na políčko pod Karlom |
| `odznac` / `odznač` | `clear` | Odobratie značky z políčka pod Karlom |
| `pomaly` | `slowly` | Spomalenie Karla |
| `rychlo` / `rýchlo` | `quickly` | Zrýchlenie Karla |

### Poznámky k tehlám
- Karel kladie a dvíha tehly **pred sebou**, nie na políčku, kde stojí.
- Karel môže vyjsť **najviac o 1 tehlu** vyššie ako je jeho aktuálne políčko. Pri väčšom výškovom rozdiele nastane chyba.
- **Veľká tehla** sa rovná 5 malým tehlám na výšku. Na veľkú tehlu Karel nevystúpi — slúži ako vnútorná stena.

---

## Riadiace štruktúry

### Definícia vlastného príkazu (procedúra)

```
prikaz MenoPrikazu
zaciatok
  ...
koniec
```

- Procedúry môžu volať navzájom aj samy seba (rekurzia).
- Maximálna hĺbka rekurzie je 500 úrovní.
- Jazyk nemá premenné — ako „pamäť" slúži hĺbka rekurzie a stoh tehál.

### Cyklus opakuj

```
opakuj N krat
  ...
koniec
```

`N` musí byť celé číslo. Príklad:

```
opakuj 4 krat
  dopredu
  vlavo
koniec
```

### Cyklus kým

```
kym podmienka rob
  ...
koniec
```

Príklad — choď dopredu, kým nenarazíš na stenu:

```
kym nie stena rob
  dopredu
koniec
```

### Podmienka ak

```
ak podmienka potom
  ...
inak
  ...
koniec
```

Vetva `inak` je nepovinná:

```
ak tehla potom
  zdvihni
koniec
```

---

## Podmienky

| Slovensky | Anglicky | Pravda keď |
|-----------|---------|-----------|
| `stena` | `wall` | Pred Karlom je stena alebo okraj miestnosti |
| `tehla` | `brick` | Pred Karlom je aspoň jedna tehla (malá alebo veľká) |
| `volno` | `free` | Pred Karlom nie je žiadna tehla |
| `znacka` / `značka` | `sign` | Karel stojí na políčku so značkou |
| `pravda` | `true` | Vždy pravda |
| `nepravda` | `false` | Vždy nepravda |

### Logické spojky

Podmienky sa dajú negovať pomocou `nie` a spájať spojkami `a` / `alebo`.
Na zoskupenie slúžia zátvorky `( )`. Priorita: **nie > a > alebo**.

| Slovensky | Anglicky | Nemecky | Francúzsky | Taliansky | Španielsky |
|-----------|----------|---------|------------|-----------|------------|
| `nie` | `not` | `nicht` | `pas` | `non` | `no` |
| `a` (`aj`) | `and` | `und` | `et` | `e` | `y` |
| `alebo` | `or` | `oder` | `ou` | `o` | `o` |

```
kym nie stena rob dopredu koniec
ak nie znacka potom oznac koniec
ak stena alebo znacka potom vlavo koniec
kym nie stena a nie tehla rob dopredu koniec
ak (stena alebo tehla) a nie znacka potom dozadu koniec
```

> **Pozor:** `volno` a `stena` nie sú presné opaky na okraji miestnosti —
> `volno` okraj ignoruje, `stena` ho deteguje. Na chôdzu k stene použi
> `kym nie stena`, nie `kym volno`.

---

## Komentáre

```
// Toto je riadkový komentár
# Aj toto je riadkový komentár
{ Toto je blokový komentár }
```

---

## Príklady programov

### Chôdza po štvorci

```
prikaz Strana
zaciatok
  opakuj 3 krat dopredu koniec
  vlavo
koniec

zaciatok
  opakuj 4 krat Strana koniec
koniec
```

### Zber všetkých tehál v rade

```
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
```

### Riešenie bludiska (pravidlo pravej ruky)

```
prikaz Krok
zaciatok
  ak stena potom vlavo inak dopredu koniec
koniec

zaciatok
  opakuj 80 krat Krok koniec
koniec
```

### Označenie každého políčka až po stenu

```
zaciatok
  kym nie stena rob
    oznac
    dopredu
  koniec
  oznac
koniec
```

### Nekonečná slučka pomocou rekurzie

```
prikaz Navzdy
zaciatok
  dopredu
  vlavo
  Navzdy
koniec

zaciatok Navzdy koniec
```

> **Poznámka:** Chvostová rekurzia beží dovtedy, kým Karel nenarazí na stenu alebo kým sa nedosiahne limit rekurzie (500 úrovní).

### Prenesenie stĺpika tehál o krok dopredu

```
prikaz PreniesStlpik
zaciatok
  kym tehla rob
    zdvihni
    dopredu
    poloz
    dozadu
  koniec
koniec

zaciatok
  PreniesStlpik
koniec
```

---

## Gramatika jazyka (zjednodušená)

```
program      = { prikaz } hlavny_blok
prikaz       = 'prikaz' MENO hlavny_blok
hlavny_blok  = 'zaciatok' { prikaz } 'koniec'
prikazs      = prikaz
             | 'opakuj' CISLO 'krat' { prikazs } 'koniec'
             | 'kym' podmienka 'rob' { prikazs } 'koniec'
             | 'ak' podmienka 'potom' { prikazs } [ 'inak' { prikazs } ] 'koniec'
             | MENO
prikaz       = 'dopredu' | 'dozadu' | 'vlavo' | 'vpravo'
             | 'poloz' | 'zdvihni' | 'poloz_velku'
             | 'oznac' | 'odznac'
             | 'pomaly' | 'rychlo'
podmienka    = [ 'nie' ] ( 'stena' | 'tehla' | 'volno' | 'znacka' | 'pravda' | 'nepravda' )
```

---

## Pedagogický postup

Jazyk Karel bol navrhnutý pre konkrétnu postupnosť výučby:

1. **Priame ovládanie** — pohyb Karla tlačidlami, pochopenie relatívnej orientácie (čo je „vľavo" keď je Karel otočený rôznymi smermi?)
2. **Základné sekvencie** — krátke programy v tvare `zaciatok … koniec`
3. **Procedúry** — učíme Karla nové príkazy (`prikaz … koniec`), rozklad problémov
4. **Cyklus opakuj** — `opakuj N krat` keď vieme počet opakovaní vopred
5. **Cyklus kým** — `kym podmienka rob` keď počet opakovaní nie je vopred známy
6. **Podmienka ak** — `ak podmienka potom … inak` na vetvenie programu
7. **Rekurzia** — chvostová rekurzia ako nekonečná slučka; počítadlo z tehál

Odporúčaná veková skupina je 3. – 7. ročník základnej školy. Karel je premostenie na Logo a neskôr Pascal/Java.

# Karel 2010 — Návod pre učiteľov

Tento návod pokrýva všetko, čo učiteľ potrebuje na tvorbu svetov, navrhovanie misií a konfiguráciu výukového prostredia pre žiakov.

---

## Pedagogické pozadie

Karel 2010 je Python port pôvodného výukového programovacieho prostredia Karel 3D (Mgr. Michal Zeman, 2004, Univerzita Komenského v Bratislave). Projekt nadväzuje na tradíciu začatú Richardom Pattisom (1981) a prispôsobenú pre slovenské základné školy Mariánom Vittekom, Andrejom Blahom a ďalšími v 80. rokoch.

### Odporúčaná veková skupina

- **3. – 4. ročník ZŠ**: Len priame ovládanie (tlačidlá a písané príkazy). Zameranie na orientáciu v priestore, relatívny pohyb, základy práce s myšou.
- **4. – 7. ročník ZŠ**: Programovací režim. Sekvencie, procedúry, cykly, podmienky, a postupne rekurzia.

Karel je **premostenie** — nie náhrada za Logo ani Pascal. Jeho cieľom je naučiť algoritmické myslenie skôr, než sa žiaci stretnú s premennými a dátovými typmi.

### Odporúčaná postupnosť výučby

| Stupeň | Pojmy | Nástroje |
|--------|-------|---------|
| 1 | Priestorová orientácia, relatívny pohyb | Tlačidlá priameho ovládania |
| 2 | Sekvencie | Krátke programy (`zaciatok … koniec`) |
| 3 | Procedúry / rozklad problémov | `prikaz … koniec` |
| 4 | Počítané opakovanie | `opakuj N krat` |
| 5 | Podmienené opakovanie | `kym podmienka rob` |
| 6 | Vetvenie | `ak podmienka potom … inak` |
| 7 | Rekurzia | Chvostová rekurzia, počítadlo z tehál |

Kľúčový pedagogický poznaток z triednych experimentov: **`kym` je pre mladších žiakov konceptuálne ťažší ako `opakuj`**. Vyhraď mu extra čas.

---

## Vytvorenie sveta

### Dialóg nastavení sveta

Otvor cez **Edituj → ⚙ Nastavenia sveta...**

Dialóg má šesť záložiek:

---

### Záložka 1 — Popis

| Pole | Účel |
|------|------|
| **Názov sveta** | Krátky názov zobrazený v titulku okna. |
| **Popis / zadanie úlohy** | HTML text zobrazený žiakovi. Použi panel nástrojov B/I/U/H1/H2/H3 na formátovanie. Opíš úlohu, daj tipy alebo motivačný kontext. |

Zadanie úlohy sa žiakovi zobrazí dvoma spôsobmi:
- **Automaticky** — dialóg sa otvorí hneď po načítaní sveta (ak pole nie je prázdne).
- **Na požiadanie** — žiak si ho môže kedykoľvek znova otvoriť tlačidlom **📋 Zadanie** v paneli nástrojov.

**Tipy pre HTML:**
- Použij `<b>tučné</b>`, `<i>kurzíva</i>`, `<u>podčiarknuté</u>` na zvýraznenie.
- Použij `<h1>`, `<h2>`, `<h3>` na nadpisy.
- Použij `<br>` na nový riadok.
- Môžeš použiť ľubovoľné HTML — obrázky, tabuľky, odkazy.

---

### Záložka 2 — Miestnosť

| Pole | Účel |
|------|------|
| **Šírka / Výška** | Rozmery mriežky miestnosti (3–50 políčok). |
| **Karel X / Y** | Štartovacia poloha Karla. Predvyplnená z *aktuálnej* polohy Karla — presun Karla priamym ovládaním a potom ulož. |
| **Smer** | Smer Karla na štarte (S / V / J / Z). |

> **Tip:** Rozmiestnenia tehál, značiek a Karla nastav v 3D pohľade, potom otvor Nastavenia a klikni **Použiť** — aktuálna poloha Karla sa stane novou štartovacou polohou.

---

### Záložka 3 — Zásoby

Obmedzenie počtu predmetov, s ktorými Karel začína. Nechaj zaškrtnuté **Neobmedzene (∞)** pre žiadne obmedzenie.

| Obmedzenie | Efekt |
|-----------|-------|
| **Malé tehly** | Celkový počet malých tehál, ktoré môže Karel položiť. |
| **Veľké tehly** | Celkový počet veľkých tehál. |
| **Značky** | Celkový počet značiek. |

Aktuálny inventár je zobrazený v paneli Navigátor počas celej relácie.

---

### Záložka 4 — Príkazy

Zaškrtni príkaz na jeho **zakázanie** v tomto svete. Zakázané príkazy:
- Sú zobrazené **červenou farbou** v editore programov.
- Pri pokuse o spustenie spôsobia chybu.
- Sú sivé v paneli priameho ovládania.

Použiť na prinútenie žiakov riešiť úlohy bez určitých skratiek. Napríklad zakáž `dozadu` na vyžiadanie predvídavého plánovania.

Zaškrtávacia políčka **„Zakázať definovanie vlastných príkazov"** vypne `prikaz … koniec` — vhodné pre začiatočnícke fázy, kde chceš len `zaciatok … koniec` programy.

---

### Záložka 5 — Pohľad

Zaškrtni **Zamknúť pohľad** na zabránenie žiakom otáčať 3D scénu. Uhol kamery nastavený v 3D okne v momente kliknutia na Použiť sa uloží a vynúti.

Použiť na:
- Zafixovanie pedagogicky vhodnej perspektívy.
- Simuláciu pohľadu „z prvej osoby" z určitého uhla.
- Zabránenie rozptýleniu.

Po zamknutí sú všetky ovládacie prvky kamery (ťahanie myšou, tlačidlá navigátora) pre žiaka vypnuté.

---

### Záložka 6 — Misia

Definuj čo musí žiak dosiahnuť. Nechaj prázdne pre slobodné objavovanie sveta.

#### Režim vyhodnocovania

| Režim | Správanie |
|-------|-----------|
| **Po skončení programu** | Podmienky sa skontrolujú raz po prirodzenom skončení programu. Vhodné pre „napíš program, ktorý urobí X". |
| **Po každom kroku** | Kontroluje sa po každej akcii Karla, vrátane priameho ovládania. Program sa automaticky zastaví keď sú všetky podmienky splnené. Vhodné pre „dostaň Karla na pozíciu X". |

**Reset pri neúspechu** (dostupné v režime *Po skončení programu*): ak program žiaka nesplní podmienky, svet sa automaticky vráti do počiatočného stavu. Program žiaka zostane v editore na opravu a opakovanie.

#### Pridávanie podmienok

Klikni na **＋ Pridať podmienku** na definovanie cieľovej podmienky. Vyber jeden z troch typov:

**1. Poloha Karla**
Karel musí byť na konkrétnej súradnici a/alebo stáť na konkrétnej výške tehál. Zaškrtni len polia, ktoré chceš kontrolovať — nezaškrtnuté polia sa ignorujú.

| Pole | Príklad | Význam |
|------|---------|--------|
| X | 5 | Karel musí byť v stĺpci 5 |
| Y | 3 | Karel musí byť v riadku 3 |
| Výška | 4 | Karel musí stáť na stohu 4 malých tehál |

**2. Stav políčka**
Konkrétne políčko musí obsahovať určitý počet tehál alebo značku.

| Pole | Príklad | Význam |
|------|---------|--------|
| X, Y | 2, 4 | Políčko na (2,4) |
| Značka | ✓ zaškrtnuté | Políčko musí mať značku |
| Malé tehly | 3 | Políčko musí mať presne 3 malé tehly |
| Veľké tehly | 1 | Políčko musí mať presne 1 veľkú tehlu |

**3. Snímok miestnosti**
Celý stav miestnosti (všetky pozície tehál a značiek) musí zodpovedať snímku zachytenému teraz. Voliteľne tiež kontroluje polohu a smer Karla.

> **Tip pre snímky:** Najprv nastav miestnosť do požadovaného cieľového stavu (presun Karla, polož tehly atď.), potom pridaj podmienku snímku. Aktuálny stav miestnosti sa zachytí v momente kliknutia na **Pridať podmienku**.

#### Viacero podmienok

Môžeš pridať ľubovoľný počet podmienok. **Všetky podmienky musia byť splnené súčasne** pre úspech misie.

#### Správy pre žiaka

Zadaj text zobrazený žiakovi po vyhodnotení:
- **Správa pri úspechu**: Zobrazí sa pri splnení všetkých podmienok (zelený dialóg).
- **Správa pri neúspechu**: Zobrazí sa pri nesplnení podmienok (červený dialóg).

Obe polia podporujú prostý text alebo HTML.

---

## Úrovne používateľov

Aktívna úroveň je uložená v `karel.ini` (vedľa skriptu). Bezpečnosť je na úrovni OS — kto má právo zápisu do tohto súboru, môže meniť úroveň.

| Úroveň | Čo môže robiť |
|--------|--------------|
| **Žiak** | Otváranie svetov; písanie a ukladanie programov |
| **Učiteľ** | Navyše: ukladanie svetov, editor nastavení sveta (⚙) |
| **Admin** | Navyše: globálne nastavenia aplikácie (rezervované) |

Aktuálna úroveň sa zobrazuje v titulku okna: `Karel 2010  [Učiteľ]`. Zmeníte ju cez **Nastavenia → Zmeniť úroveň...** — ale len ak má aktuálny OS-používateľ právo zápisu do `karel.ini`.

### Ako funguje bezpečnosť

Žiadne heslo — bezpečnosť je delegovaná na operačný systém. Admin nastaví prístupové práva k súboru `karel.ini`:

| Prístup OS k `karel.ini` | Efekt |
|--------------------------|-------|
| Čítanie + zápis | Používateľ môže meniť úroveň cez menu |
| Len čítanie | Úroveň sa načíta pri štarte, ale nedá sa meniť z aplikácie |
| Bez prístupu / súbor chýba | Predvolená úroveň **Žiak** |

**Typické nastavenie v triede:**
1. Nainštaluj Karel 2010 do priečinka, napr. `C:\KarelSchool\`.
2. Nastav učiteľský/adminský účet ako jediný so zápisom do `karel.ini`.
3. Žiacke OS-účty majú len právo čítania.
4. Vytvor `karel.ini` ručne s `role = teacher` — učiteľský počítač má zapisovateľnú kópiu, žiacke majú kópiu read-only.

### Formát karel.ini

```ini
[user]
role = teacher
```

Platné hodnoty: `student`, `teacher`, `admin`.

Ak súbor neexistuje, aplikácia štartuje s úrovňou **Admin** — čerstvé stiahnutie teda funguje bez akejkoľvek konfigurácie. Obmedzenie prístupu: vytvor `karel.ini` s `role = student` a nastav ho ako read-only pre žiacke OS-účty.

---

## Uloženie sveta

`Edituj → Uložiť svet ako XML` uloží kompletný svet do `.karxml` súboru vrátane:
- Rozloženia miestnosti (všetky tehly, značky, steny)
- Štartovacej polohy a smeru Karla
- Všetkých nastavení (limity inventára, zakázané príkazy, zámok kamery)
- Podmienok misie
- HTML popisu zadania
- Aktuálneho programu v editore

---

## Navrhovanie dobrých úloh

Poznatky z pôvodného triedneho experimentu (2004):

1. **Každú úlohu si pred odovzdaním otestuj sám.** Hraničné prípady (napr. stohy tehál na križovatkách) môžu vytvoriť nemožné alebo neočakávane ťažké situácie.

2. **Sekvencie pred podmienkami.** Žiaci nachádzajú `opakuj` jednoduchšie ako `kym`. Zaveď ich v tomto poradí.

3. **`kym` potrebuje extra čas.** Koncept „opakuj kým je podmienka splnená" je pre mnohých žiakov neintuitívny. Použi jednoduché príklady: „choď dopredu kým nenarazíš na stenu."

4. **Opíš vizuálne požadovaný stav miestnosti.** „Postav múr vysoký 5 tehál" je jasnejšie ako „použi príkaz `poloz` 5-krát."

5. **Použi misie na automatickú spätnú väzbu.** Žiaci enormne profitujú z okamžitého potvrdenia správnosti riešenia. Systém misií toto zabezpečí bez zásahu učiteľa.

6. **Zapni Reset pri neúspechu.** Pre časovo obmedzené alebo skúškové úlohy reset zabraňuje žiakom „upraviť odpoveď" po spustení programu.

7. **Zamkni kameru pre úlohy priestorovej orientácie.** Fixná perspektíva núti žiakov premýšľať o orientácii Karla namiesto otáčania pohľadu.

---

## Odporúčaná sada úloh

### Úlohy na priame ovládanie

1. Prejdi bludiskom len pomocou tlačidiel.
2. Prejdi tým istým bludiskom len pomocou písaných príkazov.
3. Postav stĺpik 5 tehál (Karel zostane na vrchu).

### Úlohy na procedúry

4. Nauč Karla príkaz `Strana` (3 kroky + otočenie). Použi ho na chôdzu po štvorci.
5. Nauč Karla `ObehnDomcek` — obehnúť domček z tehál dookola.
6. Nauč Karla `Celo-vzad` (180°) len pomocou `vlavo`.

### Úlohy na cyklus opakuj

7. Obehni miestnosť 3-krát.
8. Postav schodisko — každý stĺpik o jednu tehlu vyšší.

### Úlohy na cyklus kým

9. Zdvihni všetky tehly v rade.
10. Choď k stene a späť.
11. Zníž stĺpik o 4 tehly.

### Úlohy na podmienky + rekurziu

12. Prechádzaj bludiskom podľa pravidla pravej ruky.
13. Prenesie stĺpik tehál o krok dopredu.
14. Vydláždite miestnosť značkami ako šachovnicu.

---

## Vzorový súbor sveta

```xml
<world width="12" height="10">
  <karel x="1" y="1" dir="E"/>
  <title>Choď k stene</title>
  <intro><![CDATA[
    <h2>Úloha</h2>
    <p>Napíš program, ktorý posunie Karla dopredu, kým nenarazí na východnú stenu.</p>
    <p>Použi cyklus <b>kym</b>.</p>
  ]]></intro>
  <settings>
    <disabled_cmds>BACK,DROP,DROP_BIG,PICK,MARK,CLEAR</disabled_cmds>
  </settings>
  <mission eval="on_finish" reset_on_failure="true">
    <condition type="karel_pos" x="10" y="1"/>
  </mission>
  <program>zaciatok
  // Tu napíš svoje riešenie
koniec</program>
</world>
```

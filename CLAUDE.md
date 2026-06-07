# Karel 2010 – projektové pravidlá pre Claude

## Pred vytvorením nového súboru

Pred vytvorením akéhokoľvek nového súboru do existujúceho priečinka vždy najprv
prečítať VŠETKY miesta v kóde kde sa daný priečinok číta (loadery, glob/listdir
volania) — a až potom rozhodnúť o umiestnení súboru.

Nikdy nepredpokladať — overiť kódom.

**Príklad:** `lang/` číta `_available_ui_langs()` (všetky `*.ini`) aj
`_available_prog_langs()` (cez `lang/interpreter/`). Súbor patriaci len
programovaciemu jazyku nesmie skončiť priamo v `lang/`.

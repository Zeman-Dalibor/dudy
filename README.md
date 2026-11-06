# Strakonický dudy

Web je statický a vícejazyčný. Obsah upravujte v samostatných souborech
`src/pages/cs/`, `src/pages/en/` a `src/pages/de/`. Tituly, popisy a čisté
URL adresy jsou v odpovídajícím `pages.json`. Společná HTML struktura je
v `src/partials/`; lokalizované texty hlavičky, navigace a patičky jsou
v `src/locales.json`.

Produkční doménu změníte úpravou `baseUrl` v `src/site.json`. Z této hodnoty
se sestavují canonical a jazykové odkazy, sitemap, robots.txt, přesměrování
kontaktního formuláře i soubor `CNAME`.

Sestavení vyžaduje Python 3:

```sh
python3 build_site.py
```

Hotový web se vytvoří ve složce `dist/`. Každá stránka je samostatný HTML
dokument, například `dist/Patrik-Redina/index.html`,
`dist/en/Patrik-Redina/index.html` a `dist/de/Patrik-Redina/index.html`.
Odkazy fungují i bez JavaScriptu;
`site-router.js` přednačítá označené interní odkazy a při běžné navigaci
vymění obsah bez obnovení dokumentu. GitHub Actions sestaví a nasadí `dist/`.

Pro odesílání formuláře nahraďte hodnotu `VLOZTE-SVUJ-ACCESS-KEY` svým
Web3Forms klíčem ve všech třech jazykových verzích kontaktní stránky.

# Facts to fill in or confirm

The site only states what the old site already claimed, plus general advice. Everything below
needs a family member to fill in or confirm. Most items go in `site.json`, so no page needs
editing.

## Before going live (important)

- [ ] **Email**: does `info@markopoulos-oliveoil.gr` exist? The contact form sends to it. (`site.json` > `email`)
- [ ] **Social pages**: real Facebook/Instagram addresses, or leave empty (icons stay hidden). (`site.json` > `social`)
- [ ] **Business identification**: legal company name, ΑΦΜ, ΓΕΜΗ number for the footer and privacy policy. (`site.json` > `legal`)
- [ ] **Street address**, if there is one, and the exact map coordinates. (`site.json` > `address.street`, `geo`)
- [ ] **Privacy policy**: read `src/pages/el/aporrito.html` once; the 12-month retention period is a sensible default, change it if you prefer.

## Confirm these claims (taken from the old site)

- [ ] Lab analysis for **every** batch, showing acidity **and** polyphenols. Included in the price? Which lab? (Services page, FAQ, home)
- [ ] **Storage** for growers in closed stainless tanks. Offered? For how long and at what cost? (Services, FAQ)
- [ ] Processing line is **Pieralisi** with a decanter. Model? (The mill page)
- [ ] "Every olive variety of the area" (FAQ)
- [ ] Open **every day** 07:00 – 20:00, October to January. What about February to September? (`site.json` > `hours.offseason`)
- [ ] Is `photos-originals/today-line.jpg` an unedited photo of your current line? If it was AI-enhanced, replace it.
- [ ] English page "I own olive trees in the area but live abroad": OK to offer this?

## Would make the site much stronger

- [ ] **Milling fee** (αλεστικά) for this season, or at least "from X €/kg" (FAQ "Πόσο κοστίζει η άλεση;")
- [ ] **Minimum quantity**, typical waiting time in peak season (FAQ)
- [ ] **Mobile number** for Viber/WhatsApp (`site.json` > `mobile`); many growers prefer it
- [ ] **Names**: the grandfather who founded the mill in 1963, and who runs it today (Story page)
- [ ] **Years** for the archive photos (Story page captions)
- [ ] **New photos this season**: olives arriving, the decanter, oil flowing, family at work, growers at the gate. Add them as described in README.md.
- [ ] Bottled oil: when you start selling, fill in every `[[...]]` in `src/pages/el/to-ladi-mas.html` and `src/pages/en/our-oil.html`, then set `features.oil_page: true`.

# markopoulos-oliveoil.gr

Website of Ελαιοτριβείο Μαρκόπουλος / Markopoulos Olive Mill, Malesina.
Plain HTML/CSS, Greek and English, no database and no WordPress. It runs on any web host.

```
site.json            Phone, email, hours, season bar, legal details, on/off switches
build.py             Builds the finished site into public/
public/              THE FINISHED SITE: this is what goes on the web host
src/pages/el/        Greek page texts            src/pages/en/   English page texts
src/partials/        Blocks used on several pages (the 6-step "line", the call band)
src/assets/          CSS, JavaScript, fonts, web-size images
src/static-templates contact.php (form handler) and .htaccess (redirects, https)
photos-originals/    Full-size originals of the photos
tools/make_images.py Makes web sizes of new photos (needs: pip install pillow)
tools/make_logo.py   Rebuilds the logo (olive branch + Didot wordmark), dark and light
TODO-CONTENT.md      Facts only the family can fill in or confirm
.github/workflows/   Optional automatic upload to the host after every change
```

## Everyday changes

You need Python 3 (Windows: install from python.org, tick "Add to PATH").

1. Edit `site.json` (phone, hours, season text...) or a page in `src/pages/`.
2. Run `python build.py`. It rebuilds `public/` and checks every internal link.
3. Preview: `python build.py --serve`, then open http://localhost:8000
4. Upload the new `public/` (see below).

Typical edits in `site.json`:

| What | Where |
|---|---|
| Season bar at the top of every page | `season.label`, `season.text`; `season.open: false` after January; `season.show: false` hides it |
| Hours | `hours` |
| Mobile number (shows Viber and WhatsApp buttons) | `mobile` |
| Facebook / Instagram icons | `social` (empty = hidden) |
| Company name, ΑΦΜ, ΓΕΜΗ in footer and privacy policy | `legal` |
| Exact map position for Google | `geo` |
| Turn on the "Το λάδι μας / Our oil" page | `features.oil_page: true` (fill in its `[[...]]` first) |

Page texts are plain HTML. Keep the `{{...}}` codes: they insert the phone, hours and so on
from `site.json`, so you change those in one place. Pictures use `{{img:name|description}}`.

### New photos

1. Copy the photo into `photos-originals/` (e.g. `mill-2026.jpg`).
2. Add a line to `PHOTOS` in `tools/make_images.py`, e.g. `"mill-2026": "mill-2026.jpg",`
3. `pip install pillow` (once), then `python tools/make_images.py`
4. Use it in a page: `{{img:mill-2026|What the photo shows, in words}}`

## Going live on Hostinger (one time)

The current site is made with Hostinger's Website Builder. A builder site and a site made of files
are two different "websites" in hPanel, so the domain has to be moved from one to the other.

1. **Create the mailbox** `info@markopoulos-oliveoil.gr` (hPanel > Emails), or put an existing
   address in `site.json` > `email` and rebuild. The contact form delivers there.
2. In hPanel > **Websites** > **Add website** > **Custom PHP/HTML website** (needs a web-hosting
   plan, not only a Website Builder plan). If it asks for a domain, you can first use a temporary
   subdomain to test.
3. **File Manager** > `public_html` > upload `dist/site-upload-YYYYMMDD.zip`
   (made by `python build.py --zip`) > right-click > **Extract** here. Check that `index.html`
   and `.htaccess` sit directly inside `public_html`.
4. Test everything on the new site, including sending the contact form.
5. Disconnect the domain from the Builder site and connect it to the new website
   (Hostinger support can do this in a few minutes if the option is not visible).
   Keep the Builder site, unpublished, for a few weeks as a backup.
6. The old addresses (`/oi-yphresies-mas` etc.) redirect automatically to the new pages.

## Later updates

**By hand:** `python build.py --zip`, upload the zip to `public_html`, extract, overwrite.

**Automatic upload (GitHub):** every push to `main` builds the site and uploads `public/` over FTP.
In the GitHub repository: Settings > Secrets and variables > Actions > add the secrets
`FTP_SERVER`, `FTP_USERNAME`, `FTP_PASSWORD` (hPanel > Files > FTP Accounts). Optional variable
`FTP_SERVER_DIR` (default `public_html/`). Until the secrets exist the workflow only builds.

## After launch

- Google Search Console: add the domain and submit `https://www.markopoulos-oliveoil.gr/sitemap.xml`.
- Google Business Profile (the pin "Olive Mill | Markopoulos"): same phone, season hours,
  website link, and new photos every season. Ask growers for reviews.
- In `src/static-templates/htaccess.txt` you can switch on the "always www" redirect once
  https://www.markopoulos-oliveoil.gr works.

## Privacy

No cookies, no analytics, no Google Fonts: fonts are on our own server and the Google map
loads only when a visitor presses "Εμφάνιση χάρτη". That is why there is no cookie banner. If
you add analytics or a Facebook pixel later, you need a cookie-consent banner first.

Fonts: GFS Didot (Greek Font Society) and Commissioner, both under the SIL Open Font License
(see `src/assets/fonts/`).

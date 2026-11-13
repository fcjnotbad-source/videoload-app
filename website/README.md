# VideoLoad product website

Official canonical domain: **https://app.pdos.work/**. Chinese: **https://app.pdos.work/zh/**.

This is a public marketing website. It contains no VideoLoad application source, backend, signing material or access credentials. It is hosted on the owner's Cloudflare Pages account, not Sites hosting. R2 storage is not required for this static site.

## Build and check

Python 3 standard library only:

```sh
python3 website/build.py
python3 website/check_locales.py
python3 website/check.py
```

Generated `dist/` and Python caches are ignored. To preview, run `python3 -m http.server 8788 --directory dist`.

## Languages

English remains the default at `/`; the existing Simplified Chinese URL `/zh/` is preserved. Every language has a home, `/faq/` and `/download/` page, totaling 42 indexable pages. The native language picker preserves the current page and works without JavaScript. Arabic and Hebrew use semantic RTL direction and adapted spacing.

| Language | Path |
| --- | --- |
| English | `/` |
| 简体中文 | `/zh/` |
| 繁體中文 | `/zh-Hant/` |
| 日本語 | `/ja/` |
| Deutsch | `/de/` |
| Français | `/fr/` |
| 한국어 | `/ko/` |
| Español (Latinoamérica) | `/es-419/` |
| Português (Brasil) | `/pt-BR/` |
| Bahasa Indonesia | `/id/` |
| العربية | `/ar/` |
| हिन्दी | `/hi/` |
| Italiano | `/it/` |
| עברית | `/he/` |

Each page includes reciprocal hreflang links to all other versions. Latin American Spanish uses HTML `lang="es-419"` but language-only `hreflang="es"`, since Google does not support numeric region 419 in hreflang. See [Google's language-code documentation](https://developers.google.com/search/docs/specialty/international/localized-versions).

The public contact email, `fcjnotbad@gmail.com`, appears as a mailto link in every page footer, in the home-page feedback section and in the machine-readable product facts. External store, demo and privacy-policy pages keep their own available languages; the app screenshots remain real English-language iPhone previews, labeled in the selected website language.

## Maintain

- `content.py` registers the same fourteen languages as the Android/iOS app settings.
- `locales/*.json` contains complete localized product copy, metadata, accessibility labels, download instructions and FAQ.
- `check_locales.py` requires complete translations with matching structures and unchanged official download URLs.
- `render.py` generates static HTML, metadata and matching JSON-LD.
- `style.css` holds responsive visual styles.
- `build.py` writes the crawl files and machine-readable product facts from shared content.
- Assets come from the reviewed product images in the repository's `assets/` directory.

All visible text, structured data, `product.json`, `llms.txt` and `llms-full.txt` must stay consistent. Update `UPDATED` when product facts change. After a verified iOS release, add the real App Store URL everywhere and update the coming-soon copy. Do not infer an app listing URL from an in-app purchase ID.

The site serves substantive HTML without JavaScript, uses page-specific canonicals, reciprocal language links, a sitemap, open crawler rules and structured app/FAQ data. These make content accessible to crawlers; they do not guarantee search ranking, AI indexing, rich results or citations. `llms.txt` is an additional plain-text entry, not a universal indexing standard.

## Deploy to Cloudflare Pages

Set `CLOUDFLARE_ACCOUNT_ID` in the shell, then run:

```sh
python3 scripts/deploy_pages.py --project videoload-app --directory dist --domain app.pdos.work
```

The script reads the API token through a hidden prompt or `CLOUDFLARE_API_TOKEN`. Use a token scoped to the account with Pages Write permission. Do not put tokens in arguments, files, Git, HTML or deployment output. Account and token placeholders are documented in `.env.example`; the scripts do not automatically read `.env` files. The deployment script does not change external DNS and never modifies an existing project's build configuration.

Source is maintained in this public product repository; deployment uses Direct Upload, not automatic Git integration. Commit reviewed changes before deploying so the deployment records the source commit.

## External DNS

The Pages custom-domain association must exist before using a CNAME. At the DNS provider for `pdos.work`, add:

| Type | Host/name | Target | TTL |
| --- | --- | --- | --- |
| CNAME | `app` | `videoload-app.pages.dev` | Auto or 300 seconds |

Do not include `https://` or a path in the target. Use a DNS record, not URL forwarding. There must not be a conflicting A/AAAA/CNAME record for `app`. Leave the domain's nameservers unchanged. Once DNS propagates, Cloudflare validates the hostname and issues HTTPS. Until then the custom domain is pending, while the `pages.dev` address is usable.

If certificate issuance reports a CAA error, review existing CAA restrictions before changing them; see [Cloudflare custom domain documentation](https://developers.cloudflare.com/pages/configuration/custom-domains/).

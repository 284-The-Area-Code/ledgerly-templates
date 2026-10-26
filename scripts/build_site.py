"""Build the static storefront from products.json and guides/ into ./_site (deployed to GitHub Pages).

Payment links come from build/links.json (written by stripe_sync.py). A product gets a Buy button
and a download page only when it has a payment link and its unsealed file is present.

Usage: python3 scripts/build_site.py   (run from the repo root)
"""
import html
import json
import os
import shutil
from pathlib import Path

from tokens import download_token

ROOT = Path(__file__).resolve().parent.parent
SITE_NAME = "Ledgerly Templates"
SITE_URL = os.environ.get("SITE_URL", "").rstrip("/")
TAGLINE = "Spreadsheet templates that keep freelancers and small businesses paid, organized and ready for tax time."

CSS = """
:root{--bg:#f7f8fb;--card:#fff;--ink:#1b2433;--muted:#5b6678;--brand:#1f3a5f;--accent:#2e7d5b;--line:#e3e7ee}
@media (prefers-color-scheme:dark){:root{--bg:#0f141c;--card:#18202b;--ink:#e8edf4;--muted:#9aa6b8;--brand:#8fb4e6;--accent:#5cc497;--line:#283243}}
*{box-sizing:border-box}body{margin:0;font:16px/1.6 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--ink)}
.wrap{max-width:1040px;margin:0 auto;padding:0 16px}
header{padding:56px 0 32px}h1{font-size:clamp(28px,5vw,42px);line-height:1.15;margin:0 0 12px;color:var(--brand)}
.lead{color:var(--muted);font-size:18px;max-width:640px;margin:0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;padding:24px 0 56px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:24px;display:flex;flex-direction:column}
.card h2{font-size:20px;margin:0 0 8px}.card p{color:var(--muted);margin:0 0 12px}
.card ul{margin:0 0 20px;padding-left:20px}.price{font-size:24px;font-weight:700;margin-top:auto}
.btn{display:inline-block;text-align:center;background:var(--accent);color:#fff;text-decoration:none;font-weight:600;padding:12px 18px;border-radius:10px;margin-top:12px}
.btn.off{background:var(--muted);pointer-events:none}
nav{padding:16px 0;border-bottom:1px solid var(--line)}nav a{color:var(--brand);text-decoration:none;font-weight:600;margin-right:20px}
article.guide{max-width:720px;padding:24px 0 56px}article.guide h2{margin-top:32px}article.guide a{color:var(--accent)}
.cta{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px;margin-top:32px}
.list a{display:block;padding:14px 0;border-bottom:1px solid var(--line);color:var(--ink);text-decoration:none}.list a span{display:block;color:var(--muted);font-size:15px}
footer{border-top:1px solid var(--line);padding:24px 0 40px;color:var(--muted);font-size:14px}
"""


def page(title, body, css="assets/style.css", desc=TAGLINE, head=""):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc)}">{head}
<link rel="stylesheet" href="{css}"></head><body>
<nav><div class="wrap"><a href="{css.replace('assets/style.css', '')}./">Templates</a><a href="{css.replace('assets/style.css', '')}guides/">Guides</a></div></nav>{body}
<footer><div class="wrap">&copy; {SITE_NAME}. Instant download after checkout. Works in Excel, Google Sheets and LibreOffice.</div></footer>
</body></html>"""


def read_guide(path):
    """A guide is an HTML fragment after 'key: value' header lines and a blank line."""
    head, body = path.read_text().split("\n\n", 1)
    meta = dict(line.split(": ", 1) for line in head.splitlines())
    meta["slug"], meta["body"] = path.stem, body
    return meta


def main():
    data = json.loads((ROOT / "products.json").read_text())
    links_file = ROOT / "build" / "links.json"
    links = json.loads(links_file.read_text()) if links_file.exists() else {}
    out = ROOT / "_site"
    if out.exists():
        shutil.rmtree(out)
    (out / "assets").mkdir(parents=True)
    (out / "assets" / "style.css").write_text(CSS)
    (out / ".nojekyll").write_text("")

    cards = []
    for p in data["products"]:
        feats = "".join(f"<li>{html.escape(f)}</li>" for f in p["features"])
        src = ROOT / "products" / p["file"]
        link = links.get(p["slug"]) if src.exists() else None
        p["payment_link"] = link
        btn = (f'<a class="btn" href="{html.escape(link)}">Buy now</a>' if link
               else '<span class="btn off">Coming soon</span>')
        cards.append(f"""<article class="card"><h2>{html.escape(p['name'])}</h2>
<p>{html.escape(p['blurb'])}</p><ul>{feats}</ul>
<div class="price">${p['price'] / 100:.2f}</div>{btn}</article>""")

        if not link:
            continue
        # Download page that Stripe redirects to after payment.
        d = out / "d" / download_token(p["slug"])
        d.mkdir(parents=True)
        shutil.copy(src, d / p["file"])
        (d / "index.html").write_text(page(
            f"Download: {p['name']}",
            f"""<div class="wrap"><header><h1>Thanks for your purchase!</h1>
<p class="lead">Your copy of {html.escape(p['name'])} is ready.</p>
<a class="btn" href="{p['file']}" download>Download the template</a>
<p class="lead" style="margin-top:20px">Bookmark this page to download again later.</p></header></div>""",
            css="../../assets/style.css", head='<meta name="robots" content="noindex">'))

    (out / "index.html").write_text(page(
        SITE_NAME,
        f"""<div class="wrap"><header><h1>{SITE_NAME}</h1><p class="lead">{TAGLINE}</p></header>
<main class="grid">{''.join(cards)}</main></div>"""))
    by_slug = {p["slug"]: p for p in data["products"]}
    guides = sorted((read_guide(g) for g in (ROOT / "guides").glob("*.html")),
                    key=lambda g: g.get("date", ""), reverse=True)
    for g in guides:
        p = by_slug.get(g.get("product"))
        cta = ""
        if p:
            buy = (f'<a class="btn" href="{html.escape(p["payment_link"])}">Get it for ${p["price"] / 100:.2f}</a>'
                   if p.get("payment_link") else '<a class="btn" href="../../">See the templates</a>')
            cta = f'<div class="cta"><strong>{html.escape(p["name"])}</strong><p>{html.escape(p["blurb"])}</p>{buy}</div>'
        gd = out / "guides" / g["slug"]
        gd.mkdir(parents=True)
        (gd / "index.html").write_text(page(
            g["title"], f'<div class="wrap"><article class="guide"><h1>{html.escape(g["title"])}</h1>{g["body"]}{cta}</article></div>',
            css="../../assets/style.css", desc=g["description"]))
    links = "".join(f'<a href="{g["slug"]}/">{html.escape(g["title"])}<span>{html.escape(g["description"])}</span></a>'
                    for g in guides)
    (out / "guides" / "index.html").write_text(page(
        f"Guides | {SITE_NAME}",
        f'<div class="wrap"><header><h1>Guides</h1><p class="lead">Practical money and admin guides for freelancers.</p></header><div class="list">{links}</div></div>',
        css="../assets/style.css"))

    robots = "User-agent: *\nAllow: /\n"
    if SITE_URL:
        urls = [f"{SITE_URL}/", f"{SITE_URL}/guides/"] + [f"{SITE_URL}/guides/{g['slug']}/" for g in guides]
        (out / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            + "".join(f"<url><loc>{u}</loc></url>" for u in urls) + "</urlset>\n")
        robots += f"Sitemap: {SITE_URL}/sitemap.xml\n"
    (out / "robots.txt").write_text(robots)
    print(f"Built {len(data['products'])} products and {len(guides)} guides into {out}")


if __name__ == "__main__":
    main()

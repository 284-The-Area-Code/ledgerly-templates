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

import growth
from tokens import download_token

ROOT = Path(__file__).resolve().parent.parent
SITE_NAME = "Rowfern"
SITE_URL = os.environ.get("SITE_URL", "").rstrip("/")
TAGLINE = "Spreadsheet templates that keep freelancers and small businesses paid, organized and ready for tax time."
FONTS = ("https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600"
         "&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap")

CSS = """
:root{--paper:#faf7f2;--card:#fff;--ink:#17201c;--muted:#5d665f;--line:#e6e0d4;--green:#1f5c47;--green-2:#2f7a5f;
--cell:#fff4c7;--cell-line:#ecd98a;--good:#e3f1ea;--radius:16px;--shadow:0 1px 2px rgba(23,32,28,.06),0 8px 24px rgba(23,32,28,.06);
--serif:"Fraunces",Georgia,serif;--sans:"Inter",system-ui,-apple-system,"Segoe UI",sans-serif;--mono:"JetBrains Mono",ui-monospace,monospace}
@media (prefers-color-scheme:dark){:root{--paper:#121614;--card:#1a201d;--ink:#ecefe9;--muted:#a1aaa3;--line:#2b332f;
--green:#7fcfae;--green-2:#9adcc0;--cell:#3a3420;--cell-line:#5a4f2a;--good:#1d3329;--shadow:none}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font:400 17px/1.65 var(--sans);-webkit-font-smoothing:antialiased}
a{color:inherit}.wrap{max-width:1120px;margin:0 auto;padding:0 20px}
h1,h2,h3{font-family:var(--serif);font-weight:600;letter-spacing:-.015em;line-height:1.12;margin:0}
.eyebrow{font:500 12px/1 var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--green)}
nav{position:sticky;top:0;z-index:5;background:color-mix(in srgb,var(--paper) 88%,transparent);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
nav .wrap{display:flex;align-items:center;gap:28px;height:64px}
.logo{font:600 22px var(--serif);text-decoration:none;display:flex;align-items:center;gap:10px;margin-right:auto}
.logo i{width:26px;height:26px;border-radius:7px;background:var(--green);display:grid;place-items:center;color:var(--paper);font:500 13px var(--mono);font-style:normal}
nav a.nl{text-decoration:none;font-weight:500;font-size:15px;color:var(--muted)}nav a.nl:hover{color:var(--ink)}
.hero{display:grid;grid-template-columns:1.1fr .9fr;gap:56px;align-items:center;padding:88px 0 72px}
.hero h1{font-size:clamp(40px,6.4vw,68px);margin:18px 0 20px}.hero h1 em{font-style:italic;color:var(--green)}
.hero p{font-size:19px;color:var(--muted);max-width:520px;margin:0 0 32px}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;background:var(--green);color:var(--paper);text-decoration:none;
font:600 15px var(--sans);padding:14px 22px;border-radius:999px;border:0;transition:transform .15s,background .15s}
.btn:hover{background:var(--green-2);transform:translateY(-1px)}.btn.ghost{background:transparent;color:var(--ink);box-shadow:inset 0 0 0 1.5px var(--line)}
.btn.off{background:var(--line);color:var(--muted);pointer-events:none}
.actions{display:flex;flex-wrap:wrap;gap:12px}
.sheet{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow);overflow:hidden;font:500 14px var(--mono);transform:rotate(1.2deg)}
.sheet .bar{display:flex;gap:6px;padding:12px 14px;border-bottom:1px solid var(--line)}.sheet .bar b{width:10px;height:10px;border-radius:50%;background:var(--line)}
.sheet table{width:100%;border-collapse:collapse}.sheet td{padding:11px 14px;border-bottom:1px solid var(--line);white-space:nowrap}
.sheet td:last-child{text-align:right}.sheet tr:last-child td{border-bottom:0}
.sheet .in{background:var(--cell);box-shadow:inset 0 0 0 1px var(--cell-line)}.sheet .out{background:var(--good);color:var(--green);font-weight:600}
.sheet .lbl{color:var(--muted);font-family:var(--sans);font-weight:500}
.strip{display:flex;flex-wrap:wrap;gap:12px 32px;padding:22px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line);color:var(--muted);font-size:15px}
.strip span:before{content:"✓";color:var(--green);font-weight:600;margin-right:8px}
section{padding:80px 0}.sec-head{display:flex;justify-content:space-between;align-items:end;gap:24px;margin-bottom:36px;flex-wrap:wrap}
.sec-head h2{font-size:clamp(30px,4vw,44px);margin-top:12px}.sec-head p{color:var(--muted);max-width:420px;margin:0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:20px}
.card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:28px;display:flex;flex-direction:column;transition:box-shadow .2s,transform .2s}
.card:hover{box-shadow:var(--shadow);transform:translateY(-2px)}
.tag{align-self:flex-start;font:500 11px/1 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--green);background:var(--good);padding:7px 10px;border-radius:999px;margin-bottom:18px}
.card h3{font-size:24px;margin-bottom:10px}.card p{color:var(--muted);margin:0 0 18px;font-size:16px}
.card ul{list-style:none;padding:0;margin:0 0 24px;font-size:15px}.card li{padding:7px 0 7px 26px;position:relative;border-top:1px dashed var(--line)}
.card li:before{content:"";position:absolute;left:2px;top:14px;width:12px;height:8px;border-radius:2px;background:var(--cell);box-shadow:inset 0 0 0 1px var(--cell-line)}
.buy{margin-top:auto;display:flex;align-items:center;justify-content:space-between;gap:12px}
.price{font:600 30px var(--serif)}.price small{font:400 13px var(--sans);color:var(--muted);display:block}
.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;counter-reset:s}
.step{padding:28px;border-radius:var(--radius);background:var(--card);border:1px solid var(--line)}
.step:before{counter-increment:s;content:"0" counter(s);font:500 13px var(--mono);color:var(--green)}
.step h3{font-size:21px;margin:14px 0 8px}.step p{color:var(--muted);margin:0;font-size:16px}
.faq{max-width:760px}.faq details{border-bottom:1px solid var(--line);padding:20px 0}
.faq summary{font:600 19px var(--serif);cursor:pointer;list-style:none;display:flex;justify-content:space-between;gap:16px}
.faq summary:after{content:"+";font:400 22px var(--sans);color:var(--green)}.faq details[open] summary:after{content:"−"}
.faq p{color:var(--muted);margin:12px 0 0}
.page-head{padding:72px 0 40px;max-width:760px}.page-head h1{font-size:clamp(36px,5.5vw,56px);margin:14px 0 16px}
.page-head p{font-size:19px;color:var(--muted);margin:0}
.list{display:grid;gap:16px;padding-bottom:80px}
.list a{display:block;text-decoration:none;background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:24px 28px;transition:box-shadow .2s}
.list a:hover{box-shadow:var(--shadow)}.list strong{font:600 22px/1.25 var(--serif);display:block;margin-bottom:6px}.list span{color:var(--muted);font-size:16px}
article.guide{max-width:700px;margin:0 auto;padding:64px 0 88px;font-size:18px;line-height:1.75}
article.guide h1{font-size:clamp(34px,5vw,50px);margin:14px 0 28px}
article.guide h2{font-size:28px;margin:48px 0 12px}article.guide a{color:var(--green)}
article.guide li{margin:6px 0}article.guide strong{font-weight:600}article.guide em{color:var(--muted)}
.cta{margin-top:48px;padding:32px;border-radius:var(--radius);background:var(--card);border:1px solid var(--line);box-shadow:var(--shadow)}
.cta h3{font-size:24px;margin:12px 0 8px}.cta p{color:var(--muted);margin:0 0 20px;font-size:16px}
.thanks{text-align:center;padding:120px 0}.thanks h1{font-size:clamp(36px,6vw,56px);margin:14px 0 16px}.thanks p{color:var(--muted);font-size:18px}
footer{border-top:1px solid var(--line);padding:40px 0 56px;color:var(--muted);font-size:14px}
footer .wrap{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap}footer a{text-decoration:none;margin-left:20px}
.form.calc{display:grid;grid-template-columns:repeat(2,1fr);gap:14px 20px;margin:32px 0 20px;padding:28px;background:var(--card);border:1px solid var(--line);border-radius:var(--radius)}
.form.calc label{display:flex;flex-direction:column;justify-content:space-between;gap:8px;font-size:14px;font-weight:500;color:var(--muted);line-height:1.4}
.form.calc input{font:500 17px var(--mono);color:var(--ink);background:var(--cell);border:1px solid var(--cell-line);border-radius:10px;padding:11px 14px;width:100%;outline:none;transition:box-shadow .15s}
.form.calc input:focus{box-shadow:0 0 0 3px color-mix(in srgb,var(--green) 25%,transparent);border-color:var(--green)}
.result{display:grid;gap:2px;padding:8px 28px;border-radius:var(--radius);background:var(--good);margin-bottom:12px}
.result p{margin:0;padding:14px 0;display:flex;flex-wrap:wrap;justify-content:space-between;align-items:baseline;gap:4px 12px;font-size:16px;border-bottom:1px solid color-mix(in srgb,var(--green) 18%,transparent)}
.result p:last-child{border-bottom:0}.result strong{font:600 24px var(--mono);color:var(--green)}
.result p:first-child strong{font-size:34px}
.result p:last-child{display:block}.result p:last-child strong{font-size:17px}
.faq+article.guide{margin:0;padding-top:24px}
.contact{margin:32px 0;padding:28px;background:var(--card);border:1px solid var(--line);border-left:4px solid var(--green);border-radius:var(--radius)}
.contact p{margin:0 0 10px}.contact p:last-child{margin:0;color:var(--muted);font-size:16px}
@media (max-width:860px){.hero{grid-template-columns:1fr;padding:56px 0 48px;gap:40px}.steps{grid-template-columns:1fr}section{padding:56px 0}
.grid{grid-template-columns:1fr}.sheet{transform:none}.form.calc{grid-template-columns:1fr;padding:20px}.result{padding:4px 20px}nav .wrap{gap:18px}}
"""

SHEET = """<div class="sheet" aria-hidden="true"><div class="bar"><b></b><b></b><b></b></div><table>
<tr><td class="lbl">Take-home goal</td><td class="in">$60,000</td></tr>
<tr><td class="lbl">Business costs</td><td class="in">$4,000</td></tr>
<tr><td class="lbl">Weeks off</td><td class="in">8</td></tr>
<tr><td class="lbl">Billable hours / yr</td><td>1,056</td></tr>
<tr><td class="lbl">Minimum hourly rate</td><td class="out">$90.97</td></tr></table></div>"""

FAQ = [
    ("Which apps do the templates work in?",
     "Microsoft Excel, Google Sheets (File, then Import) and LibreOffice. Every formula is tested before a template is listed."),
    ("Is it a subscription?", "No. You pay once and the file is yours to keep and reuse."),
    ("How do I get the file?",
     "Right after checkout you're taken to a download page. Bookmark it to download again later."),
    ("Do I need spreadsheet skills?",
     "No. You only type into the yellow cells. Everything else is calculated for you, and each file opens on a short How to use sheet."),
]


def page(title, body, css="assets/style.css", desc=TAGLINE, head=""):
    base = css.replace("assets/style.css", "")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc)}">{head}
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}"><link rel="stylesheet" href="{css}"></head><body>
<nav><div class="wrap"><a class="logo" href="{base}./"><i>R</i>{SITE_NAME}</a>
<a class="nl" href="{base}./#templates">Templates</a><a class="nl" href="{base}guides/">Guides</a>
<a class="nl" href="{base}tools/">Tools</a></div></nav>{body}
<footer><div class="wrap"><span>&copy; {SITE_NAME}, a <a href="https://dezetingz.com" style="margin:0;text-decoration:underline">DezeTingz</a> product. One-time purchase, instant download.</span>
<span><a href="{base}./#templates">Templates</a><a href="{base}guides/">Guides</a><a href="{base}tools/">Free tools</a><a href="{base}help/">Help &amp; contact</a></span></div></footer>
</body></html>"""


def buy_button(p, label="Buy now"):
    if p.get("payment_link"):
        return f'<a class="btn" href="{html.escape(p["payment_link"])}">{label}</a>'
    return '<span class="btn off">Coming soon</span>'


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
        cards.append(f"""<article class="card"><span class="tag">{html.escape(p.get('tag', 'Template'))}</span>
<h3>{html.escape(p['name'])}</h3><p>{html.escape(p['blurb'])}</p><ul>{feats}</ul>
<div class="buy"><div class="price">${p['price'] / 100:.0f}<small>one-time, .xlsx</small></div>{buy_button(p)}</div></article>""")

        if not link:
            continue
        # Download page that Stripe redirects to after payment.
        d = out / "d" / download_token(p["slug"])
        d.mkdir(parents=True)
        shutil.copy(src, d / p["file"])
        (d / "index.html").write_text(page(
            f"Download: {p['name']}",
            f"""<div class="wrap thanks"><span class="eyebrow">Payment received</span><h1>Thanks for your purchase!</h1>
<p>Your copy of {html.escape(p['name'])} is ready.</p>
<p><a class="btn" href="{p['file']}" download>Download the template</a></p>
<p>Bookmark this page to download again later.</p></div>""",
            css="../../assets/style.css", head='<meta name="robots" content="noindex">'))

    faq = "".join(f"<details><summary>{html.escape(q)}</summary><p>{html.escape(a)}</p></details>" for q, a in FAQ)
    (out / "index.html").write_text(page(
        f"{SITE_NAME}: spreadsheet templates for freelancers",
        f"""<div class="wrap"><div class="hero"><div><span class="eyebrow">Templates for freelancers</span>
<h1>Spreadsheets that <em>pay you back.</em></h1><p>{TAGLINE}</p>
<div class="actions"><a class="btn" href="#templates">Browse templates</a><a class="btn ghost" href="guides/">Read the guides</a></div></div>
{SHEET}</div>
<div class="strip"><span>Excel, Google Sheets &amp; LibreOffice</span><span>One-time price, no subscription</span>
<span>Instant download</span><span>Every formula tested</span></div></div>
<section id="templates"><div class="wrap"><div class="sec-head"><div><span class="eyebrow">The collection</span><h2>Pick the job you want done</h2></div>
<p>Each template does one job well. Type into the yellow cells and the rest works itself out.</p></div>
<div class="grid">{''.join(cards)}</div></div></section>
<section><div class="wrap"><div class="sec-head"><div><span class="eyebrow">How it works</span><h2>Set up in five minutes</h2></div></div>
<div class="steps"><div class="step"><h3>Buy once</h3><p>Secure checkout, then you go straight to your download.</p></div>
<div class="step"><h3>Open anywhere</h3><p>Excel, Google Sheets or LibreOffice. Start on the How to use sheet.</p></div>
<div class="step"><h3>Fill the yellow cells</h3><p>Totals, warnings and dashboards update as you type.</p></div></div></div></section>
<section><div class="wrap"><div class="sec-head"><div><span class="eyebrow">Questions</span><h2>Good to know</h2></div></div>
<div class="faq">{faq}</div></div></section>""",
        desc=TAGLINE, head=growth.seo_head("", SITE_NAME, TAGLINE, growth.product_ld(data["products"]), home=True)))

    by_slug = {p["slug"]: p for p in data["products"]}
    guides = sorted((read_guide(g) for g in (ROOT / "guides").glob("*.html")),
                    key=lambda g: g.get("date", ""), reverse=True)
    for g in guides:
        p = by_slug.get(g.get("product"))
        cta = ""
        if p:
            btn = (buy_button(p, f"Get it for ${p['price'] / 100:.0f}") if p.get("payment_link")
                   else '<a class="btn" href="../../#templates">See the templates</a>')
            cta = (f'<div class="cta"><span class="eyebrow">Do it in a spreadsheet</span><h3>{html.escape(p["name"])}</h3>'
                   f'<p>{html.escape(p["blurb"])}</p>{btn}</div>')
        gd = out / "guides" / g["slug"]
        gd.mkdir(parents=True)
        (gd / "index.html").write_text(page(
            g["title"],
            f'<div class="wrap"><article class="guide"><span class="eyebrow">Guide</span><h1>{html.escape(g["title"])}</h1>'
            f'{g["body"]}{cta}</article></div>',
            css="../../assets/style.css", desc=g["description"],
            head=growth.seo_head(f'guides/{g["slug"]}/', g["title"], g["description"], growth.article_ld(g))))
    items = "".join(f'<a href="{g["slug"]}/"><strong>{html.escape(g["title"])}</strong>'
                    f'<span>{html.escape(g["description"])}</span></a>' for g in guides)
    (out / "guides" / "index.html").write_text(page(
        f"Guides | {SITE_NAME}",
        f'<div class="wrap"><div class="page-head"><span class="eyebrow">Guides</span><h1>Money and admin, made simple</h1>'
        f'<p>Practical guides for freelancers on pricing, invoicing and taxes.</p></div><div class="list">{items}</div></div>',
        css="../assets/style.css", desc="Practical money and admin guides for freelancers.",
        head=growth.seo_head("guides/", "Guides", "Practical money and admin guides for freelancers.")))
    extra = growth.build_extras(out, page, read_guide, buy_button, data["products"], guides)

    robots = "User-agent: *\nAllow: /\n"
    if SITE_URL:
        urls = [f"{SITE_URL}/", f"{SITE_URL}/guides/"] + [f"{SITE_URL}/guides/{g['slug']}/" for g in guides] + [f"{SITE_URL}/{x}" for x in extra]
        (out / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            + "".join(f"<url><loc>{u}</loc></url>" for u in urls) + "</urlset>\n")
        robots += f"Sitemap: {SITE_URL}/sitemap.xml\n"
    (out / "robots.txt").write_text(robots)
    print(f"Built {len(data['products'])} products and {len(guides)} guides into {out}")


if __name__ == "__main__":
    main()

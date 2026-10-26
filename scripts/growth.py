"""Lead generation and customer contact pieces of the site, called from build_site.py.

- SEO head tags: canonical URL, Open Graph, JSON-LD and search engine verification.
- Free tools from tools/ (same file format as guides, body may include a <script>).
- The Help page: FAQ plus the ways to contact support (site.json).
- RSS feed of guides and tools, and the IndexNow key file used by the deploy workflow.
"""
import html
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
SITE = json.loads((ROOT / "site.json").read_text())
SITE_URL = os.environ.get("SITE_URL", "").rstrip("/")
NAME = "Ledgerly Templates"


def seo_head(path, title, desc, jsonld=None, home=False):
    """Head tags for the page at site path `path` ("" for home, "guides/x/" etc.)."""
    if not SITE_URL:
        return ""
    url = f"{SITE_URL}/{path}"
    e = html.escape
    tags = [f'<link rel="canonical" href="{e(url)}">',
            f'<meta property="og:type" content="{"website" if home else "article"}">',
            f'<meta property="og:site_name" content="{NAME}">',
            f'<meta property="og:title" content="{e(title)}">',
            f'<meta property="og:description" content="{e(desc)}">',
            f'<meta property="og:url" content="{e(url)}">',
            '<meta name="twitter:card" content="summary">',
            f'<link rel="alternate" type="application/rss+xml" title="{NAME}" href="{SITE_URL}/feed.xml">']
    if home:
        for key, meta in (("google_site_verification", "google-site-verification"),
                          ("bing_site_verification", "msvalidate.01")):
            if SITE.get(key):
                tags.append(f'<meta name="{meta}" content="{e(SITE[key])}">')
    if jsonld:
        tags.append('<script type="application/ld+json">'
                    + json.dumps(jsonld).replace("</", "<\\/") + "</script>")
    return "\n" + "\n".join(tags)


def product_ld(products):
    """JSON-LD ItemList of products for the home page."""
    items = []
    for i, p in enumerate(products, 1):
        item = {"@type": "Product", "name": p["name"], "description": p["blurb"],
                "brand": {"@type": "Brand", "name": NAME}}
        if p.get("payment_link"):
            item["offers"] = {"@type": "Offer", "price": f"{p['price'] / 100:.2f}", "priceCurrency": "USD",
                              "availability": "https://schema.org/InStock", "url": p["payment_link"]}
        items.append({"@type": "ListItem", "position": i, "item": item})
    return {"@context": "https://schema.org", "@type": "ItemList", "itemListElement": items}


def article_ld(meta):
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": meta["title"],
          "description": meta["description"], "author": {"@type": "Organization", "name": NAME},
          "publisher": {"@type": "Organization", "name": NAME}}
    if meta.get("date"):
        ld["datePublished"] = meta["date"]
    return ld


def faq_ld(faqs):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}


def issue_url(title=""):
    repo = SITE["github_repo"]
    return f"https://github.com/{repo}/issues/new?template=question.yml&title={quote(title)}"


def faqs():
    days = SITE["refund_days"]
    return [
        ("How do I get my template after paying?",
         "Checkout takes you straight to a download page. Bookmark it: you can download again from the same page any time."),
        ("I lost my download page. What now?",
         "Contact us with the email you paid with and the template name, and we'll send the link again."),
        ("Does it work in Google Sheets, Excel and Numbers?",
         "Yes in Excel and Google Sheets (File, Import, Upload), and in LibreOffice. Numbers opens the files too, "
         "but a few formulas may display differently."),
        ("Can I get a refund?",
         f"Yes. If a template doesn't work for you, contact us within {days} days of purchase for a full refund."),
        ("Is this tax or legal advice?",
         "No. The templates help you organize numbers; check tax decisions with a qualified accountant."),
        ("Can I use a template for my clients or my team?",
         "Yes, for your own business and your team. Please don't resell or share the files publicly."),
    ]


def contact_block():
    email = SITE.get("support_email")
    parts = []
    if email:
        e = html.escape(email)
        parts.append(f'<p><strong>Email:</strong> <a href="mailto:{e}">{e}</a>. '
                     "Include the email you paid with and the template name.</p>")
    parts.append(f'<p><strong>Ask on GitHub:</strong> <a href="{html.escape(issue_url())}">open a question</a> '
                 "(free GitHub account needed). Questions there are public, so never post order details or payment information.</p>")
    parts.append("<p>We reply within one business day.</p>")
    return '<section class="contact">' + "".join(parts) + "</section>"


def build_help(out, page):
    fq = faqs()
    items = "".join(f"<details><summary>{html.escape(q)}</summary><p>{html.escape(a)}</p></details>" for q, a in fq)
    desc = "Answers to common questions about Ledgerly Templates, and how to reach support."
    d = out / "help"
    d.mkdir(parents=True)
    (d / "index.html").write_text(page(
        f"Help & contact | {NAME}",
        f'<div class="wrap"><div class="page-head"><span class="eyebrow">Help</span><h1>Help &amp; contact</h1><p>{desc}</p></div>'
        f'<div class="faq">{items}</div><article class="guide"><h2>Contact us</h2>{contact_block()}</article></div>',
        css="../assets/style.css", desc=desc, head=seo_head("help/", "Help & contact", desc, faq_ld(fq))))
    return ["help/"]


def build_tools(out, page, read_meta, buy_button, products):
    """Free tools: tools/<slug>.html -> /tools/<slug>/. Returns their metadata, newest first."""
    by_slug = {p["slug"]: p for p in products}
    tools = sorted((read_meta(t) for t in (ROOT / "tools").glob("*.html")),
                   key=lambda t: t.get("date", ""), reverse=True)
    for t in tools:
        p = by_slug.get(t.get("product"))
        cta = ""
        if p:
            btn = (buy_button(p, f"Get it for ${p['price'] / 100:.0f}") if p.get("payment_link")
                   else '<a class="btn" href="../../#templates">See the templates</a>')
            cta = (f'<div class="cta"><span class="eyebrow">Keep it in a spreadsheet</span><h3>{html.escape(p["name"])}</h3>'
                   f'<p>{html.escape(p["blurb"])}</p>{btn}</div>')
        td = out / "tools" / t["slug"]
        td.mkdir(parents=True)
        (td / "index.html").write_text(page(
            f'{t["title"]} | {NAME}',
            f'<div class="wrap"><article class="guide tool"><span class="eyebrow">Free tool</span><h1>{html.escape(t["title"])}</h1>'
            f'<p>{html.escape(t["description"])}</p>{t["body"]}{cta}</article></div>',
            css="../../assets/style.css", desc=t["description"],
            head=seo_head(f'tools/{t["slug"]}/', t["title"], t["description"],
                          {"@context": "https://schema.org", "@type": "WebApplication", "name": t["title"],
                           "description": t["description"], "applicationCategory": "FinanceApplication",
                           "operatingSystem": "Any", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}})))
    listing = "".join(f'<a href="{t["slug"]}/"><strong>{html.escape(t["title"])}</strong>'
                      f'<span>{html.escape(t["description"])}</span></a>' for t in tools)
    desc = "Free calculators for freelancers. No sign-up, nothing to download."
    (out / "tools").mkdir(exist_ok=True)
    (out / "tools" / "index.html").write_text(page(
        f"Free tools | {NAME}",
        f'<div class="wrap"><div class="page-head"><span class="eyebrow">Free tools</span><h1>Quick answers to money questions</h1>'
        f'<p>{desc}</p></div><div class="list">{listing}</div></div>',
        css="../assets/style.css", desc=desc, head=seo_head("tools/", "Free tools", desc)))
    return tools


def build_feed(out, guides, tools):
    if not SITE_URL:
        return
    entries = [(g, f"guides/{g['slug']}/") for g in guides] + [(t, f"tools/{t['slug']}/") for t in tools]
    entries.sort(key=lambda x: x[0].get("date", ""), reverse=True)

    def rfc822(d):
        dt = datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=timezone.utc) if d else datetime.now(timezone.utc)
        return dt.strftime("%a, %d %b %Y 00:00:00 +0000")

    e = html.escape
    items = "".join(f"<item><title>{e(m['title'])}</title><link>{SITE_URL}/{p}</link><guid>{SITE_URL}/{p}</guid>"
                    f"<description>{e(m['description'])}</description><pubDate>{rfc822(m.get('date'))}</pubDate></item>"
                    for m, p in entries)
    (out / "feed.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
        f"<title>{NAME}</title><link>{SITE_URL}/</link>"
        "<description>Practical money and admin guides and free tools for freelancers.</description>"
        f"{items}</channel></rss>\n")


def build_extras(out, page, read_meta, buy_button, products, guides):
    """Build tools, help, feed and the IndexNow key. Returns extra site paths for the sitemap."""
    tools = build_tools(out, page, read_meta, buy_button, products)
    paths = ["tools/"] + [f"tools/{t['slug']}/" for t in tools] + build_help(out, page)
    build_feed(out, guides, tools)
    key = SITE.get("indexnow_key")
    if key:
        (out / f"{key}.txt").write_text(key)
    return paths

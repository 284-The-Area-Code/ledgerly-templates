"""Make sure every product in products.json has a Stripe payment link, and write the links
to build/links.json for build_site.py. Runs in the deploy workflow.

Links are found again on later runs by their metadata, so nothing is written back to the repo.
Needs STRIPE_KEY (restricted key with write access to Products, Prices and Payment Links),
SITE_URL and PRODUCT_KEY. Skips quietly if STRIPE_KEY or PRODUCT_KEY is missing.
Usage: python3 scripts/stripe_sync.py   (run from the repo root)
"""
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

from tokens import download_token

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.stripe.com/v1/"


def stripe(path, params=None, method="POST"):
    data = urllib.parse.urlencode(params or {}).encode()
    url = API + path
    if method == "GET":
        url, data = f"{url}?{data.decode()}", None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Authorization": f"Bearer {os.environ['STRIPE_KEY']}"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def existing_links():
    """Map product slug -> active payment link URL, from link metadata."""
    links, params = {}, {"limit": 100, "active": "true"}
    while True:
        page = stripe("payment_links", params, method="GET")
        for link in page["data"]:
            slug = link.get("metadata", {}).get("slug")
            if slug:
                links.setdefault(slug, link["url"])
        if not page["has_more"]:
            return links
        params["starting_after"] = page["data"][-1]["id"]


def main():
    out = ROOT / "build" / "links.json"
    out.parent.mkdir(exist_ok=True)
    if not os.environ.get("STRIPE_KEY") or not os.environ.get("PRODUCT_KEY"):
        print("STRIPE_KEY or PRODUCT_KEY not set; skipping. Products will show as Coming soon.")
        out.write_text("{}")
        return
    site = os.environ["SITE_URL"].rstrip("/")
    products = json.loads((ROOT / "products.json").read_text())["products"]
    links = existing_links()
    for p in products:
        if p["slug"] in links:
            continue
        prod = stripe("products", {"name": p["name"], "description": p["blurb"],
                                   "metadata[slug]": p["slug"]})
        price = stripe("prices", {"product": prod["id"], "unit_amount": p["price"], "currency": "usd"})
        link = stripe("payment_links", {
            "line_items[0][price]": price["id"],
            "line_items[0][quantity]": 1,
            "metadata[slug]": p["slug"],
            "after_completion[type]": "redirect",
            "after_completion[redirect][url]": f"{site}/d/{download_token(p['slug'])}/",
        })
        links[p["slug"]] = link["url"]
        print(f"Listed {p['name']} on Stripe")
    out.write_text(json.dumps(links, indent=2))
    print(f"{len(links)} payment link(s) ready")


if __name__ == "__main__":
    main()

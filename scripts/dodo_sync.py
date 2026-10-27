"""Make sure every product in products.json is listed on Dodo Payments, and write a checkout link
for each to build/links.json for build_site.py. Runs in the deploy workflow.

Products are found again on later runs by their metadata, so nothing is written back to the repo.
Needs DODO_API_KEY, SITE_URL and PRODUCT_KEY. DODO_MODE=test uses Dodo's test mode (default live).
Skips quietly if DODO_API_KEY or PRODUCT_KEY is missing.
Usage: python3 scripts/dodo_sync.py   (run from the repo root)
"""
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

from tokens import download_token

ROOT = Path(__file__).resolve().parent.parent
TEST = os.environ.get("DODO_MODE", "live") == "test"
API = "https://test.dodopayments.com/" if TEST else "https://live.dodopayments.com/"
CHECKOUT = "https://test.checkout.dodopayments.com/buy/" if TEST else "https://checkout.dodopayments.com/buy/"


def dodo(path, body=None, method="POST"):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method,
                                 headers={"Authorization": f"Bearer {os.environ['DODO_API_KEY']}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def existing_products():
    """Map product slug -> Dodo product id, from product metadata."""
    found, page = {}, 0
    while True:
        items = dodo(f"products?page_size=100&page_number={page}", method="GET")["items"]
        for item in items:
            slug = (item.get("metadata") or {}).get("slug")
            if slug:
                found.setdefault(slug, item["product_id"])
        if len(items) < 100:
            return found
        page += 1


def checkout_link(product_id, redirect):
    return f"{CHECKOUT}{product_id}?" + urllib.parse.urlencode({"quantity": 1, "redirect_url": redirect})


def main():
    out = ROOT / "build" / "links.json"
    out.parent.mkdir(exist_ok=True)
    if not os.environ.get("DODO_API_KEY") or not os.environ.get("PRODUCT_KEY"):
        print("DODO_API_KEY or PRODUCT_KEY not set; skipping. Products will show as Coming soon.")
        out.write_text("{}")
        return
    site = os.environ["SITE_URL"].rstrip("/")
    products = json.loads((ROOT / "products.json").read_text())["products"]
    ids = existing_products()
    links = {}
    for p in products:
        if p["slug"] not in ids:
            prod = dodo("products", {
                "name": p["name"], "description": p["blurb"], "tax_category": "digital_products",
                "price": {"type": "one_time_price", "price": p["price"], "currency": "USD",
                          "discount": 0, "purchasing_power_parity": False},
                "metadata": {"slug": p["slug"]},
            })
            ids[p["slug"]] = prod["product_id"]
            print(f"Listed {p['name']} on Dodo Payments")
        links[p["slug"]] = checkout_link(ids[p["slug"]], f"{site}/d/{download_token(p['slug'])}/")
    out.write_text(json.dumps(links, indent=2))
    print(f"{len(links)} checkout link(s) ready")


if __name__ == "__main__":
    main()

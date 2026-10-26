"""Tell search engines (Bing, Yandex and others via IndexNow) about pages changed by the last push.

Runs in the deploy workflow after the site is live. Needs SITE_URL and the indexnow_key in site.json
(the key file is published at the site root by build_site.py). Never fails the deploy.
Usage: python3 scripts/indexnow.py   (run from the repo root, with the previous commit fetched)
"""
import json
import os
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def changed_paths():
    try:
        files = subprocess.run(["git", "diff", "--name-only", "HEAD~1", "HEAD"], cwd=ROOT,
                               capture_output=True, text=True, check=True).stdout.split()
    except subprocess.CalledProcessError:
        return [""]
    paths = set()
    for f in files:
        p = Path(f)
        if p.parts[0] in ("guides", "tools") and p.suffix == ".html" and len(p.parts) == 2:
            paths.update({f"{p.parts[0]}/{p.stem}/", f"{p.parts[0]}/"})
        elif f in ("products.json", "site.json") or f.startswith("scripts/"):
            paths.update({"", "help/", "tools/", "guides/"})
    return sorted(paths)


def main():
    site = os.environ.get("SITE_URL", "").rstrip("/")
    key = json.loads((ROOT / "site.json").read_text()).get("indexnow_key")
    paths = changed_paths()
    if not (site and key and paths):
        print("Nothing to submit to IndexNow.")
        return
    host = site.split("/")[2]
    body = {"host": host, "key": key, "keyLocation": f"{site}/{key}.txt",
            "urlList": [f"{site}/{p}" for p in paths]}
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"IndexNow: {r.status} for {len(paths)} URLs")
    except Exception as e:  # search engine pings must never break a deploy
        print(f"IndexNow failed: {e}")


if __name__ == "__main__":
    main()

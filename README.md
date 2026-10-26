# Rowfern Templates

A static store selling spreadsheet templates for freelancers, run by a weekly scheduled task
(see `ROUTINE.md`) and deployed to GitHub Pages on every push to `main`.

- `products.json` the catalog. `products/` holds the template files, sealed with
  `keys/product_public.pem` so they can't be downloaded from this public repo.
- `guides/` articles that bring in search traffic.
- `tools/` free calculators (lead magnets that link to the paid templates).
- `site.json` support email, search engine verification codes and the IndexNow key.
  `scripts/growth.py` builds the Help page, tools, RSS feed and SEO tags; `scripts/indexnow.py`
  pings search engines after each deploy.
- `SUPPORT.md` how customer questions are answered by the daily support task.
- `scripts/seal.py` seals new templates. `scripts/unseal.py`, `scripts/stripe_sync.py` and
  `scripts/build_site.py` run in the deploy workflow.

After checkout, Stripe sends the buyer to a download page whose address is derived from the
`PRODUCT_KEY` secret, so it never appears in the repo.

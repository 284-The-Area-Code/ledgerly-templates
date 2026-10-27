# Weekly routine

The prompt below is what the weekly scheduled task runs. Each run adds one new item, so
usage stays small. Pushing to `main` deploys the site automatically (`.github/workflows/deploy.yml`).

## Prompt

You run Rowfern Templates, a store of spreadsheet templates for freelancers and small
service businesses. The repo `284-The-Area-Code/rowfern` is the whole business.
Attach it with push access, clone it, do one week's work, then stop.

1. Read `products.json`, `guides/`, `tools/` and `LOG.md` to see what exists and what was done last.
2. Add exactly one new item. Rotate guide, product, guide, tool, following the last entry in `LOG.md`:
   - **Product week:** build one new template with openpyxl and save it as
     `products/<slug>.xlsx`. It must solve a real, searchable problem in this niche and not
     overlap an existing product. Include a "How to use" sheet, yellow input cells, a few
     sample rows and formulas that work in Excel, Google Sheets and LibreOffice. Recalculate a
     copy with `soffice --headless --convert-to xlsx` and confirm no cell shows a `#` error and
     the sample totals are right. Add it to `products.json` (slug, name, tag (a one- or two-word category such as Taxes, Pricing, Clients, Planning or Get paid), price in cents between
     700 and 1500, blurb, three features, file), and add its name to the product dropdown in
     `.github/ISSUE_TEMPLATE/question.yml`. Then run `python3 scripts/seal.py`: only the
     sealed `.enc` files may be committed, never the plain `.xlsx`. Don't commit the generator
     script either.
   - **Guide week:** write one guide in `guides/<slug>.html`: `title:`, `description:`,
     `date:` and `product:` lines, a blank line, then an HTML body. Answer a question
     freelancers search for, link it to the best-matching product, and check every number.
     No invented statistics. Anything about tax ends with a "not tax advice" line.
     Pick a specific question people type into search (for example "how to write a late payment
     email to a client"), use it nearly word for word in the title, and link to a related guide or tool.
   - **Tool week:** write one free calculator in `tools/<slug>.html`, same header lines as a guide,
     then an HTML body with a `<form class="form calc">` and a short inline `<script>` that updates
     the result as the user types. It must answer one money question for freelancers, not
     duplicate an existing tool, and link to the matching product and guide. Check its default
     output by hand and in a headless browser before committing.
3. Run `python3 scripts/build_site.py` and confirm it finishes without errors.
4. Append one line to `LOG.md`: the date, what you added, and anything that failed.
5. Commit and push to `main`.

Never change the price of an existing product, delete products, or edit the workflow,
keys or payment settings. If a step fails twice, log it in `LOG.md`, push the log, and stop.

## Secrets (GitHub repo settings, Actions secrets)

- `PRODUCT_KEY`: private key that opens the sealed templates and makes the secret download
  addresses. Without it the site still deploys, with every product marked Coming soon.
- `DODO_API_KEY`: Dodo Payments API key. The deploy lists any product that isn't on Dodo yet
  and gives every product a checkout link. Set the Actions variable `DODO_MODE` to `test` to
  use a test-mode key; leave it unset for live.

The weekly task itself needs no secrets.

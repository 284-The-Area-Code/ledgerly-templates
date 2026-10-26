"""Secret download addresses. Each product's download page lives at /d/<token>/, where the
token is derived from the PRODUCT_KEY secret, so it never appears in the public repo."""
import hashlib
import hmac
import os


def download_token(slug):
    secret = os.environ["PRODUCT_KEY"].strip().encode()
    return hmac.new(secret, f"download:{slug}".encode(), hashlib.sha256).hexdigest()[:32]

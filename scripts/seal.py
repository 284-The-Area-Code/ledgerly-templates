"""Encrypt every products/*.xlsx so only the deploy workflow can read it, then delete the original.

The repo is public, so template files are committed only in sealed form. Each file gets a
random AES-256 key; that key is encrypted with keys/product_public.pem. Only the private key
(the PRODUCT_KEY Actions secret) can open them. Needs no secrets to run.
Usage: python3 scripts/seal.py   (run from the repo root)
"""
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC_KEY = ROOT / "keys" / "product_public.pem"


def seal(xlsx):
    key = xlsx.with_suffix(".key")
    key.write_bytes(os.urandom(32).hex().encode())
    try:
        subprocess.run(["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-salt", "-in", str(xlsx),
                        "-out", f"{xlsx}.enc", "-pass", f"file:{key}"], check=True)
        subprocess.run(["openssl", "pkeyutl", "-encrypt", "-pubin", "-inkey", str(PUBLIC_KEY),
                        "-pkeyopt", "rsa_padding_mode:oaep", "-in", str(key),
                        "-out", f"{xlsx}.key.enc"], check=True)
    finally:
        key.unlink()
    xlsx.unlink()
    print(f"Sealed {xlsx.name}")


def main():
    files = sorted((ROOT / "products").glob("*.xlsx"))
    for f in files:
        seal(f)
    print(f"Sealed {len(files)} file(s)")


if __name__ == "__main__":
    main()

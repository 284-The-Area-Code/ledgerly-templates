"""Decrypt products/*.xlsx.enc with the private key. Runs in the deploy workflow only.

Needs PRODUCT_KEY (the private key PEM). Without it, does nothing, and the site builds
with products marked "Coming soon".
Usage: python3 scripts/unseal.py   (run from the repo root)
"""
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    pem = os.environ.get("PRODUCT_KEY", "").strip()
    if not pem:
        print("PRODUCT_KEY not set; skipping. Products will show as Coming soon.")
        return
    with tempfile.TemporaryDirectory() as tmp:
        key_path = Path(tmp) / "private.pem"
        key_path.write_text(pem + "\n")
        count = 0
        for enc in sorted((ROOT / "products").glob("*.xlsx.enc")):
            xlsx = enc.with_suffix("")  # strip .enc
            aes = Path(tmp) / "aes.key"
            subprocess.run(["openssl", "pkeyutl", "-decrypt", "-inkey", str(key_path),
                            "-pkeyopt", "rsa_padding_mode:oaep", "-in", f"{xlsx}.key.enc",
                            "-out", str(aes)], check=True)
            subprocess.run(["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-in", str(enc),
                            "-out", str(xlsx), "-pass", f"file:{aes}"], check=True)
            count += 1
    print(f"Unsealed {count} product(s)")


if __name__ == "__main__":
    main()

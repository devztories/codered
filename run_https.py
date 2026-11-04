"""
CODERED INVENTIONS - Local HTTPS development launcher.

Run with: python run_https.py
This uses mkcert when available, creates/trusts a local certificate, and
serves Django over HTTPS on 127.0.0.1:8000.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


def find_mkcert():
    found = shutil.which("mkcert")
    if found:
        return Path(found)

    local = Path(os.environ.get("LOCALAPPDATA", ""))
    package_root = local / "Microsoft" / "WinGet" / "Packages"
    if package_root.exists():
        matches = list(package_root.glob("FiloSottile.mkcert_*/*/mkcert.exe"))
        if not matches:
            matches = list(package_root.glob("FiloSottile.mkcert_*/mkcert.exe"))
        if matches:
            return matches[0]
    return None


def main():
    try:
        from django.core.wsgi import get_wsgi_application
        from werkzeug.serving import run_simple
    except ImportError as exc:
        raise SystemExit(
            "Missing development dependency. Run: python -m pip install -r requirements.txt"
        ) from exc

    mkcert = find_mkcert()
    if not mkcert:
        raise SystemExit(
            "mkcert was not found. Install it once with: "
            "winget install --id FiloSottile.mkcert -e"
        )

    cert_dir = BASE_DIR / "certs"
    cert_dir.mkdir(exist_ok=True)
    cert_file = cert_dir / "localhost.pem"
    key_file = cert_dir / "localhost-key.pem"

    print("[1/3] Trusting local development CA (may take a moment)...")
    subprocess.run([str(mkcert), "-install"], check=True)

    if not cert_file.exists() or not key_file.exists():
        print("[2/3] Creating localhost certificate...")
        subprocess.run(
            [
                str(mkcert),
                "-cert-file", str(cert_file),
                "-key-file", str(key_file),
                "localhost", "127.0.0.1", "::1",
            ],
            cwd=str(BASE_DIR),
            check=True,
        )
    else:
        print("[2/3] Existing local certificate found.")

    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()

    print("[3/3] Starting CODERED INVENTIONS over HTTPS.")
    print("Open: https://127.0.0.1:8000/")
    print("Press Ctrl+C to stop.")
    run_simple(
        hostname="127.0.0.1",
        port=8000,
        application=application,
        ssl_context=(str(cert_file), str(key_file)),
        threaded=True,
        use_reloader=False,
    )


if __name__ == "__main__":
    main()

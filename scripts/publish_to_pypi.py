#!/usr/bin/env python3
"""
Zero-Scan PyPI One-Click Release Engine
Publishes validated production packages from dist/ to PyPI Registry.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Zero-Scan PyPI Release CLI")
    parser.add_argument("--token", "-t", type=str, help="PyPI API Token (pypi-...)")
    parser.add_argument("--test", action="store_true", help="Upload to TestPyPI instead of production")
    args = parser.parse_args()

    # Auto-load .env if present
    env_file = Path(".env")
    if env_file.is_file() and not os.environ.get("PYPI_API_TOKEN"):
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("PYPI_API_TOKEN=") and not line.startswith("#"):
                os.environ["PYPI_API_TOKEN"] = line.split("=", 1)[1].strip(" \"'")

    token = args.token or os.environ.get("PYPI_API_TOKEN")
    if not token:
        print("❌ Error: PyPI API Token is required.")
        print("   Usage: python3 scripts/publish_to_pypi.py --token <pypi-token>")
        print("   Or set: export PYPI_API_TOKEN='pypi-...'")
        return 1

    dist_dir = Path("dist")
    if not dist_dir.is_dir() or not list(dist_dir.glob("*.whl")):
        print("📦 Building production packages first...")
        subprocess.run([sys.executable, "-m", "build"], check=True)

    print("🔍 Validating packages with Twine...")
    subprocess.run(["twine", "check", "dist/*"], check=True)

    repository_url = "https://test.pypi.org/legacy/" if args.test else "https://upload.pypi.org/legacy/"
    print(f"🚀 Uploading Zero-Scan to {'TestPyPI' if args.test else 'Production PyPI'}...")

    cmd = [
        "twine", "upload",
        "--repository-url", repository_url,
        "-u", "__token__",
        "-p", token,
        "dist/*"
    ]
    res = subprocess.run(cmd)
    if res.returncode == 0:
        print("\n🎉 SUCCESS! Zero-Scan is now live on PyPI!")
        print("   Install via: pip install zeroscan")
        return 0
    else:
        print("\n❌ Upload failed. Please check token permissions.")
        return res.returncode


if __name__ == "__main__":
    sys.exit(main())

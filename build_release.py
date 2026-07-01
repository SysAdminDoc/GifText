#!/usr/bin/env python3
"""
Build a signed, checksummed GifText release artifact.

Usage:
    python build_release.py [--skip-smoke] [--sign CERT_PATH]

Steps:
    1. Clean dist/ and build/
    2. Run PyInstaller via GifText.spec
    3. Generate SHA-256 checksum file
    4. Run a smoke test (launch exe, verify it starts and exits cleanly)
    5. Sign the exe if a certificate path is provided
"""

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
BUILD = ROOT / "build"
EXE_NAME = "GifText.exe"
SPEC = ROOT / "GifText.spec"


def clean():
    for d in (DIST, BUILD):
        if d.exists():
            shutil.rmtree(d)
            print(f"  Cleaned {d}")


def run_pyinstaller():
    cmd = [sys.executable, "-m", "PyInstaller", "--clean", str(SPEC)]
    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode != 0:
        print("ERROR: PyInstaller build failed")
        sys.exit(1)
    exe = DIST / EXE_NAME
    if not exe.exists():
        print(f"ERROR: Expected artifact not found: {exe}")
        sys.exit(1)
    size_mb = exe.stat().st_size / (1024 * 1024)
    print(f"  Built {exe} ({size_mb:.1f} MB)")
    return exe


def generate_checksum(exe_path: Path):
    sha = hashlib.sha256()
    with open(exe_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    digest = sha.hexdigest()
    checksum_file = exe_path.with_suffix(".exe.sha256")
    checksum_file.write_text(f"{digest}  {exe_path.name}\n", encoding="utf-8")
    print(f"  SHA-256: {digest}")
    print(f"  Written to {checksum_file}")
    return checksum_file


def smoke_test(exe_path: Path):
    print("  Launching exe for smoke test...")
    proc = subprocess.Popen(
        [str(exe_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
    )
    time.sleep(6)
    poll = proc.poll()
    if poll is not None and poll != 0:
        stderr = proc.stderr.read().decode(errors="replace") if proc.stderr else ""
        print(f"ERROR: Exe crashed on startup (exit code {poll})")
        if stderr:
            print(f"  stderr: {stderr[:500]}")
        sys.exit(1)
    if poll is None:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
    print("  Smoke test passed (exe launched and stayed alive)")


def sign_exe(exe_path: Path, cert_path: str):
    signtool = shutil.which("signtool")
    if not signtool:
        sdk_candidates = list(Path("C:/Program Files (x86)/Windows Kits/10/bin").glob("*/x64/signtool.exe"))
        if sdk_candidates:
            signtool = str(sorted(sdk_candidates)[-1])
    if not signtool:
        print("  WARNING: signtool not found; skipping code signing")
        return False
    cmd = [
        signtool, "sign",
        "/f", cert_path,
        "/fd", "sha256",
        "/tr", "http://timestamp.digicert.com",
        "/td", "sha256",
        str(exe_path),
    ]
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("  WARNING: Code signing failed (non-fatal)")
        return False
    print("  Code signed successfully")
    return True


def main():
    parser = argparse.ArgumentParser(description="Build GifText release artifact")
    parser.add_argument("--skip-smoke", action="store_true", help="Skip the smoke test")
    parser.add_argument("--sign", metavar="CERT_PATH", help="Path to .pfx certificate for code signing")
    args = parser.parse_args()

    print("=== GifText Release Build ===\n")

    print("[1/4] Cleaning build directories")
    clean()

    print("\n[2/4] Running PyInstaller")
    exe = run_pyinstaller()

    print("\n[3/4] Generating checksum")
    generate_checksum(exe)

    if not args.skip_smoke:
        print("\n[4/4] Smoke test")
        smoke_test(exe)
    else:
        print("\n[4/4] Smoke test (skipped)")

    if args.sign:
        print("\n[+] Code signing")
        sign_exe(exe, args.sign)

    print(f"\n=== Release artifact ready: {exe} ===")


if __name__ == "__main__":
    main()

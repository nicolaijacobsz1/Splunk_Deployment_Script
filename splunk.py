#!/usr/bin/env python
"""Splunk Universal Forwarder deployment script for Windows."""

import argparse
import ctypes
import os
import shutil
import string
import subprocess
import sys
from pathlib import Path
from secrets import choice as secure_choice

try:
    import requests
except ImportError:
    print("Error: 'requests' module not found. Please install it before proceeding.")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_VERSION = "10.2.2"
DEFAULT_BUILD = "979a540794c5"
DEFAULT_UF_HOME = Path(r"C:\Program Files\SplunkUniversalForwarder")
DEFAULT_TEMP_DIR = Path(r"C:\Windows\Temp")


def is_admin() -> bool:
    """Check if the script is running with administrative privileges."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except AttributeError:
        print("Could not determine admin status.")
        return False


def elevate_if_needed() -> None:
    """Relaunch with elevation if not already running as admin."""
    if is_admin():
        return

    ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        " ".join(f'"{arg}"' for arg in sys.argv),
        None,
        1,
    )
    sys.exit()


def generate_password(length: int = 20) -> str:
    """Generate a random password for the Splunk admin account."""
    chars = string.ascii_letters + string.digits + "!#*()-_+="
    password = "".join(secure_choice(chars) for _ in range(length))
    print("Generated randomized admin password.", flush=True)
    return password


def build_download_url(version: str, build: str) -> tuple[str, str]:
    """Build installer file name and download URL."""
    major_minor_patch = ".".join(version.split(".")[:3])
    file_name = f"splunkforwarder-{version}-{build}-windows-x64.msi"
    url = (
        "https://download.splunk.com/products/universalforwarder/releases/"
        f"{version}/windows/{file_name}"
    )
    local_name = f"splunkforwarder-{major_minor_patch}.msi"
    return local_name, url


def download_splunk(version: str, build: str, temp_dir: Path) -> Path:
    """Download Splunk Universal Forwarder if not already downloaded."""
    local_name, url = build_download_url(version, build)
    file_path = temp_dir / local_name

    if file_path.exists():
        print(f"Installer already present: {file_path}", flush=True)
        return file_path

    print(f"Downloading Splunk Universal Forwarder from {url}", flush=True)
    response = requests.get(url, stream=True, timeout=(10, 60))
    response.raise_for_status()

    with file_path.open("wb") as handle:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                handle.write(chunk)

    print(f"Downloaded installer to {file_path}", flush=True)
    return file_path


def run_command(command: list[str], context: str, cwd: Path | None = None) -> None:
    """Run command and fail with context-rich error if needed."""
    result = subprocess.run(command, text=True, capture_output=True, cwd=cwd, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"{context} failed (exit {result.returncode}).\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )


def install_splunk(msi_path: Path, admin_password: str) -> None:
    """Install Splunk UF silently."""
    install_command = [
        "msiexec",
        "/i",
        str(msi_path),
        "/quiet",
        "AGREETOLICENSE=Yes",
        "LAUNCHSPLUNK=0",
        f"SPLUNKPASSWORD={admin_password}",
    ]
    print("Installing Splunk Universal Forwarder...", flush=True)
    run_command(install_command, "Splunk UF installation")
    print("Installation complete.", flush=True)


def add_and_replace_folders(source_dir: Path, dest_dir: Path) -> None:
    """Replace content from source directory to destination directory."""
    if not source_dir.exists():
        print(f"Skipping missing folder: {source_dir}", flush=True)
        return

    dest_dir.mkdir(parents=True, exist_ok=True)

    for item in source_dir.iterdir():
        dest_item = dest_dir / item.name
        if dest_item.exists():
            if dest_item.is_dir():
                shutil.rmtree(dest_item)
            else:
                dest_item.unlink()

        if item.is_dir():
            shutil.copytree(item, dest_item)
        else:
            shutil.copy2(item, dest_item)

    print(f"Synced folder: {source_dir} -> {dest_dir}", flush=True)


def copy_and_replace_file(source_file: Path, dest_dir: Path) -> None:
    """Copy a file to destination and replace if it exists."""
    if not source_file.exists():
        print(f"Skipping missing file: {source_file}", flush=True)
        return

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / source_file.name

    if dest_file.exists():
        dest_file.unlink()

    shutil.copy2(source_file, dest_file)
    print(f"Copied {source_file.name} -> {dest_dir}", flush=True)


def add_license(uf_home: Path, admin_password: str) -> None:
    """Add a license file if one is present."""
    license_file = SCRIPT_DIR / "xml_license.lic"
    if not license_file.exists():
        print("No license file found; skipping license install.", flush=True)
        return

    splunk_bin = uf_home / "bin" / "splunk.exe"
    command = [str(splunk_bin), "add", "licenses", str(license_file), "-auth", f"admin:{admin_password}"]
    run_command(command, "License import", cwd=splunk_bin.parent)
    print("License added successfully.", flush=True)


def install_splunk_app(uf_home: Path, admin_password: str) -> None:
    """Install local Splunk app bundle if present."""
    app_file = SCRIPT_DIR / "splunkclouduf.spl"
    if not app_file.exists():
        print("No splunkclouduf.spl found; skipping app install.", flush=True)
        return

    splunk_bin = uf_home / "bin" / "splunk.exe"
    command = [str(splunk_bin), "install", "app", str(app_file), "-auth", f"admin:{admin_password}"]
    run_command(command, "App installation", cwd=splunk_bin.parent)
    print("App installed successfully.", flush=True)


def restart_splunk(uf_home: Path) -> None:
    """Restart Splunk UF service."""
    splunk_bin = uf_home / "bin" / "splunk.exe"
    run_command([str(splunk_bin), "restart"], "Splunk restart", cwd=splunk_bin.parent)
    print("Splunk restarted successfully.", flush=True)


def clean_up(msi_path: Path) -> None:
    """Clean up installer artifact."""
    if msi_path.exists():
        msi_path.unlink()
        print(f"Removed installer artifact: {msi_path}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deploy Splunk Universal Forwarder on Windows")
    parser.add_argument("--version", default=DEFAULT_VERSION, help="UF version, ex: 10.2.2")
    parser.add_argument("--build", default=DEFAULT_BUILD, help="UF build hash used in installer URL")
    parser.add_argument("--uf-home", default=str(DEFAULT_UF_HOME), help="UF install directory")
    parser.add_argument("--keep-installer", action="store_true", help="Keep installer in temp folder")
    return parser.parse_args()


def main() -> None:
    elevate_if_needed()
    args = parse_args()

    uf_home = Path(args.uf_home)
    installer_path = download_splunk(args.version, args.build, DEFAULT_TEMP_DIR)
    admin_password = generate_password()

    install_splunk(installer_path, admin_password)

    add_and_replace_folders(SCRIPT_DIR / "deployment-apps", uf_home / "etc" / "deployment-apps")
    add_and_replace_folders(SCRIPT_DIR / "apps", uf_home / "etc" / "apps")
    copy_and_replace_file(SCRIPT_DIR / "serverclass.conf", uf_home / "etc" / "system" / "local")

    add_license(uf_home, admin_password)
    install_splunk_app(uf_home, admin_password)
    restart_splunk(uf_home)

    if not args.keep_installer:
        clean_up(installer_path)


if __name__ == "__main__":
    main()

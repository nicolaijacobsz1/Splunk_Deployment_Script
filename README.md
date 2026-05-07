# Splunk Universal Forwarder Deployment Script (Windows)

This repository provides a Windows-focused deployment helper for Splunk Universal Forwarder (UF), suitable for rapid M&A onboarding workflows where hosts must be enrolled quickly and consistently.

## What the script does

`splunk.py` performs these actions:

- Ensures the script is running with administrator rights (and self-elevates when needed).
- Downloads a specific UF MSI from Splunk's official download endpoint.
- Installs UF silently via `msiexec`.
- Copies local onboarding content into UF directories:
  - `deployment-apps/` → `...\etc\deployment-apps`
  - `apps/` → `...\etc\apps`
  - `serverclass.conf` → `...\etc\system\local`
- Optionally installs:
  - `xml_license.lic` (if present)
  - `splunkclouduf.spl` (if present)
- Restarts UF and removes the MSI (unless you opt out).

## Prerequisites

- Windows host
- Python 3.9+
- Network access to `download.splunk.com`
- Local admin privileges
- Python dependency:

```bash
pip install requests
```

## Usage

Run from an elevated command prompt (or allow UAC when prompted):

```bash
python splunk.py
```

Optional flags:

```bash
python splunk.py --version 10.2.2 --build 979a540794c5 --uf-home "C:\Program Files\SplunkUniversalForwarder" --keep-installer
```

- `--version`: UF release version used in the download URL.
- `--build`: Build hash used in the installer filename.
- `--uf-home`: UF install path (default is `C:\Program Files\SplunkUniversalForwarder`).
- `--keep-installer`: Keep MSI in `C:\Windows\Temp` after successful deployment.

## Expected local files

Place these beside `splunk.py` if needed for your onboarding flow:

- `deployment-apps/` (optional)
- `apps/` (optional)
- `serverclass.conf` (optional)
- `xml_license.lic` (optional)
- `splunkclouduf.spl` (optional)

Missing optional files/folders are skipped gracefully with a console message.

# Manual Testing Guide (Windows)

Use this checklist to validate `splunk.py` on a Windows test VM before broad M&A rollout.

## 1) Pre-checks

- Confirm Python 3.9+ is installed.
- Install dependency:
  - `pip install requests`
- Confirm you can reach `https://download.splunk.com` from the VM.
- Place optional onboarding artifacts next to `splunk.py` as needed:
  - `deployment-apps/`
  - `apps/`
  - `serverclass.conf`
  - `xml_license.lic`
  - `splunkclouduf.spl`

## 2) Dry functional run

From an elevated PowerShell or CMD prompt:

```powershell
python .\splunk.py --version 10.2.2 --build 979a540794c5 --keep-installer
```

Validate:

- UF MSI downloads to `C:\Windows\Temp`.
- UF installs under `C:\Program Files\SplunkUniversalForwarder`.
- Files/folders copy into `etc\deployment-apps`, `etc\apps`, and `etc\system\local`.
- Optional steps are skipped with clear messages if files are not present.
- Restart completes successfully.

## 3) Service and health checks

```powershell
& 'C:\Program Files\SplunkUniversalForwarder\bin\splunk.exe' status
Get-Service -Name SplunkForwarder
```

Expected: service is running and splunk status reports healthy runtime.

## 4) Forwarding validation

- Verify your `outputs.conf`/deployment app settings applied.
- Confirm host appears on indexer/search head side.

## 5) Cleanup behavior

- Re-run without `--keep-installer` and verify MSI is removed.

```powershell
python .\splunk.py --version 10.2.2 --build 979a540794c5
```

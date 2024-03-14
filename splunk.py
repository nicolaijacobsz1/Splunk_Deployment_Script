#!/usr/bin/env python
"""Splunk Deployment Script - IPG."""

import ctypes
import os
import sys
import random
import shutil
import string
import subprocess
import time
import tqdm

try:
    import requests
except ImportError:
    print("Error: 'requests' module not found. Please install it before proceeding.")
    sys.exit(1)

def is_admin():
    """Check if the script is running with administrative privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except AttributeError:
        print("Could not determine admin status.")
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

def generate_password():
    """Generate a random password for the deployment server."""
    length = 12
    chars = string.ascii_letters + string.digits + "!#*()-_+="
    password = ''.join(random.choice(chars) for _ in range(length))
    print(f"Password has been created: {password}", flush=True)
    return password

def download_splunk():
    """Download Splunk Forwarder if not already downloaded."""
    file_path = r"C:\\Windows\\Temp\\splunk-9.2.0.msi"
    url = ("https://download.splunk.com/products/splunk/releases/"
           "9.2.0.1/windows/splunk-9.2.0.1-d8ae995bf219-x64-release.msi")
    if not os.path.exists(file_path):
        print("Downloading Splunk Universal Forwarder...", flush=True)
        response = requests.get(url, stream=True, timeout=(10, 30))
        total_size = int(response.headers.get('content-length', 0))
        with open(file_path, "wb") as file:
            for data in tqdm.tqdm(response.iter_content(1024), total=total_size // 1024, desc="Downloading", unit='KB'):
                file.write(data)
        print(f"Splunk has been downloaded and saved to {file_path}", flush=True)
    else:
        print(f"Splunk Universal Forwarder installer already exists at {file_path}", flush=True)

def install_splunk():
    """Install Splunk with a generated admin password."""
    admin_password = generate_password()
    install_command = (
        f'msiexec /i "C:\\Windows\\Temp\\splunk-9.2.0.msi" '
        f'/quiet AGREETOLICENSE=Yes LAUNCHSPLUNK=1 '
        f'SPLUNKPASSWORD="{admin_password}"'
    )

    with subprocess.Popen(install_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
        with tqdm.tqdm(total=100, desc="Installing Splunk") as progress_bar:
            while True:
                if process.poll() is not None:
                    progress_bar.update(100 - progress_bar.n)
                    break
                progress_bar.update(2)
                time.sleep(2)

    if process.returncode == 0:
        print("\nInstallation successful.", flush=True)
    else:
        stderr = process.stderr.read().decode()
        print(f"Installation failed with error code {process.returncode}: {stderr}", flush=True)

    print("Press Enter to continue...", flush=True)
    input()

    return admin_password

def add_and_replace_folders(source_dir, dest_dir):
    """Replace content from the source directory to the destination directory."""
    if not os.path.exists(source_dir):
        print(f"Source folder {source_dir} does not exist.", flush=True)
        return

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    for item in os.listdir(source_dir):
        s_item = os.path.join(source_dir, item)
        d_item = os.path.join(dest_dir, item)

        if os.path.exists(d_item):
            if os.path.isdir(d_item):
                shutil.rmtree(d_item)
            else:
                os.remove(d_item)

        if os.path.isdir(s_item):
            shutil.copytree(s_item, d_item)
        else:
            shutil.copy2(s_item, d_item)

    print(f"Contents from {source_dir} have been added to {dest_dir}.", flush=True)
    print("Press Enter to continue...", flush=True)
    input()

def copy_and_replace_file(source_file, dest_dir):
    """Copy a file to proper dest and replace it if it exists."""
    if not os.path.exists(source_file):
        print(f"Source file {source_file} does not exist.", flush=True)
        return

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    dest_file = os.path.join(dest_dir, os.path.basename(source_file))

    if os.path.exists(dest_file):
        print(f"Replacing existing file: {dest_file}", flush=True)
        os.remove(dest_file)

    shutil.copy2(source_file, dest_file)
    print(f"{os.path.basename(source_file)} has been copied to {dest_dir}", flush=True)

def add_license_and_restart(admin_password):
    """Add a license to Splunk and restart the service."""
    script_dir = os.path.dirname(os.path.realpath(__file__))
    license_file = os.path.join(script_dir, "xml_license.lic")
    splunk_bin = r"C:\Program Files\Splunk\bin\splunk.exe"
    os.chdir(os.path.dirname(splunk_bin))

    add_license_cmd = [splunk_bin, "add", "licenses", license_file, "-auth", f"admin:{admin_password}"]
    result = subprocess.run(add_license_cmd, shell=True, text=True, capture_output=True, check=False)
    if result.returncode == 0:
        print("License added successfully.", flush=True)
    else:
        print(f"Failed to add license: {result.stderr}", flush=True)

    print("Press Enter to Restart Splunk Instance", flush=True)
    input()
    print("Please Wait...", flush=True)

    restart_cmd = [splunk_bin, "restart"]
    result = subprocess.run(restart_cmd, shell=True, text=True, capture_output=True, check=False)
    if result.returncode == 0:
        print("Splunk restarted successfully.", flush=True)
    else:
        print(f"Failed to restart Splunk: {result.stderr}", flush=True)

    print("Press Enter to continue...", flush=True)
    input()

def clean_up():
    """Clean up installation artifacts."""
    print("Cleaning up...", flush=True)
    try:
        os.remove(r"C:\Windows\Temp\splunk-9.2.0.msi")
    except FileNotFoundError:
        print("File already removed.", flush=True)
    time.sleep(2)

def main():
    """Main Function."""
    if not is_admin():
        print("Script is not running with administrative privileges. Exiting.")
        return

    download_splunk()
    admin_password = install_splunk()

    script_dir = os.path.dirname(os.path.realpath(__file__))

    # Replace deployment-apps and apps folders
    deployment_apps_source = os.path.join(script_dir, 'deployment-apps')
    deployment_apps_dest = r"C:\Program Files\Splunk\etc\deployment-apps"
    add_and_replace_folders(deployment_apps_source, deployment_apps_dest)

    apps_source = os.path.join(script_dir, 'apps')
    apps_dest = r"C:\Program Files\Splunk\etc\apps"
    add_and_replace_folders(apps_source, apps_dest)

    # Copy and replace serverclass.conf
    serverclass_source = os.path.join(script_dir, "serverclass.conf")
    serverclass_dest_dir = r"C:\Program Files\Splunk\etc\system\local"
    copy_and_replace_file(serverclass_source, serverclass_dest_dir)

    add_license_and_restart(admin_password)
    clean_up()

    print("Splunk deployment script completed. Press Enter to exit.", flush=True)
    input()

if __name__ == "__main__":
    main()

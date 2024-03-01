#!/usr/bin/env python
""" Splunk Deployment Script - IPG. """

import subprocess
import os
import sys
import ctypes
import requests
import random
import string
import time
from tqdm import tqdm
import shutil

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    # Re-run the script with admin rights
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

def genPassword():
    """Generate a random password for our deployment server."""
    length = 12
    chars = string.ascii_letters + string.digits + "!@#$%&*()-_+="
    password = ''.join(random.choice(chars) for _ in range(length))
    print("Password has been created: %s" % password, flush=True)
    return password

def downloadSplunk():
    """Download Splunk Forwarder if not already downloaded."""
    file_path = "C:\\Windows\\Temp\\splunk-9.2.0.msi"
    url = "https://download.splunk.com/products/splunk/releases/9.2.0.1/windows/splunk-9.2.0.1-d8ae995bf219-x64-release.msi"
    if not os.path.exists(file_path):
        print("Downloading Splunk Universal Forwarder...", flush=True)
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        with open(file_path, "wb") as file, tqdm(
            desc="Downloading",
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for data in response.iter_content(1024):
                size = file.write(data)
                bar.update(size)
        print(f"Splunk Universal Forwarder has been downloaded and saved to {file_path}", flush=True)
    else:
        print(f"Splunk Universal Forwarder installer already exists at {file_path}", flush=True)

def installSplunk():
    """Install Splunk with generated admin password and show an artificial progress bar."""
    admin_password = genPassword()
    print(f"Admin password generated: {admin_password}", flush=True)

    install_command = f'msiexec /i "C:\\Windows\\Temp\\splunk-9.2.0.msi" /quiet AGREETOLICENSE=Yes LAUNCHSPLUNK=1 SPLUNKPASSWORD="{admin_password}"'
    process = subprocess.Popen(install_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Artificial progress bar
    with tqdm(total=100, desc="Installing Splunk") as pbar:
        while True:
            if process.poll() is not None:
                # Fill the progress bar if the process is complete
                pbar.update(100 - pbar.n)  # Ensure the progress bar completes
                break
            pbar.update(2)  # Update the progress bar arbitrarily
            time.sleep(2)  # Artificial delay between updates

    # Check if the installation was successful
    if process.returncode == 0:
        print("\nInstallation successful.", flush=True)
    else:
        print(f"Installation failed with error code {process.returncode}", flush=True)
        stderr = process.stderr.read().decode()
        print(f"Error details: {stderr}", flush=True)

    print("Press Enter to continue...", flush=True)
    input()  # Wait for user input

    return admin_password

def addAndReplaceFolders(source_dir, dest_dir):
    """Add and replace folders from the source directory to the destination directory."""
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

def add_license_and_restart(admin_password):
    """Add a license to Splunk and restart the service."""
    license_file = r"C:\Windows\Temp\xml_license.lic"
    splunk_bin = r"C:\Program Files\Splunk\bin\splunk.exe"  # Direct path to the splunk executable

    # Change the working directory to Splunk's bin directory
    os.chdir(os.path.dirname(splunk_bin))

    # Add license command
    add_license_cmd = [splunk_bin, "add", "licenses", license_file, "-auth", f"admin:{admin_password}"]
    result = subprocess.run(add_license_cmd, shell=True, text=True, capture_output=True)
    if result.returncode == 0:
        print("License added successfully.", flush=True)
    else:
        print(f"Failed to add license: {result.stderr}", flush=True)

    print("Press Enter to continue...", flush=True)
    input()

    # Restart Splunk command
    restart_cmd = [splunk_bin, "restart"]
    result = subprocess.run(restart_cmd, shell=True, text=True, capture_output=True)
    if result.returncode == 0:
        print("Splunk restarted successfully.", flush=True)
    else:
        print(f"Failed to restart Splunk: {result.stderr}", flush=True)

    print("Press Enter to continue...", flush=True)
    input()

   


def main():
    # Check and request admin privileges
    if not is_admin():
        print("Script is not running with administrative privileges. Exiting.")
        return

    # Download the Splunk installer if it's not already present
    downloadSplunk()
    
    # Install Splunk and get the admin password generated during the installation
    admin_password = installSplunk()
    
    # Uncomment the next two lines if you want to replace the apps folder in the Splunk directory
    # apps_source = r"C:\Windows\Temp\apps"
    # apps_dest = r"C:\Program Files\Splunk\etc\apps"
    # addAndReplaceFolders(apps_source, apps_dest)

    # Add and replace the deployment-apps folder in the Splunk directory
    deployment_apps_source = r"C:\Windows\Temp\deployment-apps"
    deployment_apps_dest = r"C:\Program Files\Splunk\etc\deployment-apps"
    addAndReplaceFolders(deployment_apps_source, deployment_apps_dest)

    # Add the license file to Splunk and restart the service
    add_license_and_restart(admin_password)

    # Clean up any temporary files used during the script execution
    cleanUp()

    print("Splunk deployment script completed. Press Enter to exit.", flush=True)
    input()

def cleanUp():
    """Clean up installation artifacts."""
    print("Cleaning up...")
    try:
        os.remove("C:\\Windows\\Temp\\splunk-9.2.0.msi")
    except FileNotFoundError:
        print("File already removed.")
    time.sleep(2)

if __name__ == "__main__":
    main()

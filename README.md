# Splunk Deployment Script

This script automates the process of downloading, installing, and configuring Splunk on a Windows system. It ensures that Splunk is downloaded, installed with a generated admin password, and configured with specific folder contents and license files.

## Features

- Checks and requests administrative privileges to run.
- Downloads the Splunk Universal Forwarder if it's not already present in the temp directory.
- Installs Splunk with a randomly generated admin password.
- Replaces the `deployment-apps` and `apps` folders in the Splunk directory with those provided alongside the script.
- Copies a `serverclass.conf` file to the Splunk directory, replacing the existing one.
- Adds a license file to Splunk and restarts the service.

## Prerequisites

- Python 3.x installed on the system.
- The `requests` and `tqdm` Python packages installed. These can be installed via pip:

  ```
  pip install requests tqdm
  ```

- The script must be run with administrative privileges.
- Ensure that the `deployment-apps`, `apps`, and `serverclass.conf` files are placed in the same directory as the script or modify the paths in the script accordingly.

## Usage

1. Place the script in the same directory as your `deployment-apps` and `apps` folders, and the `serverclass.conf` file.
2. Open a command prompt with administrative privileges.
3. Navigate to the directory containing the script.
4. Run the script:

   ```
   python splunk.py
   ```

5. Follow the on-screen prompts as the script progresses.

## Important Notes

- The script is intended for use on Windows systems.
- The Splunk installation command uses default parameters. Modify these parameters within the script if different settings are required.
- Ensure the Splunk service is not running before executing the script to avoid conflicts during installation and configuration.
- Always verify the success of the installation and configuration by checking the output logs and testing the Splunk instance.

## Troubleshooting

- If the script fails to download Splunk, check the URL and internet connectivity.
- If the script encounters permissions issues, ensure it's run as an administrator.
- For issues related to the Splunk service not starting, consult the Splunk logs located in `C:\Program Files\Splunk\var\log\splunk`.

## Contributing

Feel free to fork the repository and submit pull requests. For substantial changes, please open an issue first to discuss what you would like to change.

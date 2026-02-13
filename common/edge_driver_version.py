import os
import logging
import urllib3
import zipfile
import requests
import re
import time

from pathlib import Path

from common.constants import EnvVar
from common.subprocess_util import SubprocessUtil


class EdgeDriver:

    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
        self.zip_filename = 'edgedriver_win32.zip'
        self.driver_filename = 'msedgedriver.exe'
        self.edge_driver_url = 'https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/'
        self.edgedriver_file_download_url = 'https://msedgedriver.microsoft.com/'
        username = os.environ.get(EnvVar.USERNAME.value)
        self.user_bin_path = Path(rf"C:\Users\{username}\bin")

        # Create the directory if it doesn't exist
        self.user_bin_path.mkdir(parents=True, exist_ok=True)
        self.edge_driver_filename = self.user_bin_path / self.driver_filename
        self.subprocess = SubprocessUtil(self.logger)

    def __get_edgedriver_url(self, browser_version, timeout: int = 30) -> str:

        # Disable specific warning for insecure HTTPS requests
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self.logger.info("Getting Edge driver version")
        response = requests.get(self.edge_driver_url, verify=False, timeout=timeout)

        # Construct the regex pattern dynamically
        pattern = rf"{self.edgedriver_file_download_url}\d+(?:\.\d+)*\/{self.zip_filename}"

        edge_driver_versions = []
        version = None

        for line in response.text.splitlines():
            match = re.search(pattern, line)

            if match:
                version = match.group(0).split('/')[-2]  # Extract version part
                if version.startswith(browser_version):
                    edge_driver_versions.append(version)

        if edge_driver_versions:
            latest_version = sorted(edge_driver_versions, reverse=True)[0]
            return f"{self.edgedriver_file_download_url}{latest_version}/{self.zip_filename}"

        raise RuntimeError(f"No matching Edge driver found for version: {browser_version}")

    def __edge_version_requires_update(self, edge_driver_version: str, browser_version: str) -> bool:
        requires_update = edge_driver_version.split('.')[0:3] != browser_version.split('.')[0:3]
        return requires_update

    def __get_edge_driver_version(self):
        result = self.subprocess.run_command([self.edge_driver_filename.as_posix(), "--version"])

        # Extract the version number from the WebDriver output
        match = re.search(rf'(\d+\.\d+\.\d+)', result.stdout.strip())

        if match:
            return match.group(0)

        raise RuntimeError(f"Edge driver version not found.")

    def __download_edge_driver(self, edge_driver_url: str, timeout: int = 30):
        self.logger.info(f"Downloading Edge driver from {edge_driver_url}")
        response = requests.get(edge_driver_url, verify=False)
        if "checking this file" in response.text:
            time.sleep(timeout)
            response = requests.get(edge_driver_url, verify=False)

        if not response.ok:
            raise RuntimeError("Failed to download Edge driver.")

        with open(self.zip_filename, "wb") as f:
            f.write(response.content)

        with zipfile.ZipFile(self.zip_filename, "r") as zip_ref:
            zip_ref.extractall(self.user_bin_path)

        os.remove(self.zip_filename)
        self.logger.info(f"Edge driver extracted to {self.user_bin_path}")

    def ensure_driver_is_current(self, browser_version: str):
        edge_driver_url = self.__get_edgedriver_url(browser_version)

        if not self.edge_driver_filename.exists():
            self.logger.info("Microsoft Edge driver not found. Downloading new version.")
            self.__download_edge_driver(edge_driver_url)
            return

        edge_driver_version = self.__get_edge_driver_version()
        self.logger.info(
            f"Microsoft Edge Browser version: {browser_version} | Microsoft Edge Driver Version: {edge_driver_version}")
        requires_update = self.__edge_version_requires_update(edge_driver_version, browser_version)

        if requires_update:
            self.logger.info("Driver update required. Downloading new version.")
            self.__download_edge_driver(edge_driver_url)
        else:
            self.logger.info("Microsoft Edge driver already up to date.")

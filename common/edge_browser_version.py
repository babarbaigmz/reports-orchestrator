import logging
import re

from common.constants import EnvVar
from common.subprocess_util import SubprocessUtil


class EdgeBrowser:

    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
        self.subprocess = SubprocessUtil(self.logger)

    def get_edge_browser_version(self) -> str:
        query = r'reg query "HKCU\Software\Microsoft\Edge\BLBeacon" /v version'
        result = self.subprocess.run_command(query)
        # Use regex to search for the version number pattern (first 3 segments) in the output
        self.logger.info("Using regex to search for the Edge browser version number pattern (first 3 segments)")
        match = re.search(r'(\d+\.\d+\.\d+)', result.stdout.strip())
        if match:
            return match.group(0)
        raise RuntimeError("Unable to determine Microsoft Edge version.")

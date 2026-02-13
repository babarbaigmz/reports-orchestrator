import subprocess
import logging
from typing import Union


class SubprocessUtil:
    """Utility class to run subprocess commands safely."""

    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger

    def run_command(self, command: Union[str, list[str]], timeout: int = 60):
        try:
            self.logger.info("Executing command.")
            result = subprocess.run(command,
                                    shell=isinstance(command, str),
                                    check=True,
                                    capture_output=True,
                                    text=True,
                                    timeout=timeout
                                    )

            return result

        except subprocess.CalledProcessError as error:
            self.logger.error(f"Command failed: {command}", exc_info=True)
            raise
        except subprocess.TimeoutExpired as timeout_error:
            self.logger.error(f"Command timed out after {timeout}s: {command}", exc_info=True)
            raise

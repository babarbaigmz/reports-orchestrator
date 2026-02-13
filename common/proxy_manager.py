import os
import logging

from common.constants import EnvVar


class ProxyManager:
    """Handles setting and clearing HTTP/HTTPS proxy environment variables."""

    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
        self.http_proxy = os.environ.get(EnvVar.HTTP_PROXY.value)
        self.https_proxy = os.environ.get(EnvVar.HTTPS_PROXY.value)

    def clear_proxy(self):
        self.logger.info("Clearing proxy variables.")
        if self.http_proxy:
            os.environ.pop(EnvVar.HTTP_PROXY.value, None)

        if self.https_proxy:
            os.environ.pop(EnvVar.HTTPS_PROXY.value, None)

    def set_proxy(self):
        self.logger.info("Setting proxy variables.")

        if self.http_proxy:
            os.environ[EnvVar.HTTP_PROXY.value] = self.http_proxy

        if self.https_proxy:
            os.environ[EnvVar.HTTPS_PROXY.value] = self.https_proxy

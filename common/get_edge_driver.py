from common.proxy_manager import ProxyManager
from common.edge_browser_version import EdgeBrowser
from common.edge_driver_version import EdgeDriver


class GetEdgeDriver:

    def __init__(self, logger):
        self.logger = logger
        self.proxy = ProxyManager(self.logger)
        self.edge_browser_version = EdgeBrowser(self.logger)
        self.edge_driver_version = EdgeDriver(self.logger)

    def get_edge_driver(self):
        # Clear Proxy
        self.proxy.clear_proxy()

        # Get Microsoft Edge Browser version
        self.logger.info("Getting Microsoft Edge browser version")
        browser_version = self.edge_browser_version.get_edge_browser_version()
        self.edge_driver_version.ensure_driver_is_current(browser_version)
        self.logger.info("Driver ready for use")
        self.proxy.set_proxy()

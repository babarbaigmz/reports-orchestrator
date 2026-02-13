import logging
from typing import Optional
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from common.wait_utils import WaitUtils
from selenium.webdriver.remote.webdriver import WebDriver


class DriverManagerMain:
    """Context manager for Edge WebDriver lifecycle management.

    Handles browser initialization, navigation, and guaranteed cleanup.

    Usage:
        with EdgeDriverManager(logger) as manager:
            driver = manager.get_driver("https://example.com")
            # Perform automation tasks
        # Browser automatically closed, even if exceptions occur

    Attributes:
        DEFAULT_TIMEOUT: Default page load timeout in seconds
        DEFAULT_WAIT_TRIES: Default number of wait attempts for elements
    """

    DEFAULT_TIMEOUT = 60
    DEFAULT_WAIT_TRIES = 30

    def __init__(self,
                 logger: logging.Logger,
                 headless: bool = False
                 ) -> None:

        """Initialize the driver manager.
        Args:
        logger: Logger instance for tracking operations
        headless: If True, run browser in headless mode
        """
        self.logger = logger
        self.headless = headless
        self._driver: Optional[WebDriver] = None

    def get_driver(self,
                   login_url: str,
                   timeout: int = DEFAULT_TIMEOUT,
                   wait_for_body: bool = True
                   ) -> WebDriver:

        """Create Edge driver and navigate to URL.

        Args:
            login_url: URL to navigate to after browser launch
            timeout: Maximum wait time for page elements in seconds
            wait_for_body: If True, wait for body element to load

        Returns:
            Configured Edge WebDriver instance

        Raises:
            WebDriverException: If browser fails to launch or navigate
        """

        self.logger.info(f"Launching Edge and opening: {login_url}")
        options = Options()

        if self.headless:
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')

        # Selenium automatically locates Edge - no hardcoded path needed
        self._driver = webdriver.Edge(options=options)

        try:
            self._driver.get(login_url)
            if wait_for_body:
                WaitUtils.wait_for_element(
                    self._driver,
                    "body",
                    "TAG_NAME",
                    tries=self.DEFAULT_WAIT_TRIES,
                    timeout=timeout
                )

            return self._driver

        except Exception as e:
            self.logger.error(f"Failed to initialize driver: {e}")
            self._driver.quit()
            raise

    def quit_driver(self, driver: Optional[WebDriver] = None) -> None:
        """Close the browser and end WebDriver session.

        Args:
            driver: WebDriver instance to close. If None, uses internal driver.
        """
        # target_driver = driver or self._driver

        if self._driver:
            self.logger.info("Closing Edge driver.")
            try:
                self._driver.quit()
            except Exception as e:
                self.logger.error(f"Error while closing driver: {e}")

    def __enter__(self) -> "DriverManagerMain":
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Exit context manager and ensure cleanup.

        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred

        Returns:
            False to propagate any exceptions
        """
        self.quit_driver()
        return False

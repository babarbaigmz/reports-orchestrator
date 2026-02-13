import os
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from common.wait_utils import WaitUtils
from common.constants import EnvVar


class LoginManager:
    """Handles login logic for the web application."""

    def __init__(self, logger):
        self.logger = logger

    def login(self, driver):
        """Performs login if the login field is present."""
        try:
            username = os.environ.get(EnvVar.USERNAME.value)
            if not username:
                raise EnvironmentError("Missing USERNAME environment variable.")

            login_field = driver.find_element(By.NAME, "loginfmt")
            login_field.send_keys(f"{username}@company.com")
            login_field.send_keys(Keys.ENTER)

            WaitUtils.wait_for_element(driver, "shell-container", "ID", tries=30)
            self.logger.info("Login successful or page loaded after login.")

        except NoSuchElementException:
            # Login field not found - check if already authenticated
            self.logger.info("Login field not found, verifying authentication state...")

            try:
                WaitUtils.wait_for_element(driver, "shell-container", "ID", tries=2, timeout=3)
                self.logger.info("Already authenticated.")
            except TimeoutException:
                # Neither login field nor authenticated page found
                self.logger.error(f"Not authenticated and no login field. URL: {driver.current_url}")
                raise RuntimeError("Login field not found AND not authenticated. "f"Current URL: {driver.current_url}")

            except Exception as ex:
                self.logger.error(f"Unexpected error during login: {ex}", exc_info=True)
                raise

        except Exception as ex:
            self.logger.error(f"Error executing login process: {ex}", exc_info=True)
            raise

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import time


class WaitUtils:
    """Reusable wait utility for Selenium WebDriver operations."""

    @staticmethod
    def wait_for_element(driver,
                         element_name,
                         element_type,
                         tries=3,
                         timeout=10,
                         sleep_time=2,
                         clickable=False
                         ):

        element_type = element_type.upper()

        try:
            element_by = getattr(By, element_type)
            print(f"Elemnent By: {element_by}")

        except AttributeError:
            raise ValueError(f"Invalid element type '{element_type}'")

        for _ in range(tries):
            try:
                wait = WebDriverWait(driver, timeout)
                if clickable:
                    return wait.until(EC.element_to_be_clickable((element_by, element_name)))
                return wait.until(EC.presence_of_element_located((element_by, element_name)))
            except (TimeoutException, NoSuchElementException, WebDriverException):
                time.sleep(sleep_time)

        # If we get here, all retries failed
        raise TimeoutException(
            f"Element {element_type}='{element_name}' not found after "f"{tries} attempts (timeout={timeout}s each)")

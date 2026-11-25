import re
from typing import Optional
from urllib.parse import quote
from random import randint
from time import sleep

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

_driver: Optional[webdriver.Chrome] = None
_LOGIN_TIMEOUT_SECONDS = 120


def log() -> webdriver.Chrome:
    """Open WhatsApp Web and wait for the user to finish logging in."""
    global _driver

    if _driver is None:
        _driver = webdriver.Chrome()
        _driver.get("https://web.whatsapp.com")

    try:
        WebDriverWait(_driver, _LOGIN_TIMEOUT_SECONDS).until(
            EC.presence_of_element_located((By.ID, "pane-side"))
        )
    except TimeoutException as exc:
        raise TimeoutError(
            "WhatsApp Web login timed out. Scan the QR code and try again."
        ) from exc

    return _driver


def send(num: str, msg: str) -> None:
    """Send a message to an international phone number, such as +5511999999999."""
    if not num.startswith("+"):
        raise ValueError("num must include the international prefix, e.g. +55")

    phone = re.sub(r"\D", "", num)
    if not phone.isdigit() or not 8 <= len(phone) <= 15:
        raise ValueError("num must be a valid phone number with country code")
    if not msg.strip():
        raise ValueError("msg must not be empty")

    driver = log()
    driver.get(
        f"https://web.whatsapp.com/send?phone={phone}&text={quote(msg, safe='')}"
    )
    send_button = WebDriverWait(driver,randint(5,20) ).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="compose-btn-send"]'))
    )
    ActionChains(driver).move_to_element(send_button).click().perform()

if __name__=='__main__':
    print("ola")
    log()
    send('+556292549741',"oi")
    sleep(10)
    send('+556292549741',"teste 2")

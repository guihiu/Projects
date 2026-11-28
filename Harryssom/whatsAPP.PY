"""Small Selenium client for a user-operated WhatsApp Web session."""

import logging
import re
import time
from typing import TypeAlias

from selenium import webdriver
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)

Message: TypeAlias = tuple[str, str, str]
_driver: webdriver.Chrome | None = None
_CHAT_LIST = "#pane-side"
_MESSAGE_INPUT = "footer [contenteditable='true']"
_INCOMING_MESSAGES = "#main div.message-in"
_UNREAD_WORDS = ("unread", "não lida", "não lido", "nao lida", "nao lido")
_PHONE_IN_CHAT_ID = re.compile(r"(\d{7,15})@c\.us")
_PHONE_FORMAT = re.compile(r"\+?[\d\s().-]+")


def connection(timeout: float = 120) -> bool:
    """Open WhatsApp Web and wait for the user to finish scanning the QR code."""
    global _driver

    if timeout <= 0:
        raise ValueError("timeout must be greater than zero")

    if _driver is not None:
        try:
            if _driver.find_elements(By.CSS_SELECTOR, _CHAT_LIST):
                return True
            _quit_browser(_driver)
        except WebDriverException:
            logger.warning("Existing WhatsApp Web session is no longer available")
        _driver = None

    browser: webdriver.Chrome | None = None
    try:
        browser = webdriver.Chrome()
        browser.maximize_window()
        browser.get("https://web.whatsapp.com/")
        WebDriverWait(browser, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, _CHAT_LIST))
        )
    except TimeoutException:
        logger.warning("WhatsApp Web login timed out; scan the QR code and try again")
        if browser is not None:
            _quit_browser(browser)
        return False
    except WebDriverException:
        logger.exception("Could not start or connect to WhatsApp Web")
        if browser is not None:
            _quit_browser(browser)
        return False

    _driver = browser
    return True


def status() -> bool:
    """Return whether the current Chrome session is connected to WhatsApp Web."""
    if _driver is None:
        return False

    try:
        return any(
            chat_list.is_displayed()
            for chat_list in _driver.find_elements(By.CSS_SELECTOR, _CHAT_LIST)
        )
    except WebDriverException:
        logger.warning("Could not check the WhatsApp Web connection", exc_info=True)
        return False


def send(phone_number: str | int, message: str) -> bool:
    """Send one text message to a phone number in international format."""
    if isinstance(phone_number, bool) or not isinstance(phone_number, (str, int)):
        raise TypeError("phone_number must be a string or integer")
    if not isinstance(message, str):
        raise TypeError("message must be a string")

    phone_text = str(phone_number).strip()
    if not _PHONE_FORMAT.fullmatch(phone_text):
        raise ValueError("phone_number may contain only digits and common separators")
    phone = re.sub(r"\D", "", phone_text)
    if not 7 <= len(phone) <= 15:
        raise ValueError("phone_number must contain between 7 and 15 digits")
    if not message.strip():
        raise ValueError("message must not be empty")

    browser = _connected_driver()
    try:
        browser.get(f"https://web.whatsapp.com/send?phone={phone}")
        message_box = WebDriverWait(browser, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, _MESSAGE_INPUT))
        )
        message_box.click()
        lines = message.splitlines() or [message]
        for index, line in enumerate(lines):
            if index:
                message_box.send_keys(Keys.SHIFT, Keys.ENTER)
            if line:
                message_box.send_keys(line)

        previous_count = len(
            browser.find_elements(By.CSS_SELECTOR, "#main div.message-out")
        )
        message_box.send_keys(Keys.ENTER)
        WebDriverWait(browser, 15).until(
            lambda driver: len(
                driver.find_elements(By.CSS_SELECTOR, "#main div.message-out")
            )
            > previous_count
        )
    except TimeoutException:
        logger.warning("Message was not confirmed by WhatsApp Web")
        return False
    except WebDriverException:
        logger.exception("Could not send a message through WhatsApp Web")
        return False

    return True


def receive(timeout: float | None = None, poll_interval: float = 1) -> Message | None:
    """Wait for an unread chat and return (phone number, message text, contact name).

    If timeout is None, keep waiting. A timed-out call returns None.
    """
    if timeout is not None and timeout < 0:
        raise ValueError("timeout must not be negative")
    if poll_interval <= 0:
        raise ValueError("poll_interval must be greater than zero")

    browser = _connected_driver()
    deadline = None if timeout is None else time.monotonic() + timeout
    while deadline is None or time.monotonic() <= deadline:
        for chat in _unread_chats(browser):
            try:
                phone = _phone_from_chat(chat)
                chat.click()
                WebDriverWait(browser, 15).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, _INCOMING_MESSAGES)
                    )
                )
                messages = browser.find_elements(
                    By.CSS_SELECTOR, _INCOMING_MESSAGES
                )
                if not messages:
                    continue

                message = messages[-1]
                text_parts = [
                    item.get_attribute("innerText").strip()
                    for item in message.find_elements(
                        By.CSS_SELECTOR, "span.selectable-text"
                    )
                    if item.get_attribute("innerText")
                ]
                text = "\n".join(text_parts) if text_parts else message.text.strip()
                name = _contact_name(browser)
                if not phone:
                    raise RuntimeError(
                        "WhatsApp Web did not expose a phone number for this chat"
                    )
                if text:
                    return phone, text, name
            except StaleElementReferenceException:
                continue
            except TimeoutException:
                logger.debug("Unread chat did not expose an incoming message in time")

        if deadline is not None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            time.sleep(min(poll_interval, remaining))
        else:
            time.sleep(poll_interval)

    return None


def _connected_driver() -> webdriver.Chrome:
    if _driver is None:
        raise RuntimeError("Call connection() and scan the WhatsApp Web QR code first")
    return _driver


def _quit_browser(browser: webdriver.Chrome) -> None:
    try:
        browser.quit()
    except WebDriverException:
        logger.debug("Could not close the Chrome session cleanly", exc_info=True)


def _unread_chats(browser: webdriver.Chrome) -> list[WebElement]:
    chats = browser.find_elements(
        By.CSS_SELECTOR,
        "#pane-side [data-testid='cell-frame-container'], "
        "#pane-side [role='listitem']",
    )
    unread_chats: list[WebElement] = []
    for chat in chats:
        labels = [
            chat.get_attribute("aria-label") or "",
            *(
                item.get_attribute("aria-label") or ""
                for item in chat.find_elements(By.CSS_SELECTOR, "[aria-label]")
            ),
        ]
        if any(
            word in label.casefold()
            for label in labels
            for word in _UNREAD_WORDS
        ):
            unread_chats.append(chat)
    return unread_chats


def _phone_from_chat(chat: WebElement) -> str:
    elements = [chat, *chat.find_elements(By.CSS_SELECTOR, "[data-id]")]
    for element in elements:
        match = _PHONE_IN_CHAT_ID.search(element.get_attribute("data-id") or "")
        if match:
            return match.group(1)
    return ""


def _contact_name(browser: webdriver.Chrome) -> str:
    names = browser.find_elements(By.CSS_SELECTOR, "#main header span[title]")
    return names[0].get_attribute("title") if names else ""



if __name__=='__main__':

    teste=connection()
    print(status())
    time.sleep(5)
    phone_number="+5599984803624"
    send(phone_number," esta funcionando ")
    time.sleep(5)
    
    

    
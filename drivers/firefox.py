from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager

def selenium_firefox_driver() -> webdriver.Firefox:

    options = webdriver.FirefoxOptions()
    # options.add_argument('-headless')
    driver = webdriver.Firefox(options=options)
    return driver
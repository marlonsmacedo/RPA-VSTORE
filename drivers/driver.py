from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver


def get_driver():

    driver = webdriver.Chrome()
    options = webdriver.ChromeOptions()
    return driver, options



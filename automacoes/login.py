import os
import time

from selenium.webdriver.common.by import By

from drivers.driver import get_driver

def login_page():

    usuario: str = os.environ["VSTORE_USER"]
    senha: str = os.environ["VSTORE_PASSWORD"]
    url: str = os.environ["VSTORE_URL"]
    driver, driver_options = get_driver()

    driver.get(url)
    driver.find_element(By.XPATH, "//input[@id='usuarios']").send_keys(usuario)
    driver.find_element(By.XPATH, "//input[@id='senha']").send_keys(senha)
    driver.find_element(By.XPATH, "//input[@id='btnEnviar']").click()

    

    time.sleep(5)
    driver.quit()

login_page()



from selenium import webdriver

def selenium_chrome_driver() -> webdriver.Chrome:

    options = webdriver.ChromeOptions()
    # options.add_argument('-headless')
    driver = webdriver.Chrome(options=options)
    return driver
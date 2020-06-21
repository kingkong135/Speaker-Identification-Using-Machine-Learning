from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
import time

# Giữ browser để vẫn mở chung 1 tab

def log_in(browser, username, password):
    browser.get('https://uetcodehub.xyz/')

    username_input = browser.find_element_by_id("inputName")
    password_input = browser.find_element_by_id("inputPassword")
    username_input.send_keys(username)
    password_input.send_keys(password)
    browser.find_element_by_id("submit").click()

def log_out(browser):
    menu_dropdown = browser.find_element_by_id("action-menu-0-menubar")
    if menu_dropdown:
        menu_dropdown.click()
        logout = browser.find_element_by_id("actionmenuaction-6")
        logout.click()

if __name__ == "__main__":
    
    account = {}

    with open('./data/account.txt', encoding='utf-8') as f:
        for line in f.readlines():
            name, user, password = line.strip().split(',')
            account[name] = [user, password]
            
    browser = webdriver.Chrome('C:/Users/vieta/Downloads/chromedriver')
    # log_in(browser, account['VA'][0], account['VA'][1])
    # time.sleep(10)
    # log_out(browser)
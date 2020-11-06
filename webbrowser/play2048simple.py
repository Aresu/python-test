#! python 3
#
# 随机暴力play game 2048
#

import time
import random
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

url = 'https://play2048.co/'
geckodriverPath = r'D:\geckodriver\geckodriver'
actions = [Keys.UP, Keys.RIGHT, Keys.DOWN, Keys.LEFT]

browser = webdriver.Firefox(executable_path=geckodriverPath)
browser.get(url)
htmlElem = browser.find_element_by_tag_name('html')
retryButton = browser.find_element_by_class_name('retry-button')
while True:
    time.sleep(1)
    htmlElem.send_keys(actions[random.randint(0, 3)])
    if retryButton.is_displayed():
        retryButton.click()

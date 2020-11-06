#! python3
#
# AI play game 2048
#

import re
import time
import random
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

maximum = 4
url = 'https://play2048.co/'
geckodriverPath = r'D:\geckodriver\geckodriver'
actions = [Keys.UP, Keys.RIGHT, Keys.DOWN, Keys.LEFT]
tileRegex = re.compile(r'tile tile-(\d{1,4}) tile-position-(\d)-(\d)')


class Grid:
    """
    格子
    """

    def __init__(self, regex_list):
        self.size = maximum
        self.cells = []
        self.indexes = []
        self.build(regex_list)

    def build(self, regex_list):
        """
        构造格子数据
        :param regex_list:
        :return:
        """
        for x in range(self.size):
            self.cells.append([])
            for y in range(self.size):
                self.cells[x].append(0)

        for tupleElem in regex_list:
            val = int(tupleElem[0])
            y = int(tupleElem[1]) - 1
            x = int(tupleElem[2]) - 1
            if self.cells[x][y] < val:
                self.cells[x][y] = val

    def display(self):
        """
        打印格子信息
        """
        for idx in range(self.size):
            print('+----+----+----+----+')
            print('|%4d|%4d|%4d|%4d|' % tuple(self.cells[idx]))
        print('+----+----+----+----+')


browser = webdriver.Firefox(executable_path=geckodriverPath)
browser.get(url)
htmlElem = browser.find_element_by_tag_name('html')
retryButton = browser.find_element_by_class_name('retry-button')

while True:
    pageSource = browser.page_source
    newGrid = Grid(tileRegex.findall(pageSource))
    newGrid.display()
    time.sleep(4)
    # TODO AI move
    htmlElem.send_keys(actions[random.randint(0, 3)])
    if retryButton.is_displayed():
        retryButton.click()
    time.sleep(1)

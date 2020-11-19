#! python3
# 使用requests抓取手机网页数据
# 查看手机网页元素方法
# Chrome 浏览器开发者工具(F12)，点击第二个图标，即可切换为手机模式，然后可以选择手机型号
# 箭头后面的图标
# 然后便可捕捉需要的元素以及Request Headers
# 笔趣阁小说抓取
#

import re
import requests
from bs4 import BeautifulSoup

base_link = 'https://m.biqumo.com'
book_code = '/6/6919/'  # 小说编码

headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 5.0; SM-G900P Build/LRX21T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Mobile Safari/537.36'}
textFile = open('Free soldier king.txt', 'w')
chapters = []  # 章节列表
ignoreLink = ['/bookcase.html', '/', '#top']
bookRegex = re.compile(r'(/\d+/\d+)(/|.html)')
level = 10
books = {}  # 小说列表


def addBook(book_link, book_name):
    if book_link in books:
        return None
    books[book_link] = book_name


def findBooks(url, lv):
    """
    寻找小说

    :param url:链接
    :param lv:查找深度
    :return:
    """

    res = requests.get(url, headers=headers)
    if res.status_code != requests.codes.ok:
        return None
    res.encoding = res.apparent_encoding
    beautifulSoup = BeautifulSoup(res.text, 'html.parser')
    bookElems = beautifulSoup.select('a')
    for elem in bookElems:
        newLink = elem.get('href')
        name = elem.getText()
        if newLink in ignoreLink:
            continue
        if name == '':
            continue
        mo = bookRegex.search(newLink)
        if mo:
            addBook(mo.group(1) + '/', name)
        elif lv < level:
            findBooks(base_link + newLink, lv + 1)


def getChapters():
    """
    获取章节链接列表
    本来可以一直使用下一章，但是缺章会中断后续，所以改用章节列表，跳过出错章节

    :return:
    """

    res = requests.get(base_link + book_code + 'all.html', headers=headers)
    res.raise_for_status()
    res.encoding = res.apparent_encoding
    beautifulSoup = BeautifulSoup(res.text, 'html.parser')
    chapterElems = beautifulSoup.select('dd')
    for idx in range(1, len(chapterElems)):
        chapters.append(chapterElems[idx].select('a')[0].get('href'))


def getChapter(chapter_link):
    """
    抓取章节内容
    根据章节连接获取章节内容
    下一章节链接不包含'_'则此章节结束，包含则继续抓取下一页

    :param chapter_link:
    :return:
    """

    res = requests.get(base_link + chapter_link, headers=headers)
    if res.status_code != requests.codes.ok:
        return None

    res.encoding = res.apparent_encoding
    beautifulSoup = BeautifulSoup(res.text, 'html.parser')
    nextElems = beautifulSoup.select('#pb_next')
    chapterContentElems = beautifulSoup.select('#chaptercontent')
    nextPage = nextElems[0].get('href')
    content = chapterContentElems[0].getText()
    ctx = content.replace(r'(1/2)', '').replace(r'(2/2)', '').replace(
        r'(本章未完,请翻页)', '')
    textFile.write(
        ("".join([s for s in ctx.splitlines(True) if s.strip()])))
    if '_' not in nextPage:
        textFile.write('\n')
    else:
        getChapter(nextPage)


getChapters()
for chapter in chapters:
    getChapter(chapter)

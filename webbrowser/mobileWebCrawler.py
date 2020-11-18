#! python3
# 使用requests抓取手机网页数据
# 查看手机网页元素方法
# Chrome 浏览器开发者工具(F12)，点击第二个图标，即可切换为手机模式，然后可以选择手机型号
# 箭头后面的图标
# 然后便可捕捉需要的元素以及Request Headers
#

import json
import requests

link = 'https://www.xmkanshu.com/service/getContent?fr=xs_aladin_free&ctcrid=81&bkid=145626121&crid='
headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 5.0; SM-G900P Build/LRX21T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Mobile Safari/537.36'}
textFile = open('Big voyage.txt', 'w')


def getContent(content_link):
    res = requests.get(content_link, headers=headers)
    res.raise_for_status()
    res.encoding = res.apparent_encoding
    jsonStr = res.text
    jsonData = json.loads(jsonStr)
    return jsonData['result']


def getCapter(chapter_id):
    chapter_link = link + str(chapter_id) + '&pg='
    page = 1
    page_max = None

    while True:
        content = getContent(chapter_link + str(page))
        if page_max is None:
            page_max = int(content['pagecount'])

        if page == 1:
            textFile.write(str(chapter_id) + '.' + content['chaptername']
                           + '\n')
        if page == 1:
            content['content'] = '      ' + content['content']
        textFile.write(content['content'])
        page += 1
        if page > page_max:
            break
    textFile.write('\r\n')


for chapter in range(1, 634):
    getCapter(chapter)
textFile.close()

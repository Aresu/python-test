#! python3
# Usage: 省|直辖市|特别行政区 市|县|区 选项[future|history|all]
# Usage: python weather.py 北京 朝阳 all
# 根据 https://weather.cma.cn/ 抓取城市天气信息
#
# 错误码
# -1 省|直辖市|特别行政区 错误，长度不足
# -2 省|直辖市|特别行政区 错误，未找到
# -3 市|县|区 区域名字错误，长度不足
# -4 市|县|区 区域名字错误，未找到
#

import sys
import json
import pypinyin
import requests
from bs4 import BeautifulSoup
import prettytable

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 \
    (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'}
city_link = 'https://weather.cma.cn/api/dict/province/'
weather_link = 'https://weather.cma.cn/api/now/'
average_link = 'https://weather.cma.cn/api/climate?stationid='
PROVINCES = ['AAH', 'AAM', 'ABJ', 'ACQ', 'AFJ', 'AGD', 'AGS', 'AGX', 'AGZ',
             'AHA', 'AHB', 'AHE', 'AHI', 'AHL', 'AHN', 'AJL', 'AJS', 'AJX',
             'ALN', 'ANM', 'ANX', 'AQH', 'ASC', 'ASD', 'ASH', 'ASN', 'ASX',
             'ATJ', 'ATW', 'AXG', 'AXJ', 'AXZ', 'AYN', 'AZJ']


def getProvinceCode(province):
    """
    获取 省|直辖市|特别行政区 编码
    规则：A + 前两个字拼音的首字符大写

    :param province: 省|直辖市|特别行政区 名字
    :return: 省|直辖市|特别行政区 编码
    """
    if len(province) < 2:
        sys.exit(-1)

    code = 'A'
    for s in pypinyin.pinyin(province[:2], style=pypinyin.FIRST_LETTER):
        code += s[0].upper()

    if code not in PROVINCES:
        sys.exit(-2)

    return code


def getSuitability(src_name, dst_name):
    """
    计算源区域名字与目标区域名字的匹配度，从第一个字开始匹配，粗略计算

    :param src_name: 源区域名字
    :param dst_name: 目标区域名字
    :return: 匹配数量
    """
    count = 0
    for idx in range(len(src_name)):
        if len(dst_name) < idx + 1:
            break

        if src_name[idx] == dst_name[idx]:
            count += 1
        else:
            break
    return count


def getAreaCode(code, area):
    """
    根据 省|直辖市|特别行政区 编码获取地区编码

    :param code: 省|直辖市|特别行政区 编码
    :param area: 地区名字
    :return: 地区编码
    """
    if len(area) < 2:
        sys.exit(-3)

    link = city_link + code
    r = requests.get(link, headers=headers)
    r.raise_for_status()
    # 获取 json 的 string
    jsonStr = r.text
    jsonData = json.loads(jsonStr)
    cities = {}
    for cityInfo in jsonData['data'].split('|'):
        lst = cityInfo.split(',')
        if len(lst) == 2:
            cities[lst[1]] = lst[0]

    suitability = 0  # 匹配数量
    real_name = ""
    for name in cities.keys():
        count = getSuitability(area, name)
        if count > suitability:
            suitability = count
            real_name = name

    if suitability == 0:
        sys.exit(-4)

    return cities[real_name]


def getWeather(code):
    """
    根据地区编码获取天气信息

    :param code: 地区编码
    """

    link = weather_link + str(code)
    res = requests.get(link, headers=headers)
    res.raise_for_status()
    # 获取 json 的 string
    json_string = res.text
    json_data = json.loads(json_string)
    comment_dict = json_data['data']['now']
    print(json_data['data']['location']['path'].replace(",", ""))
    print('温度 ' + str(comment_dict['temperature']) + '℃')
    print('气压 ' + str(int(comment_dict['pressure'])) + 'hPa')
    print('湿度 ' + str(int(comment_dict['humidity'])) + '%')
    print(str(comment_dict['windDirection']) + str(comment_dict['windScale']))


def getFutureInfo(code):
    """
    根据地区编码获取未来天气信息

    :param code: 地区编码
    """

    res = requests.get('https://weather.cma.cn/web/weather/' + str(code)
                       + '.html')
    res.encoding = res.apparent_encoding
    res.raise_for_status()
    beautifulSoup = BeautifulSoup(res.text, 'html.parser')
    hourTableElems = beautifulSoup.select('#hourTable_0')
    rowElems = hourTableElems[0].select('tr')
    print()
    print('未来天气情况')
    rows = []
    for rowElem in rowElems:
        gridElems = rowElem.select('td')
        if gridElems[0].getText().strip() != '天气':
            for idx in range(len(gridElems)):
                gridElem = gridElems[idx]
                if len(rows) < idx + 1:
                    rows.append([])
                rows[idx].append(gridElem.getText().strip())
    pb = prettytable.PrettyTable()
    for idx in range(len(rows)):
        if idx == 0:
            pb.field_names = rows[idx]
        else:
            pb.add_row(rows[idx])
    print(pb)


def getAverageInfo(code):
    """
    根据地区编码获取年月平均气温和降水信息

    :param code: 地区编码
    """
    link = average_link + str(code)
    res = requests.get(link, headers=headers)
    res.raise_for_status()
    # 获取 json 的 string
    json_string = res.text
    json_data = json.loads(json_string)
    beginYear = json_data['data']['beginYear']
    endYear = json_data['data']['endYear']
    comment_list = json_data['data']['data']
    print()
    print("{}年-{}年月平均气温和降水".format(beginYear, endYear))
    pb = prettytable.PrettyTable()
    pb.field_names = ['月份', '最低温度', '最高温度', '雨量']

    for idx in range(len(comment_list)):
        row = []
        comment_dict = comment_list[idx]
        row.append('{:0>2d}月'.format(comment_dict['month']))
        row.append(str(comment_dict['minTemp']) + '℃')
        row.append(str(comment_dict['maxTemp']) + '℃')
        row.append(str(comment_dict['rainfall']) + 'mm')
        pb.add_row(row)

    print(pb)


def errorNotice():
    """
    参数错误提示
    """
    print('Usage: 省|直辖市|特别行政区 市|县|区 选项[future|history|all]')
    print('Usage: python weather.py 北京 朝阳 all')


if len(sys.argv) >= 3:
    province_code = getProvinceCode(sys.argv[1])
    area_code = getAreaCode(province_code, sys.argv[2])
    getWeather(area_code)
    if len(sys.argv) >= 4:
        command = sys.argv[3].lower()
        if command == 'future':
            getFutureInfo(area_code)
        elif command == 'history':
            getAverageInfo(area_code)
        elif command == 'all':
            getFutureInfo(area_code)
            getAverageInfo(area_code)
        else:
            errorNotice()
else:
    errorNotice()

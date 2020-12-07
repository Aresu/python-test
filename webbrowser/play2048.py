#! python3
#
# AI play game 2048
# 初版 2020-12-07 评估算法参考 https://github.com/gabrielecirulli/2048
#

import re
import math
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

maximum = 4
minSearchTime = 100
url = 'https://play2048.co/'
geckodriverPath = r'D:\geckodriver\geckodriver'
actions = [Keys.UP, Keys.RIGHT, Keys.DOWN, Keys.LEFT]
tileRegex = re.compile(r'tile tile-(\d{1,4}) tile-position-(\d)-(\d)')
details = ['UP', 'RIGHT', 'DOWN', 'LEFT']


def buildTraversals(vector):
    """
    Build a list of positions to traverse in the right order
    :param vector:
    :return:
    """

    traversals = {'x': [], 'y': []}
    for pos in range(maximum):
        traversals['x'].append(pos)
        traversals['y'].append(pos)

    # Always traverse from the farthest cell in the chosen direction
    if vector.x == 1:
        traversals['x'].reverse()

    if vector.y == 1:
        traversals['y'].reverse()

    return traversals


def withinBounds(position):
    return 0 <= position.x < maximum and 0 <= position.y < maximum


def positionsEqual(first, second):
    return first.x == second.x and first.y == second.y


def evaluation(grid):
    """
     静态评估
    """

    emptyCells = len(grid.availableCells())
    smoothWeight = 0.1
    mono2Weight = 1.0
    emptyWeight = 2.7
    maxWeight = 1.0

    return (grid.smoothness() * smoothWeight
            + grid.monotonicity2() * mono2Weight
            + math.log(emptyCells, math.e) * emptyWeight
            + grid.maxValue() * maxWeight)


class Position:
    """
    坐标类
    """

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def clone(self):
        newPosition = Position(self.x, self.y)
        return newPosition


class Tile(Position):
    """
    图块类，记录坐标上的值，并且移动是标记是否合并产生
    同一方向，合并产生的图块不会再与其他图块合并
    """

    def __init__(self, position, value=2):
        super().__init__(position.x, position.y)
        self.value = value
        self.mergedFrom = None  # Tracks tiles that merged together

    def updatePosition(self, position):
        self.x = position.x
        self.y = position.y

    def clone(self):
        newTile = Tile(Position(self.x, self.y), self.value)
        return newTile


class Grid:
    """
    格子
    """

    # 向量
    vectors = [
        Position(0, -1),  # 0 up
        Position(1, 0),  # 1 right
        Position(0, 1),  # 2 down
        Position(-1, 0),  # 3 left
    ]

    def __init__(self):
        self.cells = []
        self.build()

    def build(self):
        """
        初始化格子
        """

        for x in range(maximum):
            self.cells.append([])
            for y in range(maximum):
                self.cells[x].append(None)

    def initial(self, regex_list):
        """
        通过web初始化数据

        :param regex_list:
        :return:
        """
        for tupleElem in regex_list:
            val = int(tupleElem[0])
            x = int(tupleElem[1]) - 1
            y = int(tupleElem[2]) - 1
            if self.cells[x][y] is None:
                self.cells[x][y] = Tile(Position(x, y), val)
            elif self.cells[x][y].value < val:
                self.cells[x][y] = Tile(Position(x, y), val)

    def clone(self):
        newGird = Grid()
        for x in range(maximum):
            self.cells.append([])
            for y in range(maximum):
                if self.cells[x][y] is not None:
                    newGird.insertTile(self.cells[x][y].clone())

    def availableCells(self):
        """
        获取所有可用的单元格
        """
        cells = []
        for x in range(maximum):
            for y in range(maximum):
                if self.cells[x][y] is None:
                    cells.append(Position(x, y))
        return cells

    def cellContent(self, cell):
        if withinBounds(cell):
            return self.cells[cell.x][cell.y]
        else:
            return None

    def cellAvailable(self, cell):
        """
        Check if the specified cell is taken
        """
        return self.cellContent(cell) is None

    def cellOccupied(self, cell):
        return self.cellContent(cell)

    def insertTile(self, tile):
        self.cells[tile.x][tile.y] = tile

    def removeTile(self, tile):
        self.cells[tile.x][tile.y] = None

    def moveTile(self, tile, cell):
        self.cells[tile.x][tile.y] = None
        self.cells[cell.x][cell.y] = tile
        tile.updatePosition(cell)

    def smoothness(self):
        smoothness = 0
        for x in range(maximum):
            for y in range(maximum):
                tile = self.cellContent(Position(x, y))
                if tile:
                    value = math.log(tile.value, math.e) / math.log(2, math.e)
                    for direction in [1, 2]:
                        vector = Grid.vectors[direction]
                        targetCell = self.findFarthestPosition(Position(x, y),
                                                               vector)['next']
                        targetTile = self.cellContent(targetCell)
                        if targetTile:
                            targetValue = (math.log(targetTile.value, math.e)
                                           / math.log(2, math.e))
                            smoothness = smoothness - math.fabs(
                                value - targetValue)
        return smoothness

    def monotonicity(self, mark):
        flag = False
        if mark == 'left/right':
            flag = True
        totals = [0, 0]

        def getCell(pos_1, pos_2):
            if flag:
                return Position(pos_2, pos_1)
            else:
                return Position(pos_1, pos_2)

        for pos in range(maximum):
            _current = 0
            _next = _current + 1
            while _next < maximum:
                while (_next < maximum
                       and not self.cellContent(getCell(pos, _next))):
                    _next = _next + 1

                if _next >= maximum:
                    _next = _next - 1

                _currentValue = 0
                _currentTile = self.cellContent(getCell(pos, _current))
                if _currentTile:
                    _currentValue = math.log(_currentTile.value, math.e) \
                                    / math.log(2, math.e)
                _nextValue = 0
                _nextTile = self.cellContent(getCell(pos, _next))
                if _nextTile:
                    _nextValue = math.log(_nextTile.value, math.e) \
                                    / math.log(2, math.e)

                if _currentValue > _nextValue:
                    totals[0] = totals[0] + (_nextValue - _currentValue)
                elif _nextValue > _currentValue:
                    totals[1] = totals[1] + (_currentValue - _nextValue)

                _current = _next
                _next = _next + 1

        return max(totals)

    def monotonicity2(self):
        """
        measures how monotonic the grid is. This means the values of the tiles
        are strictly increasing
        or decreasing in both the left/right and up/down directions
        """
        return self.monotonicity('left/right') + self.monotonicity('up/down')

    def maxValue(self):
        """
        获取最大值
        """
        maxValue = 0
        for x in range(maximum):
            for y in range(maximum):
                if self.cells[x][y] is not None:
                    value = self.cells[x][y].value
                    if value > maxValue:
                        maxValue = value
        return math.log(maxValue, math.e) / math.log(2, math.e)

    def findFarthestPosition(self, cell, vector):

        # Progress towards the vector direction until an obstacle is found
        while True:
            previous = cell
            cell = Position(previous.x + vector.x, previous.y + vector.y)
            if not (withinBounds(cell) and self.cellAvailable(cell)):
                break

        return {
            'parthest': previous,
            'next': cell,  # Used to check if a merge is required
        }

    def move(self, direction):
        vector = Grid.vectors[direction]
        traversals = buildTraversals(vector)
        moved = False
        won = False

        # Traverse the grid in the right direction and move tiles
        for x in traversals['x']:
            for y in traversals['y']:
                cell = Position(x, y)
                tile = self.cellContent(Position(x, y))

                if tile is not None:
                    positions = self.findFarthestPosition(cell, vector)
                    nextTile = self.cellContent(positions['next'])

                    # Only one merger per row traversal?
                    if (nextTile and nextTile.value == tile.value
                            and not nextTile.mergedFrom):
                        merged = Tile(positions['next'], tile.value * 2)
                        merged.mergedFrom = [tile, nextTile]

                        self.insertTile(merged)
                        self.removeTile(tile)

                        # Converge the two tiles' positions
                        tile.updatePosition(positions['next'])

                        # The mighty 2048 tile
                        if merged.value == 2048:
                            won = True
                    else:
                        self.moveTile(tile, positions['parthest'])

                    if not positionsEqual(cell, tile):
                        moved = True  # The tile moved from its original cell!s

        return moved, won

    def line(self, y):
        ret = []
        for x in range(maximum):
            if self.cells[x][y] is None:
                ret.append(0)
            else:
                ret.append(self.cells[x][y].value)
        return ret

    def display(self):
        """
        打印格子信息
        """
        for y in range(maximum):
            print('+----+----+----+----+')
            print('|%4s|%4s|%4s|%4s|' % tuple(self.line(y)))
        print('+----+----+----+----+')


class AI:
    """
    移动AI
    """

    def __init__(self, regex_list):
        self.regex_list = regex_list
        self.grid = Grid()
        self.grid.initial(self.regex_list)
        # self.grid.display()

    def search(self):
        """

        """

        direction = None
        score = None
        for v in [0, 1, 2, 3]:
            newGird = Grid()
            newGird.initial(self.regex_list)
            moved, won = newGird.move(v)
            if won:
                direction = v
                break
            print(v, moved, won)
            if moved:
                value = evaluation(newGird)
                print(v, moved, won, value)
                if score is None:
                    score = value
                    direction = v
                elif value > score:
                    score = value
                    direction = v
        if direction is not None:
            print('move ' + details[direction])
        return direction


browser = webdriver.Firefox(executable_path=geckodriverPath)
browser.get(url)
htmlElem = browser.find_element_by_tag_name('html')
retryButton = browser.find_element_by_class_name('retry-button')

while True:
    pageSource = browser.page_source
    _direction = AI(tileRegex.findall(pageSource)).search()
    if _direction is not None:
        htmlElem.send_keys(actions[_direction])
    if retryButton.is_displayed():
        retryButton.click()
    time.sleep(0.1)

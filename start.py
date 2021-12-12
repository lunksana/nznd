import json
from pprint import pprint
import time

# 数字货币交易所作死小工具，用于自动交易，燃烧自己的资金，能不能赚钱，不知道，反正你要用了就不关我事
# 纯属联手之作，重要的事情说三遍，别作死，别作死，别作死

class Start:
    def __init__(self):
        self.config = json.load(open('config.json'))
        self.api = self.config['api']
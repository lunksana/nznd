import pymongo
import json

# 读取用户配置文件
with open('conf/config.json', 'r') as conf:
    config = json.load(conf)

# 基于配置文件信息判断是否已经进行初始化
if config['init'] != 1:
    print("请先进行初始化\n")
    exit()
else:
    addr = config['db_addr']
    port = config['db_port']
    name = config['db_name']


# 对数据库进行操作
class mgdb:
    def __init__(self,table):
        self.client = pymongo.MongoClient(addr, port)
        self.db = self.client[name]
        self.col = self.db[table]
        
    # 查询数据
    def find(self, condition):
        return self.col.find(condition)
    
    # 插入数据
    def insert(self, data):
        self.col.insert(data)
        
    # 更新数据
    def update(self, condition, data):
        self.col.update(condition, data)
    
    # 删除数据
    def delete(self, condition):
        self.col.remove(condition)

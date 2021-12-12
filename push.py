import requests

# 使用免费推送服务进行信息推送

class Push(object):
    def __init__(self, url):
        self.url = url
        
    # 服务选择
    def push(self, title, content, type):
        data = {
            'title': title,
            'content': content,
            'type': type
        }
        res = requests.post(self.url, data=data)
        return res.json()
    
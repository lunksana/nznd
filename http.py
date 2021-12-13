# 将所有仓位控制，订单操作模块化

#import ws
import time
import requests
import hashlib
import hmac
import re
from pprint import pprint
from urllib.parse import urlencode

# 基本变量设置
# bn = ccxt.binance({
#     'enableRateLimit': True,
#     'options': {
#         'defaultType': 'future',
#         'adjustForTimeDifference': True
#     },
#     'apiKey': userapi.apiKey,
#     'secret': userapi.secret
# })

class Bn:
    base_url = 'https://fapi.binance.com'
    interval_list = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
    type_list = ['LIMIT', 'MARKET', 'SOTP', 'TAKE_PROFIT', 'STOP_MARKET', 'TAKE_PROFIT_MARKET']
    def __init__(self, symbol, api_key = None, secret = None, timeout = 5):
        self.symbol = symbol
        self.api_key = api_key
        self.secret = secret
        self.timeout = timeout
        self.headers = {'X-MBX-APIKEY': self.api_key}
    
    def _generate_signature(self, params: dict):
        query_str = urlencode(params)
        return hmac.new(self.secret.encode('utf-8'), query_str.encode('utf-8'), hashlib.sha256).hexdigest()
    
    def _requests(self, Method, url, headers: bool = False, params: dict = None, private: bool = False):
        if private:
            if params:
                url += '?' + urlencode(params)
            url = url + '&signature=' + self._generate_signature(params)
        else:
            if params:
                url += '?' + urlencode(params)
        if headers:
            return requests.request(Method, url, headers = self.headers, timeout = self.timeout)
        else:
            return requests.request(Method, url, timeout = self.timeout)

    def fetch_ticker(self, symbol = None):
        path = '/fapi/v1/ticker/price'
        url = self.base_url + path
        if symbol:
            sym = symbol
        else:
            sym = self.symbol
        params = {'symbol': sym}
        #requests_data = requests.get(url, timeout=self.timeout).json()
        requests_data = self._requests('get', url, params = params).json()
        return float(requests_data['price'])
        
    def fetchOHLCV(self, symbol, interval: str, since = None, limit: int = None):
        if interval not in self.interval_list:
            return
        else:
            path = '/fapi/v1/klines'
            url = self.base_url + path
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            if since:
                params['startTime'] = since
            requests_data = self._requests('get', url, False, params).json()
            return [[ohl[i] for i in range(0,6)] for ohl in requests_data]
    
    # Private API
    def get_timestamp(self):
        return int(time.time() * 1000)

    def listenKey(self, option):
        Options = {
            'NEW': 'post', 'RENEW': 'put', 'CLOSE': 'delete'
        }
        if option not in Options.keys():
            return
        else:
            path = '/fapi/v1/listenKey'
            url = self.base_url + path
            if  Options[option] != 'delete':
                requests_data = self._requests(Options[option], url, True, private = False)
                if Options[option] == 'put':
                    return
                else:
                    return requests_data.json()['listenKey']
            else:
                self._requests(Options[option], url, True, private = False)
                return

    def fetch_open_orders(self, symbol = None, since = None, limit = None):
        path = '/fapi/v1/openOrders'
        url = self.base_url + path
        params = {
            'timestamp': self.get_timestamp()
        }
        if symbol:
            params['symbol'] = symbol
        return self._requests('get', url, True, params, True).json()

    def fetch_orders(self, symbol = None, since = None, limit = None):
        path = '/fapi/v1/allOrders'
        url = self.base_url + path
        params = {
            'timestamp': self.get_timestamp()
        }
        if symbol:
            params['symbol'] = symbol
        else:
            params['symbol'] = self.symbol
        if since:
            params['startTime'] = since
        if limit:
            params['limit'] = limit
        return self._requests('get', url, True, params, True).json()

    def fetch_order_status(self, id, symbol = None):
        path = '/fapi/v1/order'
        url = self.base_url + path
        statuses = {
            'NEW': 'open',
            'PARTIALLY_FILLED': 'open',
            'FILLED': 'closed',
            'CANCELED': 'canceled',
            'PENDING_CANCEL': 'canceling',  # currently unused
            'REJECTED': 'rejected',
            'EXPIRED': 'expired',
        }
        params = {
            'orderId': id,
            'timestamp': self.get_timestamp()
        }
        if symbol:
            params['symbol'] = symbol
        else:
            params['symbol'] = self.symbol
        return statuses[self._requests('get', url, True, params, True).json()['status']]

    def fetch_my_trades(self, symbol = None, since = None, limit = None):
        path = '/fapi/v1/userTrades'
        url = self.base_url + path
        params = {
            'timestamp': self.get_timestamp()
        }
        if symbol:
            params['symbol'] = symbol
        else:
            params['symbol'] = self.symbol
        if since:
            params['startTime'] = since
        if limit:
            params['limit'] = limit
        return self._requests('get', url, True, params, True).json()

    def fetch_total_balance(self):
        path = '/fapi/v2/balance'
        url = self.base_url + path
        params = {
            'timestamp': self.get_timestamp()
        }
        requests_data = self._requests('get', url, True, params, True).json()
        return {i['asset']:float(i['balance']) for i in requests_data}
            

    def fetch_free_balance(self):
        path = '/fapi/v2/balance'
        url = self.base_url + path
        params = {
            'timestamp': self.get_timestamp()
        }
        requests_data = self._requests('get', url, True, params, True).json()
        return {i['asset']:float(i['availableBalance']) for i in requests_data}

    def create_order(self, positionSide, type, quantity, price: float):
        if type not in self.type_list:
            return
        else:
            path = '/fapi/v1/order'
            url = self.base_url + path
            params = {
                'symbol': self.symbol,
                'timestamp': self.get_timestamp()
            }
            timeInForce_is_needed = False
            quantity_is_needed = False
            price_is_needed = False
            stopPrice_is_needed = False
            if type == 'LIMIT':
                timeInForce_is_needed = True
                quantity_is_needed = True
                price_is_needed = True
            elif type == 'MARKET':
                quantity_is_needed = True
            elif type == 'STOP' or type == 'TAKE_PROFIT':
                quantity_is_needed = True
                price_is_needed = True
                stopPrice_is_needed = True
            elif type == 'STOP_MARKET' or type == 'TAKE_PROFIT_MARKET':
                stopPrice_is_needed = True
            if timeInForce_is_needed:
                params['timeInForce'] = 'GTC'
            if quantity_is_needed:
                if isinstance(quantity, str) and re.match(r'[0-9]+%$', quantity):
                    quantity = round(abs(self.fetch_positions(positionSide)[0]['positionAmt']) * float(quantity[0:-1]) / 100, 3)
                elif isinstance(quantity, float) or isinstance(quantity, int):
                    quantity = round(quantity, 3)
                else:
                    return
                params['quantity'] = quantity
            if price_is_needed:
                params['price'] = price
            if stopPrice_is_needed:
                params['stopPrice'] = price            
            if positionSide == 'LONG':
                if type != 'LIMIT' or  type != 'MARKET':
                    side = 'SELL'
                side = 'BUY'
            else:
                if type != 'LIMIT' or  type != 'MARKET':
                    side = 'BUY'
                side = 'SELL'
            params['side'] = side
            params['positionSide'] = positionSide
            params['type'] = type
            return self._requests('post', url, True, params, True).json()
        
        

    def cancel_order(self, id):
        path = '/fapi/v1/order'
        url = self.base_url + path
        params = {
            'symbol': self.symbol,
            'timestamp': self.get_timestamp()
        }
        if isinstance(id, str) and id.isdigit():
            params['orderId'] = id
        else:
            return
        return self._requests('delete', url, True, params, True).json()
    
    def cancel_all_orders(self):
        path = '/fapi/v1/allOpenOrders'
        url = self.base_url + path
        params = {
            'symbol': self.symbol,
            'timestamp': self.get_timestamp()
        }
        return self._requests('delete', url, True, params, True).json()
        

    def fetch_positions(self, positionSide = None):
        path = '/fapi/v2/positionRisk'
        url = self.base_url + path
        params = {
            'symbol': self.symbol,
            'timestamp': self.get_timestamp()
        }
        requests_data = self._requests('get', url, True, params, True).json()
        if positionSide:
            return [pos for pos in requests_data if pos['positionSide'] == positionSide]
        else:
            return requests_data
        
    def create_pos(self, type, price, amt):
        if type not in ['LIMIT', 'MARKET']:
            return
        else:
            if amt > 0:
                positionSide = 'LONG'
                amt = round(amt, 3)
            else:
                positionSide = 'SHORT'
                amt = round(abs(amt), 3)
        return self.create_order(positionSide, type, amt, price, amt)
       
    
    def create_stop_order(self, price, pos_side, amt = None):    
        if amt:
            type = 'STOP'
        else:
            type = 'STOP_MARKET'
        return self.create_order(pos_side, type, price, amt)
    
    def create_tpsl_order(self, price, pos_side, amt = None):
        if amt:
            type = 'TAKE_PROFIT'
        else:
            type = 'TAKE_PROFIT_MARKET'
        return self.create_order(pos_side, type, amt, price)          
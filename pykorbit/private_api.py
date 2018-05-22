import requests
import time
from pykorbit.public_api import *
import sys

getframe_expr = 'sys._getframe({}).f_code.co_name'

def _send_post_request(url, headers=None, data=None):
    try:
        resp = requests_retry_session().post(url, headers=headers, data=data)
        contents = resp.json()
        return contents
    except Exception as x:
        print("send post request failed", x.__class__.__name__)
        print("caller: ", eval(getframe_expr.format(2)))
        return None
    else:
        print(resp.status_code)
        return None


def _send_get_request(url, headers=None):
    try:
        resp = requests_retry_session().get(url, headers=headers)
        contents = resp.json()
        return contents
    except Exception as x:
        print("send get request failed", x.__class__.__name__)
        print("caller: ", eval(getframe_expr.format(2)))
        return None
    else:
        print(resp.status_code)
        return None


class Korbit(object):
    def __init__(self, email=None, password=None, key=None, secret=None):
        self.email = email
        self.password = password
        self.key = key
        self.secret = secret
        self.constant = None

        self.access_token = None
        self.refresh_token = None
        self.headers = None

        self._issue_access_token()
        self._get_constants()

    def _issue_access_token(self):
        """
        access token을 처음 발급하는 메서드
        :return:
        """
        url = "https://api.korbit.co.kr/v1/oauth2/access_token"
        data = {"client_id": self.key,
                "client_secret": self.secret,
                "grant_type": "password",
                "username": self.email,
                "password": self.password}

        contents = _send_post_request(url, data=data)

        if isinstance(contents, dict):
            if 'access_token' in contents.keys():
                self.access_token = contents.get('access_token')
                self.refresh_token = contents.get('refresh_token')
            elif 'error' in contents.keys():
                print(contents.get("error_description"))

    def renew_access_token(self):
        """
        발급받은 access_token과 refresh_token을 사용해서 access_token을 갱신하는 메서드
        :return:
        """
        url = "https://api.korbit.co.kr/v1/oauth2/access_token"
        data = {"client_id": self.key,
                "client_secret": self.secret,
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token}

        contents = _send_post_request(url, data=data)

        if isinstance(contents, dict):
            if 'access_token' in contents.keys():
                self.access_token = contents.get('access_token')
                self.refresh_token = contents.get('refresh_token')
            else:
                print("renew_access_token error ", contents)

    def _get_constants(self):
        self.constant = get_constants()

    def _get_tick_size(self, currency="BTC"):
        """
        KRW 기준 호가 단위를 리턴하는 메서드
        :param currency: BTC/BCH/BTG/ETH/ETC/XRP
        :return:
        """
        if self.constant is not None:
            currency = currency.lower() + "_krw"
            currency_dic = self.constant.get(currency)

            if isinstance(currency_dic, dict):
                return currency_dic.get("tick_size")
            else:
                return None
        else:
            return None

    def _get_quantity_min_max(self, currency="BTC"):
        """
        매수/매도 수량 최소 입력값
        :param currency: BTC/BCH/BTG/ETH/ETC/XRP
        :return:
        """
        if self.constant is not None:
            currency = currency.lower() + "_krw"
            currency_dic = self.constant.get(currency)

            if isinstance(currency_dic, dict):
                return currency_dic.get("order_min_size"), currency_dic.get("order_max_size")
            else:
                return None
        else:
            return None

    def _get_price_min_max(self, currency="BTC"):
        """
        최소/최대 주문가 (원화 기준)
        :param currency: BTC/BCH/BTG/ETH/ETC/XRP
        :return:
        """
        if self.constant is not None:
            currency = currency.lower() + "_krw"
            currency_dic = self.constant.get(currency)

            if isinstance(currency_dic, dict):
                return currency_dic.get("min_price"), currency_dic.get("max_price")
            else:
                return None
        else:
            return None

    def get_headers(self):
        if self.access_token is not None:
            headers = {"Authorization": "Bearer " + self.access_token}
            return headers
        else:
            print("current access_token is not valid")
            return None

    def buy_market_order(self, currency="BTC", expenditure=None):
        """
        시장가로 매수하는 메서드
        :param currency: BTC/BCH/BTG/ETH/ETC/XRP
        :param expenditure: 지출액
        :return:
        """
        currency = currency.lower() + "_krw"
        url = "https://api.korbit.co.kr/v1/user/orders/buy"
        headers = self.get_headers()
        data = {"currency_pair": currency,
                "type": "market",
                "fiat_amount": expenditure,
                "nonce": str(int(time.time()))}

        contents = _send_post_request(url, headers=headers, data=data)
        if contents is not None:
            return contents.get('orderId'), contents.get('status'), contents.get('currencyPair')
        else:
            return None, None, None

    def buy_limit_order(self, currency="BTC", price=10000, amount=1):
        """
        지정가로 매수하는 메서드
        :param currency: BTC/BCH/BTG/ETH/ETC/XRP
        :param price: 주문가
        :param amount: 매수량
        :return:
        """
        currency = currency.lower() + "_krw"
        url = "https://api.korbit.co.kr/v1/user/orders/buy"
        headers = self.get_headers()
        data = {"currency_pair": currency,
                "type": "limit",
                "price": price,
                "coin_amount": amount,
                "nonce": str(int(time.time()))}

        contents = _send_post_request(url, headers=headers, data=data)
        if contents is not None:
            return contents.get('orderId'), contents.get('status'), contents.get('currencyPair')
        else:
            return None, None, None


    def sell_market_order(self, currency="BTC", coin_amount=1):
        """
        시장가 매도
        :param currency: BTC/BCH/BTG/ETH/ETC/XRP
        :param coin_amount:
        :return:
        """
        currency = currency.lower() + "_krw"
        url = "https://api.korbit.co.kr/v1/user/orders/sell"
        headers = self.get_headers()
        data = {"currency_pair": currency,
                "type": "market",
                "coin_amount": coin_amount,
                "nonce": str(int(time.time()))}

        contents = _send_post_request(url, headers=headers, data=data)
        if contents is not None:
            return contents.get('orderId'), contents.get('status'), contents.get('currencyPair')
        else:
            return None, None, None

    def sell_limit_order(self, currency="BTC", price=10000, coin_amount=1):
        """
        지정가 매도
        :param currency:
        :param price:
        :param coin_amount:
        :return:
        """
        currency = currency.lower() + "_krw"
        url = "https://api.korbit.co.kr/v1/user/orders/sell"
        headers = self.get_headers()
        data = {"currency_pair": currency,
                "type": "limit",
                "price": price,
                "coin_amount": coin_amount,
                "nonce": str(int(time.time()))}

        contents = _send_post_request(url, headers=headers, data=data)
        if contents is not None:
            return contents.get('orderId'), contents.get('status'), contents.get('currencyPair')
        else:
            return None, None, None

    def cancel_order(self, currency="BTC", id=10000):
        """
        주문 취소
        :param currency:
        :param id:
        :return:
        """
        currency = currency.lower() + "_krw"
        url = "https://api.korbit.co.kr/v1/user/orders/cancel"
        headers = self.get_headers()
        data = {"currency_pair": currency,
                "id": id,
                "nonce": str(int(time.time()))}

        return _send_post_request(url, headers=headers, data=data)

    def get_balances(self):
        url = "https://api.korbit.co.kr/v1/user/balances"
        headers = self.get_headers()
        return _send_get_request(url, headers=headers)


if __name__ == "__main__":
    with open("korbit.conf") as f:
        email, password, key, secret = (x.strip() for x in f)

    korbit = Korbit(email, password, key, secret)

    # 주문 제약 조건
    #print(korbit._get_tick_size("BTC"))
    #print(korbit._get_quantity_min_max("BTC"))
    #print(korbit._get_price_min_max("BTC"))

    # 매수-시장
    #print("시장가 매수")
    #print(korbit.buy_market_order("ETC", 9800))

    # 매수-지정가
    #print("지정가 매수")
    #print(korbit.buy_limit_order("ETC", 30000, 0.1))

    # 지정가 매도
    #print(korbit.sell_limit_order("ETC", 45000, 0.28))

    # 시장가 매도
    #print(korbit.sell_market_order("ETC", 0.1))


    # 주문 취소
    #time.sleep(1)
    #print(korbit.cancel_order("BTC", 9000))
    #print(korbit.cancel_order("BTC", [1000, 10001]))
    #print(ret)

    # 지갑 잔고 조회
    print(korbit.get_balances())

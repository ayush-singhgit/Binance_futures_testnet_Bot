import hashlib
import hmac
import time
from urllib.parse import urlencode

import requests

from bot.logging_config import setup_logger

logger = setup_logger("trading_bot.client")

BASE_URL = "https://testnet.binancefuture.com"


class BinanceClient:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
        self.session.headers.update({
            "X-MBX-APIKEY": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded",
        })

        self.time_offset = self._get_server_time_offset()

    def _get_server_time_offset(self) -> int:
        """
        Synchronize local system time with Binance server time.
        """

        try:
            response = requests.get(
                f"{BASE_URL}/fapi/v1/time",
                timeout=5
            )

            server_time = response.json()["serverTime"]

            local_time = int(time.time() * 1000)

            offset = server_time - local_time

            logger.info(
                "Server time synchronized | offset=%sms",
                offset
            )

            return offset

        except Exception as e:
            logger.warning(
                "Failed to synchronize server time: %s",
                e
            )

            return 0

    def _sign(self, params: dict) -> dict:
        params["timestamp"] = int(time.time() * 1000) + self.time_offset
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        params["signature"] = signature
        return params

    def _request(self, method: str, endpoint: str, params: dict = None) -> dict:
        url = BASE_URL + endpoint
        params = self._sign(params or {})

        logger.debug("REQUEST  %s %s | params=%s", method, endpoint, params)

        try:
            resp = self.session.request(method, url, params=params, timeout=10)
            data = resp.json()
        except requests.exceptions.ConnectionError as e:
            logger.error("Network error: %s", e)
            raise ConnectionError(f"Cannot reach Binance testnet: {e}") from e
        except requests.exceptions.Timeout:
            logger.error("Request timed out: %s %s", method, endpoint)
            raise TimeoutError("Request timed out")
        except Exception as e:
            logger.error("Unexpected request error: %s", e)
            raise

        logger.debug("RESPONSE %s | status=%s | body=%s", endpoint, resp.status_code, data)

        if not resp.ok or "code" in data:
            code = data.get("code", resp.status_code)
            msg = data.get("msg", "Unknown API error")
            logger.error("API error: code=%s msg=%s", code, msg)
            raise RuntimeError(f"Binance API error {code}: {msg}")

        return data

    def place_order(self, params: dict) -> dict:
        return self._request("POST", "/fapi/v1/order", params)

    def get_account_info(self) -> dict:
        return self._request("GET", "/fapi/v2/account")
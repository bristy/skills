"""Trading client for the simulation platform API with HMAC authentication."""

import hashlib
import hmac
import json
import os
import secrets
import time
import urllib.request
import urllib.parse
from typing import Optional


BASE_URL = os.environ.get("TRADE_API_URL", "http://54.255.3.5:8088")
API_PREFIX = "/api/v1/moss/agent"


class TradingClient:
    def __init__(self, api_key: str = "", api_secret: str = "", agent_id: str = ""):
        self.api_key = api_key
        self.api_secret = api_secret
        self.agent_id = agent_id
        self.base_url = BASE_URL

    def _sign(self, method: str, path: str, query: str, body: str) -> tuple[str, str, str]:
        ts = str(int(time.time()))
        nonce = secrets.token_hex(12)
        payload = f"{method}\n{path}\n{query}\n{body}\n{ts}\n{nonce}"
        signature = hmac.new(
            self.api_secret.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()
        return ts, nonce, signature

    def _request(self, method: str, path: str, body: dict = None,
                 query: dict = None, need_auth: bool = True) -> dict:
        full_path = f"{API_PREFIX}{path}"
        url = f"{self.base_url}{full_path}"

        canonical_query = ""
        if query:
            sorted_params = sorted(query.items())
            canonical_query = urllib.parse.urlencode(sorted_params)
            url = f"{url}?{canonical_query}"

        raw_body = ""
        if body is not None:
            raw_body = json.dumps(body, separators=(",", ":"))

        headers = {"Content-Type": "application/json"}

        if need_auth and self.api_key:
            ts, nonce, sig = self._sign(method, full_path, canonical_query, raw_body)
            headers["X-API-KEY"] = self.api_key
            headers["X-TS"] = ts
            headers["X-NONCE"] = nonce
            headers["X-SIGNATURE"] = sig

        req = urllib.request.Request(
            url,
            data=raw_body.encode() if raw_body else None,
            headers=headers,
            method=method,
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            try:
                return json.loads(error_body)
            except json.JSONDecodeError:
                return {"code": "HTTP_ERROR", "message": f"{e.code}: {error_body}"}

    # ── Binding ──

    def create_pair_code(self, user_uuid: str) -> dict:
        return self._request("POST", "/pair-codes", query={"user_uuid": user_uuid}, need_auth=False)

    def bind(self, pair_code: str, agent_name: str = "Bot", fingerprint: str = "") -> dict:
        if not fingerprint:
            fingerprint = f"sha256:{secrets.token_hex(16)}"
        return self._request("POST", "/agents/bind", {
            "pair_code": pair_code,
            "agent_name": agent_name,
            "agent_fingerprint": fingerprint,
        }, need_auth=False)

    # ── Trading ──

    def get_price(self) -> dict:
        return self._request("GET", "/market/price")

    def get_account(self) -> dict:
        return self._request("GET", "/account")

    def get_positions(self) -> list:
        return self._request("GET", "/positions")

    def get_orders(self, limit: int = 100) -> list:
        return self._request("GET", "/orders", query={"limit": str(limit)})

    def get_trades(self, limit: int = 100) -> list:
        return self._request("GET", "/trades", query={"limit": str(limit)})

    def open_long(self, notional_usdt: str, leverage: int, client_order_id: str = "") -> dict:
        body = {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "position_side": "LONG",
            "notional_usdt": notional_usdt,
            "leverage": leverage,
        }
        if self.agent_id:
            body["agent_id"] = self.agent_id
        if client_order_id:
            body["client_order_id"] = client_order_id
        return self._request("POST", "/orders/market", body)

    def open_short(self, notional_usdt: str, leverage: int, client_order_id: str = "") -> dict:
        body = {
            "symbol": "BTCUSDT",
            "side": "SELL",
            "position_side": "SHORT",
            "notional_usdt": notional_usdt,
            "leverage": leverage,
        }
        if self.agent_id:
            body["agent_id"] = self.agent_id
        if client_order_id:
            body["client_order_id"] = client_order_id
        return self._request("POST", "/orders/market", body)

    def close_position(self, position_side: str, close_qty_btc: str = "") -> dict:
        body = {
            "symbol": "BTCUSDT",
            "position_side": position_side,
        }
        if self.agent_id:
            body["agent_id"] = self.agent_id
        if close_qty_btc:
            body["close_qty_btc"] = close_qty_btc
        return self._request("POST", "/positions/close", body)

    def unbind(self, agent_id: str, user_uuid: str) -> dict:
        return self._request("POST", f"/agents/{agent_id}/unbind",
                             query={"user_uuid": user_uuid}, need_auth=False)

    # ── Display (human-side, user_uuid required) ──

    def get_overview(self, user_uuid: str) -> dict:
        return self._request("GET", "/trader/overview",
                             query={"user_uuid": user_uuid}, need_auth=False)

    def get_bots(self, user_uuid: str) -> dict:
        return self._request("GET", "/trader/bots",
                             query={"user_uuid": user_uuid, "category": "agents"}, need_auth=False)

    def get_bot_detail(self, user_uuid: str, bot_id: str = "") -> dict:
        bid = bot_id or self.agent_id
        return self._request("GET", f"/trader/bots/{bid}",
                             query={"user_uuid": user_uuid}, need_auth=False)

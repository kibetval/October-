
"""Scheduled Deriv even/odd signal scanner for GitHub Actions. Never places trades."""
import json
import os
import time
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal

import websocket

APP_ID = os.getenv("DERIV_APP_ID", "").strip()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
WINDOW = int(os.getenv("ANALYSIS_WINDOW", "300"))
THRESHOLD = float(os.getenv("EDGE_THRESHOLD", "0.07"))
WS_URL = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"


def last_digit(price, pip_size):
    decimals = max(0, min(10, int(pip_size)))
    formatted = f"{Decimal(str(price)):.{decimals}f}"
    return int(formatted[-1])


def request_once(payload, timeout=25):
    ws = websocket.create_connection(
        WS_URL, timeout=timeout, suppress_origin=True
    )
    try:
        ws.send(json.dumps(payload))
        deadline = time.time() + timeout
        wanted = payload.get("req_id")

        while time.time() < deadline:
            data = json.loads(ws.recv())

            if data.get("error"):
                message = data["error"].get("message", "Deriv API error")
                raise RuntimeError(message)

            if wanted is None or data.get("req_id") == wanted:
                return data

        raise TimeoutError("Timed out waiting for Deriv")
    finally:
        ws.close()


def get_symbols():
    data = request_once({
        "active_symbols": "brief",
        "product_type": "basic",
        "req_id": 1
    })

    symbols = {}
    for item in data.get("active_symbols", []):
        description = " ".join([
            item.get("display_name", ""),
            item.get("market_display_name", ""),
            item.get("submarket_display_name", "")
        ]).lower()

        if (
            "symbol" in item
            and "volatility" in description
            and item.get("is_trading_suspended") != 1
        ):
            symbols[item["symbol"]] = item.get(
                "display_name", item["symbol"]
            )

    return sorted(symbols.items())


def decide(prices, pip_size):
    digits = [last_digit(p, pip_size) for p in prices][-WINDOW:]

    if len(digits) < min(WINDOW, 100):
        return {"entry": "WAIT", "score": 0, "n": len(digits)}

    even_rate = sum(d % 2 == 0 for d in digits) / len(digits)
    recent = digits[-min(50, len(digits)):]
    recent_even_rate = sum(d % 2 == 0 for d in recent) / len(recent)

    edge = even_rate - 0.5
    recent_edge = recent_even_rate - 0.5
    same_direction = (
        (edge > 0 and recent_edge > 0)
        or (edge < 0 and recent_edge < 0)
    )

    entry = "WAIT"
    if (
        same_direction
        and abs(edge) >= THRESHOLD
        and abs(recent_edge) >= 0.08
    ):
        entry = "EVEN" if edge > 0 else "ODD"

    score = round(min(
        99,
        50 + abs(edge) * 150 + abs(recent_edge) * 35
    ))

    return {
        "entry": entry,
        "score": score,
        "n": len(digits),
        "even_pct": round(even_rate * 100, 1),
        "odd_pct": round((1 - even_rate) * 100, 1)
    }


def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        raise RuntimeError(
            "Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID secret"
        )

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    body = json.dumps({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "disable_web_page_preview": True
    }).encode()

    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        result = json.loads(response.read().decode())
        if not result.get("ok"):
            raise RuntimeError("Telegram rejected the message")


def main():
    if not APP_ID:
        raise SystemExit("Missing DERIV_APP_ID secret")

    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        raise SystemExit(
            "Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID secret"
        )

    symbols = get_symbols()
    print(f"Found {len(symbols)} volatility markets")

    alerts = []

    for index, (symbol, name) in enumerate(symbols, start=10):
        try:
            data = request_once({
                "ticks_history": symbol,
                "count": max(1000, WINDOW),
                "end": "latest",
                "style": "ticks",
                "req_id": index
            })

            history = data.get("history", {})
            result = decide(
                history.get("prices", []),
                data.get("pip_size", 2)
            )

            print(symbol, name, result)

            if result["entry"] != "WAIT":
                alerts.append((symbol, name, result))

        except Exception as error:
            print(f"ERROR {symbol}: {error}")

    if not alerts:
        print("No entries met the filter; no Telegram message sent.")
        return

    lines = [
        "🔎 DIGIT PULSE — DERIV EVEN/ODD SCAN",
        datetime.now(timezone.utc).strftime("UTC %Y-%m-%d %H:%M"),
        ""
    ]

    for symbol, name, result in alerts:
        lines.append(
            f"{name} ({symbol})\n"
            f"ENTRY: {result['entry']} | "
            f"analysis score {result['score']}/99\n"
            f"Sample: {result['n']} ticks · "
            f"EVEN {result['even_pct']}% · "
            f"ODD {result['odd_pct']}%"
        )

    send_telegram("\n\n".join(lines))


if __name__ == "__main__":
    main()
          

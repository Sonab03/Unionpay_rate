import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests


BASE_URL = "https://www.unionpayintl.com/upload/jfimg/{}.json"

JST = ZoneInfo("Asia/Tokyo")


def fetch_unionpay(day):
    date_string = day.strftime("%Y%m%d")
    url = BASE_URL.format(date_string)

    response = requests.get(url, timeout=20)

    if response.status_code != 200:
        return None

    return response.json(), url


def find_rate(data):
    for item in data["exchangeRateJson"]:
        if (
            item["transCur"] == "JPY"
            and item["baseCur"] == "CNY"
        ):
            return float(item["rateData"])

    raise RuntimeError("JPY/CNY rate not found")


def main():
    today = datetime.now(JST).date()

    # 最多向前找 7 天
    result = None

    for offset in range(7):
        day = today - timedelta(days=offset)

        try:
            result = fetch_unionpay(day)
        except requests.RequestException:
            result = None

        if result is not None:
            break

    if result is None:
        raise RuntimeError("No UnionPay JSON available")

    data, source_url = result

    rate = find_rate(data)
    amount = rate * 10000

    output = {
        "source": "UnionPay International",
        "source_url": source_url,
        "curDate": data["curDate"],
        "transCur": "JPY",
        "baseCur": "CNY",
        "rateData": rate,
        "jpy_10000_cny": round(amount, 4),
        "fetched_at": datetime.now(JST).isoformat(),
    }

    Path("history").mkdir(exist_ok=True)

    with open("latest.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    history_file = Path("history") / f"{data['curDate']}.json"

    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
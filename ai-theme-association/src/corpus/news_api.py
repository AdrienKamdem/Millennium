import requests
import os
import json
import time
from datetime import datetime


ALPHA_VANTAGE_API_KEY = "YOUR_API_KEY"

TICKERS = [
    "ADBE",
    "CAT",
    "DELL",
    "INTC",
    "MU",
    "NVDA",
    "PG",
    "TEAM",
    "WM",
]

ENDPOINT = "https://www.alphavantage.co/query"

FETCH_LIMIT = 1000

# Be conservative with API rate limiting
MIN_INTERVAL = 15.0


def fetch_news(ticker: str):

    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": ticker,
        "time_from": "20230101T0000",
        "time_to": "20260914T2359",
        "limit": FETCH_LIMIT,
        "sort": "LATEST",
        "apikey": ALPHA_VANTAGE_API_KEY,
    }

    print(f"Fetching news for {ticker}...")

    response = requests.get(
        ENDPOINT,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


if __name__ == "__main__":

    output_dir = "data/NEWS_API_RSS"
    os.makedirs(output_dir, exist_ok=True)

    all_data = {}

    for ticker in TICKERS:

        try:

            data = fetch_news(ticker)

            feed = data.get("feed", [])

            print(
                f"{ticker}: {len(feed)} articles returned"
            )

            all_data[ticker] = data

        except requests.RequestException as error:

            print(
                f"Failed to fetch {ticker}: {error}"
            )

            continue

        # Avoid hammering the API
        time.sleep(MIN_INTERVAL)

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    output_file = os.path.join(
        output_dir,
        f"alpha_vantage_news_{timestamp}.json",
    )

    raw_output = {
        "metadata": {
            "source": "Alpha Vantage",
            "function": "NEWS_SENTIMENT",
            "tickers": TICKERS,
            "time_from": "20230101T0000",
            "time_to": "20260914T2359",
            "fetch_limit_per_ticker": FETCH_LIMIT,
            "fetched_at": datetime.now().isoformat(),
        },
        "data": all_data,
    }

    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            raw_output,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print("\nFinished.")
    print(f"Raw data saved to: {output_file}")
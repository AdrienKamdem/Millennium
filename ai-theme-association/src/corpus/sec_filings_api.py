import requests
import pandas as pd


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

FORMS = ["10-K", "10-Q", "8-K"]

START_DATE = pd.Timestamp("2023-01-01")
END_DATE = pd.Timestamp.today().normalize()

HEADERS = {
    "User-Agent": "kamdemadrien@gmail.com"
}


def get_ticker_cik_map(tickers):
    """
    Get SEC CIK numbers for requested tickers.
    """

    url = "https://www.sec.gov/files/company_tickers.json"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()

    company_data = pd.DataFrame.from_dict(
        response.json(),
        orient="index",
    )

    # SEC submissions endpoint expects 10-digit CIK
    company_data["cik_str"] = (
        company_data["cik_str"]
        .astype(str)
        .str.zfill(10)
    )

    company_data = company_data[
        company_data["ticker"].isin(tickers)
    ].copy()

    return company_data


def get_company_filings(cik, ticker, company_name):
    """
    Retrieve filing metadata for one company.
    """

    url = f"https://data.sec.gov/submissions/CIK{cik}.json"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()

    metadata = response.json()

    # ----------------------------------
    # Most recent filings
    # ----------------------------------

    filings = pd.DataFrame(
        metadata["filings"]["recent"]
    )

    all_filings = [filings]

    # ----------------------------------
    # Older filing metadata
    # ----------------------------------

    for historical_file in metadata["filings"].get("files", []):

        filename = historical_file["name"]

        historical_url = (
            f"https://data.sec.gov/submissions/{filename}"
        )

        historical_response = requests.get(
            historical_url,
            headers=HEADERS,
            timeout=30,
        )
        historical_response.raise_for_status()

        historical_data = historical_response.json()

        historical_df = pd.DataFrame(historical_data)

        all_filings.append(historical_df)

    # Combine filing history
    filings = pd.concat(
        all_filings,
        ignore_index=True,
    )

    # Company information
    filings["ticker"] = ticker
    filings["cik"] = cik
    filings["company"] = company_name

    return filings


def build_document_url(row):
    """
    Construct URL to primary SEC filing document.
    """

    cik = str(int(row["cik"]))

    accession = row["accessionNumber"].replace("-", "")

    primary_document = row["primaryDocument"]

    return (
        "https://www.sec.gov/Archives/edgar/data/"
        f"{cik}/"
        f"{accession}/"
        f"{primary_document}"
    )


if __name__ == "__main__":

    # ==========================================================
    # 1. Get CIKs for requested companies
    # ==========================================================

    companies = get_ticker_cik_map(TICKERS)

    print(
        companies[
            ["ticker", "cik_str", "title"]
        ]
    )

    # ==========================================================
    # 2. Get filing metadata for every company
    # ==========================================================

    all_company_filings = []

    for _, company in companies.iterrows():

        ticker = company["ticker"]
        cik = company["cik_str"]
        company_name = company["title"]

        print(f"Fetching filings for {ticker}...")

        filings = get_company_filings(
            cik=cik,
            ticker=ticker,
            company_name=company_name,
        )

        all_company_filings.append(filings)

    # ==========================================================
    # 3. Combine all companies
    # ==========================================================

    filings_df = pd.concat(
        all_company_filings,
        ignore_index=True,
    )

    # ==========================================================
    # 4. Convert dates
    # ==========================================================

    filings_df["filingDate"] = pd.to_datetime(
        filings_df["filingDate"]
    )

    filings_df["reportDate"] = pd.to_datetime(
        filings_df["reportDate"],
        errors="coerce",
    )

    # ==========================================================
    # 5. Filter by form
    # ==========================================================

    filings_df = filings_df[
        filings_df["form"].isin(FORMS)
    ]

    # ==========================================================
    # 6. Filter from 2023-01-01 to today
    # ==========================================================

    filings_df = filings_df[
        filings_df["filingDate"].between(
            START_DATE,
            END_DATE,
        )
    ]

    # ==========================================================
    # 7. Build primary filing document URL
    # ==========================================================

    filings_df["doc_url"] = filings_df.apply(
        build_document_url,
        axis=1,
    )

    # ==========================================================
    # 8. Keep useful columns
    # ==========================================================

    filings_df = filings_df[
        [
            "ticker",
            "company",
            "cik",
            "form",
            "filingDate",
            "reportDate",
            "accessionNumber",
            "primaryDocument",
            "doc_url",
        ]
    ]

    # ==========================================================
    # 9. Sort
    # ==========================================================

    filings_df = (
        filings_df
        .sort_values(
            ["ticker", "filingDate"],
            ascending=[True, False],
        )
        .reset_index(drop=True)
    )

    print(filings_df)

    # Optional
    filings_df.to_csv(
        "sec_filings_2023_present.csv",
        index=False,
    )
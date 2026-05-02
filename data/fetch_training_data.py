"""
fetch_training_data.py
----------------------
Fetches GitHub issues that already have difficulty labels assigned by
maintainers, then saves them to data/issues_labeled.csv for ML training.

Strategy to bypass the GitHub Search 1000-results-per-query cap:
  Each label is queried across 6 half-year date windows, giving up to
  6 x 1000 = 6,000 results per label instead of 1,000.

Usage:
    python data/fetch_training_data.py

Requirements:
    pip install requests python-dotenv
    Set GITHUB_TOKEN in your .env file.
"""

import csv
import os
import time
from http.client import RemoteDisconnected

import requests
from requests.exceptions import ConnectionError as RequestsConnectionError
from dotenv import load_dotenv

# -- Load .env from project root (one level up from data/) ------------------
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise EnvironmentError(
        "GITHUB_TOKEN is not set. Add it to your .env file and try again."
    )

# -- Output file -------------------------------------------------------------
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "issues_labeled.csv")

# -- Label -> difficulty mapping ---------------------------------------------
LABEL_GROUPS = {
    "beginner": [
        "good first issue",
        "good-first-issue",
        "beginner",
        "easy",
        "first timers only",
        "first-timers-only",
        "low-hanging-fruit",
        "newbie",
        "trivial",
    ],
    "intermediate": [
        "help wanted",
        "help-wanted",
        "moderate",
        "intermediate",
        "difficulty: medium",
    ],
    "advanced": [
        "hard",
        "difficulty: hard",
        "difficulty: high",
        "advanced",
        "complex",
        "expert",
    ],
}

# -- Date ranges to split queries and bypass the 1000-result cap -------------
DATE_RANGES = [
    "2024-07-01..2024-12-31",
    "2024-01-01..2024-06-30",
    "2023-07-01..2023-12-31",
    "2023-01-01..2023-06-30",
    "2022-07-01..2022-12-31",
    "2022-01-01..2022-06-30",
]

# -- API settings ------------------------------------------------------------
MAX_PAGES_PER_QUERY = 10        # 100 results x 10 pages = 1,000 per query
PER_PAGE = 100
DELAY_BETWEEN_REQUESTS = 2      # seconds between every API call
RATE_LIMIT_WAIT = 60            # seconds to wait on 403 / 429
NETWORK_ERROR_WAIT = 30         # seconds to wait on connection errors
NETWORK_MAX_RETRIES = 3         # max retries on connection errors
LOG_EVERY = 500                 # print progress every N issues

CSV_COLUMNS = [
    "title",
    "body",
    "labels",
    "repo_name",
    "issue_number",
    "difficulty_label",
    "url",
]


# -- Helpers -----------------------------------------------------------------

def make_headers() -> dict:
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def fetch_page(label: str, date_range: str, page: int) -> list[dict]:
    """
    Fetch one page of GitHub issues for a label + date range combination.
    - Retries up to NETWORK_MAX_RETRIES times on connection errors (30s wait).
    - Retries once on rate-limit responses 403/429 (60s wait).
    Returns a list of raw issue dicts, or [] on unrecoverable failure.
    """
    api_url = "https://api.github.com/search/issues"
    params = {
        "q": f'label:"{label}" created:{date_range} type:issue',
        "per_page": PER_PAGE,
        "page": page,
        "sort": "created",
        "order": "desc",
    }

    # -- Network-error retry loop -------------------------------------------
    for net_attempt in range(1, NETWORK_MAX_RETRIES + 1):
        try:
            response = requests.get(
                api_url, headers=make_headers(), params=params, timeout=30
            )
        except (RequestsConnectionError, RemoteDisconnected, Exception) as exc:
            print(
                f"  [NET ERROR] Attempt {net_attempt}/{NETWORK_MAX_RETRIES} - "
                f"{type(exc).__name__}. Waiting {NETWORK_ERROR_WAIT}s..."
            )
            time.sleep(NETWORK_ERROR_WAIT)
            continue  # retry

        # -- HTTP-level handling --------------------------------------------
        if response.status_code == 200:
            return response.json().get("items", [])

        if response.status_code in (403, 429):
            print(
                f"  [RATE LIMIT] HTTP {response.status_code}. "
                f"Waiting {RATE_LIMIT_WAIT}s before retry..."
            )
            time.sleep(RATE_LIMIT_WAIT)
            # Count rate-limit wait as a network attempt so we don't loop forever
            continue

        # Any other HTTP error - skip this page immediately
        print(
            f"  [HTTP ERROR] {response.status_code} for label='{label}' "
            f"range={date_range} page={page}. Skipping."
        )
        return []

    # All retries exhausted
    print(
        f"  [SKIP] Exhausted retries for label='{label}' "
        f"range={date_range} page={page}."
    )
    return []


def is_valid(issue: dict) -> bool:
    """Return True only if the issue passes the body/title quality filters."""
    title = (issue.get("title") or "").strip()
    body = (issue.get("body") or "").strip()
    return bool(title) and bool(body) and len(body) >= 100


def parse_issue(issue: dict, difficulty: str) -> dict:
    """Extract the CSV columns from a raw GitHub issue dict."""
    repo_url: str = issue.get("repository_url", "")
    repo_name = "/".join(repo_url.rstrip("/").split("/")[-2:]) if repo_url else ""
    label_names = ",".join(lb["name"] for lb in issue.get("labels", []))

    return {
        "title": issue["title"].strip(),
        "body": (issue.get("body") or "").strip(),
        "labels": label_names,
        "repo_name": repo_name,
        "issue_number": issue.get("number", ""),
        "difficulty_label": difficulty,
        "url": issue.get("html_url", ""),
    }


# -- Main --------------------------------------------------------------------

def main() -> None:
    counts = {d: 0 for d in LABEL_GROUPS}
    total = 0

    # Deduplicate by issue URL (more reliable than ID across label queries)
    seen_urls: set[str] = set()

    total_queries = sum(len(v) for v in LABEL_GROUPS.values()) * len(DATE_RANGES)
    print(f"\nTotal queries planned: {total_queries}  "
          f"({len(DATE_RANGES)} date ranges x "
          f"{sum(len(v) for v in LABEL_GROUPS.values())} labels)")
    print(f"Max possible results : {total_queries * MAX_PAGES_PER_QUERY * PER_PAGE:,}")
    print(f"Target               : 50,000+ unique issues\n")

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)
        writer.writeheader()

        for difficulty, labels in LABEL_GROUPS.items():
            print("\n" + "-" * 60)
            print(f"  Difficulty: {difficulty.upper()}  ({len(labels)} labels)")
            print("-" * 60)

            for label in labels:
                print(f"\n  Label: \"{label}\"")

                for date_range in DATE_RANGES:
                    print(f"    Date range: {date_range}")

                    for page in range(1, MAX_PAGES_PER_QUERY + 1):
                        raw_issues = fetch_page(label, date_range, page)

                        if not raw_issues:
                            # Empty page means no more results for this query
                            break

                        for issue in raw_issues:
                            issue_url: str = issue.get("html_url", "")

                            # Skip duplicates and low-quality issues
                            if issue_url in seen_urls or not is_valid(issue):
                                continue

                            seen_urls.add(issue_url)
                            row = parse_issue(issue, difficulty)
                            writer.writerow(row)
                            csv_file.flush()

                            counts[difficulty] += 1
                            total += 1

                            if total % LOG_EVERY == 0:
                                print(
                                    f"  [{difficulty.capitalize()}] "
                                    f"{counts[difficulty]:,} {difficulty} issues | "
                                    f"Total: {total:,}"
                                )

                        # Polite delay between every API request
                        time.sleep(DELAY_BETWEEN_REQUESTS)

    # -- Final summary -------------------------------------------------------
    print("\n" + "=" * 60)
    print("  DONE - Summary")
    print("=" * 60)
    print(f"  Total issues saved : {total:,}")
    print(f"  Beginner           : {counts['beginner']:,}")
    print(f"  Intermediate       : {counts['intermediate']:,}")
    print(f"  Advanced           : {counts['advanced']:,}")
    print(f"  Output file        : {OUTPUT_CSV}")
    print("=" * 60 + "\n")

    if total < 50_000:
        print(
            f"  [WARN] Only {total:,} issues collected - below the 50,000 target.\n"
            "     Consider extending DATE_RANGES to cover 2021 or 2020 as well.\n"
        )
    else:
        print(f"  [OK] Target of 50,000 reached! ({total:,} issues)\n")


if __name__ == "__main__":
    main()

"""
fetch_advanced_intermediate.py
-------------------------------
Appends more Intermediate and Advanced issues to the existing
data/issues_labeled.csv file.

Task 1 - More Intermediate issues
  Searches GitHub for issues with "help wanted" style labels across
  specific date ranges to bypass the 1,000-result cap.

Task 2 - Advanced issues
  Fetches issues directly from well-known complex repos using the
  GitHub Issues REST API (not search). Labels them "advanced".
  Filters out beginner-tagged issues and short/empty bodies.

Output
  Appends to data/issues_labeled.csv (same columns as existing file).
  Deduplicates by URL - skips any URL already in the CSV.

Usage:
    python data/fetch_advanced_intermediate.py

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

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Load .env from project root (one level up from data/)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise EnvironmentError(
        "GITHUB_TOKEN is not set. Add it to your .env file and try again."
    )

OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "issues_labeled.csv")

CSV_COLUMNS = [
    "title",
    "body",
    "labels",
    "repo_name",
    "issue_number",
    "difficulty_label",
    "url",
]

# -- Task 1: Intermediate search labels -------------------------------------
INTERMEDIATE_LABELS = [
    "help wanted",
    "help-wanted",
    "status: help wanted",
    "community help wanted",
]

# Date ranges to bypass the 1,000-result cap per query
INTERMEDIATE_DATE_RANGES = [
    "2024-01-01..2024-06-30",
    "2023-07-01..2023-12-31",
    "2023-01-01..2023-06-30",
    "2022-07-01..2022-12-31",
]

# -- Task 2: Advanced repos -------------------------------------------------
ADVANCED_REPOS = [
    "facebook/react",
    "vuejs/vue",
    "angular/angular",
    "laravel/laravel",
    "symfony/symfony",
    "python/cpython",
    "nodejs/node",
    "denoland/deno",
    "llvm/llvm-project",
    "opencv/opencv",
    "scikit-learn/scikit-learn",
    "huggingface/transformers",
    "elastic/elasticsearch",
    "redis/redis",
    "postgres/postgres",
    "mysql/mysql-server",
    "docker/docker-ce",
    "ansible/ansible",
    "hashicorp/terraform",
    "grafana/grafana",
    "prometheus/prometheus",
    "apache/spark",
    "apache/flink",
    "cockroachdb/cockroach",
    "etcd-io/etcd",
]

# Labels that mark an issue as NOT advanced
NON_ADVANCED_LABELS = {"good first issue", "good-first-issue", "help wanted", "help-wanted"}

# -- API settings -----------------------------------------------------------
PER_PAGE = 100
MAX_SEARCH_PAGES = 10           # 10 pages x 100 = 1,000 per label+date combo
ADVANCED_PAGES_PER_REPO = 8    # 8 pages x 100 = 800 per repo
DELAY_SECONDS = 2              # polite delay between every API call
RATE_LIMIT_WAIT = 60           # wait on 403 / 429
MAX_RETRIES = 3                # retries on network / rate-limit errors
LOG_EVERY = 100                # print progress every N issues


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_headers() -> dict:
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def safe_get(url: str, params: dict | None = None) -> requests.Response | None:
    """
    GET request with retry logic:
      - Up to MAX_RETRIES attempts total.
      - On 403/429: wait RATE_LIMIT_WAIT seconds, then retry.
      - On network error: wait 30 seconds, then retry.
      - On other HTTP errors: return the response immediately (caller handles).
    Returns the Response object, or None after all retries are exhausted.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=make_headers(), params=params, timeout=30)
        except (RequestsConnectionError, RemoteDisconnected, Exception) as exc:
            print(
                f"  [NET ERROR] Attempt {attempt}/{MAX_RETRIES} - "
                f"{type(exc).__name__}. Waiting 30s..."
            )
            time.sleep(30)
            continue

        if resp.status_code == 200:
            return resp

        if resp.status_code in (403, 429):
            print(
                f"  [RATE LIMIT] HTTP {resp.status_code}. "
                f"Waiting {RATE_LIMIT_WAIT}s before retry (attempt {attempt}/{MAX_RETRIES})..."
            )
            time.sleep(RATE_LIMIT_WAIT)
            continue

        # Non-retriable HTTP error
        print(f"  [HTTP ERROR] {resp.status_code} - {url}")
        return resp  # caller can check status_code

    print(f"  [SKIP] All {MAX_RETRIES} retries exhausted for {url}")
    return None


def is_valid_body(body: str | None) -> bool:
    """Return True if body is non-empty and >= 100 characters."""
    cleaned = (body or "").strip()
    return len(cleaned) >= 100


def parse_search_issue(issue: dict, difficulty: str) -> dict:
    """Extract CSV columns from a GitHub Search API issue dict."""
    repo_url: str = issue.get("repository_url", "")
    repo_name = "/".join(repo_url.rstrip("/").split("/")[-2:]) if repo_url else ""
    label_names = ",".join(lb["name"] for lb in issue.get("labels", []))
    return {
        "title": (issue.get("title") or "").strip(),
        "body": (issue.get("body") or "").strip(),
        "labels": label_names,
        "repo_name": repo_name,
        "issue_number": issue.get("number", ""),
        "difficulty_label": difficulty,
        "url": issue.get("html_url", ""),
    }


def parse_repo_issue(issue: dict, repo: str, difficulty: str) -> dict:
    """Extract CSV columns from a GitHub Issues REST API issue dict."""
    label_names = ",".join(lb["name"] for lb in issue.get("labels", []))
    return {
        "title": (issue.get("title") or "").strip(),
        "body": (issue.get("body") or "").strip(),
        "labels": label_names,
        "repo_name": repo,
        "issue_number": issue.get("number", ""),
        "difficulty_label": difficulty,
        "url": issue.get("html_url", ""),
    }


def load_existing_urls(csv_path: str) -> set[str]:
    """Read all existing URLs from the CSV so we can skip duplicates."""
    seen: set[str] = set()
    if not os.path.exists(csv_path):
        return seen
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get("url", "").strip()
            if url:
                seen.add(url)
    print(f"[INFO] Loaded {len(seen):,} existing URLs from {csv_path}")
    return seen


# ---------------------------------------------------------------------------
# Task 1 — Intermediate issues via GitHub Search API
# ---------------------------------------------------------------------------

def fetch_intermediate_issues(writer: csv.DictWriter, seen_urls: set[str]) -> int:
    """
    Search for issues with "help wanted" family labels across date ranges.
    Returns count of new intermediate issues added.
    """
    added = 0
    api_url = "https://api.github.com/search/issues"

    print("\n" + "=" * 60)
    print("  TASK 1 - Fetching INTERMEDIATE issues (help wanted labels)")
    print("=" * 60)

    for label in INTERMEDIATE_LABELS:
        print(f"\n  Label: \"{label}\"")
        for date_range in INTERMEDIATE_DATE_RANGES:
            print(f"    Date range: {date_range}")
            for page in range(1, MAX_SEARCH_PAGES + 1):
                params = {
                    "q": f'label:"{label}" created:{date_range} type:issue',
                    "per_page": PER_PAGE,
                    "page": page,
                    "sort": "created",
                    "order": "desc",
                }

                resp = safe_get(api_url, params=params)
                time.sleep(DELAY_SECONDS)

                if resp is None or resp.status_code != 200:
                    break  # skip to next date range

                items = resp.json().get("items", [])
                if not items:
                    break  # no more pages for this combo

                for issue in items:
                    url = issue.get("html_url", "")
                    if not url or url in seen_urls:
                        continue
                    body = issue.get("body") or ""
                    title = (issue.get("title") or "").strip()
                    if not title or not is_valid_body(body):
                        continue

                    seen_urls.add(url)
                    row = parse_search_issue(issue, "intermediate")
                    writer.writerow(row)
                    added += 1

                    if added % LOG_EVERY == 0:
                        print(f"    [Intermediate] {added:,} new issues added so far...")

    print(f"\n  >> INTERMEDIATE total added: {added:,}")
    return added


# ---------------------------------------------------------------------------
# Task 2 — Advanced issues via GitHub Issues REST API
# ---------------------------------------------------------------------------

def fetch_advanced_issues(writer: csv.DictWriter, seen_urls: set[str]) -> int:
    """
    Fetch up to 500 issues per repo (5 pages × 100) from well-known complex
    repos. Filters out beginner/help-wanted tagged issues and short bodies.
    Returns count of new advanced issues added.
    """
    added = 0

    print("\n" + "=" * 60)
    print("  TASK 2 - Fetching ADVANCED issues from major repos")
    print("=" * 60)

    for repo in ADVANCED_REPOS:
        repo_added = 0
        print(f"\n  Repo: {repo}")
        api_url = f"https://api.github.com/repos/{repo}/issues"

        for page in range(1, ADVANCED_PAGES_PER_REPO + 1):
            params = {
                "state": "all",
                "per_page": PER_PAGE,
                "page": page,
            }

            resp = safe_get(api_url, params=params)
            time.sleep(DELAY_SECONDS)

            if resp is None or resp.status_code != 200:
                print(f"    [WARN] Could not fetch page {page} for {repo}, stopping.")
                break

            items = resp.json()
            if not items:
                break

            for issue in items:
                # Skip pull requests (the Issues API includes PRs when state=all)
                if "pull_request" in issue:
                    continue

                url = issue.get("html_url", "")
                if not url or url in seen_urls:
                    continue

                # Filter out issues with beginner / help-wanted labels
                issue_label_names = {lb["name"].lower() for lb in issue.get("labels", [])}
                if issue_label_names & {l.lower() for l in NON_ADVANCED_LABELS}:
                    continue

                # Filter out empty or short bodies
                body = issue.get("body") or ""
                title = (issue.get("title") or "").strip()
                if not title or not is_valid_body(body):
                    continue

                seen_urls.add(url)
                row = parse_repo_issue(issue, repo, "advanced")
                writer.writerow(row)
                added += 1
                repo_added += 1

                if added % LOG_EVERY == 0:
                    print(f"    [Advanced] {added:,} new issues added so far...")

        print(f"    >> {repo}: {repo_added} advanced issues added")

    print(f"\n  >> ADVANCED total added: {added:,}")
    return added


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("\n" + "=" * 60)
    print("  fetch_advanced_intermediate.py - Starting")
    print("=" * 60)

    # Step 1: Load all existing URLs to avoid duplicates
    seen_urls = load_existing_urls(OUTPUT_CSV)
    initial_count = len(seen_urls)

    # Step 2: Open CSV in append mode and write new rows
    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)
        # No header — file already has one

        intermediate_added = fetch_intermediate_issues(writer, seen_urls)
        csv_file.flush()

        advanced_added = fetch_advanced_issues(writer, seen_urls)
        csv_file.flush()

    # Step 3: Final summary
    total_added = intermediate_added + advanced_added
    new_total = initial_count + total_added

    print("\n" + "=" * 60)
    print("  DONE - Final Summary")
    print("=" * 60)
    print(f"  Issues already in CSV  : {initial_count:,}")
    print(f"  New Intermediate added : {intermediate_added:,}")
    print(f"  New Advanced added     : {advanced_added:,}")
    print(f"  Total NEW added        : {total_added:,}")
    print(f"  New CSV total (approx) : {new_total:,}")
    print(f"  Output file            : {OUTPUT_CSV}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

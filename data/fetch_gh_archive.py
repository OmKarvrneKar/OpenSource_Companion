# ── fetch_gh_archive.py ──────────────────────────────────────────
# Fetches resolved GitHub issues from GH Archive via BigQuery API
# Saves raw data to data/raw/gh_archive_raw.csv
#
# SETUP (one time):
#   pip install google-cloud-bigquery pandas pyarrow
#   1. Go to https://console.cloud.google.com
#   2. Create a project (or use existing one)
#   3. Enable BigQuery API
#   4. Create a Service Account → download JSON key
#   5. Set GOOGLE_APPLICATION_CREDENTIALS in your .env
#
# USAGE:
#   python data/fetch_gh_archive.py
# ────────────────────────────────────────────────────────────────

import os
import sys
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Config ───────────────────────────────────────────────────────

GCP_PROJECT_ID   = os.getenv("GCP_PROJECT_ID")      # your GCP project ID
OUTPUT_DIR       = Path(__file__).parent / "raw"
OUTPUT_FILE      = OUTPUT_DIR / "gh_archive_raw.csv"
SQL_FILE         = Path(__file__).parent / "gh_archive_query.sql"
TARGET_ROWS      = 50_000


def check_credentials():
    """Verify GCP credentials are configured."""
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path:
        print("ERROR: GOOGLE_APPLICATION_CREDENTIALS not set in .env")
        print("  1. Go to https://console.cloud.google.com/iam-admin/serviceaccounts")
        print("  2. Create service account → download JSON key")
        print('  3. Add to .env: GOOGLE_APPLICATION_CREDENTIALS=path/to/key.json')
        sys.exit(1)
    if not Path(creds_path).exists():
        print(f"ERROR: Credentials file not found: {creds_path}")
        sys.exit(1)
    if not GCP_PROJECT_ID:
        print("ERROR: GCP_PROJECT_ID not set in .env")
        sys.exit(1)
    print(f"Credentials OK. Project: {GCP_PROJECT_ID}")


def fetch_from_bigquery() -> pd.DataFrame:
    """Run the SQL query on BigQuery and return results as DataFrame."""
    try:
        from google.cloud import bigquery
    except ImportError:
        print("ERROR: google-cloud-bigquery not installed")
        print("  Run: pip install google-cloud-bigquery pandas pyarrow")
        sys.exit(1)

    print("Connecting to BigQuery...")
    client = bigquery.Client(project=GCP_PROJECT_ID)

    # Read SQL from file
    sql = SQL_FILE.read_text()
    print(f"Running query (this may take 2-5 minutes)...")
    print(f"Targeting {TARGET_ROWS:,} rows")

    job_config = bigquery.QueryJobConfig(
        use_query_cache=True,         # cache results for repeated runs
    )

    query_job = client.query(sql, job_config=job_config)

    print("Query running... (check BigQuery console for progress)")
    df = query_job.to_dataframe()

    print(f"Query complete. Got {len(df):,} rows")
    return df


def save_raw(df: pd.DataFrame) -> None:
    """Save raw data to CSV."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    print(f"Saved raw data to: {OUTPUT_FILE}")
    print(f"File size: {OUTPUT_FILE.stat().st_size / 1024 / 1024:.1f} MB")


def print_summary(df: pd.DataFrame) -> None:
    """Print distribution summary."""
    print("\n── Dataset Summary ──────────────────────────────")
    print(f"Total rows:     {len(df):,}")
    print(f"Columns:        {list(df.columns)}")
    print(f"\nDifficulty distribution:")
    print(df["difficulty"].value_counts())
    print(f"\nMissing values:")
    print(df.isnull().sum())
    print(f"\nSample rows:")
    print(df[["title", "difficulty", "resolver_prior_prs"]].head(5))
    print("─────────────────────────────────────────────────")


if __name__ == "__main__":
    print("── GH Archive Fetcher ───────────────────────────")

    check_credentials()

    # Check if already fetched
    if OUTPUT_FILE.exists():
        size_mb = OUTPUT_FILE.stat().st_size / 1024 / 1024
        print(f"Raw file already exists ({size_mb:.1f} MB): {OUTPUT_FILE}")
        resp = input("Re-fetch? This will overwrite existing data. (y/N): ")
        if resp.lower() != "y":
            print("Skipping fetch. Run process_data.py to process existing raw data.")
            sys.exit(0)

    df = fetch_from_bigquery()
    save_raw(df)
    print_summary(df)

    print("\nNext step: python data/process_data.py")

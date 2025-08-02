#!/usr/bin/env python3
"""
Add referrer data to all existing article JSON files
"""

import json
import time
from pathlib import Path
from fetch_stats import DevToStatsFetcher

def add_referrers_to_all_articles():
    """Add referrer data to all existing article files"""

    # Get all article files
    article_files = list(Path("./data/articles").glob("*.json"))
    if not article_files:
        print("No article files found")
        return

    # Filter out backup files
    article_files = [f for f in article_files if not f.name.endswith('.backup')]

    print(f"Found {len(article_files)} article files to update")

    # Create fetcher instance
    fetcher = DevToStatsFetcher()

    updated_count = 0
    skipped_count = 0

    for i, article_file in enumerate(article_files, 1):
        try:
            # Extract article ID from filename
            article_id = int(article_file.stem.split("-")[0])

            print(f"[{i}/{len(article_files)}] Processing article {article_id} ({article_file.name})")

            # Load existing article data
            with open(article_file) as f:
                existing_data = json.load(f)

            # Check if referrers already exist
            if "referrers" in existing_data:
                print(f"  → Skipping (referrers already exist)")
                skipped_count += 1
                continue

            # Fetch referrer data
            referrers = fetcher.fetch_article_referrers(article_id)
            referrer_domains = referrers.get("domains", []) if referrers else []

            # Add referrers to existing data
            existing_data["referrers"] = referrer_domains

            # Save updated data
            with open(article_file, 'w') as f:
                json.dump(existing_data, f, indent=2)

            print(f"  → Updated with {len(referrer_domains)} referrer domains")
            updated_count += 1

            # Add a small delay to be respectful to the API
            time.sleep(0.5)

        except Exception as e:
            print(f"  → Error processing {article_file}: {e}")
            continue

    print(f"\nSummary:")
    print(f"  Updated: {updated_count} files")
    print(f"  Skipped: {skipped_count} files")
    print(f"  Total: {len(article_files)} files")

if __name__ == "__main__":
    add_referrers_to_all_articles()
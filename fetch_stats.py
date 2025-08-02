#!/usr/bin/env python3
"""
Python version of fetch_stats.sh
Fetches Dev.to article statistics and analytics data
"""

import os
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import sys
import argparse


class DevToStatsFetcher:
    def __init__(self, from_second_last_day=False):
        self.base_url = "https://dev.to/api"
        self.api_key = self._load_api_key()
        self.headers = {"api-key": self.api_key}
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.from_second_last_day = from_second_last_day
        self.username = None  # Will be set when fetching articles

        # Create data directories
        Path("./data/articles").mkdir(parents=True, exist_ok=True)

    def _load_api_key(self) -> str:
        """Load API key from .env file"""
        env_path = Path(".env")
        if not env_path.exists():
            print("Error: .env file not found")
            sys.exit(1)

        api_key = None
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("API_KEY="):
                    api_key = line.split("=", 1)[1].strip('"\'')
                elif line.startswith("DEVTO_API_KEY="):
                    api_key = line.split("=", 1)[1].strip('"\'')

        if not api_key:
            print("Error: Neither API_KEY nor DEVTO_API_KEY set in .env file")
            sys.exit(1)

        return api_key

    def fetch_article_analytics(self, article_id: int, start_date: str, end_date: str) -> Dict[str, Any]:
        """Fetch article analytics for a date range"""
        print(f"Fetching analytics for article {article_id} from {start_date} to {end_date}", file=sys.stderr)

        url = f"{self.base_url}/analytics/historical"
        params = {
            "start": start_date,
            "end": end_date,
            "article_id": article_id
        }

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching analytics for article {article_id}: {e}", file=sys.stderr)
            return {}
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON response for article {article_id}", file=sys.stderr)
            return {}

    def fetch_published_articles(self) -> List[Dict[str, Any]]:
        """Fetch all published articles"""
        print("Fetching published articles...")
        all_articles = []
        page = 1

        while True:
            url = f"{self.base_url}/articles/me/published"
            params = {"page": page, "per_page": 100}

            try:
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                articles = response.json()

                # Check for API error
                if isinstance(articles, dict) and "error" in articles:
                    print(f"API Error: {articles.get('error')}")
                    print(f"Status: {articles.get('status')}")
                    print("Please check your API key in the .env file")
                    print(f"Response: {articles}")
                    sys.exit(1)

                # Check if we got an empty array
                if not articles or len(articles) == 0:
                    break

                all_articles.extend(articles)

                # Capture username from first article if not already set
                if not self.username and articles and len(articles) > 0:
                    first_article = articles[0]
                    if 'user' in first_article and 'username' in first_article['user']:
                        self.username = first_article['user']['username']
                        print(f"Detected username: {self.username}")

                page += 1

            except requests.exceptions.RequestException as e:
                print(f"Error fetching articles: {e}")
                sys.exit(1)

        return all_articles

    def process_analytics_data(self, analytics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process analytics data into breakdown format"""
        breakdown = []
        for date, data in analytics.items():
            breakdown.append({
                "date": date,
                "views": data.get("page_views", {}).get("total", 0),
                "comments": data.get("comments", {}).get("total", 0),
                "reactions": data.get("reactions", {}).get("total", 0)
            })
        return sorted(breakdown, key=lambda x: x["date"])

    def get_next_date(self, date_str: str) -> str:
        """Get the next day from a date string"""
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        next_date = date_obj + timedelta(days=1)
        return next_date.strftime("%Y-%m-%d")

    def process_article(self, article: Dict[str, Any]) -> None:
        """Process a single article"""
        article_id = article["id"]
        slug = article["slug"]
        published_at = article["published_at"].split("T")[0]

        # Extract organization or username for URL construction
        article_org_username = None
        if 'organization' in article and article['organization']:
            article_org_username = article['organization']['slug']
        elif 'user' in article and article['user']:
            article_org_username = article['user']['username']

        file_path = Path(f"./data/articles/{article_id}-{slug}.json")

        # Check if article has been processed before
        if file_path.exists() and file_path.stat().st_size > 0:
            try:
                with open(file_path) as f:
                    existing_data = json.load(f)

                print(f"Updating existing article: {slug}")

                # Get the last date from breakdown to continue from the next day
                breakdown = existing_data.get("breakdown", [])
                if breakdown:
                    last_date = max(breakdown, key=lambda x: x["date"])["date"]

                    if self.from_second_last_day:
                        # Start from 2nd last day to refresh potentially incomplete data
                        last_date_obj = datetime.strptime(last_date, "%Y-%m-%d")
                        second_last_date = (last_date_obj - timedelta(days=1)).strftime("%Y-%m-%d")

                        # Remove the last day's data to refresh it
                        existing_data["breakdown"] = [item for item in breakdown if item["date"] != last_date]

                        next_date = second_last_date
                    else:
                        next_date = self.get_next_date(last_date)

                    # Only fetch if next_date is not in the future
                    if next_date <= self.today:
                        analytics = self.fetch_article_analytics(article_id, next_date, self.today)
                    else:
                        print(f"No new data needed for article {article_id} (up to date)", file=sys.stderr)
                        analytics = {}
                else:
                    analytics = self.fetch_article_analytics(article_id, published_at, self.today)

            except (json.JSONDecodeError, KeyError):
                print(f"Invalid existing file for {slug}, treating as new")
                analytics = self.fetch_article_analytics(article_id, published_at, self.today)
                existing_data = {"breakdown": []}
        else:
            print(f"Creating new article file: {slug}")
            analytics = self.fetch_article_analytics(article_id, published_at, self.today)
            existing_data = {"breakdown": []}

        # Process analytics data
        if analytics:
            new_breakdown = self.process_analytics_data(analytics)
        else:
            print(f"No analytics data for article {article_id}", file=sys.stderr)
            new_breakdown = []

        # Update breakdown data
        all_breakdown = existing_data.get("breakdown", []) + new_breakdown

        # Remove duplicates and sort by date
        unique_breakdown = {}
        for item in all_breakdown:
            unique_breakdown[item["date"]] = item

        final_breakdown = sorted(unique_breakdown.values(), key=lambda x: x["date"])

        # Calculate totals
        total_views = sum(item["views"] for item in final_breakdown)
        total_comments = sum(item["comments"] for item in final_breakdown)
        total_reactions = sum(item["reactions"] for item in final_breakdown)

        # Create article data
        article_data = {
            "title": article["title"],
            "views": total_views,
            "comments": total_comments,
            "reactions": total_reactions,
            "org_username": article_org_username,
            "breakdown": final_breakdown
        }

        # Save to file
        with open(file_path, "w") as f:
            json.dump(article_data, f, indent=2)

    def update_account_stats(self, articles: List[Dict[str, Any]]) -> None:
        """Update account.json with total statistics"""
        print("Updating account statistics...")

        total_articles = len(articles)
        total_views = 0
        total_comments = 0
        total_reactions = 0
        all_breakdowns = []

        # Process all article files
        for file_path in Path("./data/articles").glob("*.json"):
            if file_path.stat().st_size > 0:
                try:
                    with open(file_path) as f:
                        data = json.load(f)

                    total_views += data.get("views", 0)
                    total_comments += data.get("comments", 0)
                    total_reactions += data.get("reactions", 0)
                    all_breakdowns.extend(data.get("breakdown", []))

                except (json.JSONDecodeError, KeyError):
                    print(f"Skipping invalid JSON file: {file_path}")

        # Combine all breakdowns and aggregate by date
        date_aggregates = {}
        for item in all_breakdowns:
            date = item["date"]
            if date not in date_aggregates:
                date_aggregates[date] = {"date": date, "views": 0, "comments": 0, "reactions": 0}

            date_aggregates[date]["views"] += item["views"]
            date_aggregates[date]["comments"] += item["comments"]
            date_aggregates[date]["reactions"] += item["reactions"]

        combined_breakdown = sorted(date_aggregates.values(), key=lambda x: x["date"])

        # Create account data
        account_data = {
            "articles": total_articles,
            "views": total_views,
            "comments": total_comments,
            "reactions": total_reactions,
            "username": self.username,
            "breakdown": combined_breakdown
        }

        # Save account.json
        with open("./data/account.json", "w") as f:
            json.dump(account_data, f, indent=2)

    def create_top_articles(self) -> None:
        """Create top_articles.json"""
        print("Creating top articles rankings...")

        article_stats = []

        # Process all article files
        for file_path in Path("./data/articles").glob("*.json"):
            if file_path.stat().st_size > 0:
                try:
                    with open(file_path) as f:
                        data = json.load(f)

                    # Extract slug from filename
                    filename = file_path.stem
                    slug = "-".join(filename.split("-")[1:])  # Remove ID prefix

                    article_stats.append({
                        "slug": slug,
                        "title": data.get("title", slug.replace('-', ' ').title()),
                        "views": data.get("views", 0),
                        "reactions": data.get("reactions", 0),
                        "org_username": data.get("org_username")
                    })

                except (json.JSONDecodeError, KeyError):
                    print(f"Skipping invalid JSON file: {file_path}")

        # Create rankings (with stable sorting by slug as secondary key)
        top_articles = {
            "by_reaction": sorted(
                [{"slug": item["slug"], "title": item["title"], "reactions": item["reactions"], "org_username": item["org_username"]} for item in article_stats],
                key=lambda x: (-x["reactions"], x["slug"])
            ),
            "by_views": sorted(
                [{"slug": item["slug"], "title": item["title"], "views": item["views"], "org_username": item["org_username"]} for item in article_stats],
                key=lambda x: (-x["views"], x["slug"])
            )
        }

        # Save top_articles.json
        with open("./data/top_articles.json", "w") as f:
            json.dump(top_articles, f, indent=2)

    def run(self) -> None:
        """Main execution method"""
        try:
            # 1. Fetch all published articles
            articles = self.fetch_published_articles()

            # 2. Process each article
            print("Processing articles...")
            for article in articles:
                self.process_article(article)

            # 3. Update account statistics
            self.update_account_stats(articles)

            # 4. Create top articles rankings
            self.create_top_articles()

            print("Data fetching complete!")

        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fetch Dev.to article statistics')
    parser.add_argument('--from-second-last-day', action='store_true',
                       help='Start fetching from the 2nd last day to refresh potentially incomplete data')

    args = parser.parse_args()

    fetcher = DevToStatsFetcher(from_second_last_day=args.from_second_last_day)
    fetcher.run()
#!/usr/bin/env python3
"""
Generate SVG graphs for top 3 articles by views and reactions.
"""

import json
import sys
import argparse
from pathlib import Path


def load_top_articles_data():
    """Load the top_articles.json data."""
    try:
        with open('./data/top_articles.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: ./data/top_articles.json not found. Run fetch_stats.py first.")
        sys.exit(1)


def load_account_data():
    """Load the account.json data to get username."""
    try:
        with open('./data/account.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: ./data/account.json not found. Run fetch_stats.py first.")
        sys.exit(1)


def truncate_title(title, max_length=50):
    """Truncate title if needed."""
    if len(title) > max_length:
        return title[:max_length-3] + "..."
    return title


def generate_top_articles_svg(metric='views', count=3):
    """Generate SVG for top articles by specified metric."""
    data = load_top_articles_data()
    account_data = load_account_data()
    fallback_username = account_data.get('username')

    if metric == 'views':
        articles = data.get('by_views', [])[:count]
        color = "#2563eb"  # Blue
        title = f"Top {count} Articles by Views"
        unit = "views"
    else:  # reactions
        articles = data.get('by_reaction', [])[:count]
        color = "#7c3aed"  # Purple
        title = f"Top {count} Articles by Reactions"
        unit = "reactions"

    if not articles:
        print(f"No articles found for metric: {metric}")
        return ""

    # SVG dimensions
    width = 600
    height = 80 + (count * 80) + 40  # Header + bars + footer
    bar_height = 40
    bar_spacing = 80
    max_bar_width = 400

    # Find max value for scaling
    max_value = max(article[metric] for article in articles)

    svg_lines = [
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
        '<defs>',
        '<style>',
        '.title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 18px; font-weight: 600; fill: #24292e; }',
        '.article-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 14px; font-weight: 500; fill: #24292e; }',
        '.metric-value { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 12px; font-weight: 600; fill: #ffffff; }',
        '.rank { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 16px; font-weight: 700; fill: #6b7280; }',
        '.bar { rx: 4; ry: 4; }',
        '.bar:hover { opacity: 0.8; cursor: pointer; }',
        'a { text-decoration: none; }',
        'a:hover .article-title { fill: #0969da; text-decoration: underline; }',
        'a:hover .bar { opacity: 0.9; }',
        '</style>',
        '</defs>',
        '',
        f'<text x="30" y="35" class="title">{title}</text>',
        '',
    ]

    # Generate bars for each article
    for i, article in enumerate(articles):
        y_pos = 60 + (i * bar_spacing)
        value = article[metric]
        bar_width = (value / max_value) * max_bar_width if max_value > 0 else 0

        # Rank number
        svg_lines.append(f'<text x="15" y="{y_pos + 25}" class="rank">#{i+1}</text>')

        # Create clickable link group for the article
        # Use article-specific org_username, fallback to account username, then to slug-only
        article_org_username = article.get('org_username')
        if article_org_username:
            article_url = f"https://dev.to/{article_org_username}/{article['slug']}"
        elif fallback_username:
            article_url = f"https://dev.to/{fallback_username}/{article['slug']}"
        else:
            article_url = f"https://dev.to/{article['slug']}"  # Final fallback
        svg_lines.append(f'<a href="{article_url}" target="_blank">')

        # Article title
        article_title = truncate_title(article.get('title', article['slug'].replace('-', ' ').title()))
        svg_lines.append(f'<text x="50" y="{y_pos + 15}" class="article-title">{article_title}</text>')

        # Bar
        svg_lines.append(f'<rect x="50" y="{y_pos + 20}" width="{bar_width}" height="{bar_height}" fill="{color}" class="bar">')
        svg_lines.append(f'<title>{article_title}: {value:,} {unit} - Click to view article</title>')
        svg_lines.append('</rect>')

        # Value text on bar
        text_x = 60 if bar_width < 80 else 60 + bar_width - 70
        text_color = "#24292e" if bar_width < 80 else "#ffffff"
        svg_lines.append(f'<text x="{text_x}" y="{y_pos + 45}" class="metric-value" fill="{text_color}">{value:,} {unit}</text>')

        # Close link group
        svg_lines.append('</a>')

    svg_lines.append('</svg>')

    return '\n'.join(svg_lines)


def main():
    """Main function with command line arguments."""
    parser = argparse.ArgumentParser(description='Generate top articles SVG graphs')
    parser.add_argument('--metric', choices=['views', 'reactions'],
                       default='views', help='Metric to visualize')
    parser.add_argument('--count', type=int, default=3,
                       help='Number of top articles to show (default: 3)')
    parser.add_argument('--output', help='Output filename (auto-generated if not specified)')

    args = parser.parse_args()

    # Auto-generate output filename if not specified
    if not args.output:
        args.output = f'./graphs/top_{args.count}_{args.metric}.svg'

    svg_content = generate_top_articles_svg(
        metric=args.metric,
        count=args.count
    )

    if svg_content:
        # Ensure graphs directory exists
        Path('./graphs').mkdir(exist_ok=True)

        # Write to file
        with open(args.output, 'w') as f:
            f.write(svg_content)

        print(f"✅ Generated top articles graph: {args.output}")
    else:
        print("❌ Failed to generate graph")
        sys.exit(1)


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
Generate an advanced GitHub-style contribution graph with multiple metrics.
"""

import json
import datetime
from collections import defaultdict
import sys
import argparse
import math

def load_account_data():
    """Load the account.json data."""
    try:
        with open('./data/account.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: ./data/account.json not found. Run fetch_stats.sh first.")
        sys.exit(1)

def get_color_scheme(scheme_name):
    """Return color scheme based on name."""
    schemes = {
        'github': {
            0: "#ebedf0",  # No activity
            1: "#9be9a8",  # Low activity
            2: "#40c463",  # Medium activity
            3: "#30a14e",  # High activity
            4: "#216e39"   # Very high activity
        },
        'blue': {
            0: "#ebedf0",
            1: "#c6e48b",
            2: "#7bc96f",
            3: "#239a3b",
            4: "#196127"
        },
        'purple': {
            0: "#ebedf0",
            1: "#e1bee7",
            2: "#ba68c8",
            3: "#8e24aa",
            4: "#4a148c"
        },
        'orange': {
            0: "#ebedf0",
            1: "#fed7aa",
            2: "#fb923c",
            3: "#ea580c",
            4: "#c2410c"
        }
    }
    return schemes.get(scheme_name, schemes['github'])

def calculate_activity_level(day_data, metric, max_value):
    """Calculate activity level (0-4) based on selected metric using log scale."""
    if max_value == 0:
        return 0

    if metric == 'views':
        value = day_data['views']
    elif metric == 'comments':
        value = day_data['comments']
    elif metric == 'reactions':
        value = day_data['reactions']
    else:  # combined
        value = day_data['views'] + (day_data['comments'] * 5) + (day_data['reactions'] * 3)

    if value == 0:
        return 0

    # Use logarithmic scale for better distribution
    log_value = math.log10(value + 1)  # +1 to handle log(0)
    log_max = math.log10(max_value + 1)

    # Normalize to 1-4 scale using log values
    normalized = (log_value / log_max) * 4
    return min(4, max(1, int(normalized) + 1))

def generate_advanced_graph(metric='combined', color_scheme='github', show_stats=True):
    """Generate an advanced SVG contribution graph."""
    data = load_account_data()
    breakdown = data.get('breakdown', [])

    if not breakdown:
        print("No breakdown data found.")
        return

    # Create a dictionary of date -> activity data
    daily_data = {}
    max_value = 0

    for day in breakdown:
        date_str = day['date']
        views = day['views']
        comments = day['comments']
        reactions = day['reactions']

        daily_data[date_str] = {
            'views': views,
            'comments': comments,
            'reactions': reactions
        }

        # Calculate max value based on selected metric
        if metric == 'views':
            max_value = max(max_value, views)
        elif metric == 'comments':
            max_value = max(max_value, comments)
        elif metric == 'reactions':
            max_value = max(max_value, reactions)
        else:  # combined
            combined_score = views + (comments * 5) + (reactions * 3)
            max_value = max(max_value, combined_score)

    # Generate date range for the last year
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=364)

    # Adjust start_date to be a Sunday
    days_since_sunday = start_date.weekday() + 1
    if days_since_sunday == 7:
        days_since_sunday = 0
    start_date = start_date - datetime.timedelta(days=days_since_sunday)

    # SVG dimensions
    cell_size = 12
    cell_gap = 2
    weeks = 53
    days_per_week = 7

    width = weeks * (cell_size + cell_gap) + 150
    height = days_per_week * (cell_size + cell_gap) + 150

    colors = get_color_scheme(color_scheme)

    # Metric display names
    metric_names = {
        'views': 'Views',
        'comments': 'Comments',
        'reactions': 'Reactions',
        'combined': 'Combined Activity'
    }

    # Start building SVG
    svg_lines = [
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
        '<defs>',
        '<style>',
        '.day { stroke: rgba(27,31,35,0.06); stroke-width: 1px; cursor: pointer; }',
        '.day:hover { stroke: rgba(27,31,35,0.3); stroke-width: 2px; }',
        '.month-label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 10px; fill: #586069; }',
        '.day-label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 9px; fill: #586069; }',
        '.title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 16px; font-weight: 600; fill: #24292e; }',
        '.subtitle { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 12px; fill: #586069; }',
        '.stats { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 11px; fill: #586069; }',
        '.legend-text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 10px; fill: #586069; }',
        '</style>',
        '</defs>',
        '',
        f'<text x="20" y="25" class="title">dev.to Article Activity - {metric_names[metric]}</text>',
        f'<text x="20" y="45" class="subtitle">{data["articles"]} articles • {data["views"]:,} total views • {data["reactions"]} total reactions</text>',
        '',
        '<!-- Day labels -->',
        '<text x="10" y="80" class="day-label">Mon</text>',
        '<text x="10" y="102" class="day-label">Wed</text>',
        '<text x="10" y="124" class="day-label">Fri</text>',
        '',
    ]

    # Track months for labels
    month_positions = {}
    current_month = None

    # Generate the grid
    current_date = start_date
    week = 0
    total_active_days = 0

    while current_date <= end_date and week < weeks:
        for day in range(days_per_week):
            if current_date > end_date:
                break

            date_str = current_date.strftime('%Y-%m-%d')
            x = 30 + week * (cell_size + cell_gap)
            y = 65 + day * (cell_size + cell_gap)

            # Get activity data for this date
            day_data = daily_data.get(date_str, {'views': 0, 'comments': 0, 'reactions': 0})
            activity_level = calculate_activity_level(day_data, metric, max_value)

            if activity_level > 0:
                total_active_days += 1

            color = colors[activity_level]

            # Create detailed tooltip
            tooltip = f"{current_date.strftime('%B %d, %Y')}: {day_data['views']} views, {day_data['comments']} comments, {day_data['reactions']} reactions"

            svg_lines.append(
                f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" '
                f'fill="{color}" class="day" data-date="{date_str}" data-level="{activity_level}">'
                f'<title>{tooltip}</title></rect>'
            )

            # Track month changes for labels
            if current_date.day == 1:
                if current_date.month != current_month:
                    current_month = current_date.month
                    month_name = current_date.strftime('%b')
                    month_positions[month_name] = x

            current_date += datetime.timedelta(days=1)

        week += 1

    # Add month labels
    svg_lines.append('')
    svg_lines.append('<!-- Month labels -->')
    for month_name, x_pos in month_positions.items():
        svg_lines.append(f'<text x="{x_pos}" y="60" class="month-label">{month_name}</text>')

    # Add legend
    legend_y = height - 60
    svg_lines.extend([
        '',
        '<!-- Legend -->',
        f'<text x="30" y="{legend_y - 5}" class="legend-text">Less</text>',
    ])

    for i in range(5):
        x = 65 + i * (cell_size + 2)
        color = colors[i]
        svg_lines.append(f'<rect x="{x}" y="{legend_y - 15}" width="{cell_size}" height="{cell_size}" fill="{color}" class="day"></rect>')

    svg_lines.append(f'<text x="{65 + 5 * (cell_size + 2) + 5}" y="{legend_y - 5}" class="legend-text">More</text>')

    # Add summary stats if requested
    if show_stats:
        svg_lines.extend([
            '',
            f'<text x="30" y="{legend_y + 15}" class="stats">{total_active_days} days with activity in the last year</text>',
        ])

    svg_lines.append('</svg>')

    return '\n'.join(svg_lines)

def main():
    """Main function with command line arguments."""
    parser = argparse.ArgumentParser(description='Generate dev.to contribution graph')
    parser.add_argument('--metric', choices=['views', 'comments', 'reactions', 'combined'],
                       default='combined', help='Metric to visualize')
    parser.add_argument('--color', choices=['github', 'blue', 'purple', 'orange'],
                       default='github', help='Color scheme')
    parser.add_argument('--no-stats', action='store_true', help='Hide statistics')
    parser.add_argument('--output', default='./graphs/devto_advanced_graph.svg', help='Output filename')

    args = parser.parse_args()

    svg_content = generate_advanced_graph(
        metric=args.metric,
        color_scheme=args.color,
        show_stats=not args.no_stats
    )

    # Write to file
    with open(args.output, 'w') as f:
        f.write(svg_content)

    print(f"✅ Generated advanced contribution graph: {args.output}")
    print("🎨 Open the SVG file in a browser to view your dev.to activity!")

if __name__ == '__main__':
    main()
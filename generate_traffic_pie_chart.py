#!/usr/bin/env python3
"""
Generate SVG pie chart for dev.to traffic sources
"""

import json
import math
import argparse
from datetime import datetime

def load_account_data():
    """Load account data with referrer information"""
    try:
        with open('./data/account.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: account.json not found. Run fetch_stats.py first.")
        return None

def get_top_referrers(referrers, count=10):
    """Get top N referrers with distinct colors"""
    # Color palette with good contrast
    colors = [
        '#1f77b4',  # Blue
        '#ff7f0e',  # Orange
        '#2ca02c',  # Green
        '#d62728',  # Red
        '#9467bd',  # Purple
        '#8c564b',  # Brown
        '#e377c2',  # Pink
        '#7f7f7f',  # Gray
        '#bcbd22',  # Olive
        '#17becf',  # Cyan
        '#aec7e8',  # Light Blue
        '#ffbb78',  # Light Orange
    ]
    
    # Sort referrers by count and take top N
    sorted_referrers = sorted(referrers, key=lambda x: x['count'], reverse=True)
    top_referrers = sorted_referrers[:count]
    
    # Add colors and format domain names
    for i, referrer in enumerate(top_referrers):
        referrer['color'] = colors[i % len(colors)]
        # Format domain name for display
        if referrer['domain'] is None:
            referrer['display_name'] = 'Direct Traffic'
        else:
            referrer['display_name'] = referrer['domain']
    
    return top_referrers

def create_pie_chart_svg(referrers, total_views, output_file='graphs/traffic_sources_pie.svg'):
    """Generate SVG pie chart for traffic sources"""
    
    # SVG dimensions
    width = 1000
    height = 600
    center_x = 300
    center_y = 300
    radius = 180
    
    # Calculate total views from top referrers
    top_views = sum(r['count'] for r in referrers)
    
    # Calculate angles for each referrer
    angles = []
    current_angle = 0
    
    for referrer in referrers:
        percentage = (referrer['count'] / total_views) * 100
        angle = (referrer['count'] / total_views) * 360
        angles.append({
            'domain': referrer['domain'],
            'display_name': referrer['display_name'],
            'count': referrer['count'],
            'percentage': percentage,
            'start_angle': current_angle,
            'end_angle': current_angle + angle,
            'color': referrer['color']
        })
        current_angle += angle
    
    # Start building SVG
    svg_parts = []
    svg_parts.append(f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <style>
            .title {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-size: 24px; font-weight: 600; fill: #1f2937; }}
            .subtitle {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-size: 14px; fill: #6b7280; }}
            .legend-text {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-size: 14px; fill: #374151; font-weight: 500; }}
            .legend-percentage {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-size: 13px; fill: #6b7280; }}
            .slice {{ cursor: pointer; }}
            .slice:hover {{ opacity: 0.8; }}
        </style>
    </defs>
    
    <!-- Title -->
    <text x="{width//2}" y="30" text-anchor="middle" class="title">Top Traffic Sources</text>
    <text x="{width//2}" y="50" text-anchor="middle" class="subtitle">Top {len(referrers)} sources: {top_views:,} views ({(top_views/total_views)*100:.1f}% of {total_views:,} total)</text>
    ''')
    
    # Draw pie slices
    for angle_data in angles:
        start_angle_rad = math.radians(angle_data['start_angle'] - 90)  # -90 to start from top
        end_angle_rad = math.radians(angle_data['end_angle'] - 90)
        
        # Calculate arc path
        x1 = center_x + radius * math.cos(start_angle_rad)
        y1 = center_y + radius * math.sin(start_angle_rad)
        x2 = center_x + radius * math.cos(end_angle_rad)
        y2 = center_y + radius * math.sin(end_angle_rad)
        
        # Large arc flag
        large_arc = 1 if (angle_data['end_angle'] - angle_data['start_angle']) > 180 else 0
        
        # Create path
        path = f"M {center_x} {center_y} L {x1} {y1} A {radius} {radius} 0 {large_arc} 1 {x2} {y2} Z"
        
        # Escape display name for XML
        display_name_escaped = angle_data['display_name'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        svg_parts.append(f'''    <path d="{path}" fill="{angle_data['color']}" class="slice">
        <title>{display_name_escaped}: {angle_data['count']:,} views ({angle_data['percentage']:.1f}%)</title>
    </path>''')
    
    # Draw legend
    legend_x = 550
    legend_y = 120
    legend_item_height = 30
    
    svg_parts.append('    <!-- Legend -->')
    svg_parts.append(f'    <text x="{legend_x}" y="{legend_y - 20}" class="legend-text" style="font-size: 16px; font-weight: 600;">Traffic Sources</text>')
    
    for i, angle_data in enumerate(angles):
        y_pos = legend_y + i * legend_item_height
        
        # Legend color box
        svg_parts.append(f'    <rect x="{legend_x}" y="{y_pos - 12}" width="18" height="18" fill="{angle_data["color"]}" rx="3"/>')
        
        # Legend text
        display_name_escaped = angle_data['display_name'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        svg_parts.append(f'    <text x="{legend_x + 28}" y="{y_pos}" class="legend-text">{display_name_escaped}</text>')
        svg_parts.append(f'    <text x="{legend_x + 28}" y="{y_pos + 15}" class="legend-percentage">{angle_data["count"]:,} views ({angle_data["percentage"]:.1f}%)</text>')
    
    # Add generation timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    svg_parts.append(f'    <text x="{width - 10}" y="{height - 10}" text-anchor="end" class="legend-percentage">Generated: {timestamp}</text>')
    
    svg_parts.append('</svg>')
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(svg_parts))
    
    print(f"✅ Traffic sources pie chart saved to {output_file}")
    
    # Print summary
    print(f"\n📊 Top Traffic Sources Summary:")
    print(f"Total Views: {total_views:,}")
    print(f"Top {len(referrers)} Sources: {top_views:,} ({(top_views/total_views)*100:.1f}%)")
    print("-" * 50)
    for angle_data in angles:
        print(f"{angle_data['display_name']:<25} {angle_data['count']:>6,} ({angle_data['percentage']:>5.1f}%)")

def main():
    parser = argparse.ArgumentParser(description='Generate traffic sources pie chart')
    parser.add_argument('--output', default='graphs/traffic_sources_pie.svg', 
                       help='Output SVG file path (default: graphs/traffic_sources_pie.svg)')
    parser.add_argument('--count', type=int, default=10,
                       help='Number of top referrers to show (default: 10)')
    
    args = parser.parse_args()
    
    # Load data
    account_data = load_account_data()
    if not account_data:
        return
    
    if 'referrers' not in account_data:
        print("Error: No referrer data found. Run fetch_stats.py to collect referrer data.")
        return
    
    # Get top referrers
    top_referrers = get_top_referrers(account_data['referrers'], args.count)
    
    # Generate pie chart
    create_pie_chart_svg(top_referrers, account_data['views'], args.output)

if __name__ == '__main__':
    main()

# 📊 dev.to Article Activity Graphs

> 🤖 This entire project was created by [Kiro IDE](https://kiro.dev/) - an AI-powered development environment

GitHub-style contribution graphs for your dev.to article analytics

This repository fetches your article statistics on dev.to weekly via its v1 API and generates beautiful visualizations of your writing activity.

## 📈 Views Activity
Shows daily article views with GitHub's classic green color scheme

![Views Graph](graphs/devto_views_graph.svg)

## 💜 Reactions Activity
Shows daily article reactions (likes, unicorns, bookmarks) with purple color scheme

![Reactions Graph](graphs/devto_reactions_graph.svg)

## 🔥 Combined Activity
Shows weighted combined activity (views + comments×5 + reactions×3) with orange color scheme

![Combined Graph](graphs/devto_combined_graph.svg)

## 🏆 Top Articles by Views
Shows your top 3 most viewed articles

![Top Views](graphs/top_3_views.svg)

## ⭐ Top Articles by Reactions
Shows your top 3 most reacted articles

![Top Reactions](graphs/top_3_reactions.svg)

## 🛠 Usage

Generate custom graphs with different metrics and color schemes:

```bash
# Activity graphs (GitHub-style contribution graphs)
python3 generate_advanced_graph.py --metric views --color github
python3 generate_advanced_graph.py --metric reactions --color purple
python3 generate_advanced_graph.py --metric comments --color blue
python3 generate_advanced_graph.py --metric combined --color orange

# Top articles graphs
python3 generate_top_articles.py --metric views --count 3
python3 generate_top_articles.py --metric reactions --count 5
```

**Activity graph options:**
- `--metric`: views, comments, reactions, combined
- `--color`: github, blue, purple, orange
- `--output`: custom filename
- `--no-stats`: hide statistics

**Top articles options:**
- `--metric`: views, reactions
- `--count`: number of top articles to show (default: 3)
- `--output`: custom filename

**Update data:**
```bash
./fetch_stats.sh
```

## Data Structure

The application stores data in the following structure:
- `./data/articles/{id}-{slug}.json` - Individual article statistics
- `./data/account.json` - Account-wide statistics
- `./data/top_articles.json` - Top performing articles by metrics

## API Endpoints

The application uses the following dev.to API endpoints:
- `/analytics/historical` - Historical analytics data for articles
- `/analytics/referrers` - Referrer data for articles
- `/articles/me/published` - List of published articles
- `/articles/{username}/{slug}` - Individual article details

## Procedures

1. List all published articles of the API key's user
2. For each article,
   - If it has been processed before (i.e. ./data/articles/{slug}.json exists), locate the 2nd last date in "breakdown", use the analytics and referrer APIs to update the `.breakdown` array with the new data.
   - If it has not been processed before, create a new file with the article's ID and slug, and fetch the analytics and referrer data to populate the file. Start from the day when the article was published.
3. Update the `./data/account.json` file with the total statistics of the user.

## Setup

### Local Setup
1. Copy `.env.example` to `.env` and add your dev.to API key
2. Run `python fetch_stats.py` to collect your article data
3. Generate visualizations with the Python scripts above

### Automated Daily Updates (GitHub Actions)

This repository includes a GitHub Actions workflow that automatically updates your stats daily.

**Setup:**
1. Fork this repository
2. Go to your repository's Settings → Secrets and variables → Actions
3. Add a new repository secret:
   - Name: `DEVTO_API_KEY`
   - Value: Your dev.to API key
4. The workflow will run daily at 6 AM UTC and update your graphs

**Features:**
- Runs daily to keep your stats current
- Starts from the 2nd last day to refresh potentially incomplete data
- Automatically commits and pushes updated graphs
- Can be manually triggered from the Actions tab

**Manual trigger:**
Go to Actions → "Update Dev.to Stats" → "Run workflow" to update immediately.
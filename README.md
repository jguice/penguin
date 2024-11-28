# 🐧 Slack Search Scraper

A Python tool for scraping Slack search results and saving them to a file. Built with Playwright for reliable web automation.

## ✨ Features

- 🔍 Search across your Slack workspace and export results
- 💾 Automatically saves messages as they're found
- 🔐 Handles authentication seamlessly (saves auth state after first login)
- ⏱️ Smart timeout handling for partial result pages
- 🛟 Graceful interrupt handling (Ctrl+C safe)
- 📝 Exports messages in text format
- 🧊 Cool as ice - gentle scrolling for reliable data collection
- 🐠 Goes fishing for those hard-to-find messages

## Installation

1. Clone the repository:
```bash
git clone https://github.com/jguice/penguin.git
cd penguin
```

2. Install Poetry (if you haven't already):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

3. Install dependencies:
```bash
poetry install
poetry run playwright install
```

## Usage

Basic usage:
```bash
poetry run python slack_search_scraper.py "your search query"
```

All available options:
```bash
poetry run python slack_search_scraper.py [options] "search query"

Options:
  --workspace WORKSPACE  Slack workspace URL (default: https://app.slack.com/client)
  --format {text,json}  Output format (default: text)
  --output OUTPUT       Output file (default: slack_export_[timestamp].txt)
  --auth-file AUTH_FILE Path to save/load authentication (default: slack_auth.json)
  --verbose            Enable verbose debug output
  -h, --help           Show this help message and exit
```

Example with options:
```bash
poetry run python slack_search_scraper.py --format json --output my_search.json "from:@user after:2023-01-01"
```

### First Run Authentication
On first run, you'll need to log in to your Slack workspace. The script will:
1. Open a browser window
2. Navigate to Slack's login page
3. Wait for you to complete authentication
4. Save the authentication state for future runs

After the first successful login, authentication will be automatic for subsequent runs.

### Search Query Notes
**Important**: Slack's search interface applies its own autocomplete/query processing. This means:
- Queries with spaces might be modified by Slack's autocomplete
- The actual search performed might differ from your exact input
- You may need to adjust your query to achieve the desired search
- Slack limits search results to 100 pages (~2000 messages), so for large exports you may need multiple runs with different date ranges

For example, searching for "John Smith" might be processed differently than expected. Try variations or check Slack's web interface to see how your query is interpreted.

**Tip**: For large exports, break up your search into smaller date ranges:
```bash
# Example: Export messages for each quarter
poetry run python slack_search_scraper.py "from:@user after:2023-01-01 before:2023-04-01"
poetry run python slack_search_scraper.py "from:@user after:2023-04-01 before:2023-07-01"
```

## 📦 Output
Results are saved to a text file with a timestamp in the filename:
- Format: `slack_export_YYYYMMDD_HHMMSS.txt`

## Development

This project uses:
- [Conventional Commits](https://www.conventionalcommits.org/) for commit messages
- Semantic versioning
- GitHub Actions for CI/CD

### Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/jguice/penguin/blob/main/LICENSE) file for details.

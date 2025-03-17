# Trustbud Reddit Scraper

Automated Reddit data collector for Trustbud, focusing on THCA-related subreddits.

## Features

- Collects posts and comments from r/CultoftheFranklin, r/thca, and other relevant subreddits
- Performs sentiment analysis on posts and comments
- Extracts vendor and product information
- Stores data in Supabase for real-time access
- Updates every 4 hours for new content

## Setup

### Prerequisites

- Python 3.11+
- Reddit API credentials
- Supabase project

### Environment Variables

Create a `.env` file with:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
```

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the scraper
python src/scraper.py
```

## Deployment

This project is deployed on Railway. To deploy your own instance:

1. Fork this repository
2. Connect your Railway account
3. Set up environment variables in Railway
4. Deploy!

## Contributing

Pull requests are welcome. For major changes, please open an issue first.

## License

MIT
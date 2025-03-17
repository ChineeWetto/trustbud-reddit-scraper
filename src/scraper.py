import os
import praw
import pandas as pd
from datetime import datetime, timezone
from supabase import create_client, Client
from textblob import TextBlob
import schedule
import time
import re
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

# Initialize Reddit client
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent="trustbud_data_collector v1.0 (by /u/your_username)"
)

SUBREDDITS = ["CultoftheFranklin", "thca", "cultofcannabis"]

def extract_sentiment(text: str) -> float:
    """Extract sentiment score from text using TextBlob."""
    try:
        blob = TextBlob(text)
        return blob.sentiment.polarity
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {e}")
        return 0.0

def extract_vendor_name(text: str) -> str:
    """Extract vendor name from text using regex patterns."""
    patterns = [
        r"(?i)vendor[:\s]+([A-Za-z0-9\s\-\_\.]+)",
        r"(?i)from\s+([A-Za-z0-9\s\-\_\.]+)",
        r"(?i)ordered\s+from\s+([A-Za-z0-9\s\-\_\.]+)"
    ]
    
    for pattern in patterns:
        try:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        except Exception as e:
            logger.error(f"Error in vendor extraction: {e}")
    return None

def process_post(post) -> dict:
    """Process a Reddit post and extract relevant information."""
    try:
        return {
            "reddit_id": post.id,
            "subreddit": post.subreddit.display_name,
            "title": post.title,
            "content": post.selftext,
            "author": str(post.author),
            "url": f"https://reddit.com{post.permalink}",
            "created_utc": datetime.fromtimestamp(post.created_utc, tz=timezone.utc),
            "score": post.score,
            "upvote_ratio": post.upvote_ratio,
            "num_comments": post.num_comments,
            "post_type": "review" if any(word in post.title.lower() for word in ["review", "experience"]) else "discussion",
            "sentiment_score": extract_sentiment(f"{post.title} {post.selftext}"),
            "extracted_vendor_name": extract_vendor_name(f"{post.title} {post.selftext}"),
            "processed": False
        }
    except Exception as e:
        logger.error(f"Error processing post {post.id}: {e}")
        return None

def scrape_subreddit_data(subreddit_name: str, limit: int = None):
    """Scrape data from a subreddit and store in Supabase."""
    try:
        logger.info(f"Starting scrape of r/{subreddit_name}")
        subreddit = reddit.subreddit(subreddit_name)
        
        for post in subreddit.new(limit=limit):
            try:
                # Check if post already exists
                existing = supabase.table("reddit_posts").select("id").eq("reddit_id", post.id).execute()
                
                if not existing.data:
                    post_data = process_post(post)
                    if post_data:
                        supabase.table("reddit_posts").insert(post_data).execute()
                        logger.info(f"Inserted post {post.id} from r/{subreddit_name}")
            except Exception as e:
                logger.error(f"Error processing individual post: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error scraping subreddit {subreddit_name}: {e}")

def update_existing_posts():
    """Update scores and comments for existing posts."""
    try:
        logger.info("Starting update of existing posts")
        posts = supabase.table("reddit_posts").select("*").execute()
        
        for post_data in posts.data:
            try:
                post = reddit.submission(id=post_data["reddit_id"])
                supabase.table("reddit_posts").update({
                    "score": post.score,
                    "num_comments": post.num_comments,
                    "upvote_ratio": post.upvote_ratio
                }).eq("reddit_id", post.id).execute()
                logger.info(f"Updated post {post.id}")
            except Exception as e:
                logger.error(f"Error updating post {post_data['reddit_id']}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error in update_existing_posts: {e}")

def check_environment():
    """Check if all required environment variables are set."""
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

def main():
    """Main function to run the scraper."""
    logger.info("Starting Reddit scraper")
    
    # Initial scrape of historical data
    for subreddit in SUBREDDITS:
        scrape_subreddit_data(subreddit, limit=100)  # Start with fewer posts for testing
    
    # Schedule regular updates
    schedule.every(4).hours.do(lambda: [scrape_subreddit_data(sub, limit=25) for sub in SUBREDDITS])
    schedule.every(6).hours.do(update_existing_posts)
    
    logger.info("Scraper scheduled, entering main loop")
    
    # Keep the script running
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(300)  # Wait 5 minutes before retrying

if __name__ == "__main__":
    try:
        check_environment()
        main()
    except Exception as e:
        logger.critical(f"Critical error: {e}")
        raise
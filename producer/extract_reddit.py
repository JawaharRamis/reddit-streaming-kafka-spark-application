import praw
import os
from dotenv import load_dotenv

load_dotenv()

def initialize_reddit():
    # Initialize the Reddit instance
    return praw.Reddit(
        client_id= os.getenv("REDDIT_APP_ID"),
        client_secret=os.getenv("REDDIT_APP_SECRET"),
        user_agent=os.getenv("REDDIT_APP_AGENT")
    )
    
def collect_submission_details(subreddit_name):
    reddit = initialize_reddit()
    subreddit = reddit.subreddit(subreddit_name)

    submission_details = []
    for submission in subreddit.hot(limit=10):
        submission_info = {
        "id": submission.id,
        "title": submission.title,
        "author": submission.author.name,
        "post_time": submission.created_utc,
        "upvotes": submission.ups,
        "downvotes": submission.downs,
        "num_comments": submission.num_comments,
        "score": submission.score,
        "comment_karma": 0,
        "first_level_comments_count": 0,
        "second_level_comments_count": 0,
        }

        # Retrieve redditor's karma breakdown
        if submission.author:
            redditor = reddit.redditor(submission.author.name)
            submission_info["comment_karma"] = redditor.comment_karma
            
        # Count first level comments
        submission_info["first_level_comments_count"] = len(submission.comments)
    
        # Count second level comments
        submission.comments.replace_more(limit=None)
        for top_level_comment in submission.comments:
            submission_info["second_level_comments_count"] += len(top_level_comment.replies)

        submission_details.append(submission_info)
    
    return submission_details

def collect_subreddit_details(subreddit_name):
    reddit = initialize_reddit()
    subreddit = reddit.subreddit(subreddit_name)
    
    rules = []
    for rule in subreddit.rules:
        # rule_dict = {
        #     "short_name": rule.short_name,
        #     "description": rule.description,
        #     # Add other relevant attributes here
        # }
        rules.append(rule.short_name)
    subreddit_info = {
    "name": subreddit.display_name,
    "subscribers": subreddit.subscribers,
    "active_users": subreddit.active_user_count,
    "description": subreddit.description,
    "created_utc": subreddit.created_utc,
    "url": subreddit.url,
    "nsfw": subreddit.over18,
    "rules": rules
    }
    return subreddit_info
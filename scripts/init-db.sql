DROP TABLE IF EXISTS public.reddit_analysis_results;

CREATE TABLE public.reddit_analysis_results (
    batch_id FLOAT PRIMARY KEY,
    most_upvoted_author TEXT,
    higher_downvotes_title TEXT,
    most_num_comments_title TEXT,
    highest_score_title TEXT,
    highest_comment_karma_author TEXT
);

DROP TABLE IF EXISTS public.reddit_submission_data;

CREATE TABLE public.reddit_submission_data (
    timestamp TIMESTAMP,
    id VARCHAR(255),
    title VARCHAR(255),
    author VARCHAR(255),
    post_time BIGINT,
    upvotes INT,
    downvotes INT,
    num_comments INT,
    score INT,
    comment_karma INT,
    first_level_comments_count INT,
    second_level_comments_count INT
);

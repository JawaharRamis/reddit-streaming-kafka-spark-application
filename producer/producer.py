from confluent_kafka import Producer
# from kafka import KafkaProducer
import os
import json
from dotenv import load_dotenv
load_dotenv()
import time
from extract_reddit import collect_submission_details, collect_subreddit_details
from logs.logger import setup_logger

def main():
    # Kafka Producer Configuration
    kafka_bootstrap_servers = "localhost:9094"
    kafka_config = {
        "bootstrap.servers": kafka_bootstrap_servers,
    }
    producer = Producer(kafka_config)
    
    while True:
        try:
            submission_details = collect_submission_details(os.getenv("SUBREDDIT_NAME"))   
            for submission_info in submission_details:
                message = json.dumps(submission_info)
                producer.produce("reddit-submissions", message.encode("utf-8"))
                producer.poll(10)  # Poll to handle delivery reports
            producer.flush()

            submission_details = collect_subreddit_details(os.getenv("SUBREDDIT_NAME"))
            message = json.dumps(submission_details)
            producer.produce("reddit-subreddit", message.encode("utf-8"))
            producer.poll(0)  # Poll to handle delivery reports
            producer.flush()

            logger.info("Produced subreddit details")
        except Exception as e:
            logger.error("An error occurred while retrieving from reddit: %s", str(e))
        
        logger.info("Production done, sleeping for 60 seconds...")
        time.sleep(30)
        logger.info("Starting over again") 

if __name__ == "__main__":
    logger = setup_logger(__name__, 'producer.log')
    main()



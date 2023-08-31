import sys
# append the path of the parent directory
sys.path.append("/app")


from pyspark.sql import SparkSession, Row
from pyspark.sql.window import Window
from pyspark.sql.functions import *
from pyspark.sql.types import *
import psycopg2
from logs.logger import setup_logger
import findspark
findspark.init()

KAFKA_TOPIC_NAME = "reddit-submissions"
KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"
postgresql_properties  = {
    "user": "admin",
    "password": "admin",
    "driver": "org.postgresql.Driver"
}

scala_version = '2.12'
spark_version = '3.3.3'
packages = [
    f'org.apache.spark:spark-sql-kafka-0-10_{scala_version}:{spark_version}',
    'org.apache.kafka:kafka-clients:2.8.1'
]

def process_batch(batch_df, batch_id):
    logger.info("Processing the batch with ID: %s", batch_id)
    
    try:
        connection = psycopg2.connect(
            host='postgresql',
            port=5432,
            dbname='reddit-postgres',
            user='admin',
            password='admin'
        )
        batch_df.write.jdbc(
                    url="jdbc:postgresql://postgresql:5432/reddit-postgres",
                    table="public.reddit_submission_data",
                    mode="append",
                    properties=postgresql_properties
                )
        # Find the most upvoted author
        most_upvoted_author = (
            batch_df.groupBy("author")
            .agg(max("upvotes").alias("max_upvotes"))
            .orderBy(desc("max_upvotes"))
            .limit(1)
            .collect()
        )
        most_upvoted_author = most_upvoted_author[0]["author"] if most_upvoted_author else None

        # Find the post title with higher downvotes
        higher_downvotes_title = (
            batch_df.orderBy(desc("downvotes"))
            .select("title")
            .limit(1)
            .collect()
        )
        higher_downvotes_title = higher_downvotes_title[0]["title"] if higher_downvotes_title else None

        # Find the title with the most num_comments
        most_num_comments_title = (
            batch_df.orderBy(desc("num_comments"))
            .select("title")
            .limit(1)
            .collect()
        )
        most_num_comments_title = most_num_comments_title[0]["title"] if most_num_comments_title else None

        # Find the title with the highest score
        highest_score_title = (
            batch_df.orderBy(desc("score"))
            .select("title")
            .limit(1)
            .collect()
        )
        highest_score_title = highest_score_title[0]["title"] if highest_score_title else None

        # Find the author with the highest comment karma
        highest_comment_karma_author = (
            batch_df.groupBy("author", "comment_karma")
            .agg(col("author"), col("comment_karma"))
            .orderBy(desc("comment_karma"))
            .limit(1)
            .collect()
        )
        highest_comment_karma_author = (
            highest_comment_karma_author[0]["author"]
            if highest_comment_karma_author
            else None
        )

        logger.info(
            "Batch ID: %s | Most Upvoted Author: %s | Higher Downvotes Title: %s | Most Num Comments Title: %s | Highest Score Title: %s | Highest Comment Karma Author: %s",
            batch_id,
            most_upvoted_author,
            higher_downvotes_title,
            most_num_comments_title,
            highest_score_title,
            highest_comment_karma_author,
        )

        insert_query = """
            INSERT INTO public.reddit_analysis_results
            (batch_id, most_upvoted_author, higher_downvotes_title, most_num_comments_title, highest_score_title, highest_comment_karma_author)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        cursor = connection.cursor()
        cursor.execute(insert_query, (
            batch_id,
            most_upvoted_author,
            higher_downvotes_title,
            most_num_comments_title,
            highest_score_title,
            highest_comment_karma_author
        ))

        # Commit the transaction and close the cursor
        connection.commit()
        cursor.close()

    except Exception as e:
        logger.error("Error processing batch with ID %s: %s", batch_id, str(e))

    logger.info("Batch processing completed for ID: %s", batch_id)
    
if __name__ == "__main__":
    logger = setup_logger(__name__, 'consumer.log')
    spark = (
        SparkSession.builder.appName("Kafka Pyspark Streamin Learning")
        .master("spark://spark-master:7077")
        .config("spark.jars.packages", ",".join(packages))
        .config("spark.executor.extraClassPath", "/app/packages/postgresql-42.2.18.jar")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")

    sampleDataframe = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", KAFKA_TOPIC_NAME) \
        .load()

    base_df = sampleDataframe.selectExpr("CAST(value as STRING)", "timestamp")

    data_schema = StructType([
        StructField("id", StringType(), True),
        StructField("title", StringType(), True),
        StructField("author", StringType(), True),
        StructField("post_time", LongType(), True),
        StructField("upvotes", IntegerType(), True),
        StructField("downvotes", IntegerType(), True),
        StructField("num_comments", IntegerType(), True),
        StructField("score", IntegerType(), True),
        StructField("comment_karma", IntegerType(), True),
        StructField("first_level_comments_count", IntegerType(), True),
        StructField("second_level_comments_count", IntegerType(), True)
    ])

    info_dataframe = base_df.select(
        from_json(col("value"), data_schema).alias("info"), "timestamp"
    )
    info_df_fin = info_dataframe.select("info.*", "timestamp")

    query = info_df_fin.writeStream.foreachBatch(process_batch).start()
    query.awaitTermination()





   
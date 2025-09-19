import os
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

FIREHOSE = boto3.client('firehose')
STREAM_NAME = os.environ['STREAM_NAME']

def lambda_handler(event, context):
    records = []
    for r in event['Records']:
        body = r['body']
        records.append({"Data": (body if body.endswith('\n') else body + "\n").encode('utf-8')})
    
    logger.info(f"Sending {len(records)} records to Firehose")

    for i in range(0, len(records), 500):
        FIREHOSE.put_record_batch(
            DeliveryStreamName=STREAM_NAME,
            Records=records[i:i+500]
        )
import boto3
import csv
import json
import uuid
import os
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    s3 = boto3.client('s3')
    dynamodb = boto3.resource('dynamodb')
    table_name = os.environ.get('TABLE_NAME', 'saastest1')

    # Try to get the table, create it if it doesn't exist
    try:
        table = dynamodb.Table(table_name)
        table.load()
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            logger.info(f"Table {table_name} does not exist. Creating...")
            table = dynamodb.create_table(
                TableName=table_name,
                AttributeDefinitions=[
                    {'AttributeName': 'userId', 'AttributeType': 'S'},
                    {'AttributeName': 'billId', 'AttributeType': 'S'},
                    {'AttributeName': 'key', 'AttributeType': 'S'}
                ],
                KeySchema=[
                    {'AttributeName': 'userId', 'KeyType': 'HASH'},
                    {'AttributeName': 'billId', 'KeyType': 'RANGE'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            table.wait_until_exists()
            logger.info(f"Table {table_name} created successfully.")
        else:
            raise

    # Extract bucket and key from the event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    logger.info(f"Processing file: {key} from bucket: {bucket_name}")

    if not key.endswith('-forms.csv'):
        logger.info(f"File {key} is not a -forms.csv file. Skipping.")
        return {'statusCode': 200, 'body': 'File is not a -forms.csv file'}

    # Generate placeholder user ID and bill ID
    user_id = 'placeholder_user_id'
    bill_id = str(uuid.uuid4())

    # Download the CSV file
    csv_file_name = '/tmp/data.csv'
    s3.download_file(bucket_name, key, csv_file_name)

    # Process CSV and write to DynamoDB
    with open(csv_file_name, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            for k, v in row.items():
                if v:  # Only add non-empty values
                    item = {
                        'userId': user_id,
                        'billId': bill_id,
                        'key': k,
                        'value': str(v)
                    }
                    try:
                        table.put_item(Item=item)
                        logger.info(f"Successfully wrote item: {json.dumps(item)}")
                    except Exception as e:
                        logger.error(f"Error writing item to DynamoDB: {str(e)}")
                        logger.error(f"Problematic item: {json.dumps(item)}")


    logger.info(f"CSV data loaded to DynamoDB table: {table_name}")
    return {'statusCode': 200, 'body': f'CSV data loaded to DynamoDB table: {table_name}'}
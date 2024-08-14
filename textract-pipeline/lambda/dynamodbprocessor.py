import boto3
import csv
import json
import uuid

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    dynamodb = boto3.resource('dynamodb')
    table_name = 'saastest1'  # Replace with your desired table name

    try:
        table = dynamodb.Table(table_name)
        table.load()  # Raise an exception if table doesn't exist
    except Exception as e:
        # Create the table if it doesn't exist
        table = dynamodb.create_table(
            TableName=table_name,
            AttributeDefinitions=[
                {
                    'AttributeName': 'userId',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'billId',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'key',
                    'AttributeType': 'S'
                }
            ],
            KeySchema=[
                {
                    'AttributeName': 'userId',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'billId',
                    'KeyType': 'RANGE'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        table.wait_until_exists()

    # Extract bucket and key from the event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    # Check if the file is a CSV with "forms" in the name
    if not key.endswith('.csv') or 'forms' not in key:
        return {'statusCode': 200, 'body': 'File is not a CSV or does not contain "forms"'}

    # Generate placeholder user ID and bill ID
    user_id = 'placeholder_user_id'  # Replace with actual user ID logic
    bill_id = str(uuid.uuid4())

    # Download the CSV file
    csv_file_name = '/tmp/data.csv'
    s3.download_file(bucket_name, key, csv_file_name)

    # Process CSV and load to DynamoDB
    with open(csv_file_name, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        with table.batch_writer() as batch:
            for row in reader:
                for k, v in row.items():
                    item = {
                        'userId': user_id,
                        'billId': bill_id,
                        'key': k,
                        'value': v
                    }
                    batch.put_item(Item=item)

    return {'statusCode': 200, 'body': 'CSV data loaded to DynamoDB'}

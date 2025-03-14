import os
import boto3
from PIL import Image
from io import BytesIO

# Initialize AWS clients
s3 = boto3.client('s3')
sns = boto3.client('sns')

# Define the S3 buckets and SNS topic
source_bucket = 'image-non-resized-1'  # Change this to your source bucket name
destination_bucket = 'image-updated-resized-1'  # Change this to your destination bucket name
sns_topic_arn = 'arn:aws:sns:ap-south-1:390402569672:image-resizing-topic:a2a5d2d7-6b7a-4912-92f3-c317f8fe595c'  # Change this to your SNS topic ARN

def lambda_handler(event, context):
    """AWS Lambda function triggered by S3 event"""
    if 'Records' in event:
        for record in event['Records']:
            handle_s3_record(record)
    else:
        print("No records found in the event.")

def handle_s3_record(record):
    """Handles individual S3 event records"""
    try:
        # Get the uploaded image file details
        bucket_name = record['s3']['bucket']['name']
        object_key = record['s3']['object']['key']

        print(f"Processing image: {object_key} from bucket: {bucket_name}")

        # Download the image from S3
        image_data = s3.get_object(Bucket=bucket_name, Key=object_key)['Body'].read()
        
        # Open image using Pillow
        image = Image.open(BytesIO(image_data))

        # Resize the image
        resized_image = resize_image(image)

        # Save the resized image to a BytesIO buffer
        buffer = BytesIO()
        resized_image.save(buffer, format="JPEG")
        buffer.seek(0)

        # Upload the resized image to the destination S3 bucket
        new_object_key = f"resized-{object_key}"
        s3.put_object(Bucket=destination_bucket, Key=new_object_key, Body=buffer, ContentType="image/jpeg")

        print(f"Resized image uploaded to {destination_bucket}/{new_object_key}")

        # Send SNS notification
        send_sns_notification(object_key, new_object_key)

    except Exception as e:
        print(f"Error processing image {record}: {str(e)}")

def resize_image(image, size=(300, 300)):
    """Resize the image to the specified dimensions"""
    return image.resize(size, Image.ANTIALIAS)

def send_sns_notification(original_key, resized_key):
    """Send an SNS notification after processing the image"""
    message = (
        f"Image Processing Completed!\n\n"
        f"Original Image: {original_key}\n"
        f"Resized Image: {resized_key}\n"
        f"Stored in bucket: {destination_bucket}"
    )

    sns.publish(TopicArn=sns_topic_arn, Message=message, Subject="AWS Image Resizing Notification")
    print("SNS Notification Sent!")
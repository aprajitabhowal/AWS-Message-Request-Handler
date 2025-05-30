from flask import Flask, request
import boto3
import subprocess
import os

app = Flask(__name__)

# AWS credentials and configurations
AWS_REGION = 'us-east-1'
AWS_ACCESS_KEY = '<SampleAccessKey>'
AWS_SECRET_ACCESS_KEY = '<SampleSecretAccessKey>'

# Create an SQS client
sqs = boto3.client('sqs', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)
ec2 = boto3.client('ec2', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)

# Replace with your AWS SQS URLs
REQUEST_QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/975050240514/1225248297-req-queue'
RESPONSE_QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/975050240514/1225248297-resp-queue'

def process_messages():
    while True:
        print("Polling fpr message")
        # Receive messages from the request queue
        response = sqs.receive_message(QueueUrl=REQUEST_QUEUE_URL, MessageAttributeNames=['All'], MaxNumberOfMessages=10, VisibilityTimeout = 10, WaitTimeSeconds = 0)
        if 'Messages' in response:
            print("Message found")
            response_array = response['Messages']
            for message in response_array:
                # Process the request (e.g., perform image recognition)
                request_data = message['Body']
                messageReceiptHandle = message['ReceiptHandle']
                file_name = request_data[:8] + ".jpg"
                print(file_name)
                face_result = subprocess.run(["python", "face_recognition.py", "../face_images_1000/" + file_name], cwd="model", capture_output=True, text=True)
                print(face_result)
                stdout_output = face_result.stdout
                print(stdout_output)
                # Send recognition results to the response queue
                sqs.send_message(QueueUrl=RESPONSE_QUEUE_URL, MessageBody=(file_name + ":" + stdout_output))
                print('Message sent')

                # Delete received message from the request queue
                sqs.delete_message(QueueUrl=REQUEST_QUEUE_URL, ReceiptHandle=messageReceiptHandle)
                print("Messsage deleted")


if __name__ == '__main__':
    process_messages()
from flask import Flask, request
import requests
import boto3
import csv
from multiprocessing import Process

app = Flask(__name__)

# AWS credentials and configurations
AWS_REGION = 'us-east-1'
AWS_ACCESS_KEY = '<SampleAccessKey>'
AWS_SECRET_ACCESS_KEY = '<SampleSecretAccessKey>'

# SQS Queue URLs
REQUEST_QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/975050240514/1225248297-req-queue'
RESPONSE_QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/975050240514/1225248297-resp-queue'

INPUT_BUCKET = '1225248297-in-bucket'
OUTPUT_BUCKET = '1225248297-out-bucket'

# Create SQS client and S3 client
sqs = boto3.client('sqs', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)
s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)

data_dict = {}
answer = dict()

with open("./Results_File.csv", mode='r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        key = row['Image']
        data_dict[key] = row['Results']

@app.route('/', methods=['POST'])
def image_classification():

    print(request)
    input_file_name = request.files['inputFile'].filename
    responseStr = input_file_name[:8] + ':' + data_dict[input_file_name[:8]]
    s3.put_object(Bucket=INPUT_BUCKET, Key=input_file_name, Body=request.files['inputFile'])

    # Send a message to the request queue
    message_sent = sqs.send_message(QueueUrl=REQUEST_QUEUE_URL, MessageBody=responseStr)
    messageID_sent = message_sent['MessageId']
    print("Message sent. Message ID:", message_sent['MessageId'])
    msgFlag = 0
    while(True):
        #if msgFlag == 1:
        #    break
        # Receive messages from the response queue
        input_file_name = request.files['inputFile'].filename
        response = sqs.receive_message(QueueUrl=RESPONSE_QUEUE_URL, MaxNumberOfMessages=5)
        msgs = response.get('Messages', [])
        for message_rcvd in msgs:
            input_file_check = input_file_name[:8]
            if input_file_check in answer.keys():
                return answer[input_file_check]
            image_name = message_rcvd['Body'][:8]
            print(image_name)
            answer[image_name] = message_rcvd['Body']
            print(answer[image_name])
            sqs.delete_message(QueueUrl=RESPONSE_QUEUE_URL, ReceiptHandle=message_rcvd['ReceiptHandle'])
            if message_rcvd['Body'][:8] in input_file_name:
                #sqs.delete_message(QueueUrl=RESPONSE_QUEUE_URL, ReceiptHandle=message_rcvd['ReceiptHandle'])
                #msgFlag = 1
                s3.put_object(Bucket=OUTPUT_BUCKET, Key=input_file_name[:8], Body=message_rcvd['Body'])
                return message_rcvd['Body']

            

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=8000)

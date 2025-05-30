from flask import Flask, jsonify
import boto3
import base64
import time


app = Flask(__name__)

# AWS credentials and configurations
AWS_REGION = 'us-east-1'
AWS_ACCESS_KEY = '<SampleAccessKey>'
AWS_SECRET_ACCESS_KEY = '<SampleSecretAccessKey>'
# SQS Queue URLs
REQUEST_QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/975050240514/1225248297-req-queue'
RESPONSE_QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/975050240514/1225248297-resp-queue'

# Thresholds for scaling actions
SCALE_OUT_THRESHOLD = 3  # Adjust as needed
SCALE_IN_THRESHOLD = 1     # Adjust as needed

# Create an ec2 client
ec2 = boto3.client('ec2', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)
sqs = boto3.client('sqs', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)

# Specify the launch configuration parameters
AMI_ID = 'ami-0f7eb2b2d249fb4b6'
INSTANCE_TYPE = 't2.micro'
SECURITY_GROUP_ID = 'sg-09629321888fa895f'
SUBNET_ID = 'subnet-07b63607277acea6c'
KEY_NAME = 'appInstance-key-pair'
USERNAME = 'ubuntu'
INSTANCE_PUBLIC_IP = '3.83.93.218'
APP_TIER_DIRECTORY = '/home/ubuntu/myApp/'

# User data script to initialize the app-tier code and establish SSH connection
user_data_script = """
#!/bin/bash
echo "Running script"
cd /home/ubuntu/myApp/

# Connect to the EC2 instance remotely
sudo -u ubuntu python3 app-tier.py
"""

instance_count = 1
request_count = 0

def autoscaler():
    global instance_count
    attributes = sqs.get_queue_attributes(
        QueueUrl=REQUEST_QUEUE_URL,
        AttributeNames=['ApproximateNumberOfMessages']
    )
    queueMessages = int(attributes['Attributes']['ApproximateNumberOfMessages'])
    launch_config = {
        'ImageId': AMI_ID,
        'InstanceType': INSTANCE_TYPE,
        'KeyName': KEY_NAME,
        'UserData': user_data_script,
        'TagSpecifications': [{
        'ResourceType': 'instance',
        'Tags': [
            {'Key': 'Name', 'Value': f'app-tier-instance-{instance_count}'}  # Assign custom name to the instance
        ]
    }],
        'MinCount': 1, 
        'MaxCount': 1
    }
    print("queueMessages:", queueMessages)
    # Check if scale out is needed
    if queueMessages >= SCALE_OUT_THRESHOLD:
        
        # Define the parameters for the new instances
        # Launch new instances
        response = create_instance()
        print("Instances launched")
        instance_count += 1

        # # Optional: Wait for instance to be in running state
        # instance_id = response['Instances'][0]['InstanceId']
        # waiter = ec2.get_waiter('instance_running')
        # waiter.wait(InstanceIds=[instance_id])

    return

def create_instance():
    response = ec2.run_instances(ImageId='ami-0b36cdf3acfe1ae94',
                        InstanceType='t2.micro',
                        MinCount=1,
                        MaxCount=1,
                        KeyName='appInstance-key-pair',
                        UserData="""#!/bin/bash
                                    exec > >(tee /var/log/user-data.log /dev/console) 2>&1
                                    echo "Starting user data script"
                                    cd /home/ubuntu/myApp || exit
                                    sudo -u ubuntu nohup python3 app-tier.py &
                                """,
                        TagSpecifications=[
                            {
                                'ResourceType': 'instance',
                                'Tags': [{'Key': 'Name','Value': 'app-tier-instance-' + str(instance_count)}]
                            },
                        ],
                        )
    return response['Instances'][0]['InstanceId']


while True:
    autoscaler()
    time.sleep(20)
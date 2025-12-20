import os
import json
import boto3
from botocore.exceptions import ClientError
from datetime import datetime

EC2 = boto3.client('ec2')
DDB = boto3.resource('dynamodb')

AMI_ENV = os.environ.get('AMI_ID')
DEFAULT_INSTANCE_TYPE = os.environ.get('INSTANCE_TYPE', 't2.micro')
INSTANCES_TABLE = os.environ.get('INSTANCES_TABLE')


def find_latest_amzn2_ami():
    # Find latest Amazon Linux 2 HVM AMI
    try:
        images = EC2.describe_images(
            Owners=['amazon'],
            Filters=[
                {'Name': 'name', 'Values': ['amzn2-ami-hvm-*-x86_64-gp2']},
                {'Name': 'state', 'Values': ['available']}
            ]
        )['Images']
        # sort by CreationDate descending
        images.sort(key=lambda i: i.get('CreationDate', ''), reverse=True)
        return images[0]['ImageId'] if images else None
    except ClientError as e:
        print('Error finding AMI:', e)
        return None


def lambda_handler(event, context):
    # Simple Lambda to create one EC2 instance
    try:
        headers = event.get('headers') or {}
        # Authorization header is expected to be validated by API Gateway/Cognito authorizer

        body = event.get('body')
        if isinstance(body, str) and body:
            try:
                body = json.loads(body)
            except Exception:
                body = {}
        elif body is None:
            body = {}

        instance_type = body.get('instance_type') or DEFAULT_INSTANCE_TYPE

        ami = AMI_ENV or find_latest_amzn2_ami()
        if not ami:
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'No AMI found'})
            }

        resp = EC2.run_instances(
            ImageId=ami,
            InstanceType=instance_type,
            MinCount=1,
            MaxCount=1
        )
        instance_id = resp['Instances'][0]['InstanceId']

        # Optionally tag the instance
        try:
            EC2.create_tags(Resources=[instance_id], Tags=[{'Key': 'CreatedBy', 'Value': 'LambdaCreateEC2'}])
        except Exception:
            pass

        # Save instance metadata to DynamoDB (if configured)
        if INSTANCES_TABLE:
            try:
                table = DDB.Table(INSTANCES_TABLE)
                item = {
                    'InstanceId': instance_id,
                    'State': 'pending',
                    'CreatedAt': datetime.utcnow().isoformat()
                }
                table.put_item(Item=item)
            except Exception as e:
                print('Error writing to DynamoDB:', e)

        return {
            'statusCode': 200,
            'body': json.dumps({'instance_id': instance_id})
        }

    except ClientError as e:
        print('AWS error:', e)
        return {'statusCode': 500, 'body': json.dumps({'message': str(e)})}
    except Exception as e:
        print('Error:', e)
        return {'statusCode': 500, 'body': json.dumps({'message': str(e)})}
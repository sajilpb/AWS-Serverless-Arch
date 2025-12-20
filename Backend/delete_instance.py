import os
import json
import boto3
from botocore.exceptions import ClientError

INSTANCES_TABLE = os.environ.get('INSTANCES_TABLE')
DDB = boto3.resource('dynamodb')
EC2 = boto3.client('ec2')


def lambda_handler(event, context):
    try:
        # API Gateway proxy integration passes pathParameters
        instance_id = None
        if isinstance(event, dict):
            path_params = event.get('pathParameters') or {}
            instance_id = path_params.get('id')
            if not instance_id:
                # try body
                body = event.get('body')
                if isinstance(body, str) and body:
                    try:
                        body = json.loads(body)
                    except Exception:
                        body = {}
                instance_id = (body or {}).get('instance_id')

        if not instance_id:
            return {'statusCode': 400, 'body': json.dumps({'message': 'instance id required'})}

        # Terminate the EC2 instance
        try:
            EC2.terminate_instances(InstanceIds=[instance_id])
        except ClientError as e:
            print('EC2 error:', e)
            # continue to attempt DB cleanup

        # Remove from DynamoDB
        if INSTANCES_TABLE:
            try:
                table = DDB.Table(INSTANCES_TABLE)
                table.delete_item(Key={'InstanceId': instance_id})
            except Exception as e:
                print('DynamoDB delete error:', e)

        return {'statusCode': 200, 'body': json.dumps({'message': 'terminated', 'instance_id': instance_id})}

    except Exception as e:
        print('Error:', e)
        return {'statusCode': 500, 'body': json.dumps({'message': str(e)})}

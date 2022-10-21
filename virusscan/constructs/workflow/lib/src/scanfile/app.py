import json
import boto3
import os
import errno
import subprocess
import copy

from common import VIRUS_SCAN_TAG_KEY,VIRUS_SCAN_TAG_CLEAN_VALUE,VIRUS_SCAN_TAG_INFECTED_VALUE

transfer = boto3.client('transfer')

def lambda_handler(event, context):

    s3 = boto3.resource("s3")
    s3_client = boto3.client("s3")    
    
    bucket_name = event['fileLocation']['bucket']
    key_name =event['fileLocation']['key']
    s3_object = s3.Object(bucket_name, key_name)
    
    file_path = get_local_path(s3_object, "/tmp")
    create_dir(os.path.dirname(file_path))
    s3_object.download_file(file_path)

    output = subprocess.run(
        ["/usr/bin/clamscan", "-v", "-a", "--stdout", file_path],
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE
    )

    if output.returncode == 0:
      tagValue = VIRUS_SCAN_TAG_CLEAN_VALUE
      status = 'SUCCESS'
    else:
      tagValue = VIRUS_SCAN_TAG_INFECTED_VALUE
      status = 'FAILURE'

    curr_tags = s3_client.get_object_tagging(
        Bucket=s3_object.bucket_name, Key=s3_object.key
    )["TagSet"]
    new_tags = copy.copy(curr_tags)
    for tag in curr_tags:
        if tag["Key"] in [
            VIRUS_SCAN_TAG_KEY
        ]:
            new_tags.remove(tag)
    new_tags.append({"Key": VIRUS_SCAN_TAG_KEY, "Value": tagValue})
    s3_client.put_object_tagging(
        Bucket=s3_object.bucket_name, Key=s3_object.key, Tagging={"TagSet": new_tags}
    )
    response = transfer.send_workflow_step_state(
      WorkflowId=event['serviceMetadata']['executionDetails']['workflowId'],
      ExecutionId=event['serviceMetadata']['executionDetails']['executionId'],
      Token=event['token'],
      Status= status
    )
    return {
      'statusCode': 200,
      'body': json.dumps(response)
    }

def create_dir(path):
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise

def get_local_path(s3_object, local_prefix):
    return os.path.join(local_prefix, s3_object.bucket_name, s3_object.key)

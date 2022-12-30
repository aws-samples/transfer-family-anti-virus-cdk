import boto3
import json
import os
import subprocess

transfer = boto3.client('transfer')
s3 = boto3.resource('s3')

def lambda_handler(event):

  #Download file from S3 to TMP directory for analysis
    TEMP = '/tmp/'
    fileLocation = event['fileLocation']
    destination_path = TEMP + fileLocation['key']
    destination_dir = TEMP + event['serviceMetadata']['transferDetails']['userName']

    if not os.path.exists(os.path.join(destination_dir)):
        os.makedirs(destination_dir)

    s3.Bucket(fileLocation['bucket']).download_file(fileLocation['key'],destination_path )

    scanCommand = [
            "clamscan",
            "--stdout",
            "-r",
            f"--database=/var/task/database/",
            f"{destination_path}"
    ]
    
    scan_summary = subprocess.run(
        scanCommand,
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE
    )

    print(scan_summary)

    scanStatus = 'SUCCESS' if scan_summary.returncode == 0 else "FAILURE"

    response = transfer.send_workflow_step_state(
      WorkflowId=event['serviceMetadata']['executionDetails']['workflowId'],
      ExecutionId=event['serviceMetadata']['executionDetails']['executionId'],
      Token=event['token'],
      Status=scanStatus)


    return {
      'statusCode': 200,
      'body': json.dumps(response)
    }
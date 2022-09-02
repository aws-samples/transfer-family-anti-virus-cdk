from ast import Str
import json
import boto3
import os
import errno
import subprocess
import copy
import sys

from common import VIRUS_SCAN_TAG_KEY,VIRUS_SCAN_TAG_CLEAN_VALUE,VIRUS_SCAN_TAG_INFECTED_VALUE
# Increase lambda timeout by 15 mins
# Issue with lambda getting permission to access read access to bucket
# Increase fileszie of lambda contaier to 10gb
# Add permission to Lambda to add Tag to file
transfer = boto3.client('transfer')
#@property
def get_LOCAL_AV_DEFINATION_PATH()->Str:
  return "/tmp/clamav_defs"

#@property
def get_AV_DEFINATION_FILENAMES():
  return ["main.cvd","daily.cld","bytecode.cvd"]

#@property
def get_AV_DEFINATION_S3():
  return "antivirus-definitions-d34f7780"

#@property
def get_AV_DEFINATION_S3_PREFIX():
  return "clamav_defs"



def lambda_handler(event, context):


    # call the SendWorkflowStepState API to notify the worfklow about the step's SUCCESS or FAILURE status
    response = transfer.send_workflow_step_state(
      WorkflowId=event['serviceMetadata']['executionDetails']['workflowId'],
      ExecutionId=event['serviceMetadata']['executionDetails']['executionId'],
      Token=event['token'],
      Status='SUCCESS'
    )

    #print(json.dumps(response))
    print("Satish")
    s3 = boto3.resource("s3")
    s3_client = boto3.client("s3")    
    
    bucket_name = event['fileLocation']['bucket']
    print("event bucket_name:",bucket_name)
    key_name =event['fileLocation']['key']
    print("event key_name:",key_name)
    s3_object = s3.Object(bucket_name, key_name)
    print("S3 Object:",s3_object)
    
    file_path = get_local_path(s3_object, "/tmp")
    print("local file_path:",file_path)
    create_dir(os.path.dirname(file_path))
    s3_object.download_file(file_path)

    #File is already downloaded
    #print("after downloading file from s3")
    #downlaod_defs_from_s3()

    print("before Popen")
    av_proc = subprocess.Popen(
        ["clamscan", "-v", "-a", "--stdout", "-d", get_LOCAL_AV_DEFINATION_PATH(), file_path],
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE
    )
    print("before decode")
    output = av_proc.communicate()[0].decode()
    summary = scan_output_to_json(output)
    print("clamscan summary:\n%s" % summary)

    if av_proc.returncode == 0:
      tagValue = VIRUS_SCAN_TAG_CLEAN_VALUE
    else:
      tagValue = VIRUS_SCAN_TAG_INFECTED_VALUE

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
    print("new tags:",new_tags)
    s3_client.put_object_tagging(
        Bucket=s3_object.bucket_name, Key=s3_object.key, Tagging={"TagSet": new_tags}
    )
    print("after put tags")

    return {
      'statusCode': 200,
      'body': json.dumps(response)
    }

def create_dir(path):
    if not os.path.exists(path):
        try:
            print("Attempting to create directory %s.\n" % path)
            os.makedirs(path)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise

def get_local_path(s3_object, local_prefix):
    return os.path.join(local_prefix, s3_object.bucket_name, s3_object.key)

def downlaod_defs_from_s3( ):
  if not os.path.exists(get_LOCAL_AV_DEFINATION_PATH()):
    create_dir(get_LOCAL_AV_DEFINATION_PATH())
    print("downlaod_defs_from_s3 function")
    s3 = boto3.resource("s3")
    s3_av_bucket = s3.Bucket(get_AV_DEFINATION_S3())
    print("AV_DEFINATION_S3:",get_AV_DEFINATION_S3())
    
    for filename in get_AV_DEFINATION_FILENAMES():
      print("File to download:",filename)
      local_path = os.path.join(get_LOCAL_AV_DEFINATION_PATH(), filename)
      print("Local path:",local_path)
      s3_path = os.path.join(get_AV_DEFINATION_S3_PREFIX(), filename)
      print("s3_path for file:",s3_path," local_path:",local_path)
      s3_av_bucket.download_file(s3_path, local_path)

def scan_output_to_json(output):
    summary = {}
    for line in output.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            summary[key] = value.strip()
    return summary
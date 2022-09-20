from ast import Str
import json
import boto3
import os
import errno
import subprocess
import copy
import sys
import pwd

from common import VIRUS_SCAN_TAG_KEY,VIRUS_SCAN_TAG_CLEAN_VALUE,VIRUS_SCAN_TAG_INFECTED_VALUE
# Increase lambda timeout by 15 mins
# Issue with lambda getting permission to access read access to bucket
# Increase fileszie of lambda contaier to 10gb
# Add permission to Lambda to add Tag to file
transfer = boto3.client('transfer')
#@property
def get_LOCAL_AV_DEFINATION_PATH()->Str:
  return "/var/task/clamav_defs/"

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


    #print(json.dumps(response))
    s3 = boto3.resource("s3")
    s3_client = boto3.client("s3")    
    
    bucket_name = event['fileLocation']['bucket']
    key_name =event['fileLocation']['key']
    s3_object = s3.Object(bucket_name, key_name)
    
    file_path = get_local_path(s3_object, "/tmp")
    create_dir(os.path.dirname(file_path))
    s3_object.download_file(file_path)

    print("local file path:",file_path)
    #subprocess.call(['chmod', '0644', file_path])
    
    #print("File read permission:",os.access(file_path, os.R_OK))
    #File is already downloaded
    #print("after downloading file from s3")
    #downlaod_defs_from_s3()
   

    # av_proc = subprocess.Popen(
    #     ["freshclam", "-datadir=/tmp/clamav_defs"],
    #     stderr=subprocess.STDOUT,
    #     stdout=subprocess.PIPE
    # )
    # output = av_proc.communicate()[0].decode()
    # #summary = scan_output_to_json(output)
    # print("output freshclam:", output)
    #print("clam_def files :",os.listdir(get_LOCAL_AV_DEFINATION_PATH()))    
    #print("clam_def files:",os.listdir(get_LOCAL_AV_DEFINATION_PATH()))
    # av_proc = subprocess.Popen(
    #     ["clamscan", "-v", "-a", "--stdout", "-d", get_LOCAL_AV_DEFINATION_PATH(), file_path],
    #     stderr=subprocess.STDOUT,
    #     stdout=subprocess.PIPE
    # )
    # output = subprocess.run(
    #     [
    #         "freshclam",
    #         "-u %s" % pwd.getpwuid(os.getuid())[0],
    #         "--config-file=/etc/freshclam.conf",
    #         "--datadir=~/task/clamav_defs"
    #     ],
    #     stderr=subprocess.STDOUT,
    #     stdout=subprocess.PIPE,
    #     #shell=True
    # )   
    #print("after freshclam")
    # output = subprocess.run(
    #     ["ls", "-al", "/var/task/clamav_defs/"],
    #     shell=True,
    #     stderr=subprocess.STDOUT,
    #     stdout=subprocess.PIPE
    # )    
    # print("ls outoput:",output)



    output = subprocess.run(
        ["/usr/bin/clamscan", "-v", "-a", "--stdout", 
        #"--database=/tmp/clamav_defs/", 
        file_path],
        #shell=True,
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE
    )    

    print("after run")
    #output = av_proc.communicate()[0].decode()
    #output = av_proc.run()
    
    #summary = scan_output_to_json(output)
    print("output:", output)
    print("scan returncode",output.returncode)

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
#!/usr/bin/env python3
from http import server
from os import environ
from os import path
import sys
from typing import List
import aws_cdk as cdk
from constructs import Construct
from aws_cdk import(
  aws_s3 as s3,
  aws_iam as iam,
  aws_logs as logs,
  aws_transfer as tfx,
  aws_lambda as lambda_,
  aws_iam as iam,
)
sys.path.insert(0, './src/scanfile')
from  common import VIRUS_SCAN_TAG_KEY, VIRUS_SCAN_TAG_CLEAN_VALUE


SRC_ROOT_DIR = path.join(path.dirname(__file__),'src')

class DataStorageConstruct(Construct):
  @property
  def incoming_bucket(self)->s3.IBucket:
    return self._incoming_bucket

  @incoming_bucket.setter
  def incoming_bucket(self,value)->None:
    self._incoming_bucket = value
  
  def __init__(self, scope: Construct, id:str, **kwargs) -> None:
    super().__init__(scope, id, **kwargs)

    self.incoming_bucket = s3.Bucket(self,'Bucket',
      removal_policy= cdk.RemovalPolicy.DESTROY)


  def add_to_policy(self, policyStatement:iam.PolicyStatement)->None:
    self.incoming_bucket.add_to_resource_policy(
      policyStatement
    )



  def grant_read(self,identity:iam.IGrantable)->None:
    self.incoming_bucket.grant_read(identity)

  def grant_read_write(self,identity:iam.IGrantable)->None:
    self.incoming_bucket.grant_read_write(identity)

class FunctionsConstruct(Construct):
  def __init__(self, scope: Construct, id:str, storage:DataStorageConstruct, **kwargs) -> None:
    super().__init__(scope, id, **kwargs)

    self.scan_file_function = lambda_.DockerImageFunction(self,'ScanFile',
      description='Scans incoming file from TransferFamily Server',
      timeout= cdk.Duration.seconds(60),
      architecture= lambda_.Architecture.X86_64,
      log_retention= logs.RetentionDays.TWO_WEEKS,
      tracing= lambda_.Tracing.ACTIVE,
      environment={
        'asdf':'jkld'
      },
      code = lambda_.DockerImageCode.from_image_asset(
        directory=path.join(SRC_ROOT_DIR,'scanfile'),build_args={"--platform": "linux/amd64"}))    
    storage.incoming_bucket.grant_read_write(self.scan_file_function.role)
  def grant_invoke(self,identity:iam.IGrantable)->None:
    self.scan_file_function.grant_invoke(identity)

  def add_to_role_policy(self, policyStatement: iam.PolicyStatement)->None:
    self.scan_file_function.add_to_role_policy(policyStatement)



class TransferWorkflowConstruct(Construct):
  '''
  Creates the AWS Transfer Family Workflow.
  see: https://docs.aws.amazon.com/transfer/latest/userguide/nominal-steps-workflow.html
  '''
  @property
  def execution_role(self)->iam.IRole:
    return self.__execution_role

  @property
  def workflow(self)->tfx.CfnWorkflow:
    return self.__workflow

  @property
  def functions(self)->FunctionsConstruct:
    return self._functions

  @property
  def storage(self)->DataStorageConstruct:
    return self._storage

  def __init__(self, scope: Construct, id:str, **kwargs) -> None:
    super().__init__(scope, id, **kwargs)

    self.__execution_role = iam.Role(self,'WorkflowExecutionRole',
      assumed_by=iam.ServicePrincipal(service='transfer'))    



    self._storage = DataStorageConstruct(self,'Storage', **kwargs)    
    #storage.grant_read_write(self.execution_role)
    self._functions = FunctionsConstruct(self,'Functions',storage=self._storage)
    self._functions.grant_invoke(self.execution_role)


    self._storage.grant_read(self._functions.scan_file_function.role)
    
    storageVirusDefination = s3.Bucket.from_bucket_name(self, "VirusBucket", "antivirus-definitions-d34f7780")
    storageVirusDefination.grant_read(self._functions.scan_file_function.role)

    self.__workflow = tfx.CfnWorkflow(self,'Definition',
      steps=[

        tfx.CfnWorkflow.WorkflowStepProperty(
          type= "CUSTOM",
          custom_step_details={
            "Name":"VirusScan",
            "Target": self._functions.scan_file_function.function_arn,
            "TimeoutSeconds": self._functions.scan_file_function.timeout.to_seconds()
          }),

      ])
    


  



  def to_details(self)->tfx.CfnServer.WorkflowDetailProperty:
    return tfx.CfnServer.WorkflowDetailProperty(
      execution_role=self.execution_role.role_arn,
      workflow_id= self.workflow.ref
    )

class TransferServerConstruct(Construct):
  def __init__(self, scope: Construct, id:str, **kwargs) -> None:
    super().__init__(scope, id, **kwargs)

    logging_role = iam.Role(self,'LoggingRole',
      assumed_by=iam.ServicePrincipal(service='transfer'),
      managed_policies=[
        iam.ManagedPolicy.from_aws_managed_policy_name('CloudWatchLogsFullAccess')
      ])

    self.transfer_workflow = TransferWorkflowConstruct(self,'Workflow', **kwargs)
    self.server = tfx.CfnServer(self,'TransferServer',
      domain='S3',
      endpoint_type='PUBLIC',
      logging_role= logging_role.role_arn,
      protocols=['SFTP'],
      workflow_details= tfx.CfnServer.WorkflowDetailsProperty(
        on_upload=[self.transfer_workflow.to_details()
        ]
      )
      )  

    user_policy = iam.PolicyDocument(
        statements=[
        #   iam.PolicyStatement(
        #     actions=["s3:ListAllMyBuckets"
        #     ],
        #     #principals=[iam.AccountRootPrincipal()],
        #     resources=[self.transfer_workflow.storage.incoming_bucket.bucket_arn]
        # ),
          iam.PolicyStatement(
            actions=["s3:ListBucket","s3:GetBucketLocation"
            ],
            #principals=[iam.AccountRootPrincipal()],
            resources=[self.transfer_workflow.storage.incoming_bucket.bucket_arn]
        ),
            iam.PolicyStatement(
                  actions=["s3:PutObject", "s3:GetObject","s3:DeleteObject",
                "s3:DeleteObjectVersion", "s3:GetObjectVersion", "s3:GetObjectACL",
                "s3:PutObjectACL"
                  ],
                  resources=[self.transfer_workflow.storage.incoming_bucket.bucket_arn+"/*"]
        ) 
        ]
    )

    self.user_role = iam.Role(self, "UserRole",
      assumed_by=iam.ServicePrincipal(service='transfer'),
      description="VirusScan User Role",
      inline_policies={"userpolicy":user_policy}
    )


    self.cfn_user = tfx.CfnUser(self, "client1",
      role = self.user_role.role_arn,
      server_id= self.server.attr_server_id,
      user_name = "client1",
      home_directory = "/"+self.transfer_workflow.storage.incoming_bucket.bucket_name

    )

class IngestionConstruct(Construct):
  def __init__(self, scope: Construct, id:str, **kwargs) -> None:
    super().__init__(scope, id, **kwargs)
    server=TransferServerConstruct(self,'TransferServer',**kwargs)
    arn = server.transfer_workflow.workflow.attr_arn
    
  

    server.transfer_workflow.functions.scan_file_function.role.attach_inline_policy(iam.Policy(self, "userpool-policy",
      statements=[iam.PolicyStatement(
                  actions=["transfer:SendWorkflowStepState"],
                  resources=[arn]
      )]
    ))     

    policyStatementDownload = iam.PolicyStatement(
      principals  = [iam.AnyPrincipal()],
      actions = ["s3:GetObject"],
      resources = [server.transfer_workflow.storage.incoming_bucket.bucket_arn+"/*"],
      effect = iam.Effect.DENY,
      conditions =  {
        "StringNotEquals":{
          "s3:ExistingObjectTag/"+VIRUS_SCAN_TAG_KEY:VIRUS_SCAN_TAG_CLEAN_VALUE
        },

        "ArnNotEquals":{
          "aws:PrincipalArn": server.user_role.role_arn
        }
      
      }
    )
    server.transfer_workflow._storage.add_to_policy(policyStatementDownload)
    policyStatementTagging = iam.PolicyStatement(
      not_principals  = [server.transfer_workflow.functions.scan_file_function.role],
      actions = ["s3:DeleteObjectTagging","s3:PutObjectTagging"],
      resources = [server.transfer_workflow.storage.incoming_bucket.bucket_arn+"/*"],
      effect = iam.Effect.DENY,
    )
    server.transfer_workflow._storage.add_to_policy(policyStatementTagging)

    cdk.CfnOutput(self, "ServerID", value=server.server.attr_server_id, description="ServerID")
    return

class DefaultStack(cdk.Stack):
  def __init__(self, scope:Construct, id:str, **kwargs)->None:
    super().__init__(scope,id,**kwargs)
    IngestionConstruct(self,'Ingestion')
    return

class AntiVirusApp(cdk.App):
  def __init__(self, **kwargs)->None:
    super().__init__(**kwargs)
    DefaultStack(self,'AntiVirusStack',**kwargs)

app = AntiVirusApp()
app.synth()
from constructs import Construct
from aws_cdk import (
    App,
    Stack,
    aws_iam as iam,
    aws_s3 as s3,    
)
from auth import Auth
from server import Server
from workflow import (
    Workflow,
    #SFTPProps,
)
import aws_cdk as cdk

class VirusScanStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #
        # Create s3 bucket for sftp
        #
        bucket = s3.Bucket(self,'Bucket',
            removal_policy= cdk.RemovalPolicy.DESTROY)

        auth = Auth(self,"authprovider", sftp_bucket_arn=bucket.bucket_arn,sftp_bucket_name=bucket.bucket_name)


        workflow = Workflow(self,"workflow",sftp_bucket_arn=bucket.bucket_arn)
      


        server = Server(self,"myserver",authfunc_arn=auth.function_arn, workflowDetailsProperty=workflow.get_workflowDetailsProperty())
        # props = SFTPProps(
        #     bucket_arn = server.bucket_arn
        # )
        # workflow.add_scanfile_role_policy(
        #     iam.PolicyStatement(
        #         actions=["s3:GetObject","s3:PutObjectTagging"],
        #         resources=[bucket.bucket_arn]
        #     )
        # )

        auth.grant_invoke_transfer(server_arn=server.server_arn)
        cdk.CfnOutput(self, 'SFTPEndpoint', value=server.serverID+".server.transfer."+Stack.of(self).region+".amazonaws.com")
        cdk.CfnOutput(self, 'SFTPBucket', value= bucket.bucket_name)        
        cdk.CfnOutput(self, 'Password', value=auth.password)    
        cdk.CfnOutput(self, 'Username', value="client1")    

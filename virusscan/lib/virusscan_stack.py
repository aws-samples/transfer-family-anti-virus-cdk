from constructs import Construct
from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_s3 as s3
)
from auth import Auth
from server import Server
from build import Build
from workflow import (
    Workflow
)
import aws_cdk as cdk

class VirusScanStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #
        # Create s3 bucket for sftp
        #
        bucket = s3.Bucket(self,'Landingzone',
            removal_policy= cdk.RemovalPolicy.DESTROY)

        policyStatement = iam.PolicyStatement(
            effect=iam.Effect.DENY,
            actions=["s3:GetObject"],
            resources=[bucket.bucket_arn, bucket.bucket_arn + "/*"]
        )

        policyStatement.add_any_principal()

        bucket.add_to_resource_policy(policyStatement)

        auth = Auth(self,"authprovider", sftp_bucket_arn=bucket.bucket_arn,sftp_bucket_name=bucket.bucket_name)

        workflow = Workflow(self,"workflow",sftp_bucket_arn=bucket.bucket_arn)
      
        server = Server(self,"myserver",authfunc_arn=auth.function_arn, workflowDetailsProperty=workflow.get_workflowDetailsProperty())
        policyStatement.add_condition("StringNotEquals", {"s3:ExistingObjectTag/Virus_Scan_Result": "CLEAN","aws:PrincipalArn":[workflow.get_lambda_service_role(),auth.user_role_arn]})

        auth.grant_invoke_transfer(server_arn=server.server_arn)

        build= Build(self,"avcodebuild", workflow.get_lambda_function_arn())

        cdk.CfnOutput(self, 'SFTPEndpoint', value=server.serverID+".server.transfer."+Stack.of(self).region+".amazonaws.com")
        cdk.CfnOutput(self, 'SFTPBucket', value= bucket.bucket_name)        
        cdk.CfnOutput(self, 'Password', value=auth.password)    
        cdk.CfnOutput(self, 'Username', value=auth.username)    

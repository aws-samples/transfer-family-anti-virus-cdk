from aws_cdk import (
    # Duration,
    Stack,
    aws_iam as iam,
    aws_transfer as tfx,
    aws_lambda as _lambda,
    aws_s3 as s3,
    # aws_sqs as sqs,
)
#from aws_cdk.core Arn 
from constructs import Construct
import aws_cdk as cdk



class Server(Construct):
    @property
    def server_arn(self):
        return self._server.attr_arn

    @property
    def serverID(self):
        return self._server.attr_server_id

    def __init__(self, scope: Construct, construct_id: str, authfunc_arn:str, workflowDetailsProperty:tfx.CfnServer.WorkflowDetailsProperty, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)




        logging_role = iam.Role(self,'LoggingRole',
        assumed_by=iam.ServicePrincipal(service='transfer'),
        managed_policies=[
            iam.ManagedPolicy.from_aws_managed_policy_name('CloudWatchLogsFullAccess')
        ])

        self._server = tfx.CfnServer(self,'TransferServer',
            domain='S3',
            endpoint_type='PUBLIC',
            logging_role= logging_role.role_arn,
            protocols=['SFTP'],
            identity_provider_type= "AWS_LAMBDA",
            identity_provider_details=tfx.CfnServer.IdentityProviderDetailsProperty(
                function=authfunc_arn,
                
            ),
            workflow_details= tfx.CfnServer.WorkflowDetailsProperty(
                on_upload=[workflowDetailsProperty])

        )

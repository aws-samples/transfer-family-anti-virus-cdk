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

    def __init__(self, scope: Construct, construct_id: str, authfunc_arn:str, workflowDetailsProperty:tfx.CfnServer.WorkflowDetailsProperty, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        # #
        # # Lambda execution role
        # #
        # lambdaExecutionRole = iam.Role(self,'AuthLambdaExecutionRole',
        # assumed_by=iam.ServicePrincipal(service='lambda'),
        # managed_policies=[
        #     iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole')
        # ])
        # lambdaExecutionRole.attach_inline_policy(iam.Policy(self,"getsecretspolicy",
        #     statements=[
        #         iam.PolicyStatement(
        #             actions=["secretsmanager:GetSecretValue"],
        #             resources= ["arn:aws:secretsmanager:*:*:secret:SFTP/*"]
        #             )
        #         ]
        #     )

        # )
        # #
        # # Lambda authentication code
        # #
        # auth_lambda = _lambda.Function(
        #     self, 'AuthHandler',
        #     runtime=_lambda.Runtime.PYTHON_3_7,
        #     code=_lambda.Code.from_asset('constructs/server/lib/src'),
        #     handler='smauthentication.lambda_handler',
        #     environment={
        #         "SecretsManagerRegion":cdk.Stack.of(self).region
        #     },
        #     role=lambdaExecutionRole
        # )


        logging_role = iam.Role(self,'LoggingRole',
        assumed_by=iam.ServicePrincipal(service='transfer'),
        managed_policies=[
            iam.ManagedPolicy.from_aws_managed_policy_name('CloudWatchLogsFullAccess')
        ])

        #self.transfer_workflow = TransferWorkflowConstruct(self,'Workflow', **kwargs)
        self._server = tfx.CfnServer(self,'TransferServer',
            domain='S3',
            endpoint_type='PUBLIC',
            logging_role= logging_role.role_arn,
            protocols=['SFTP'],
            identity_provider_type= "AWS_LAMBDA",
            identity_provider_details=tfx.CfnServer.IdentityProviderDetailsProperty(
                #directory_id="directoryId",
                function=authfunc_arn,
                #invocation_role="invocationRole",
                
            ),
            workflow_details= tfx.CfnServer.WorkflowDetailsProperty(
                on_upload=[workflowDetailsProperty])

        )

        # #
        # # Lambda invoke permission to the sftp server
        # #   
        # servicePrincipal=iam.ServicePrincipal("transfer.amazonaws.com")
        # servicePrincipalWithConditions = iam.PrincipalWithConditions(servicePrincipal, 
        #     {
        #         "ArnLike":{
        #             "aws:SourceArn":self.server.attr_arn
        #         }
        #     }
        # )
        # auth_lambda.grant_invoke(
        #     servicePrincipalWithConditions
        # )
        # #
        # # Create s3 bucket for sftp
        # #
        # bucket = s3.Bucket(self,'Bucket',
        #     removal_policy= cdk.RemovalPolicy.DESTROY)


        #
        # bucket policy to allow scanfile lambda to getobject and tag object
        #
        # bucket.add_to_resource_policy(
        #     iam.PolicyStatement(
        #         effect=iam.Effect.ALLOW,
        #         principals=[iam.ServicePrincipal("lambda")],
        #         actions=["s3:GetObject","s3:TagObject"],
        #         resources=["*"],
        #         conditions=
        #             {
        #             "StringEquals":{"aws:SourceArn":auth_lambda.function_arn }
        #             }
                
        #     )
        # )

        # #
        # # Create iam user policy 
        # #
        # user_policy = iam.PolicyDocument(
        #     statements=[

        #     iam.PolicyStatement(
        #         actions=["s3:ListBucket","s3:GetBucketLocation","s3:ListAllMyBuckets"
        #         ],
        #         resources=["*"]
        #     ),
        #         iam.PolicyStatement(
        #             actions=["s3:PutObject", "s3:GetObject","s3:DeleteObject",
        #             "s3:DeleteObjectVersion", "s3:GetObjectVersion", "s3:GetObjectACL",
        #             "s3:PutObjectACL"
        #             ],
        #             resources=[bucket.bucket_arn+"/*",
        #                 bucket.bucket_arn
        #             ]
        #     ) 
        #     ]
        # )



        # user_role = iam.Role(self, "UserRole",
        #     assumed_by=iam.ServicePrincipal(service='transfer'),
        #     description="VirusScan User Role",
        #     inline_policies={"userpolicy":user_policy}
        # )

        # #
        # # Create client1 secret
        # #
        
        # #
        # # Assign property values
        # #
        # self._bucket_arn = bucket.bucket_arn


        # cdk.CfnOutput(self, 'UserRoleArn', value=user_role.role_arn)
        # cdk.CfnOutput(self, 'UserHomeDirectory', value="/"+bucket.bucket_name)
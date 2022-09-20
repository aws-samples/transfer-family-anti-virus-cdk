from aws_cdk import (
    # Duration,
    Stack,
    aws_iam as iam,
    aws_transfer as tfx,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_secretsmanager as sm,
    # aws_sqs as sqs,
)
#from aws_cdk.core Arn 
from constructs import Construct
import aws_cdk as cdk



class Auth(Construct):

    @property
    def function_arn(self):
        return self._auth_lambda.function_arn

    def __init__(self, scope: Construct, construct_id: str, sftp_bucket_arn:str, sftp_bucket_name:str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #sftp_bucket_arn = sftp_bucket.bucket_arn
        #
        # Lambda execution role
        #
        lambdaExecutionRole = iam.Role(self,'AuthLambdaExecutionRole',
        assumed_by=iam.ServicePrincipal(service='lambda'),
        managed_policies=[
            iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole')
        ])
        lambdaExecutionRole.attach_inline_policy(iam.Policy(self,"getsecretspolicy",
            statements=[
                iam.PolicyStatement(
                    actions=["secretsmanager:GetSecretValue"],
                    resources= ["arn:aws:secretsmanager:*:*:secret:SFTP/*"]
                    )
                ]
            )

        )
        #
        # Lambda authentication code
        #
        self._auth_lambda = _lambda.Function(
            self, 'AuthHandler',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.from_asset('constructs/auth/lib/src'),
            handler='smauthentication.lambda_handler',
            environment={
                "SecretsManagerRegion":cdk.Stack.of(self).region
            },
            role=lambdaExecutionRole
        )

        #
        # Create iam user policy 
        #
        user_policy = iam.PolicyDocument(
            statements=[

            iam.PolicyStatement(
                actions=["s3:ListBucket","s3:GetBucketLocation","s3:ListAllMyBuckets"
                ],
                resources=["*"]
            ),
                iam.PolicyStatement(
                    actions=["s3:PutObject", "s3:GetObject","s3:DeleteObject",
                    "s3:DeleteObjectVersion", "s3:GetObjectVersion", "s3:GetObjectACL",
                    "s3:PutObjectACL"
                    ],
                    resources=[sftp_bucket_arn+"/*",
                        sftp_bucket_arn
                    ]
            ) 
            ]
        )



        user_role = iam.Role(self, "UserRole",
            assumed_by=iam.ServicePrincipal(service='transfer'),
            description="VirusScan User Role",
            inline_policies={"userpolicy":user_policy}
        )

        #
        # Create client1 secret
        #
        sm.Secret(self,"client1",
            secret_name="SFTP/client1",
            secret_object_value={
                "Password":cdk.SecretValue.unsafe_plain_text("password1"),
                "Role":cdk.SecretValue.unsafe_plain_text(user_role.role_arn),
                "HomeDirectory":cdk.SecretValue.unsafe_plain_text("/"+sftp_bucket_name)
            }

        )

        cdk.CfnOutput(self, 'UserRoleArn', value=user_role.role_arn)

    def grant_invoke_transfer(self, server_arn:str):
        #
        # Lambda invoke permission to the sftp server
        #   
        servicePrincipal=iam.ServicePrincipal("transfer.amazonaws.com")
        servicePrincipalWithConditions = iam.PrincipalWithConditions(servicePrincipal, 
            {
                "ArnLike":{
                    "aws:SourceArn":server_arn
                }
            }
        )
        self._auth_lambda.grant_invoke(
            servicePrincipalWithConditions
        )        
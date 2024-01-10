# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import aws_cdk as cdk
from constructs import Construct
import os.path
from aws_cdk import (
    aws_s3_assets as s3_assets,
    aws_codebuild as codebuild,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as _lambda
)

class Build(Construct):

    def __init__(self, scope: Construct, construct_id: str, lambda_func_arn: str , **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        repository = ecr.CfnRepository(self, "AVScanRepo", repository_name="clamav-scan-file")

        abspath = os.path.abspath(os.path.join(__file__,"../../.."))
        avScanAsset = s3_assets.Asset(self, "AVScanAsset",
                         path=os.path.join(abspath, "workflow/lib/src/scanfile"))

        avScanproject=codebuild.Project(self, "AVScanUpdateDefinitions",
                            source=codebuild.Source.s3(
                                bucket=avScanAsset.bucket,
                                path=avScanAsset.s3_object_key
                            ),
                            environment=codebuild.BuildEnvironment(
                                        build_image=codebuild.LinuxBuildImage.STANDARD_6_0,
                                        privileged=True
                            ),
                            environment_variables={
                                    "REPO_URI": codebuild.BuildEnvironmentVariable(
                                    value=repository.attr_repository_uri),
                                    "AWS_DEFAULT_REGION": codebuild.BuildEnvironmentVariable(
                                    value=repository.stack.region),
                                    "AWS_ACCOUNT_ID": codebuild.BuildEnvironmentVariable(
                                    value=repository.stack.account)
                            })

        avScanproject.add_to_role_policy(
            iam.PolicyStatement(
                    actions = ["ecr:GetAuthorizationToken"],
                    resources = ["*"],
                    effect = iam.Effect.ALLOW
                ))

        avScanproject.add_to_role_policy(
            iam.PolicyStatement(
                    actions = ["ecr:CompleteLayerUpload","ecr:UploadLayerPart","ecr:InitiateLayerUpload","ecr:BatchCheckLayerAvailability","ecr:PutImage"],
                    resources = [repository.attr_arn],
                    effect = iam.Effect.ALLOW
                ))

        update_func_policies = iam.PolicyDocument(
            statements=[
                    iam.PolicyStatement(
                            actions = ["lambda:UpdateFunctionCode"],
                            resources = [repository.attr_arn],
                            effect = iam.Effect.ALLOW
                    ),
                    iam.PolicyStatement(
                            actions = ["ecr:SetRepositoryPolicy","ecr:GetRepositoryPolicy"],
                            resources = [lambda_func_arn],
                            effect = iam.Effect.ALLOW
                    )
            ]
        )

        update_func_role = iam.Role(self, "Update_Defintions_Role",
            assumed_by=iam.ServicePrincipal(service='lambda'),
            description="AV Definitions update role",
            inline_policies={"userpolicy":update_func_policies}
        )

        func = _lambda.Function(
            self, 'updateAVdefinitions',
            runtime=_lambda.Runtime.PYTHON_3_12,
            code=_lambda.Code.from_asset('constructs/build/lib/src'),
            handler='updatefunc.lambda_handler',
            environment={
                "imageuri":repository.attr_repository_uri,
                "funcname":lambda_func_arn
            },
            role=update_func_role
        )

        updatefuncrule = avScanproject.on_build_succeeded("eventsuccessid")
        updatefuncrule.add_target(targets.LambdaFunction(func))
        
        rule = events.Rule(self, "AV-updates-rule",
                    schedule=events.Schedule.cron(minute='0',hour='5',day='*',month='*',year='*'))
        
        rule.add_target(targets.CodeBuildProject(avScanproject))

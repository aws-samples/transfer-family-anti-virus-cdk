#!/usr/bin/env python3
from http import server
from os import environ
from os import path
import sys
from typing import List
import aws_cdk as cdk
from constructs import Construct
from aws_cdk import(
  aws_iam as iam,
  aws_transfer as tfx,
  aws_lambda as lambda_,
  aws_iam as iam,
  Size as Size
)

SRC_ROOT_DIR = path.join(path.dirname(__file__),'src')

class Workflow(Construct):

    def add_scanfile_role_policy(self,statement:iam.PolicyStatement):
        self._scan_file_function.add_to_role_policy(statement)

    def __init__(self, scope: Construct, construct_id: str, sftp_bucket_arn:str , **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #
        # Lamba execution role
        #
        lambdaRole = iam.Role(self,'LambdaRole',
            assumed_by=iam.ServicePrincipal(service='lambda'))    
        lambdaRole.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"))
        lambdaRole.add_to_policy(
            iam.PolicyStatement(
                actions = ["s3:GetObject"],
                resources = [sftp_bucket_arn+"/*"],
                effect = iam.Effect.ALLOW
            )                
        )

        self._lambda_service_role_arn = lambdaRole.role_arn

        self._scan_file_function = lambda_.DockerImageFunction(self,'ScanFile',
            description='Scans incoming file from TransferFamily Server',
            timeout= cdk.Duration.seconds(600),
            architecture= lambda_.Architecture.X86_64,
            tracing= lambda_.Tracing.ACTIVE,
            ephemeral_storage_size = Size.gibibytes(10),
            code = lambda_.DockerImageCode.from_image_asset(
                directory=path.join(SRC_ROOT_DIR,'scanfile'),build_args={"--platform": "linux/amd64"}),
            role=lambdaRole,
            memory_size=2048,
        )

        self._lambda_arn = self._scan_file_function.function_arn

        self._workflow = tfx.CfnWorkflow(self,'VirusScanWorkflow',
        steps=[
            tfx.CfnWorkflow.WorkflowStepProperty(
            type= "CUSTOM",
            custom_step_details={
                "Name":"VirusScan",
                "Target": self._scan_file_function.function_arn,
                "TimeoutSeconds": self._scan_file_function.timeout.to_seconds()
            }),
            tfx.CfnWorkflow.WorkflowStepProperty(
                type= "TAG",
                tag_step_details={
                    "Name": 'TAG_SUCCESS',
                    "Tags": [{
                        "Key": 'VIRUS_SCAN_RESULT',
                        "Value": 'CLEAN'
                    }]})
        ],
        on_exception_steps=[
            tfx.CfnWorkflow.WorkflowStepProperty(
                type= "TAG",
                tag_step_details={
                    "Name": 'TAG_FAILURE',
                    "Tags": [{
                        "Key": 'VIRUS_SCAN_RESULT',
                        "Value": 'INFECTED'
                    }]})
        ])

        self._scan_file_function.role.attach_inline_policy(iam.Policy(self, "workflowupdate-policy",
        statements=[iam.PolicyStatement(
                    actions=["transfer:SendWorkflowStepState"],
                    resources=[self._workflow.attr_arn]
            )]
        ))   

        self._execution_role = iam.Role(self,'WorkflowExecutionRole',
            assumed_by=iam.ServicePrincipal(service='transfer')) 
        self._execution_role.add_to_policy(
            iam.PolicyStatement(
                actions = ["s3:PutObjectTagging"],
                resources = [sftp_bucket_arn+"/*"],
                effect = iam.Effect.ALLOW
            )                
        )  
        self._scan_file_function.grant_invoke(self._execution_role)

    #
    # Returns WorkflowDetailProperty required during server creation
    #

    def get_workflowDetailsProperty(self)->tfx.CfnServer.WorkflowDetailProperty:
        return tfx.CfnServer.WorkflowDetailProperty(
            execution_role=self._execution_role.role_arn,
            workflow_id= self._workflow.ref
        )

    def get_lambda_service_role(self):
        return self._lambda_service_role_arn

    def get_lambda_function_arn(self):
        return self._lambda_arn
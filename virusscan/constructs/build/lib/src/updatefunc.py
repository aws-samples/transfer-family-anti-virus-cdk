# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import boto3
import os

client = boto3.client('lambda')

def lambda_handler(event,context):
    imageuri = os.environ['imageuri']
    funcname = os.environ['funcname']
    response = client.update_function_code(
    FunctionName=funcname,
    ImageUri=imageuri+':latest',
    Architectures=['x86_64'])
    return response
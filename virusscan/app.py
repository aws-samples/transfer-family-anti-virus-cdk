# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
#!/usr/bin/env python3
import os

import aws_cdk as cdk
from aws_cdk import(
    App
)
from lib.virusscan_stack import VirusScanStack
app = cdk.App()
virusscanstack = VirusScanStack(app,"VirusScan")
app.synth()

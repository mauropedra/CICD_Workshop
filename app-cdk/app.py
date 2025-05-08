#!/usr/bin/env python3
import os

import aws_cdk as cdk

from app_cdk.app_cdk_stack import AppCdkStack
from app_cdk.pipeline_cdk_stack import PipelineCdkStack
from app_cdk.ecr_cdk_stack import EcrCdkStack

app = cdk.App()

ecr_stack = EcrCdkStack(
    app,
    'ecr-stack'
)

test_app_stack = AppCdkStack(
    app,
    'test-app-stack',
    ecr_repository = ecr_stack.ecr_data
)

pipeline_stack = PipelineCdkStack(
    app,
    'pipeline-stack',
    ecr_repository = ecr_stack.ecr_data,
)

app.synth()

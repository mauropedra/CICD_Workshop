#!/usr/bin/env python3
import aws_cdk as cdk

from app_cdk.app_cdk_stack import AppCdkStack
from app_cdk.pipeline_cdk_stack import PipelineCdkStack

app = cdk.App()

app_stack = AppCdkStack(
    app,
    'app-stack'
)

pipeline_stack = PipelineCdkStack(
    app,
    'pipeline-stack',
)

app.synth()

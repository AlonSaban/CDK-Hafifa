#!/usr/bin/env python3
import aws_cdk as cdk
from infrastructure_stack import S3ToEC2Stack
from pipeline_stack import PipelineStack

app = cdk.App()
ENV = cdk.Environment(account="472043656714", region="eu-west-1")
S3ToEC2Stack(app, "S3ToEC2Stack", env=ENV)
PipelineStack(app, "PipelineStack", env=ENV)
app.synth()
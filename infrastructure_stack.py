from aws_cdk import (
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_lambda_event_sources as lambda_event_sources,
    aws_ssm as ssm,
    Stack,
    RemovalPolicy,
)

from constructs import Construct


class S3ToEC2Stack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create S3 bucket
        bucket = s3.Bucket(
            self,
            "AlonBucket2",
            bucket_name="alon-bucket2",
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Reference an existing VPC by its ID
        vpc = ec2.Vpc.from_lookup(
            self,
            "spoke-vpc",
            vpc_id="vpc-0eec10f30e39be533",
        )

        subnet = ec2.Subnet.from_subnet_attributes(
            self,
            "SpokeSubnetAz1",
            availability_zone="eu-west-1a",
            subnet_id="subnet-0b0f6400b1ce714fa",
        )

        # Reference an existing Security Group by its ID
        security_group = ec2.SecurityGroup.from_security_group_id(
            self, "launch-wizard-alon", security_group_id="sg-04b45d6bc7f9fe45a"
        )

        ec2_role = iam.Role(
            self,
            "EC2Role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMFullAccess"),
            ],
        )

        # Create EC2 instance
        ec2_instance = ec2.Instance(
            self,
            "EC2Instance",
            instance_type=ec2.InstanceType("t3.medium"),
            machine_image=ec2.MachineImage.latest_amazon_linux2(),
            role=ec2_role,
            vpc=vpc,
            security_group=security_group,
            vpc_subnets=ec2.SubnetSelection(subnets=[subnet]),
        )

        # Store EC2 instance ID in Parameter Store
        ssm.StringParameter(
            self,
            "EC2InstanceIDParameter",
            parameter_name="/myapp/ec2-instance-id",
            string_value=ec2_instance.instance_id,
        )

        # Store destination path in Parameter Store
        ssm.StringParameter(
            self,
            "EC2DestinationPathParameter",
            parameter_name="/myapp/ec2-destination-path",
            string_value="/home/ec2-user",
        )

        # IAM role for Lambda to interact with EC2 and S3
        lambda_role = iam.Role(
            self,
            "LambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSSMManagedInstanceCore"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMFullAccess"),
            ],
        )

        # Create the Lambda function
        lambda_function = _lambda.Function(
            self,
            "S3ToEC2Function",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            role=lambda_role,
        )

        # Add S3 event notification to trigger Lambda
        lambda_function.add_event_source(
            lambda_event_sources.S3EventSource(
                bucket, events=[s3.EventType.OBJECT_CREATED]
            )
        )

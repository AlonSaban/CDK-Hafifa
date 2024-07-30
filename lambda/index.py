import json
import time
import boto3


def lambda_handler(event):
    # Initialize S3 and SSM clients
    s3 = boto3.client("s3")
    ssm = boto3.client("ssm")

    # Get bucket and key from the S3 event
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = event["Records"][0]["s3"]["object"]["key"]


    print(f"Processing file: {key} from bucket: {bucket}")

    try:
        # Get EC2 instance ID from Parameter Store
        ec2_instance_id = ssm.get_parameter(Name="/myapp/ec2-instance-id")["Parameter"][
            "Value"
        ]
        print(f"EC2 Instance ID: {ec2_instance_id}")

        # Get destination path from Parameter Store
        destination_path = ssm.get_parameter(Name="/myapp/ec2-destination-path")[
            "Parameter"
        ]["Value"]
        print(f"Destination Path: {destination_path}")

        # Copy file to EC2 instance using SSM Send Command
        response = ssm.send_command(
            InstanceIds=[ec2_instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={
                "commands": [
                    f"aws s3 cp s3://{bucket}/{key} {destination_path}",
                    f'echo "File copied successfully: {key}"',
                    f"ls -l {destination_path}/{key}",
                ]
            },
        )

        # Get the command ID
        command_id = response["Command"]["CommandId"]
        print(f"SSM Command ID: {command_id}")

        # Wait for the command to complete (max 2 minutes)
        start_time = time.time()
        while time.time() - start_time < 120:
            time.sleep(10)  # Wait for 10 seconds before checking again
            result = ssm.get_command_invocation(
                CommandId=command_id, InstanceId=ec2_instance_id
            )
            status = result["Status"]
            print(f"Command status: {status}")
            if status in ["Success", "Failed", "Cancelled", "TimedOut"]:
                break

        if status == "Success":
            print(f"Command output: {result.get('StandardOutputContent', 'No output')}")
            # Delete the file from S3
            s3.delete_object(Bucket=bucket, Key=key)
            print(f"File {key} deleted from {bucket}")
        else:
            print(f"Command failed. Status: {status}")
            print(
                f"Error details: {result.get('StandardErrorContent', 'No error details')}"
            )
            raise Exception(f"Failed to copy file. Status: {status}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error processing file {key}: {str(e)}"),
        }

    return {"statusCode": 200, "body": json.dumps(f"File {key} processed successfully")}

from constructs import Construct
from aws_cdk import (
    Stack,
    pipelines,
    SecretValue,
)

class PipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        repo_name = "CDK-Hafifa"
        github_branch = "main"
        repo_owner = "AlonSaban"

        # Retrieve GitHub token from AWS Secrets Manager
        secret_name = "hafifa/github_token"

        github_secret = SecretValue.secrets_manager(
            secret_id=secret_name, json_field="Github-Hafifa"
        )

        # Create the source from GitHub
        source = pipelines.CodePipelineSource.git_hub(
            repo_string=f"{repo_owner}/{repo_name}",
            branch=github_branch,
            authentication=github_secret,
        )

        # Add a lint step as a pre-step
        lint_step = pipelines.CodeBuildStep(
            "Lint",
            input=source,
            commands=[
                "pip install -r requirements.txt",
                "pip install pylint",
                "pylint **/*.py",
            ],
        )

        # Create the synth step
        synth_step = pipelines.ShellStep(
            "Synth",
            input=source,
            commands=[
                "pip install -r requirements.txt",
                "npm install -g aws-cdk",
                "cdk synth",
            ],
        )

        # Create the pipeline with the synth step
        pipeline = pipelines.CodePipeline(
            self,
            "Pipeline",
            pipeline_name="LintAndSynthPipeline",
            synth=synth_step,
        )

        # Add the lint step as a pre-step to the pipeline
        pipeline.add_wave("lint", pre=[lint_step])

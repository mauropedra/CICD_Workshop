from constructs import Construct
from aws_cdk import (
    Stack,
    CfnOutput,
    aws_codeconnections as codeconnections,
    aws_codepipeline as codepipeline,
    aws_codebuild as codebuild,
    aws_codepipeline_actions as codepipeline_actions,
)

class PipelineCdkStack(Stack):

    def __init__(self, scope: Construct, id: str, ecr_repository, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Creates a CodeConnections resource called 'CICD_Workshop_Connection'
        SourceConnection = codeconnections.CfnConnection(self, "CICD_Workshop",
                connection_name="CICD_Workshop_Connection",
                provider_type="GitHub",
        )

        pipeline = codepipeline.Pipeline(
            self, 'CICD_Pipeline',
            cross_account_keys = False,
            pipeline_type=codepipeline.PipelineType.V2,
            execution_mode=codepipeline.ExecutionMode.QUEUED
        )

        code_quality_build = codebuild.PipelineProject(
            self, 'CodeBuild',
            build_spec = codebuild.BuildSpec.from_source_filename('./buildspec_test.yml'),
            environment = codebuild.BuildEnvironment(
                build_image = codebuild.LinuxBuildImage.STANDARD_5_0,
                privileged = True,
                compute_type = codebuild.ComputeType.LARGE,
            ),
        )

        source_output = codepipeline.Artifact()
        unit_test_output = codepipeline.Artifact()

        source_action = codepipeline_actions.CodeStarConnectionsSourceAction(
          action_name = 'GitHub',
          owner = "mauropedra",
          repo = "CICD_Workshop",
          output = source_output,
          branch = "main",
          trigger_on_push = True,
          connection_arn = "arn:aws:codeconnections:us-east-2:676393689272:connection/e35ed35a-01ed-4645-a89e-c6dc34a57ec9"
        )

        pipeline.add_stage(
          stage_name = 'Source',
          actions = [source_action]
        )

        build_action = codepipeline_actions.CodeBuildAction(
            action_name = 'Unit-Test',
            project = code_quality_build,
            input = source_output,  # The build action must use the CodeStarConnectionsSourceAction output as input.
            outputs = [unit_test_output]
        )

        pipeline.add_stage(
            stage_name = 'Code-Quality-Testing',
            actions = [build_action]
        )

        CfnOutput(
            self, 'SourceConnectionArn',
            value = SourceConnection.attr_connection_arn
        )

        CfnOutput(
            self, 'SourceConnectionStatus',
            value = SourceConnection.attr_connection_status
        )
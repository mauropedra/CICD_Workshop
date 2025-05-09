import os
from constructs import Construct
from aws_cdk import (
    Stack,
    CfnOutput,
    aws_codecommit as codecommit,
    aws_codepipeline as codepipeline,
    aws_codebuild as codebuild,
    aws_codepipeline_actions as codepipeline_actions,
    aws_iam as iam,
    aws_codedeploy as codedeploy,
    aws_cloudwatch as cloudwatch,
    Duration as duration,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_events as events,
    aws_events_targets as targets
)


class PipelineCdkStack(Stack):

    def __init__(self, scope: Construct, id: str, ecr_repository, test_app_fargate, prod_app_fargate, green_target_group, green_load_balancer_listener, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Pipeline code will go here
        repo = codecommit.Repository(
            self, 'CICD_Workshop',
            repository_name='CICD_Workshop',
            description='Repository for my application code and infrastructure'
        )

        pipeline = codepipeline.Pipeline(
            self, 'CICD_Pipeline',
            cross_account_keys=False
        )

        code_quality_build = codebuild.PipelineProject(
            self, 'Code Quality',
            build_spec=codebuild.BuildSpec.from_source_filename('./buildspec_test.yml'),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_5_0,
                privileged=True,
                compute_type=codebuild.ComputeType.LARGE,
            ),
        )

        docker_build_project = codebuild.PipelineProject(
            self, 'Docker Build',
            build_spec=codebuild.BuildSpec.from_source_filename('./buildspec_docker.yml'),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_5_0,
                privileged=True,
                compute_type=codebuild.ComputeType.LARGE,
                environment_variables={
                    'IMAGE_TAG': codebuild.BuildEnvironmentVariable(
                        type=codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                        value='latest'
                    ),
                    'IMAGE_REPO_URI': codebuild.BuildEnvironmentVariable(
                        type=codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                        value=ecr_repository.repository_uri
                    ),
                    'AWS_DEFAULT_REGION': codebuild.BuildEnvironmentVariable(
                        type=codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                        value=os.environ['CDK_DEFAULT_REGION']
                    )
                }
            ),
        )

        docker_build_project.add_to_role_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                'ecr:GetAuthorizationToken',
                'ecr:BatchCheckLayerAvailability',
                'ecr:GetDownloadUrlForLayer',
                'ecr:GetRepositoryPolicy',
                'ecr:DescribeRepositories',
                'ecr:ListImages',
                'ecr:DescribeImages',
                'ecr:BatchGetImage',
                'ecr:InitiateLayerUpload',
                'ecr:UploadLayerPart',
                'ecr:CompleteLayerUpload',
                'ecr:PutImage'
            ],
            resources=['*'],
        ))

        source_output = codepipeline.Artifact()
        unit_test_output = codepipeline.Artifact()
        docker_build_output = codepipeline.Artifact()

        source_action = codepipeline_actions.CodeCommitSourceAction(
            action_name='CodeCommit',
            repository=repo,
            output=source_output,
            branch='main'
        )

        pipeline.add_stage(
            stage_name='Source',
            actions=[source_action]
        )

        build_action = codepipeline_actions.CodeBuildAction(
            action_name='Unit-Test',
            project=code_quality_build,
            input=source_output,
            outputs=[unit_test_output]
        )

        pipeline.add_stage(
            stage_name='Code-Quality-Testing',
            actions=[build_action]
        )

        docker_build_action = codepipeline_actions.CodeBuildAction(
            action_name='Docker-Build',
            project=docker_build_project,
            input=source_output,
            outputs=[docker_build_output]
        )

        pipeline.add_stage(
            stage_name='Docker-Build',
            actions=[docker_build_action]
        )

        pipeline.add_stage(
            stage_name='Deploy-Test',
            actions=[
                codepipeline_actions.EcsDeployAction(
                    action_name='Deploy-Test',
                    service=test_app_fargate.service,
                    input=docker_build_output
                )
            ]
        )

        ecs_code_deploy_app = codedeploy.EcsApplication(self, "my-app",
            application_name="my-app"
        )

        prod_ecs_deployment_group = codedeploy.EcsDeploymentGroup(self, "my-app-dg",
            service=prod_app_fargate.service,
            blue_green_deployment_config=codedeploy.EcsBlueGreenDeploymentConfig(
                blue_target_group=prod_app_fargate.target_group,
                green_target_group=green_target_group,
                listener=prod_app_fargate.listener,
                test_listener=green_load_balancer_listener
            ),
            deployment_config=codedeploy.EcsDeploymentConfig.LINEAR_10_PERCENT_EVERY_1_MINUTES,
            application=ecs_code_deploy_app
        )

        pipeline.add_stage(
            stage_name='Deploy-Production',
            actions=[
                codepipeline_actions.ManualApprovalAction(
                action_name='Approve-Prod-Deploy',
                run_order=1
              ),
              codepipeline_actions.CodeDeployEcsDeployAction(
                  action_name='ABlueGreen-deployECS',
                  deployment_group=prod_ecs_deployment_group,
                  app_spec_template_input=source_output,
                  task_definition_template_input=source_output,
                  run_order=2
              )
            ]
        )
        CfnOutput(
            self, 'CodeCommitRepositoryUrl',
            value=repo.repository_clone_url_grc
        )

        build_rate = cloudwatch.GraphWidget(
        title="Build Successes and Failures",
        width=6,
        height=6,
        view=cloudwatch.GraphWidgetView.PIE,
        left=[
            cloudwatch.Metric(
                namespace="AWS/CodeBuild",
                metric_name="SucceededBuilds",
                statistic='sum',
                label='Succeeded Builds',
                period=duration.days(30)
            ),
            cloudwatch.Metric(
                namespace="AWS/CodeBuild",
                metric_name="FailedBuilds",
                statistic='sum',
                label='Failed Builds',
                period=duration.days(30)
            )
        ]
        )

        builds_count = cloudwatch.SingleValueWidget(
            title="Successes and Failures",
            width=6,
            height=6,
            metrics=[
                cloudwatch.Metric(
                    namespace="AWS/CodeBuild",
                    metric_name="Builds",
                    statistic='sum',
                    label='Builds',
                    period=duration.days(30)
                )
            ]
        )

        average_duration = cloudwatch.GaugeWidget(
            title="Average Build Time",
            width=6,
            height=6,
            metrics=[
                cloudwatch.Metric(
                    namespace="AWS/CodeBuild",
                    metric_name="Duration",
                    statistic='Average',
                    label='Duration',
                    period=duration.hours(1)
                )
            ],
            left_y_axis={
                'min': 0,
                'max': 300,
            }
        )

        queued_duration = cloudwatch.GaugeWidget(
            title="Build Queue Duration",
            width=6,
            height=6,
            metrics=[
                cloudwatch.Metric(
                    namespace="AWS/CodeBuild",
                    metric_name="QueuedDuration",
                    statistic='Average',
                    label='Duration',
                    period=duration.hours(1)
                )
            ],
            left_y_axis={
                'min': 0,
                'max': 60,
            }
        )

        download_duration = cloudwatch.GraphWidget(
        title="Checkout Duration",
        width=24,
        height=5,
        left=[
            cloudwatch.Metric(
                namespace="AWS/CodeBuild",
                metric_name="DownloadSourceDuration",
                statistic='max',
                label='Duration',
                period=duration.minutes(5),
                color=cloudwatch.Color.PURPLE
            )
        ]
        )
  
        dashboard = cloudwatch.Dashboard(
            self, 'CICD_Dashboard',
            dashboard_name='CICD_Dashboard',
            widgets=[
                [build_rate, builds_count, average_duration, queued_duration, download_duration]
            ]
        )
        # Create SNS topic for failures
        failure_topic = sns.Topic(
            self, "BuildFailure",
            display_name="BuildFailure"
        )

        # Create a subscription for email
        email_subscription = subscriptions.EmailSubscription('YOUR_EMAIL_ADDRESS@your_provider.com')

        # Add the email subscription to the failureTopic
        failure_topic.add_subscription(email_subscription)

        # CloudWatch Event Rule for pipeline failures
        pipeline_failure_rule = events.Rule(self, "PipelineFailureRule",
          description="Notify on pipeline failures",
          event_pattern={
            "source": ["aws.codepipeline"],
            "detail_type": ["CodePipeline Pipeline Execution State Change"],
            "detail": {
                "state": ["FAILED"]
            }
          }
        )

        # Add SNS topic as a target with input transformer
        pipeline_failure_rule.add_target(targets.SnsTopic(
          failure_topic,
          message=events.RuleTargetInput.from_text(
            f"Pipeline Failure Detected! Pipeline: {events.EventField.from_path('$.detail.pipeline')} "
            f"Execution ID: {events.EventField.from_path('$.detail.execution-id')}"
          )
        ))

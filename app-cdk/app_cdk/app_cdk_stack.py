from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    Duration,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
)
from constructs import Construct

class AppCdkStack(Stack):

    @property
    def ecs_service_data(self):
        return self.service

    def __init__(self, scope: Construct, construct_id: str, ecr_repository, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc(
            self, 'my-vpc',
        )

        ecs_cluster = ecs.Cluster(
            self, 'ecs-cluster',
            vpc = vpc
        )

        service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, 'service',
            cluster = ecs_cluster,
            memory_limit_mib = 1024,
            desired_count = 1,
            cpu = 512,
            task_image_options = ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_ecr_repository(ecr_repository),
                container_port = 8081,
                container_name = 'my-app'
            )
        )

        service.target_group.configure_health_check(
            healthy_threshold_count = 2,
            unhealthy_threshold_count = 2,
            timeout = Duration.seconds(10),
            interval = Duration.seconds(11)
        )

        service.target_group.set_attribute('deregistration_delay.timeout_seconds', '5')

        self.service = service

        # The code that defines your stack goes here

        # example resource
        # queue = sqs.Queue(
        #     self, "AppCdkQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )

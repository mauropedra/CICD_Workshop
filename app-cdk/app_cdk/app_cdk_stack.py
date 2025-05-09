from constructs import Construct
from aws_cdk import (
    Stack,
    Duration,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_elasticloadbalancingv2 as elbv2,  
)

class AppCdkStack(Stack):

    @property
    def ecs_service_data(self):
        return self.service
      
    @property
    def green_target_group(self):
        return self.target_group

    @property
    def green_load_balancer_listener(self):
        return self.load_balancer_listener      

    def __init__(self, scope: Construct, construct_id: str, ecr_repository, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc(
            self, 'my-vpc'
        )

        ecs_cluster = ecs.Cluster(
            self, 'ecs-cluster',
            vpc = vpc
        )

        if construct_id == "prod-app-stack":
            # Prod service definition
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
                ),
                deployment_controller = ecs.DeploymentController(
                    type = ecs.DeploymentControllerType.CODE_DEPLOY
                )    
            )

            green_load_balancer_listener=service.load_balancer.add_listener(
                'green_load_balancer_listener',
                port = 81,
                protocol = elbv2.ApplicationProtocol.HTTP,
            )

            green_target_group=elbv2.ApplicationTargetGroup(
                self, 'green_target_group',
                port = 80,
                target_type = elbv2.TargetType.IP,
                vpc = vpc
            )

            green_load_balancer_listener.add_target_groups(
                'green_target_group',
                target_groups = [green_target_group]
            )

            self.target_group = green_target_group
            self.load_balancer_listener = green_load_balancer_listener

        else:
            # Test service definition
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
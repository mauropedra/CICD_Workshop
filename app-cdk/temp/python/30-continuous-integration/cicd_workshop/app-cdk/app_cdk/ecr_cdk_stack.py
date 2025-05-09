from constructs import Construct
from aws_cdk import (
    Stack,
    aws_ecr as ecr,
    RemovalPolicy
)

class EcrCdkStack(Stack):

    @property
    def ecr_data(self):
        return self.ecr

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        ecr_repository = ecr.Repository(
            self, 'my-app',
            removal_policy = RemovalPolicy.DESTROY
        )

        self.ecr = ecr_repository
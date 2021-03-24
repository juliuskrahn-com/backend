from aws_cdk import core
from .constructs import Api
from . import Environment
from tools.get_testing_env_id import get_testing_env_id


class Testing(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        construct_id += get_testing_env_id()
        super().__init__(scope, construct_id, **kwargs)

        core.Tags.of(self).add("Project", "BlogBackend")
        core.Tags.of(self).add("Stack", "Testing")

        api = Api(self, f"{construct_id}Api", environment=Environment.TESTING)

        core.CfnOutput(self, "ApiIEndpoint", value=api.instance.url)  # I -> Instance

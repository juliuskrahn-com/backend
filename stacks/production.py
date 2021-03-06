from aws_cdk import core
import aws_cdk.aws_apigateway as apigw
import aws_cdk.aws_certificatemanager as cm
import aws_cdk.aws_route53 as route53
import aws_cdk.aws_route53_targets as route53_targets
from .constructs import Api
from . import Environment


class Production(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        core.Tags.of(self).add("Project", "JuliusKrahnBlogBackend")
        core.Tags.of(self).add("Environment", "Production")

        api = Api(self, f"{construct_id}Api", environment=Environment.PRODUCTION)

        api_domain_name = apigw.DomainName(
            self,
            "ApiDomainName",
            domain_name="api.juliuskrahn.com",
            certificate=cm.Certificate.from_certificate_arn(
                self,
                "blog-api-domain-name-certificate",
                "arn:aws:acm:eu-central-1:473883619336:certificate/4e5cacb4-f88b-45c3-abea-ce543b125499"
            ),
            endpoint_type=apigw.EndpointType.REGIONAL
        )

        api_domain_name.add_base_path_mapping(api.instance)

        route53.ARecord(
            self,
            "ApiARecord",
            record_name="api",
            target=route53.RecordTarget.from_alias(route53_targets.ApiGatewayDomain(api_domain_name)),
            zone=route53.HostedZone.from_lookup(self, "blog-hosted-zone", domain_name="juliuskrahn.com")
        )

from aws_cdk import core
import aws_cdk.aws_apigateway as apigw
import aws_cdk.aws_certificatemanager as cm
import aws_cdk.aws_route53 as route53
import aws_cdk.aws_route53_targets as route53_targets
from .constructs import API
from .constants import Environment


class Testing(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        core.Tags.of(self).add("project", "blog.backend")
        core.Tags.of(self).add("stack", "testing")

        # API

        api = API(self, "api", environment=Environment.TESTING)

        # API domain name

        api_domain_name = apigw.DomainName(
            self,
            "api.domainName",
            domain_name="testing.api.juliuskrahn.com",
            certificate=cm.Certificate.from_certificate_arn(
                self,
                "blog-api-testing-domain-name-certificate",
                "arn:aws:acm:us-east-1:473883619336:certificate/4cd06cae-17fc-41b2-a312-3c73d9c8a146"
            ),
            endpoint_type=apigw.EndpointType.REGIONAL
        )

        api_domain_name.add_base_path_mapping(api.instance)

        route53.ARecord(
            self,
            "api.aRecord",
            record_name="testing.api",
            target=route53.RecordTarget.from_alias(route53_targets.ApiGatewayDomain(api_domain_name)),
            zone=route53.HostedZone.from_lookup(self, "blog-hosted-zone", domain_name="juliuskrahn.com")
        )

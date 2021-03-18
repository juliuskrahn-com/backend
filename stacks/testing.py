from aws_cdk import core
import aws_cdk.aws_apigateway as apigw
import aws_cdk.aws_certificatemanager as cm
import aws_cdk.aws_route53 as route53
import aws_cdk.aws_route53_targets as route53_targets
from .constructs import API


class Testing(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        core.Tags.of(self).add("Project", "Blog")
        core.Tags.of(self).add("Environment", "Testing")

        # API

        api = API(self, "blog-api")

        # API domain name

        api_domain_name = apigw.DomainName(
            self,
            "blog-api-domain-name",
            domain_name="testing.api.juliuskrahn.com",
            certificate=cm.Certificate.from_certificate_arn(
                self,
                "blog-api-testing-domain-name-certificate",
                "arn:aws:acm:us-east-1:473883619336:certificate/4cd06cae-17fc-41b2-a312-3c73d9c8a146"
            ),
            endpoint_type=apigw.EndpointType.EDGE
        )

        api_domain_name.add_base_path_mapping(api)

        route53.ARecord(
            self,
            "blog-api-testing-a-record",
            record_name="testing.api",
            target=route53.RecordTarget.from_alias(route53_targets.ApiGatewayDomain(api_domain_name)),
            zone=route53.HostedZone.from_lookup(self, "blog-hosted-zone", domain_name="juliuskrahn.com")
        )

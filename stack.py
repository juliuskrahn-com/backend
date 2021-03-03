from aws_cdk import core
import aws_cdk.aws_apigateway as apigw
import aws_cdk.aws_lambda as lambda_
import aws_cdk.aws_dynamodb as dynamodb
import aws_cdk.aws_secretsmanager as sm
import aws_cdk.aws_certificatemanager as cm
import aws_cdk.aws_route53 as route53
import aws_cdk.aws_route53_targets as route53_targets


class Stack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        core.Tags.of(self).add("Project", "Blog")

        core_layer = lambda_.LayerVersion(
            self,
            "blog-core-layer",
            code=lambda_.Code.from_asset("lambda/core_layer"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_8]
        )

        proxy_fn = lambda_.Function(
            self,
            "blog-proxy-fn",
            runtime=lambda_.Runtime.PYTHON_3_8,
            handler="lambda_function.handler",
            code=lambda_.Code.from_asset("lambda/proxy"),
            layers=[core_layer]
        )

        proxy_fn_integration = apigw.LambdaIntegration(proxy_fn)

        domain_name = apigw.DomainName(
            self,
            "blog-api-domain-name",
            domain_name="api.juliuskrahn.com",
            certificate=cm.Certificate.from_certificate_arn(
                self,
                "blog-domain-name-certificate",
                "arn:aws:acm:us-east-1:473883619336:certificate/1ad12871-4b46-44ef-a24d-7af5ac43972b"
            ),
            endpoint_type=apigw.EndpointType.EDGE
        )

        api = apigw.RestApi(
            self,
            "blog-api",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS
            ),
            default_integration=proxy_fn_integration
        )

        domain_name.add_base_path_mapping(api)

        route53.ARecord(
            self,
            "blog-api-a-record",
            record_name="api",
            target=route53.RecordTarget.from_alias(route53_targets.ApiGatewayDomain(domain_name)),
            zone=route53.HostedZone.from_lookup(self, "blog-hosted-zone", domain_name="juliuskrahn.com")
        )

        api.root.add_proxy()

        article_table = dynamodb.Table(
            self,
            "blog-article-table",
            table_name="blog-article",
            partition_key=dynamodb.Attribute(name="urlTitle", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True
        )

        article_table.add_global_secondary_index(
            index_name="tagIndex",
            partition_key=dynamodb.Attribute(name="tag", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="published", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.INCLUDE,
            non_key_attributes=["urlTitle", "title", "desc"]
        )

        article_table.grant_read_write_data(proxy_fn)

        comment_table = dynamodb.Table(
            self,
            "blog-comment-table",
            table_name="blog-comment",
            partition_key=dynamodb.Attribute(name="articleUrlTitle", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST
        )

        comment_table.grant_read_write_data(proxy_fn)

        admin_key_secret = sm.Secret(
            self,
            "blog-admin-key",
            secret_name="blog-admin-key"
        )

        admin_key_secret.grant_read(proxy_fn)

from aws_cdk import core
import aws_cdk.aws_apigateway as apigw
import aws_cdk.aws_lambda as lambda_
import aws_cdk.aws_dynamodb as dynamodb
import aws_cdk.aws_secretsmanager as sm


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

        api = apigw.RestApi(
            self,
            "blog-api",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS
            ),
            default_integration=proxy_fn_integration
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

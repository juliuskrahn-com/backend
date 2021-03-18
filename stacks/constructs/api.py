import aws_cdk.core
import aws_cdk.aws_apigateway as apigw
import aws_cdk.aws_lambda as lambda_
import aws_cdk.aws_dynamodb as dynamodb
import aws_cdk.aws_secretsmanager as sm


class API(apigw.RestApi):

    def __init__(self, scope: aws_cdk.core.Construct, construct_id: str, **kwargs):
        super().__init__(
            scope,
            construct_id,
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
            ),
            default_integration=APIIntegration(self, "default"),
            deploy_options=apigw.StageOptions(
                throttling_rate_limit=256,
                throttling_burst_limit=64,  # concurrent
                caching_enabled=True,
                cache_ttl=aws_cdk.core.Duration.minutes(3)
            ),
            endpoint_configuration=apigw.EndpointConfiguration.EDGE,
            **kwargs
        )

        # Resources

        resource_article_collection = self.root.add_resource(path_part="/article")
        resource_article = self.root.add_resource(path_part="/article/{articleUrlTitle}")
        resource_article_comment_collection = self.root.add_resource(path_part="/article/{articleUrlTitle}/comments")
        resource_article_comment = self.root.add_resource(path_part="/article/{articleUrlTitle}/comments/{commentId}")
        resource_article_comment_resp_collection = self.root.add_resource(
            path_part="/article/{articleUrlTitle}/comments/{commentId}/resps")
        resource_article_comment_resp = self.root.add_resource(
            path_part="/article/{articleUrlTitle}/comments/{commentId}/resps/{respId}")
        resource_tag_collection = self.root.add_resource(path_part="/tag")
        resource_tag = self.root.add_resource(path_part="/tag/{tagName}")
        resource_admin_login = self.root.add_resource(path_part="/admin-login")

        # Integration dependencies

        #   (applied to integrations auto., accessed by integration construct via scope)

        self.lambda_layers = [
            lambda_.LayerVersion(
                self,
                "blog-middleware-layer",
                code=lambda_.Code.from_asset("../../build/middleware_layer"),
                compatible_runtimes=[lambda_.Runtime.PYTHON_3_8]
            )
        ]

        # TODO pydantic layer

        self.admin_key_secret = sm.Secret(  # read access granted in integration construct
            self,
            "blog-admin-key",
            secret_name="blog-admin-key"
        )

        self.article_table_name = construct_id + "-article-table"
        self.comment_table_name = construct_id + "-comment-table"

        #   (applied to integrations individually)

        article_table = dynamodb.Table(
            self,
            "blog-article-table",
            table_name=self.article_table_name,
            partition_key=dynamodb.Attribute(name="urlTitle", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True
        )

        article_table.add_global_secondary_index(
            index_name="tagIndex",
            partition_key=dynamodb.Attribute(name="tag", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="published", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.INCLUDE,
            non_key_attributes=["urlTitle", "title", "description"]
        )

        comment_table = dynamodb.Table(
            self,
            "blog-comment-table",
            table_name=self.comment_table_name,
            partition_key=dynamodb.Attribute(name="articleUrlTitle", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST
        )

        # Integrations

        integration_article_get = APIIntegration(self, "article_get")
        article_table.grant_read_data(integration_article_get)
        resource_article.add_method("GET", integration=integration_article_get)

        integration_article_get_collection = APIIntegration(self, "article_get_collection")
        article_table.grant_read_data(integration_article_get_collection)
        resource_article_collection.add_method("GET", integration=integration_article_get_collection)

        integration_article_create = APIIntegration(self, "article_create")
        article_table.grant_read_write_data(integration_article_create)
        resource_article.add_method("POST", integration=integration_article_create)

        integration_article_update = APIIntegration(self, "article_update")
        article_table.grant_read_write_data(integration_article_update)
        resource_article.add_method("PATCH", integration=integration_article_update)

        integration_article_delete = APIIntegration(self, "article_delete")
        article_table.grant_read_write_data(integration_article_delete)
        resource_article.add_method("DELETE", integration=integration_article_delete)

        integration_comment_get_collection = APIIntegration(self, "comment_get_collection")
        comment_table.grant_read_data(integration_comment_get_collection)
        resource_article_comment_collection.add_method("GET", integration=integration_comment_get_collection)

        integration_comment_create = APIIntegration(self, "comment_create")
        comment_table.grant_read_write_data(integration_comment_create)
        resource_article_comment_collection.add_method("POST", integration=integration_comment_create)

        integration_comment_delete = APIIntegration(self, "comment_delete")
        comment_table.grant_read_write_data(integration_comment_delete)
        resource_article_comment.add_method("POST", integration=integration_comment_delete)

        integration_resp_create = APIIntegration(self, "resp_create")
        comment_table.grant_read_write_data(integration_resp_create)
        resource_article_comment_resp_collection.add_method("POST", integration=integration_resp_create)

        integration_resp_delete = APIIntegration(self, "resp_delete")
        comment_table.grant_read_write_data(integration_resp_delete)
        resource_article_comment_resp.add_method("DELETE", integration=integration_resp_delete)

        integration_tag_get_collection = APIIntegration(self, "tag_get_collection")
        article_table.grant_read_data(integration_tag_get_collection)
        resource_tag_collection.add_method("GET", integration=integration_tag_get_collection)

        integration_tag_get_article_collection = APIIntegration(self, "tag_get_article_collection")
        article_table.grant_read_data(integration_tag_get_article_collection)
        resource_tag.add_method("GET", integration_tag_get_article_collection)

        integration_admin_login = APIIntegration(self, "admin_login")
        resource_admin_login.add_method("POST", integration=integration_admin_login)


class APIIntegration(apigw.LambdaIntegration):

    def __init__(self, scope: API, name: str):
        self.lambda_function = lambda_.Function(
            scope,
            f"blog-{name}-lambda-fn",
            runtime=lambda_.Runtime.PYTHON_3_8,
            handler=f"{name}.handler",
            code=lambda_.Code.from_asset(f"../../backend/lambda_functions/{name}.py"),
            environment={
                "ArticleTableName": scope.article_table_name,
                "CommentTableName": scope.comment_table_name
            },
            layers=scope.lambda_layers
        )
        super().__init__(
            handler=self.lambda_function
        )
        scope.admin_key_secret.grant_read(self)

    @property
    def grant_principle(self):
        # pass through to lambda function
        return self.lambda_function.grant_principal

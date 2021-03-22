import aws_cdk.core
import aws_cdk.aws_apigateway as apigw
import aws_cdk.aws_lambda as lambda_
import aws_cdk.aws_dynamodb as dynamodb
import aws_cdk.aws_secretsmanager as sm
import aws_cdk.aws_logs as logs
from .. import Environment
from stacks.stack_utils import to_camel_case


class Api(aws_cdk.core.Construct):

    def __init__(
            self, scope: aws_cdk.core.Construct,
            construct_id: str,
            environment: object = Environment.TESTING):
        super().__init__(scope, construct_id)

        # Integration dependencies
        # have to be created before creating the RestApi
        # because the RestApi 'default integration' also has to be created at this time
        #
        #   (applied to integrations auto., accessed by integration construct via scope)

        self.table_article_name = construct_id + "Article"
        self.table_comment_name = construct_id + "Comment"

        self.lambda_layers = [
            lambda_.LayerVersion(
                self,
                "MiddlewareLayer",
                code=lambda_.Code.from_asset("build/middleware_layer"),
                compatible_runtimes=[lambda_.Runtime.PYTHON_3_8]
            ),
            lambda_.LayerVersion(
                self,
                "VendorLayer",
                code=lambda_.Code.from_asset("build/vendor_layer"),
                compatible_runtimes=[lambda_.Runtime.PYTHON_3_8]
            )
        ]

        self.secret_admin_key = sm.Secret.from_secret_arn(  # read access granted in integration construct
            self,
            "blog-backend-admin-key",
            "arn:aws:secretsmanager:us-east-1:473883619336:secret:blog-backend-admin-key-bctwKR"
        )

        #   (applied to integrations individually)

        table_article = dynamodb.Table(
            self,
            "ArticleTable",
            table_name=self.table_article_name,
            partition_key=dynamodb.Attribute(name="urlTitle", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=aws_cdk.core.RemovalPolicy.RETAIN if environment is Environment.PRODUCTION
            else aws_cdk.core.RemovalPolicy.DESTROY,
            point_in_time_recovery=environment is Environment.PRODUCTION
        )

        table_article.add_global_secondary_index(
            index_name="tagIndex",
            partition_key=dynamodb.Attribute(name="tag", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="published", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.INCLUDE,
            non_key_attributes=["urlTitle", "title", "description"]
        )

        table_comment = dynamodb.Table(
            self,
            "CommentTable",
            table_name=self.table_comment_name,
            partition_key=dynamodb.Attribute(name="articleUrlTitle", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=aws_cdk.core.RemovalPolicy.RETAIN if environment is Environment.PRODUCTION
            else aws_cdk.core.RemovalPolicy.DESTROY,
        )

        # RestApi

        self.instance = apigw.RestApi(
            self,
            construct_id + "I",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
            ),
            default_integration=APIIntegration(self, "default"),
            deploy_options=apigw.StageOptions(
                throttling_rate_limit=256,
                throttling_burst_limit=64,  # concurrent
                caching_enabled=True if environment is Environment.PRODUCTION else False,
                cache_ttl=aws_cdk.core.Duration.minutes(5)
            ),
            endpoint_configuration=apigw.EndpointConfiguration(
                types=[apigw.EndpointType.EDGE] if environment is Environment.PRODUCTION
                else [apigw.EndpointType.REGIONAL]
            ),
        )

        # Endpoints

        self.instance.root.add_proxy()

        # /article
        resource_article_collection = self.instance.root.add_resource(path_part="article")

        integration_article_get_collection = APIIntegration(self, "article_get_collection")
        table_article.grant_read_data(integration_article_get_collection.lambda_function)
        resource_article_collection.add_method("GET", integration=integration_article_get_collection)

        integration_article_create = APIIntegration(self, "article_create")
        table_article.grant_read_write_data(integration_article_create.lambda_function)
        resource_article_collection.add_method("POST", integration=integration_article_create)

        # /article/{}
        resource_article = resource_article_collection.add_resource(path_part="{articleUrlTitle}")

        integration_article_get = APIIntegration(self, "article_get")
        table_article.grant_read_data(integration_article_get.lambda_function)
        resource_article.add_method("GET", integration=integration_article_get)

        integration_article_update = APIIntegration(self, "article_update")
        table_article.grant_read_write_data(integration_article_update.lambda_function)
        resource_article.add_method("PATCH", integration=integration_article_update)

        integration_article_delete = APIIntegration(self, "article_delete")
        table_article.grant_read_write_data(integration_article_delete.lambda_function)
        resource_article.add_method("DELETE", integration=integration_article_delete)

        # /article/{}/comments
        resource_article_comment_collection = resource_article.add_resource(path_part="comments")

        integration_comment_get_collection = APIIntegration(self, "comment_get_collection")
        table_comment.grant_read_data(integration_comment_get_collection.lambda_function)
        resource_article_comment_collection.add_method("GET", integration=integration_comment_get_collection)

        integration_comment_create = APIIntegration(self, "comment_create")
        table_comment.grant_read_write_data(integration_comment_create.lambda_function)
        resource_article_comment_collection.add_method("POST", integration=integration_comment_create)

        # /article/{}/comments/{}
        resource_article_comment = resource_article_comment_collection.add_resource(path_part="{commentId}")

        integration_comment_delete = APIIntegration(self, "comment_delete")
        table_comment.grant_read_write_data(integration_comment_delete.lambda_function)
        resource_article_comment.add_method("DELETE", integration=integration_comment_delete)

        # /article/{}/comments/{}/resps
        resource_article_comment_resp_collection = resource_article_comment.add_resource(path_part="resps")

        integration_resp_create = APIIntegration(self, "resp_create")
        table_comment.grant_read_write_data(integration_resp_create.lambda_function)
        resource_article_comment_resp_collection.add_method("POST", integration=integration_resp_create)

        # /article/{}/comments/{}/resps/{}
        resource_article_comment_resp = resource_article_comment_resp_collection.add_resource(path_part="{respId}")

        integration_resp_delete = APIIntegration(self, "resp_delete")
        table_comment.grant_read_write_data(integration_resp_delete.lambda_function)
        resource_article_comment_resp.add_method("DELETE", integration=integration_resp_delete)

        # /tag
        resource_tag_collection = self.instance.root.add_resource(path_part="tag")

        integration_tag_get_collection = APIIntegration(self, "tag_get_collection")
        table_article.grant_read_data(integration_tag_get_collection.lambda_function)
        resource_tag_collection.add_method("GET", integration=integration_tag_get_collection)

        # /tag/{}
        resource_tag = resource_tag_collection.add_resource(path_part="{tagName}")

        integration_tag_get_article_collection = APIIntegration(self, "tag_get_article_collection")
        table_article.grant_read_data(integration_tag_get_article_collection.lambda_function)
        resource_tag.add_method("GET", integration_tag_get_article_collection)

        # /admin-login
        resource_admin_login = self.instance.root.add_resource(path_part="admin-login")

        integration_admin_login = APIIntegration(self, "admin_login")
        resource_admin_login.add_method("POST", integration=integration_admin_login)


class APIIntegration(apigw.LambdaIntegration):

    def __init__(self, scope: Api, name: str):
        self.lambda_function = lambda_.Function(
            scope,
            f"{to_camel_case(name)}Fn",
            runtime=lambda_.Runtime.PYTHON_3_8,
            handler=f"lambda_function.handler",
            code=lambda_.Code.from_asset(f"backend/lambda_functions/{name}"),
            environment={
                "ArticleTableName": scope.table_article_name,
                "CommentTableName": scope.table_comment_name
            },
            memory_size=256,
            log_retention=logs.RetentionDays.FIVE_DAYS,
            layers=scope.lambda_layers
        )
        super().__init__(
            handler=self.lambda_function
        )
        scope.secret_admin_key.grant_read(self.lambda_function)

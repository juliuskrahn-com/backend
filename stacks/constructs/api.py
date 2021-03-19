import aws_cdk.core
import aws_cdk.aws_apigateway as apigw
import aws_cdk.aws_lambda as lambda_
import aws_cdk.aws_dynamodb as dynamodb
import aws_cdk.aws_secretsmanager as sm
import aws_cdk.aws_logs as logs
from ..constants import Environment


class API(aws_cdk.core.Construct):

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

        self.article_table_name = construct_id + "article"
        self.comment_table_name = construct_id + "comment"

        self.lambda_layers = [
            lambda_.LayerVersion(
                self,
                "middleware.layer",
                code=lambda_.Code.from_asset("build/middleware_layer"),
                compatible_runtimes=[lambda_.Runtime.PYTHON_3_8]
            ),
            lambda_.LayerVersion(
                self,
                "vendor.layer",
                code=lambda_.Code.from_asset("build/vendor_layer"),
                compatible_runtimes=[lambda_.Runtime.PYTHON_3_8]
            )
        ]

        self.admin_key_secret = sm.Secret.from_secret_arn(  # read access granted in integration construct
            self,
            "blog-backend-admin-key",
            "arn:aws:secretsmanager:us-east-1:473883619336:secret:blog-backend-admin-key-bctwKR"
        )

        #   (applied to integrations individually)

        article_table = dynamodb.Table(
            self,
            "article.table",
            table_name=self.article_table_name,
            partition_key=dynamodb.Attribute(name="urlTitle", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=aws_cdk.core.RemovalPolicy.RETAIN if environment is Environment.PRODUCTION
            else aws_cdk.core.RemovalPolicy.DESTROY,
            point_in_time_recovery=environment is Environment.PRODUCTION
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
            "comment.table",
            table_name=self.comment_table_name,
            partition_key=dynamodb.Attribute(name="articleUrlTitle", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=aws_cdk.core.RemovalPolicy.RETAIN if environment is Environment.PRODUCTION
            else aws_cdk.core.RemovalPolicy.DESTROY,
        )

        # RestApi

        self.apigw_rest_api = apigw.RestApi(
            self,
            "api",
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

        # Resources

        resource_article_collection = self.apigw_rest_api.root.add_resource(path_part="article")
        resource_article = resource_article_collection.add_resource(path_part="{articleUrlTitle}")
        resource_article_comment_collection = resource_article.add_resource(path_part="comments")
        resource_article_comment = resource_article_comment_collection.add_resource(path_part="{commentId}")
        resource_article_comment_resp_collection = resource_article_comment.add_resource(path_part="resps")
        resource_article_comment_resp = resource_article_comment_resp_collection.add_resource(path_part="{respId}")

        resource_tag_collection = self.apigw_rest_api.root.add_resource(path_part="tag")
        resource_tag = resource_tag_collection.add_resource(path_part="{tagName}")

        resource_admin_login = self.apigw_rest_api.root.add_resource(path_part="admin-login")

        # Integrations

        self.apigw_rest_api.root.add_proxy()

        integration_article_get = APIIntegration(self, "article_get")
        article_table.grant_read_data(integration_article_get.lambda_function)
        resource_article.add_method("GET", integration=integration_article_get)

        integration_article_get_collection = APIIntegration(self, "article_get_collection")
        article_table.grant_read_data(integration_article_get_collection.lambda_function)
        resource_article_collection.add_method("GET", integration=integration_article_get_collection)

        integration_article_create = APIIntegration(self, "article_create")
        article_table.grant_read_write_data(integration_article_create.lambda_function)
        resource_article.add_method("POST", integration=integration_article_create)

        integration_article_update = APIIntegration(self, "article_update")
        article_table.grant_read_write_data(integration_article_update.lambda_function)
        resource_article.add_method("PATCH", integration=integration_article_update)

        integration_article_delete = APIIntegration(self, "article_delete")
        article_table.grant_read_write_data(integration_article_delete.lambda_function)
        resource_article.add_method("DELETE", integration=integration_article_delete)

        integration_comment_get_collection = APIIntegration(self, "comment_get_collection")
        comment_table.grant_read_data(integration_comment_get_collection.lambda_function)
        resource_article_comment_collection.add_method("GET", integration=integration_comment_get_collection)

        integration_comment_create = APIIntegration(self, "comment_create")
        comment_table.grant_read_write_data(integration_comment_create.lambda_function)
        resource_article_comment_collection.add_method("POST", integration=integration_comment_create)

        integration_comment_delete = APIIntegration(self, "comment_delete")
        comment_table.grant_read_write_data(integration_comment_delete.lambda_function)
        resource_article_comment.add_method("POST", integration=integration_comment_delete)

        integration_resp_create = APIIntegration(self, "resp_create")
        comment_table.grant_read_write_data(integration_resp_create.lambda_function)
        resource_article_comment_resp_collection.add_method("POST", integration=integration_resp_create)

        integration_resp_delete = APIIntegration(self, "resp_delete")
        comment_table.grant_read_write_data(integration_resp_delete.lambda_function)
        resource_article_comment_resp.add_method("DELETE", integration=integration_resp_delete)

        integration_tag_get_collection = APIIntegration(self, "tag_get_collection")
        article_table.grant_read_data(integration_tag_get_collection.lambda_function)
        resource_tag_collection.add_method("GET", integration=integration_tag_get_collection)

        integration_tag_get_article_collection = APIIntegration(self, "tag_get_article_collection")
        article_table.grant_read_data(integration_tag_get_article_collection.lambda_function)
        resource_tag.add_method("GET", integration_tag_get_article_collection)

        integration_admin_login = APIIntegration(self, "admin_login")
        resource_admin_login.add_method("POST", integration=integration_admin_login)


class APIIntegration(apigw.LambdaIntegration):

    def __init__(self, scope: API, name: str):
        self.lambda_function = lambda_.Function(
            scope,
            f"{snake_case_to_camel_case(name)}.fn",
            runtime=lambda_.Runtime.PYTHON_3_8,
            handler=f"lambda_function.handler",
            code=lambda_.Code.from_asset(f"backend/lambda_functions/{name}"),
            environment={
                "ArticleTableName": scope.article_table_name,
                "CommentTableName": scope.comment_table_name
            },
            memory_size=256,
            log_retention=logs.RetentionDays.FIVE_DAYS,
            layers=scope.lambda_layers
        )
        super().__init__(
            handler=self.lambda_function
        )
        scope.admin_key_secret.grant_read(self.lambda_function)


def snake_case_to_camel_case(string):
    string = "".join(word.title() for word in string.split("_"))
    return string[:1].lower() + string[1:] if string else ""

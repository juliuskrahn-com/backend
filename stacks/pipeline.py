from aws_cdk import core
import aws_cdk.aws_codepipeline as codepipeline
import aws_cdk.aws_codepipeline_actions as codepipeline_actions


class Pipeline(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        core.Tags.of(self).add("Project", "Blog")
        core.Tags.of(self).add("Stack", "Pipeline")

        pipeline = codepipeline.Pipeline(
            self,
            "blog-backend-pipeline",
            pipeline_name="blog-backend-pipeline",
            cross_account_keys=False
        )

        source_output = codepipeline.Artifact()

        source_action = codepipeline_actions.GitHubSourceAction(
            action_name="blog-backend-github-source",
            owner="juliuskrahn-com",
            repo="backend",
            oauth_token=core.SecretValue.secrets_manager("github-token"),
            output=source_output,
            branch="dev"
        )

        pipeline.add_stage(
            stage_name="Source",
            actions=[source_action]
        )

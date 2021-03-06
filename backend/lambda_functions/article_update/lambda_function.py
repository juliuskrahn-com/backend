import backend.middleware as middleware
from pydantic import BaseModel
import botocore.exceptions


class Model(BaseModel):
    urlTitle: str
    title: str
    description: str
    tag: str
    content: str

    @classmethod
    def build(cls, event: middleware.Event, context):
        kwargs = {**event.body, "urlTitle": event.path_parameters.get("articleUrlTitle")}
        return cls(**kwargs)


article_table = middleware.get_article_table()


@middleware.middleware
@middleware.register_user
@middleware.admin_guard
@middleware.data(Model)
def handler(event: middleware.Event, context, data: Model):
    try:
        article_table.update_item(
            Key={
                "urlTitle": data.urlTitle
            },
            UpdateExpression="SET title=:title, description=:description, tag=:tag, content=:content",
            ExpressionAttributeValues={
                ":title": data.title,
                ":description": data.description,
                ":tag": data.tag,
                ":content": data.content
            },
            ConditionExpression="attribute_exists(urlTitle)"
        )
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return middleware.Response(status_code=404, error_messages=["Article does not exist"])
    return middleware.Response()

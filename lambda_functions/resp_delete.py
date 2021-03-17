import middleware
from pydantic import BaseModel
import botocore.exceptions


class Model(BaseModel):
    articleUrlTitle: str
    commentId: str
    respId: str

    @classmethod
    def build(cls, event: middleware.Event, context):
        return cls(articleUrlTitle=event.path_parameters.get("articleUrlTitle"),
                   commentId=event.path_parameters.get("commentId"),
                   respId=event.path_parameters.get("respId"))


comment_table = middleware.get_comment_table()


@middleware.middleware
@middleware.register_user
@middleware.admin_guard
@middleware.data(Model)
def handler(event: middleware.Event, context, data: Model):
    try:
        comment_table.update_item(
            Key={
                "articleUrlTitle": data.articleUrlTitle,
                "id": data.commentId
            },
            UpdateExpression="REMOVE resps.#resp_id",
            ExpressionAttributeNames={
                "#resp_id": data.respId
            },
            ConditionExpression="attribute_exists(id)"
        )
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            pass
    return middleware.Response()

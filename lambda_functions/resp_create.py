import middleware
from pydantic import BaseModel
import datetime
from uuid import uuid4
import botocore.exceptions


class Model(BaseModel):
    articleUrlTitle: str
    commentId: str
    author: str
    content: str

    @classmethod
    def build(cls, event: middleware.Event, context):
        return cls(articleUrlTitle=event.path_parameters.get("articleUrlTitle"),
                   commentId=event.path_parameters.get("commentId"),
                   **event.body)


comment_table = middleware.get_comment_table()


@middleware.data(Model)
@middleware.register_user
@middleware.middleware
def handler(event: middleware.Event, context, data: Model):
    id_ = f"{datetime.datetime.utcnow().isoformat()}#{uuid4()}"
    author = data.author
    if data.author == "admin" and not middleware.authenticator.current_user_is_admin:
        author += "#not-the-real-admin"
    try:
        comment_table.update_item(
            Key={
                "articleUrlTitle": data.articleUrlTitle,
                "id": data.commentId
            },
            UpdateExpression="SET resps.#resp_id=:resp",
            ExpressionAttributeNames={
                "#resp_id": id_
            },
            ExpressionAttributeValues={
                ":resp": {
                    "content": data.content,
                    "author": author
                }
            },
            ConditionExpression="attribute_exists(id)"
        )
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return middleware.Response(status_code=404, error_messages=["Comment does not exist"])
    return middleware.Response(status_code=201, body={"id": id_})

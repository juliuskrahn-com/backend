import middleware
from pydantic import BaseModel
import datetime
from uuid import uuid4


class Model(BaseModel):
    articleUrlTitle: str
    author: str
    content: str

    @classmethod
    def build(cls, event: middleware.Event, context):
        return cls(articleUrlTitle=event.path_parameters["articleUrlTitle"], **event.body)


comment_table = middleware.get_comment_table()


@middleware.middleware
@middleware.data(Model)
def handler(event: middleware.Event, context, data: Model):
    id_ = f"{datetime.datetime.utcnow().isoformat()}#{uuid4()}"
    author = data.author
    if data.author == "admin" and not middleware.authenticator.current_user_is_admin:
        author += "#not-the-real-admin"
    comment_table.put_item(
        Item={
            "articleUrlTitle": data.articleUrlTitle,
            "id": id_,
            "content": data.content,
            "author": author,
            "resps": {}
        }
    )
    return middleware.Response(status_code=201, body={"id": id_})

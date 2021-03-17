import middleware
from pydantic import BaseModel


class Model(BaseModel):
    articleUrlTitle: str
    commentId: str

    @classmethod
    def build(cls, event: middleware.Event, context):
        return cls(articleUrlTitle=event.path_parameters["articleUrlTitle"],
                   commentId=event.path_parameters["commentId"])


comment_table = middleware.get_comment_table()


@middleware.data(Model)
@middleware.admin_guard
@middleware.register_user
@middleware.middleware
def handler(event: middleware.Event, context, data: Model):
    comment_table.delete_item(Key={"articleUrlTitle": data.articleUrlTitle, "id": data.commentId})
    return middleware.Response()

import middleware
from pydantic import BaseModel


class Model(BaseModel):
    articleUrlTitle: str
    commentId: str

    @classmethod
    def build(cls, event: middleware.Event, context):
        return cls(articleUrlTitle=event.path_parameters.get("articleUrlTitle"),
                   commentId=event.path_parameters.get("commentId"))


comment_table = middleware.get_comment_table()


@middleware.middleware
@middleware.register_user
@middleware.admin_guard
@middleware.data(Model)
def handler(event: middleware.Event, context, data: Model):
    comment_table.delete_item(Key={"articleUrlTitle": data.articleUrlTitle, "id": data.commentId})
    return middleware.Response()

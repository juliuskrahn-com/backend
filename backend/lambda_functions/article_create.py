import backend.middleware as middleware
from pydantic import BaseModel
import datetime


class Model(BaseModel):
    urlTitle: str
    title: str
    description: str
    tag: str
    content: str

    @classmethod
    def build(cls, event: middleware.Event, context):
        return cls(**event.body)


article_table = middleware.get_article_table()


@middleware.middleware
@middleware.register_user
@middleware.admin_guard
@middleware.data(Model)
def handler(event: middleware.Event, context, data: Model):
    article_table.put_item(
        Item={
            "urlTitle": data.urlTitle,
            "title": data.title,
            "tag": data.tag,
            "content": data.content,
            "description": data.description,
            "published": datetime.date.today().isoformat()
        }
    )
    return middleware.Response(status_code=201)

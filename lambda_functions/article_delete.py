import middleware
from pydantic import BaseModel


class Model(BaseModel):
    urlTitle: str

    @classmethod
    def build(cls, event: middleware.Event, context):
        return cls(urlTitle=event.path_parameters["articleUrlTitle"])


article_table = middleware.get_article_table()


@middleware.data(Model)
@middleware.admin_guard
@middleware.register_user
@middleware.middleware
def handler(event: middleware.Event, context, data: Model):
    article_table.delete_item(Key={"urlTitle": data.urlTitle})
    return middleware.Response()

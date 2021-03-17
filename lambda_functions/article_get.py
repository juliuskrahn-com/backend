import middleware
from pydantic import BaseModel


class Model(BaseModel):
    urlTitle: str

    @classmethod
    def build(cls, event: middleware.Event, context):
        return cls(urlTitle=event.path_parameters.get("articleUrlTitle"))


article_table = middleware.get_article_table()


@middleware.middleware
@middleware.data(Model)
def handler(event: middleware.Event, context, data: Model):
    article = article_table.get_item(Key={"urlTitle": data.urlTitle}).get("Item")
    if not article:
        return middleware.Response(status_code=404, error_messages=["Article does not exist"])
    return middleware.Response(body={"article": article})

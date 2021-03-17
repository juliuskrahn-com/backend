import middleware
from pydantic import BaseModel
import boto3.dynamodb.conditions


class Model(BaseModel):
    articleUrlTitle: str

    @classmethod
    def build(cls, event: middleware.Event, context):
        return cls(articleUrlTitle=event.path_parameters.get("articleUrlTitle"))


comment_table = middleware.get_comment_table()


@middleware.data(Model)
@middleware.middleware
def handler(event: middleware.Event, context, data: Model):
    comments = comment_table.query_paginate_items(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("articleUrlTitle").eq(data.articleUrlTitle))
    return middleware.Response(body={"comments": comments})

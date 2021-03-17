import middleware
from pydantic import BaseModel
import boto3.dynamodb.conditions


class Model(BaseModel):
    tagName: str

    @classmethod
    def build(cls, event: middleware.Event, context):
        return cls(tagName=event.path_parameters.get("tagName"))


article_table = middleware.get_article_table()


@middleware.middleware
@middleware.data(Model)
def handler(event: middleware.Event, context, data: Model):
    articles = article_table.query_paginate_items(
        IndexName="tagIndex",
        KeyConditionExpression=boto3.dynamodb.conditions.Key("tag").eq(data.tagName),
        Select="ALL_PROJECTED_ATTRIBUTES",
        ScanIndexForward=False
    )
    return middleware.Response(body={"articles": articles})

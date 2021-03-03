import boto3
import boto3.dynamodb.conditions
import datetime
from functools import lru_cache
from .auth import admin
from .utils import wrap_table_for_pagination


class Article:

    _table = wrap_table_for_pagination(boto3.resource("dynamodb").Table("blog-article"))

    @lru_cache(maxsize=16)
    def desc_all(self, pagination_key=None):
        resp = self._table.scan(
            Limit=50,
            ExclusiveStartKey=pagination_key,
            ProjectionExpression="urlTitle,title,published,tag,description"
        )
        return resp.get("Items"), resp.get("LastEvaluatedKey")

    @lru_cache(maxsize=16)
    def desc_all_with_tag(self, tag, pagination_key=None):
        resp = self._table.query(
            IndexName="tagIndex",
            KeyConditionExpression=boto3.dynamodb.conditions.Key("tag").eq(tag),
            Select="ALL_PROJECTED_ATTRIBUTES",
            Limit=50,
            ExclusiveStartKey=pagination_key
        )
        return resp.get("Items"), resp.get("LastEvaluatedKey")

    @lru_cache(maxsize=None)
    def get_all_tags(self):
        items = []
        exclusive_start_key = None

        while True:
            resp = self._table.scan(
                IndexName="tagIndex",
                ProjectionExpression="tag",
                ExclusiveStartKey=exclusive_start_key
            )
            if resp.get("Items"):
                items += resp.get("Items")

            if resp.get("LastEvaluatedKey"):
                exclusive_start_key = resp.get("LastEvaluatedKey")
            else:
                break

        return list(set([item["tag"] for item in items]))

    @lru_cache(maxsize=16)
    def get(self, url_title):
        return self._table.get_item(Key={"urlTitle": url_title})["Item"]

    @admin
    def create(self, url_title, title, tag, text, desc):
        self._table.put_item(
            Item={
                "urlTitle": url_title,
                "title": title,
                "tag": tag,
                "text": text,
                "description": desc,
                "published": datetime.date.today().isoformat()
            }
        )

    @admin
    def update(self, url_title, new_title, new_tag, new_text, new_desc):
        self._table.update_item(
            Key={
                "urlTitle": url_title
            },
            UpdateExpression="SET title=:title, tag=:tag, text=:text, description=:description",
            ExpressionAttributeValues={
                ":title": new_title,
                ":tag": new_tag,
                ":text": new_text,
                ":description": new_desc
            }
        )

    @admin
    def delete(self, url_title):
        self._table.delete_item(
            Key={
                "urlTitle": url_title
            }
        )

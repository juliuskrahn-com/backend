import boto3
import boto3.dynamodb.conditions
import datetime
from functools import lru_cache
from .auth import admin
from .utils import wrap_table_for_pagination


class Article:

    _table = wrap_table_for_pagination(boto3.resource("dynamodb").Table("blog-article"))

    @lru_cache(maxsize=None)
    def _all_articles_desc(self):
        items = []
        exclusive_start_key = None

        while True:
            resp = self._table.scan(
                ExclusiveStartKey=exclusive_start_key,
                ProjectionExpression="urlTitle,title,published,tag,description"
            )
            if resp.get("Items"):
                items += resp.get("Items")

            if resp.get("LastEvaluatedKey"):
                exclusive_start_key = resp.get("LastEvaluatedKey")
            else:
                break

        items.sort(key=lambda item: item["published"], reverse=True)
        return items

    def desc_all(self, pagination_key):
        if not pagination_key or pagination_key < 0:
            pagination_key = 0
        all_articles_desc = self._all_articles_desc()
        end = pagination_key + 50
        if len(all_articles_desc) <= end:
            end = len(all_articles_desc)
            pagination_key = None
        else:
            pagination_key = pagination_key + end
        return all_articles_desc[pagination_key:end], pagination_key

    @lru_cache(maxsize=16)
    def desc_all_with_tag(self, tag, pagination_key=None):
        resp = self._table.query(
            IndexName="tagIndex",
            KeyConditionExpression=boto3.dynamodb.conditions.Key("tag").eq(tag),
            Select="ALL_PROJECTED_ATTRIBUTES",
            Limit=50,
            ExclusiveStartKey=pagination_key,
            ScanIndexForward=False
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
        return self._table.get_item(Key={"urlTitle": url_title}).get("Item")

    @admin
    def create(self, url_title, title, tag, content, desc):
        self._table.put_item(
            Item={
                "urlTitle": url_title,
                "title": title,
                "tag": tag,
                "content": content,
                "description": desc,
                "published": datetime.date.today().isoformat()
            }
        )

    @admin
    def update(self, url_title, new_title, new_tag, new_content, new_desc):
        self._table.update_item(
            Key={
                "urlTitle": url_title
            },
            UpdateExpression="SET title=:title, tag=:tag, content=:content, description=:description",
            ExpressionAttributeValues={
                ":title": new_title,
                ":tag": new_tag,
                ":content": new_content,
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

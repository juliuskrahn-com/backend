import boto3
import boto3.dynamodb.conditions
import datetime
from functools import lru_cache
from uuid import uuid4
from .auth import admin, auth
from .utils import wrap_table_for_pagination


class Comment:

    _table = wrap_table_for_pagination(boto3.resource("dynamodb").Table("blog-comment"))

    @lru_cache(maxsize=16)
    def get_all_for_article(self, article_url_title, pagination_key=None):
        resp = self._table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key("articleUrlTitle").eq(article_url_title),
            Limit=50,
            ExclusiveStartKey=pagination_key
        )
        return resp.get("Items"), resp.get("LastEvaluatedKey")

    def create(self, article_url_title, text):
        id_ = f"{datetime.datetime.utcnow().isoformat()}#{uuid4()}"
        self._table.put_item(
            Item={
                "articleUrlTitle": article_url_title,
                "id": id_,
                "text": text,
                "author": "admin" if auth.current_user_is_admin else None,
                "resps": {}
            }
        )
        return id_

    @admin
    def update(self, article_url_title, id_, new_text):
        self._table.update_item(
            Key={
                "articleUrlTitle": article_url_title,
                "id": id_
            },
            UpdateExpression="SET text=:text",
            ExpressionAttributeValues={
                ":text": new_text
            }
        )

    @admin
    def delete(self, article_url_title, id_):
        self._table.delete_item(
            Key={
                "articleUrlTitle": article_url_title,
                "id": id_
            }
        )

    def create_resp(self, article_url_title, comment_id, resp_text):
        resp_id = f"{datetime.datetime.utcnow().isoformat()}#{uuid4()}"
        self._table.update_item(
            Key={
                "articleUrlTitle": article_url_title,
                "id": comment_id
            },
            UpdateExpression="SET resps.:resp_id=:resp",
            ExpressionAttributeValues={
                ":resp_id": resp_id,
                ":resp": {
                    "text": resp_text,
                    "author": "admin" if auth.current_user_is_admin else None
                }
            }
        )
        return resp_id

    @admin
    def update_resp(self, article_url_title, comment_id, resp_id, new_resp_text):
        self._table.update_item(
            Key={
                "articleUrlTitle": article_url_title,
                "id": comment_id
            },
            UpdateExpression="SET resps.:resp_id=:resp",
            ExpressionAttributeValues={
                ":resp_id": resp_id,
                ":resp": {
                    "text": new_resp_text,
                    "author": "admin" if auth.current_user_is_admin else None
                }
            }
        )

    @admin
    def delete_resp(self, article_url_title, comment_id, resp_id):
        self._table.update_item(
            Key={
                "articleUrlTitle": article_url_title,
                "id": comment_id
            },
            UpdateExpression="REMOVE resps.:resp_id",
            ExpressionAttributeValues={
                ":resp_id": resp_id
            }
        )

import boto3
import boto3.dynamodb.conditions
import datetime
from uuid import uuid4
from .auth import admin, auth
from .utils import wrap_table_for_pagination


class Comment:

    _table = wrap_table_for_pagination(boto3.resource("dynamodb").Table("blog-comment"))

    def get_all_for_article(self, article_url_title, pagination_key=None):
        resp = self._table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key("articleUrlTitle").eq(article_url_title),
            Limit=50,
            ExclusiveStartKey=pagination_key
        )
        return resp.get("Items"), resp.get("LastEvaluatedKey")

    def create(self, article_url_title, author, content):
        id_ = f"{datetime.datetime.utcnow().isoformat()}#{uuid4()}"
        self._table.put_item(
            Item={
                "articleUrlTitle": article_url_title,
                "id": id_,
                "content": content,
                "author": self.author_name(author),
                "resps": {}
            }
        )
        return id_

    @admin
    def delete(self, article_url_title, id_):
        self._table.delete_item(
            Key={
                "articleUrlTitle": article_url_title,
                "id": id_
            }
        )

    def create_resp(self, article_url_title, comment_id, author, resp_content):
        resp_id = f"{datetime.datetime.utcnow().isoformat()}#{uuid4()}"
        self._table.update_item(
            Key={
                "articleUrlTitle": article_url_title,
                "id": comment_id
            },
            UpdateExpression="SET resps.#resp_id=:resp",
            ExpressionAttributeNames={
                "#resp_id": resp_id
            },
            ExpressionAttributeValues={
                ":resp": {
                    "content": resp_content,
                    "author": self.author_name(author)
                }
            }
        )
        return resp_id

    @admin
    def delete_resp(self, article_url_title, comment_id, resp_id):
        self._table.update_item(
            Key={
                "articleUrlTitle": article_url_title,
                "id": comment_id
            },
            UpdateExpression="REMOVE resps.#resp_id",
            ExpressionAttributeNames={
                "#resp_id": resp_id
            },
        )

    @staticmethod
    def author_name(author):
        if not author:
            author = 'anonymous'
        elif author == "admin" and not auth.current_user_is_admin:
            author += "#not-the-real-admin"
        return author

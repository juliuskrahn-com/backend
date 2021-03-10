import core
import json
import urllib.parse


article = core.Article()
comment = core.Comment()


def apply_defaults(handler_fn):
    def wrapper(*args, **kwargs):
        resp = handler_fn(*args, **kwargs)
        if "headers" not in resp:
            resp["headers"] = {}
        resp["headers"]["Access-Control-Allow-Origin"] = "*"
        resp["headers"]["Access-Control-Allow-Methods"] = "*"
        resp["headers"]["Access-Control-Allow-Headers"] = "*"
        return resp
    return wrapper


@apply_defaults
def handler(event, context):
    body = json.loads(event["body"]) if event["body"] else {}

    path = core.parse_path(event["path"])
    if not path:
        return {"statusCode": 404}

    core.authenticator.register(body.get("key"))

    root_resource = path.pop(0)

    #########################################################################
    # resource: /admin-login
    #########################################################################

    if root_resource == "admin-login":
        if core.authenticator.current_user_is_admin:
            return {"statusCode": 200}
        return {"statusCode": 400}

    #########################################################################
    # resource: /tag
    #########################################################################

    if root_resource == "tag":
        # desc all articles with specific tag
        if path:  # next path element is specific tag
            articles, pagination_key = article.desc_all_with_tag(path.pop(0), body.get("paginationKey"))
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "articles": articles,
                    "paginationKey": pagination_key
                })
            }

        # get all tags
        return {
            "statusCode": 200,
            "body": json.dumps({
                "tags": article.get_all_tags()
            })
        }

    #########################################################################
    # resource: /article
    #########################################################################

    if root_resource != "article":
        return {"statusCode": 404}

    if not path:
        # create article
        if event["httpMethod"] == "POST":
            try:
                article.create(
                    body["urlTitle"],
                    body["title"],
                    body["tag"],
                    body["content"],
                    body["description"]
                )
                return {"statusCode": 201}
            except PermissionError:
                return {"statusCode": 401}

        # desc all articles
        articles, pagination_key = article.desc_all(body.get("paginationKey"))
        return {
            "statusCode": 200,
            "body": json.dumps({
                "articles": articles,
                "paginationKey": pagination_key
            })
        }

    # specific article
    # next path element is an article url title
    article_url_title = path.pop(0)

    if not path:
        # update article
        if event["httpMethod"] == "PUT":
            try:
                article.update(
                    article_url_title,
                    body["title"],
                    body["tag"],
                    body["content"],
                    body["description"]
                )
                return {"statusCode": 200}
            except PermissionError:
                return {"statusCode": 401}

        # delete article
        elif event["httpMethod"] == "DELETE":
            try:
                article.delete(article_url_title)
                return {"statusCode": 200}
            except PermissionError:
                return {"statusCode": 401}

        # get article
        return {
            "statusCode": 200,
            "body": json.dumps({
                "article": article.get(article_url_title)
            })
        }

    # article comments
    # next path element should be comments
    if path.pop(0) != "comments":
        return {"statusCode": 404}

    if not path:
        # create comment
        if event["httpMethod"] == "POST":
            comment_id = comment.create(article_url_title, body["author"], body["content"])
            return {
                "statusCode": 201,
                "body": json.dumps({"id": comment_id})
            }

        # get all comments for article
        comments, pagination_key = comment.get_all_for_article(article_url_title, body.get("paginationKey"))
        return {
            "statusCode": 200,
            "body": json.dumps({
                "comments": comments,
                "pagination_key": pagination_key
            })
        }

    # specific comment
    # next path element is the id of a comment
    comment_id = urllib.parse.unquote(path.pop(0))

    if not path:  # operations on comment
        # delete comment
        if event["httpMethod"] == "DELETE":
            try:
                comment.delete(article_url_title, comment_id)
                return {"statusCode": 200}
            except PermissionError:
                return {"statusCode": 401}

    # comment resps
    # next path element should be resps
    if path.pop(0) != "resps":
        return {"statusCode": 404}

    if not path:
        # create resp
        if event["httpMethod"] == "POST":
            resp_id = comment.create_resp(article_url_title, comment_id, body["author"], body["content"])
            return {
                "statusCode": 201,
                "body": json.dumps({"id": resp_id})
            }

    # specific resp
    # next path element is the id of a resp
    resp_id = urllib.parse.unquote(path.pop(0))

    # delete resp
    if event["httpMethod"] == "DELETE":
        try:
            comment.delete_resp(
                article_url_title,
                comment_id,
                resp_id
            )
            return {"statusCode": 200}
        except PermissionError:
            return {"statusCode": 401}

    #########################################################################
    # 400
    #########################################################################

    return {"statusCode": 400}

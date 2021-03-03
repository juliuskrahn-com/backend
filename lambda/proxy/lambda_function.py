import core
import json


article = core.Article()
comment = core.Comment()


def handler(event, context):
    body = event["body"] if type(event["body"]) is dict else {}

    path = core.parse_path(event["path"])
    if not path:
        return {"statusCode": 404}

    try:
        core.authenticator.register(body.get("key"))
    except:
        core.authenticator.current_user_is_admin = False

    root_resource = path.pop(0)

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
    # TODO check for duplicate article title on create/ update

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
                    body["text"],
                    body["desc"]
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
    # next path element is an article title
    article_url_title = path.pop(0)

    if not path:
        # update article
        if event["httpMethod"] == "PUT":
            try:
                article.update(
                    article_url_title,
                    body["title"],
                    body["tag"],
                    body["text"],
                    body["desc"]
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
            comment_id = comment.create(article_url_title, body["text"])
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
    comment_id = path.pop(0)

    if not path:  # operations on comment
        # update comment
        if event["httpMethod"] == "PUT":
            try:
                comment.update(article_url_title, comment_id, body["text"])
                return {"statusCode": 200}
            except PermissionError:
                return {"statusCode": 401}

        # delete comment
        elif event["httpMethod"] == "DELETE":
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
            resp_id = comment.create_resp(article_url_title, comment_id, body["text"])
            return {
                "statusCode": 201,
                "body": json.dumps({"id": resp_id})
            }

    # specific resp
    # next path element is the id of a resp
    resp_id = path.pop(0)

    # update resp
    if event["httpMethod"] == "PUT":
        try:
            comment.update_resp(
                article_url_title,
                comment_id,
                resp_id,
                body["text"]
            )
            return {"statusCode": 200}
        except PermissionError:
            return {"statusCode": 401}

    # delete resp
    elif event["httpMethod"] == "DELETE":
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

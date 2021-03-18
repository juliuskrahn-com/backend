import backend.middleware as middleware


article_table = middleware.get_article_table()


@middleware.middleware
def handler(event: middleware.Event, context):
    articles = article_table.scan_paginate_items(ProjectionExpression="urlTitle,title,description,tag,published")\
        .get("Items", [])
    articles.sort(key=lambda item: item["published"], reverse=True)
    return middleware.Response(body={"articles": articles})

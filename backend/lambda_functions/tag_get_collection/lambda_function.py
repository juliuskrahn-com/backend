import backend.middleware as middleware


article_table = middleware.get_article_table()


@middleware.middleware
def handler(event: middleware.Event, context):
    items = article_table.scan_paginate_items(
        IndexName="tagIndex",
        ProjectionExpression="tag"
    )
    return middleware.Response(body={"tags": list(set([item["tag"] for item in items]))})

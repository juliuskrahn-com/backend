import middleware


@middleware.middleware
def handler(event: middleware.Event, context):
    return middleware.Response(
        status_code=404,
        error_messages=["This endpoint does not exist. API documentation: "
                        "https://app.swaggerhub.com/apis/julius-krahn/blog"]
    )

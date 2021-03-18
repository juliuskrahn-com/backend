import backend.middleware as middleware


@middleware.middleware
@middleware.register_user
def handler(event: middleware.Event, context):
    if middleware.authenticator.current_user_is_admin:
        return middleware.Response()
    return middleware.Response(400)

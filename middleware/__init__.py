"""Middleware between API Gateway and a Lambda handler (+ boto3 utils)

Use the handler decorators like this, in this order!:

@middleware
@register_user
@admin_guard
@data(Model)
"""

from .main import middleware, Event, Response
from .utils import authenticator, register_user, admin_guard, data, get_article_table, get_comment_table

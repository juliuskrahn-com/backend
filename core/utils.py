from urllib.parse import urlparse
from typing import List


def parse_path(path: str) -> List[str]:
    path = urlparse(path).path
    path = path.split("/")
    if path[0] == "":
        path.pop(0)
    if path[-1] == "":
        path.pop()
    return path


def pagination_wrapper(fn):
    def wrapper(*args, **kwargs):
        try:
            if kwargs["ExclusiveStartKey"] is None:
                del kwargs["ExclusiveStartKey"]
        except AttributeError:
            pass
        return fn(*args, **kwargs)
    return wrapper


def wrap_table_for_pagination(table):
    table.scan = pagination_wrapper(table.scan)
    table.query = pagination_wrapper(table.query)
    return table

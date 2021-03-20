from uuid import uuid4


def generate_article_data():
    return {
        "urlTitle": "my-article-" + uuid4().hex,
        "title": "My article " + uuid4().hex,
        "tag": "test " + uuid4().hex,
        "description": "A very cool article " + uuid4().hex,
        "content": "This is so cool... Just upload it and be done... " + uuid4().hex
    }

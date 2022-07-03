class URL:
    schema: bytes
    host: bytes
    port: object
    path: bytes
    query: bytes
    fragment: bytes
    userinfo: bytes


def parse_url(url: bytes) -> URL:
    ...

from typing import Union
from array import array

class URL:
    schema: bytes
    host: bytes
    port: int
    path: bytes
    query: bytes
    fragment: bytes
    userinfo: bytes

def parse_url(url: Union[bytes, bytearray, memoryview, array[int]]) -> URL:
    """Parse URL strings into a structured Python object.

    Returns an instance of ``httptools.URL`` class with the
    following attributes:

      - schema(bytes): The schema of the URL.
      - host(bytes): The host of the URL.
      - port: int
      - path(bytes): The path of the URL.
      - query(bytes): The query of the URL.
      - fragment(bytes): The fragment of the URL.
      - userinfo(bytes): The userinfo of the URL.
    """

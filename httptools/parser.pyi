from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from httptools.parser.parser import URL

class HttpRequestParser:
    def __init__(self, protocol):
        """HttpRequestParser

        protocol -- a Python object with the following methods
        (all optional):

          - on_message_begin()
          - on_url(url: bytes)
          - on_header(name: bytes, value: bytes)
          - on_headers_complete()
          - on_body(body: bytes)
          - on_message_complete()
          - on_chunk_header()
          - on_chunk_complete()
          - on_status(status: bytes)
        """
        pass

    def get_http_version(self) -> str:
        """Return an HTTP protocol version."""
        pass

    def should_keep_alive(self) -> bool:
        """Return ``True`` if keep-alive mode is preferred."""
        pass

    def should_upgrade(self) -> bool:
        """Return ``True`` if the parsed request is a valid Upgrade request.
	The method exposes a flag set just before on_headers_complete.
	Calling this method earlier will only yield `False`.
	"""
        pass

    def feed_data(self, data: bytes):
        """Feed data to the parser.

        Will eventually trigger callbacks on the ``protocol``
        object.

        On HTTP upgrade, this method will raise an
        ``HttpParserUpgrade`` exception, with its sole argument
        set to the offset of the non-HTTP data in ``data``.
        """
        pass

    def get_method(self) -> bytes:
        """Return HTTP request method (GET, HEAD, etc)"""
        pass


class HttpResponseParser:

    """Has all methods except ``get_method()`` that
    HttpRequestParser has."""

    def get_status_code(self) -> int:
        """Return the status code of the HTTP response"""
        pass

def parse_url(url: bytes) -> "URL":
    """Parse URL strings into a structured Python object.

    Returns an instance of ``httptools.URL`` class with the
    following attributes:

      - schema: bytes
      - host: bytes
      - port: int
      - path: bytes
      - query: bytes
      - fragment: bytes
      - userinfo: bytes
    """
    pass

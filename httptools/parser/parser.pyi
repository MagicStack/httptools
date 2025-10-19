from typing import Union
from array import array
from .protocol import HTTPProtocol

class HttpParser:
    def __init__(self, protocol: HTTPProtocol) -> None:
        """The HTTP parser.

        Args:
            protocol(HTTPProtocol): a Python object with the following methods (all optional):
                - on_message_begin(self): ...
                - on_url(self, url: bytes): ...
                - on_header(self, name: bytes, value: bytes): ...
                - on_headers_complete(self): ...
                - on_body(self, body: bytes): ...
                - on_message_complete(self): ...
                - on_chunk_header(self): ...
                - on_chunk_complete(self): ...
                - on_status(self, status: bytes): ...
        """

    def get_http_version(self) -> str:
        """Return an HTTP protocol version."""

    def should_keep_alive(self) -> bool:
        """Return ``True`` if keep-alive mode is preferred."""

    def should_upgrade(self) -> bool:
        """Return ``True`` if the parsed request is a valid Upgrade request.
        The method exposes a flag set just before on_headers_complete.
        Calling this method earlier will only yield `False`."""

    def feed_data(self, data: Union[bytes, bytearray, memoryview, array[int]]) -> None:
        """Feed data to the parser.

        Will eventually trigger callbacks on the ``protocol`` object.

        On HTTP upgrade, this method will raise an
        ``HttpParserUpgrade`` exception, with its sole argument
        set to the offset of the non-HTTP data in ``data``.
        """

class HttpRequestParser(HttpParser):
    """Used for parsing http requests from the server side."""

    def get_method(self) -> bytes:
        """Retrieve the HTTP method of the request."""

class HttpResponseParser(HttpParser):
    """Used for parsing http responses from the client side."""

    def get_status_code(self) -> int:
        """Retrieve the status code of the HTTP response."""

from typing import Protocol

class HTTPProtocol(Protocol):
    """Used for providing static type-checking when parsing through the http protocol"""

    def on_message_begin() -> None:...
    def on_url(url: bytes) -> None:...
    def on_header(name: bytes, value: bytes) -> None:...
    def on_headers_complete() -> None:...
    def on_body(body: bytes) -> None:...
    def on_message_complete() -> None:...
    def on_chunk_header() -> None:...
    def on_chunk_complete() -> None:...
    def on_status(status: bytes) -> None:...


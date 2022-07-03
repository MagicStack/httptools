import typing


class Protocol(typing.Protocol):
    def on_message_begin(self) -> None:
        ...

    def on_url(self, url: bytes) -> None:
        ...

    def on_header(self, name: bytes, value: bytes) -> None:
        ...

    def on_headers_complete(self) -> None:
        ...

    def on_body(self, body: bytes) -> None:
        ...

    def on_message_complete(self) -> None:
        ...

    def on_chunk_header(self) -> None:
        ...

    def on_chunk_complete(self) -> None:
        ...

    def on_status(self) -> None:
        ...


class HttpRequestParser:
    protocol: Protocol

    def __init__(self, protocol: Protocol) -> None:
        ...

    def feed_data(self, data: bytes) -> None:
        ...

    def get_method(self) -> bytes:
        ...
